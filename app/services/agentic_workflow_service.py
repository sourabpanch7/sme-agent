import os
import re
import json
import logging
import uuid
from datetime import datetime, timezone
from typing_extensions import TypedDict
from typing import List, Annotated
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langchain_core.prompts import MessagesPlaceholder
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch
from langchain.retrievers import EnsembleRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_community.document_compressors import FlashrankRerank
from langchain.retrievers import ContextualCompressionRetriever
from app.models.schemas import QuestionValidator, QuizTopicValidator, WebSearchRequired, RelevantDocsExists, \
    GenerateContextualizedQuiz
from app.utils.utility import get_interim_retrievers, format_docs
from app.core.constants import EXAMPLES, RETRIEVER_PROMPT, HALLUCINATION_GRADER_PROMPT, ANSWER_GRADER_PROMPT, \
    QUESTION_VALIDATOR_PROMPT, QUIZ_VALIDATOR_PROMPT, QUESTION_ROUTER_PROMPT, QUIZ_ROUTER_PROMPT, \
    CONTEXTUALIZE_QUESTION_PROMPT, RELEVANT_DOC_CHECKER_PROMPT, MAIL_SUBJECT, MAIL_BODY, QUIZ_TYPE_EVALUATOR_PROMPT
from app.services.agent_service import IpQuizAgent
from app.services.service_interface import GenericAgentWorkflow

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    """

    messages: Annotated[list[AnyMessage], add_messages]
    generation: str
    generate_quiz: bool
    web_search_required: bool
    valid_question: bool
    valid_quiz_topic: bool
    generate_quiz: bool
    relevant_docs_exist: bool
    generate_contextualized_quiz: bool
    documents: List[str]


class IPAgenticWorkflow(GenericAgentWorkflow):
    def __init__(self, embedding, llm, agent_model="gemini-2.5-pro", weights=[0.7, 0.2, 0.1]):
        super().__init__()
        self.embedding = embedding
        self.retriever = EnsembleRetriever(
            retrievers=get_interim_retrievers(ip_embedding=embedding),
            weights=weights
        )
        self.agent = IpQuizAgent(retriever=self.retriever, model=agent_model)
        examples = EXAMPLES
        example_prompt = ChatPromptTemplate.from_messages([
            ("human", "{question}"),
            ("ai", "{answer}")
        ])
        self.compressor = FlashrankRerank()
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=examples
        )
        self.llm = llm
        self.expert_llm = ChatGoogleGenerativeAI(
            model=agent_model,
            reasoning_effort="none",
            google_api_key=os.getenv('GEMINI_API_KEY'))
        self.compression_retriever = ContextualCompressionRetriever(base_compressor=self.compressor,
                                                                    base_retriever=self.retriever)

        self.prompt = ChatPromptTemplate.from_messages([("system", RETRIEVER_PROMPT
                                                         ), ("placeholder", "{chat_history}"), few_shot_prompt,
                                                        ("human", "{question}")
                                                        ])
        self.prompt.input_variables = ["context", "question"]

        self.contextualize_system_prompt = CONTEXTUALIZE_QUESTION_PROMPT

        hallucination_grader_prompt = PromptTemplate(
            template=HALLUCINATION_GRADER_PROMPT,
            input_variables=["generation", "documents"],
        )

        self.hallucination_grader = hallucination_grader_prompt | self.llm | JsonOutputParser()

        answer_grader_prompt = PromptTemplate(
            template=ANSWER_GRADER_PROMPT,
            input_variables=["generation", "question"],
        )

        self.answer_grader = answer_grader_prompt | self.llm | JsonOutputParser()

        question_validator_prompt = PromptTemplate(template=QUESTION_VALIDATOR_PROMPT, input_variables=["question"])

        self.question_validator = question_validator_prompt | self.llm | JsonOutputParser(
            pydantic_object=QuestionValidator)

        quiz_topic_validator_prompt = PromptTemplate(template=QUIZ_VALIDATOR_PROMPT, input_variables=["question"])

        self.quiz_topic_validator = (quiz_topic_validator_prompt | self.llm
                                     | JsonOutputParser(pydantic_object=QuizTopicValidator))

        question_router_prompt = PromptTemplate(
            template=QUESTION_ROUTER_PROMPT,
            input_variables=["question", "documents"],
        )

        self.question_router = question_router_prompt | self.llm | JsonOutputParser(pydantic_object=WebSearchRequired)

        quiz_router_prompt = ChatPromptTemplate.from_messages(
            [("system", QUIZ_ROUTER_PROMPT), ("human", "{question}")])

        quiz_router_prompt.input_variables = ["question"]
        # State

        self.quiz_router = quiz_router_prompt | self.llm | JsonOutputParser()

        quiz_type_evaluator_prompt = PromptTemplate(
            template=QUIZ_TYPE_EVALUATOR_PROMPT,
            input_variables=["question", "documents"],
        )

        self.quiz_type_evaluator = quiz_type_evaluator_prompt | self.expert_llm | JsonOutputParser(
            pydantic_object=GenerateContextualizedQuiz)

        relevant_doc_checker_prompt = PromptTemplate(template=RELEVANT_DOC_CHECKER_PROMPT,
                                                     input_varaibles=["question", "documents"])

        self.relevant_doc_checker = relevant_doc_checker_prompt | self.llm | JsonOutputParser(
            pydantic_object=RelevantDocsExists)

        self.web_search_tool = TavilySearch(
            max_results=5,
            topic="general",
        )
        thread_id = uuid.uuid4()
        self.thread_id = str(thread_id)
        self.checkpointer = InMemorySaver()
        self.config = {"configurable": {"thread_id": self.thread_id}}
        self.workflow = None
        self.history_chain = None
        self.rag_chain = None
        self.history_aware_retriever = None
        self.chat_history = []

    def build_history_aware_rag_chain(self):
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.contextualize_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{question}")
            ]
        )

        self.history_chain = contextualize_q_prompt | self.llm | StrOutputParser()

    def build_rag_chain(self):
        self.compression_retriever = ContextualCompressionRetriever(base_compressor=self.compressor,
                                                                    base_retriever=self.retriever)
        self.build_history_aware_rag_chain()
        self.rag_chain = (
                RunnablePassthrough.assign(
                    context=self.contextualized_question | self.compression_retriever | format_docs)
                | self.prompt
                | self.llm
                | StrOutputParser()
        )

    def contextualized_question(self, ip: dict):
        if ip.get("chat_history") or ip.get("context"):
            return self.history_chain
        else:
            return ip["question"]

    def validate_question(self, state):
        logging.info("--VALIDATE QUESTION--")
        question = state["messages"][-1]
        question = question.content
        valid_question_flag = self.question_validator.invoke(question)
        return {**state, "valid_question": valid_question_flag.get('valid_question')}

    def validate_quiz_topic(self, state):
        logging.info("--VALIDATE QUIZ TOPIC--")
        question = state["messages"][-1]
        question = question.content
        valid_quiz_topic_flag = self.quiz_topic_validator.invoke({"question": question})
        return {**state, "valid_quiz_topic": valid_quiz_topic_flag.get('valid_quiz_topic')}

    @staticmethod
    def get_quiz_type(state):

        # documents = state["messages"][:-1]
        # question = state["messages"][-1]
        # question = question.content
        # generate_contextualized_quiz = self.quiz_type_evaluator.invoke({"question": question, "documents": documents})
        # return {**state,
        #         "generate_contextualized_quiz": generate_contextualized_quiz.get('generate_contextualized_quiz')}
        return state

    def retrieve(self, state):
        """
        Retrieve documents from vectorstore

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        logging.info("---RETRIEVE---")
        question = state["messages"][-1]
        question = question.content

        # Retrieval
        documents = self.retriever.invoke(question)
        documents = [doc.page_content for doc in documents]

        documents = state.get("documents", []) + state["messages"][:-1] + documents
        return {"documents": documents}

    def generate(self, state):
        """
        Generate answer using RAG on retrieved documents

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        logging.info("---GENERATE---")
        question = state["messages"][-1]
        question = question.content
        documents = state.get("documents", []) + state["messages"][:-1]
        # RAG generation
        self.build_rag_chain()
        generation = self.rag_chain.invoke({"chat_history": documents, "question": question})
        return {**state, "generation": generation}

    def web_search(self, state):
        """
        Web search based on the question

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Appended web results to documents
        """

        logging.info("---WEB SEARCH---")
        question = state["messages"][-1]
        question = question.content
        documents = state.get("documents", []) + state["messages"][:-1]

        # Web search
        docs = self.web_search_tool.invoke({"query": question})
        print(docs)
        web_results = "\n".join([d["content"] for d in docs["results"]])
        # web_results = Document(page_content=web_results)
        if documents is not None:
            documents.append(web_results)
        else:
            documents = [web_results]
        return {"documents": documents, "question": question}

    def route_question(self, state):
        """
        Route question to web search or RAG.

        Args:
            state (dict): The current graph state

        Returns:
            str: Next node to call
        """
        documents = state.get("documents", []) + state["messages"][:-1]
        question = state["messages"][-1]
        question = question.content
        is_web_search_required = self.question_router.invoke({"question": question, "documents": documents})
        return {**state, "web_search_required": is_web_search_required.get('web_search_required')}

    def grade_generation_v_documents_and_question(self, state):
        """
        Determines whether the generation is grounded in the document and answers question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Decision for next node to call
        """

        logging.info("---CHECK HALLUCINATIONS---")

        question = state["messages"][-1]
        question = question.content
        documents = state.get("documents", []) + state["messages"][:-1]
        generation = state["generation"]

        score = self.hallucination_grader.invoke(
            {"documents": documents, "generation": generation}
        )
        grade = score["score"]

        # Check hallucination
        if grade == "yes":
            logging.info("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
            # Check question-answering
            logging.info("---GRADE GENERATION vs QUESTION---")
            score = self.answer_grader.invoke({"question": question, "generation": generation})
            grade = score["score"]
            if grade == "yes":
                logging.info("---DECISION: GENERATION ADDRESSES QUESTION---")
                return "useful"
            else:
                logging.info("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
                return "not useful"
        else:
            logging.info("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
            return "not supported"

    def choose_initial_path(self, state):
        question = state["messages"][-1]

        is_generate_quiz = self.quiz_router.invoke({"question": question.content})
        return {**state, "generate_quiz": is_generate_quiz.get("generate_quiz", False)}

    def make_contextual_quiz(self, state):
        logging.info("---STARTING CONTEXTUAL QUIZ GENERATION---")
        question = state["messages"][-1]
        documents = state.get("documents", [])
        print(documents)
        rsp = self.agent.invoke_agent(query=question.content, documents=documents,
                                      thread_id=self.config.get("thread_id", "1234"))
        rsp = rsp.strip()
        return {**state, "generation": rsp}

    def make_quiz(self, state):
        logging.info("---STARTING QUIZ GENERATION---")
        question = state["messages"][-1]
        rsp = self.agent.invoke_agent(query=question.content, thread_id=self.config.get("thread_id", "1234"))
        rsp = rsp.strip()
        return {**state, "generation": rsp}

    def check_relevant_doc_exists(self, state):
        is_relevant_docs_exist = {}
        logging.info("---CHECK RELEVANT DOCUMENTS EXIST---")
        documents = state.get("documents", []) + state["messages"][:-1]
        question = state["messages"][-1]
        if documents:
            logging.info("---DOCUMENTS EXIST---")
            is_relevant_docs_exist = self.relevant_doc_checker.invoke({"question": question, "documents": documents})
            logging.info(is_relevant_docs_exist)
        return {**state, "relevant_docs_exist": is_relevant_docs_exist.get('relevant_docs_exist', False)}

    @staticmethod
    def send_email(data):
        """
        Tool to be used by LLM to send email to user with generated quiz PDF file
        """
        try:
            email_regex = r'[\w\.-]+@[\w\.-]+\.\w+'

            emails = []

            for msg in data["messages"]:
                found = re.findall(email_regex, msg.content)
                emails.extend(found)

            print(emails)

            logging.info("---Sending EMAIL---")
            subject = MAIL_SUBJECT
            body = MAIL_BODY
            for recipient_email in emails:
                msg = MIMEMultipart()
                msg['From'] = EMAIL_ADDRESS
                msg['To'] = recipient_email
                msg['Subject'] = subject

                msg.attach(MIMEText(body, 'plain'))
                script_dir = os.path.dirname(__file__)
                filename = '/'.join(script_dir.split("/")[:-2]) + '/' + "outputs/QUIZ.pdf"

                # Construct the full path using os.path.join for platform independence
                # filename = os.path.join(script_dir, relative_file_path)
                attachment = open(filename, "rb")
                attachment_name = filename.split("/")[-1]

                # instance of MIMEBase and named as p
                p = MIMEBase('application', 'octet-stream')

                # To change the payload into encoded form
                p.set_payload(attachment.read())
                encoders.encode_base64(p)

                p.add_header('Content-Disposition', "attachment; filename= %s" % attachment_name)

                # attach the instance 'p' to instance 'msg'
                msg.attach(p)

                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                    server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())

                logging.info(f"Email sent successfully to {recipient_email}")

        except Exception as err_msg:
            logging.error(f"Error sending mail:{err_msg}")
            raise err_msg
        return {"generation": "Email sent successfully to all recipients"}

    @staticmethod
    def generate_invalid_question_response(state):
        generation = "Answer:I can only answer questions related to Indian IP Laws."
        return {**state, "generation": generation}

    @staticmethod
    def generate_invalid_quiz_topic_response(state):
        generation = "Answer:I can only generate quizzes on topics related to Indian IP Laws."
        return {**state, "generation": generation}

    @staticmethod
    def is_valid_question(state):
        if state["valid_question"]:
            return "check_relevant_doc_exists"
        else:
            return "generate_invalid_question_response"

    @staticmethod
    def is_relevant_docs_exist(state):
        if state["relevant_docs_exist"]:
            return "generate"
        else:
            return "retrieve"

    @staticmethod
    def is_valid_quiz_topic(state):
        if state["valid_quiz_topic"]:
            return "get_quiz_type"
        else:
            return "generate_invalid_quiz_topic_response"

    @staticmethod
    def is_web_search_required(state):
        if state["web_search_required"]:
            return "web_search"
        else:
            return "generate"

    @staticmethod
    def should_generate_quiz(state):
        question = state["messages"][-1]
        if state["generate_quiz"]:
            return "validate_quiz_topic"
        else:
            if "send" in question.content.lower() or "email" in question.content.lower() or "@" in question.content.lower():
                return "send_email"
            else:
                return "validate_question"

    @staticmethod
    def is_quiz_contextual(state):
        logging.info("--VALIDATE CONTEXTUALIZED QUIZ GENERATION--")
        documents = state.get("documents", []) + state.get("messages")[:-1]
        if documents and state.get("generate_quiz"):
            return "make_contextual_quiz"
        # if state.get("generate_contextualized_quiz",False):
        #     return "make_contextual_quiz"
        else:
            return "make_quiz"

    @staticmethod
    def interact(response, user_id="", message_id=""):
        docs = response.get("documents", [])
        rsp = response.get('generation', '')
        try:
            rsp = rsp.split("Answer:", 1)[1]

        except IndexError:
            pass
        rsp = rsp.strip()
        rsp = rsp.replace("\n", "")
        rsp = json.dumps(rsp)
        text = json.loads(rsp)
        op = {"user_id": user_id,
              "role": "assistant",
              "message_id": message_id,
              "timestamp": datetime.now(timezone.utc).isoformat(),
              "content": [
                  {"text": text,
                   "source_docs": docs
                   }
              ]
              }
        return op

    def create_workflow(self):
        self.workflow = StateGraph(GraphState)

        self.workflow.add_node("choose_initial_path", self.choose_initial_path)
        self.workflow.add_node("generate_invalid_question_response", self.generate_invalid_question_response)
        self.workflow.add_node("retrieve", self.retrieve)
        self.workflow.add_node("route_question", self.route_question)
        self.workflow.add_node("validate_question", self.validate_question)
        self.workflow.add_node("validate_quiz_topic", self.validate_quiz_topic)
        self.workflow.add_node("web_search", self.web_search)
        self.workflow.add_node("generate", self.generate)
        self.workflow.add_node("make_quiz", self.make_quiz)
        self.workflow.add_node("make_contextual_quiz", self.make_contextual_quiz)
        self.workflow.add_node("generate_invalid_quiz_topic_response", self.generate_invalid_quiz_topic_response)
        self.workflow.add_node("get_quiz_type", self.get_quiz_type)
        self.workflow.add_node("check_relevant_doc_exists", self.check_relevant_doc_exists)
        self.workflow.add_node("send_email", self.send_email)

        self.workflow.set_entry_point("choose_initial_path")
        self.workflow.add_conditional_edges("choose_initial_path",
                                            self.should_generate_quiz,
                                            {"validate_question": "validate_question",
                                             "validate_quiz_topic": "validate_quiz_topic",
                                             "send_email": "send_email"
                                             })
        self.workflow.add_edge("send_email", END)

        self.workflow.add_conditional_edges("validate_quiz_topic",
                                            self.is_valid_quiz_topic,
                                            {
                                                "generate_invalid_quiz_topic_response":
                                                    "generate_invalid_quiz_topic_response",
                                                "get_quiz_type": "get_quiz_type"})
        self.workflow.add_conditional_edges("get_quiz_type",
                                            self.is_quiz_contextual,
                                            {"make_contextual_quiz": "make_contextual_quiz",
                                             "make_quiz": "make_quiz"
                                             })

        self.workflow.add_edge("make_contextual_quiz", END)

        self.workflow.add_edge("make_quiz", END)

        self.workflow.add_conditional_edges("validate_question",
                                            self.is_valid_question,
                                            {
                                                "generate_invalid_question_response":
                                                    "generate_invalid_question_response",
                                                "check_relevant_doc_exists": "check_relevant_doc_exists"
                                            }
                                            )
        self.workflow.add_conditional_edges("check_relevant_doc_exists",
                                            self.is_relevant_docs_exist,
                                            {"retrieve": "retrieve", "generate": "generate"})
        self.workflow.add_edge("generate_invalid_question_response", END)
        self.workflow.add_edge("retrieve", "route_question")
        self.workflow.add_conditional_edges("route_question",
                                            self.is_web_search_required,
                                            {"web_search": "web_search", "generate": "generate"})
        self.workflow.add_edge("web_search", "generate")
        self.workflow.add_conditional_edges(
            "generate",
            self.grade_generation_v_documents_and_question,
            {
                "useful": END,
                "not useful": "web_search",
                "not supported": END
            },
        )

    def compile_workflow(self):
        # Compile
        self.create_workflow()
        return self.workflow.compile(checkpointer=self.checkpointer)

    def end_langgraph_session(self):
        # This deletes all checkpoints associated with the given thread_id
        self.checkpointer.delete_thread(self.thread_id)
        print(f"Session/thread {self.thread_id} state has been cleared from the checkpointer.")
