import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank
from langchain_core.prompts import MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from app.services.service_interface import GenericLLM

load_dotenv()


class IpExpertLLM(GenericLLM):
    def __init__(self, retriever, model, temperature=0):
        super().__init__(model=model, temperature=temperature, retriever=retriever)
        self.llm = ChatGoogleGenerativeAI(
            model=model,  # Or another Gemma-based Gemini model like "gemma-3-27b-it"
            reasoning_effort="none",
            google_api_key=os.getenv('GEMINI_API_KEY')

        )
        self.compressor = None
        self.query = None
        self.compression_retriever = None
        self.examples = [{"question": "What information does an applicant need to provide?"
                             , "answer": """An applicant is required to disclose the name, address and "
                                         nationality of the true and first inventor(s)"""},
                         {"question": "Who can be an 'assignee'?"
                             , "answer": """"Assignee" can be a natural person or legal person such as, a
registered company, small entity, startup, research organization, an
educational institute or the Government. Assignee includes assignee of an assignee also."""},
                         {"question": "What are the types of patent applications?"
                             , "answer": """1) Ordinary Application
                             2) Convention Application
                             3) PCT National Phase Application.
                             4) Divisional Application
                             5) Patent of Addition
                             """}

                         ]
        self.example_prompt = ChatPromptTemplate.from_messages([
            ("human", "{question}"),
            ("ai", "{answer}")
        ])

        self.few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=self.example_prompt,
            examples=self.examples
        )
        self.prompt = ChatPromptTemplate.from_messages([("system", """
        You are IP Expert, an AI Intellectual Property Laws Professor. You will be interacting with the user in a
        friendly manner and help them answer their Intellectual Property Laws queries.
        Use the following pieces of information to provide a concise answer to the question enclosed in <question> tags.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Do NOT make up information which you are unable to find in the context enclosed in <context> tags.
        If the question seems abstract and doesn't seem to specific, don't answer the question.
        You are supposed to answer only Intellectual Property Laws related queries. If user asks any question not related to Intellectual
        Property Laws, just say that you can't answer questions which are unrelated to Intellectual Property Laws, don't try to make up 
        an answer.
        Use the following format:
        Question:the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take,should be based on the information available in the context enclosed in <context> 
        tags.
        Action Input: the input to the action
        Observation: the result of the action
        Thought: I now know the final answer
        Answer: the final answer to the original input question
            <context>
            {context}
            </context>
            
            <question>
            {question}
            </question>
        
        The response should be friendly and well informed. Think through and provide a reasoning behind your thought.
        Think through on your reasoning before providing the response.
        
        Assistant:
        """), ("placeholder", "{chat_history}"), self.few_shot_prompt, ("human", "{question}")
                                                        ])
        self.prompt.input_variables = ["context", "question"]
        self.compressor = FlashrankRerank()
        self.retriever = retriever
        self.rag_chain = None
        self.history_chain = None

        self.contextualize_system_prompt = """
        Given a chat history and the latest user question
        which might reference context in the chat history,
        formulate a standalone question which can be understood
        without the chat history. Think through and try and find the context of the question from the chat history.
        Finding context of the question from the chat history as priority.
        Do NOT answer the question,
        just reformulate it if needed and otherwise return it as is.
        """

        self.history_aware_retriever = None
        self.chat_history = []

    @staticmethod
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def contextualized_question(self, ip: dict):
        if ip.get("chat_history"):
            return self.history_chain
        else:
            return ip["question"]

    def build_rag_chain(self):
        self.compression_retriever = ContextualCompressionRetriever(base_compressor=self.compressor,
                                                                    base_retriever=self.retriever)
        self.build_history_aware_rag_chain()
        self.rag_chain = (
                RunnablePassthrough.assign(
                    context=self.contextualized_question | self.compression_retriever | self.format_docs)
                | self.prompt
                | self.llm
                | StrOutputParser()
        )

    def build_history_aware_rag_chain(self):
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.contextualize_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{question}")
            ]
        )

        self.history_chain = contextualize_q_prompt | self.llm | StrOutputParser()

    def invoke_llm(self, query):
        self.query = query
        self.build_rag_chain()
        return self.rag_chain.invoke({"question": self.query, "chat_history": self.chat_history})
