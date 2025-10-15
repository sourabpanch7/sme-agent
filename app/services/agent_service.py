import os
import json
from fpdf import FPDF
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.models.base import Quiz
from app.services.service_interface import GenericAgent

load_dotenv()


class IpQuizAgent(GenericAgent):
    def __init__(self, retriever, model):
        super().__init__()
        self.retriever = retriever
        self.llm = ChatGoogleGenerativeAI(
            model=model,  # Or another Gemma-based Gemini model like "gemma-3-27b-it"
            reasoning_effort="none",
            google_api_key=os.getenv('GEMINI_API_KEY')

        )
        self.prompt = PromptTemplate.from_template("""
        You are an AI assistant designed to create quizzes from documents.
        When a user asks for a quiz on a specific topic, you should:
        1. Use the 'document_retriever' tool to find relevant information in the vector database.
        2. Use the 'generate_quiz' tool to create quiz questions from the retrieved content.
        3. Use 'create_pdf' to create PDF of the generated questions and store them in a file.
        4. Present the quiz to the user.
        You have access to the following tools:

        {tools}

        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat 3 times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        Begin!

        Question: {input}
        Thought:{agent_scratchpad}
        """)
        self.retrieval_tool = None
        self.agent_executor = None
        self.generate_quiz_tool = None
        self.write_as_pdf_tool = None
        self.tools = []

    @staticmethod
    def write_to_pdf(text_content,
                     output_filename="/Users/sourabpanchanan/PycharmProjects/SME_Agent/outputs/quiz.pdf"):
        """
           Tool that can be used by the LLM to PDF from the  input text_content.
        """
        text_content = text_content.replace("'", '"').replace('\n', '\\n')
        text_content = json.loads(text_content)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        # Split the text into lines and add each line to the PDF
        for key, value in text_content.items():
            pdf.cell(0, 10, txt=key, ln=True)
            for line in value.split('\n'):
                pdf.cell(0, 10, txt=line, ln=True)  # 0 for full width, 10 for line height, ln=True for new line

        pdf.output(output_filename)

    def generate_quiz(self, docs, num_questions=2):
        """
           Tool that can be used by the LLM to generate quiz questions with input document_content.
        """
        llm = self.llm
        parser = JsonOutputParser(pydantic_object=Quiz)
        prompt = PromptTemplate(template="""Generate {num_questions} distinct multiple-choice quiz questions on Indian 
        Intellectual Property Laws from the docs and return it as JSON object.\n{format_instructions}\n.\n{docs}\n.
        Do NOT make up questions that you can't make form the provided docs.
        Do NOT make up information that you can't find in the provided docs.
        If you are unable to make questions from the provided docs, just make Questions = NA and the Answer_Key = NA.
            """,
                                input_variables=["docs", "num_questions"],
                                partial_variables={"format_instructions": parser.get_format_instructions()},
                                )

        chain = prompt | llm | parser

        quiz = chain.invoke({"docs": docs, "num_questions": num_questions})
        return quiz

    def create_tools(self):
        self.retrieval_tool = Tool(
            name="document_retriever",
            func=self.retriever.invoke,
            description="Useful for retrieving information from the document store."
        )
        self.generate_quiz_tool = Tool(
            name="generate_quiz",
            func=self.generate_quiz,
            description="Useful for generating multiple-choice quiz questions from provided document content."
        )
        self.write_as_pdf_tool = Tool(
            name="create_pdf",
            func=self.write_to_pdf,
            description="Useful for generating quiz questions from provided document content."
        )

        self.tools.extend([self.retrieval_tool, self.generate_quiz_tool, self.write_as_pdf_tool])

    def create_agent(self):
        agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.tools, verbose=False,
                                                                 handle_parsing_errors=True)

    def invoke_agent(self, query):
        self.create_tools()
        self.create_agent()
        response = self.agent_executor.invoke({"input": query})
        return response["output"]
