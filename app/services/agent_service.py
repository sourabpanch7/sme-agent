import json
import os
import warnings
import ast
from fpdf import FPDF
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.services.service_interface import GenericAgent
from app.models.schemas import Quiz, NumQuestions, DifficultyLevel
from app.core.constants import QUIZ_AGENT_PROMPT, NUM_QUESTIONS_IDENTIFIER_PROMPT, DIFFICULTY_LEVEL_IDENTIFIER_PROMPT, \
    GENERATE_QUIZ_PROMPT

warnings.filterwarnings("ignore")
load_dotenv()


class IpQuizAgent(GenericAgent):
    def __init__(self, retriever, model):
        super().__init__()
        self.retriever = retriever
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            reasoning_effort="none",
            google_api_key=os.getenv('GEMINI_API_KEY')

        )
        self.prompt = PromptTemplate.from_template(template=QUIZ_AGENT_PROMPT)
        self.retrieval_tool = None
        self.agent_executor = None
        self.generate_quiz_tool = None
        self.write_as_pdf_tool = None
        self.difficulty_level = None
        self.num_questions = None
        self.tools = []
        self.create_tools()
        self.create_agent()

    @staticmethod
    def write_to_pdf(text_content):
        """
           Tool that can be used by the LLM to generate PDF from the  input text_content.
        """
        print(text_content)
        print(type(text_content))

        script_dir = os.path.dirname(__file__)
        op_file = '/'.join(script_dir.split("/")[:-2]) + '/' + "outputs/QUIZ.pdf"
        try:
            text_content = ast.literal_eval(text_content)
        except SyntaxError:
            text_content = text_content.split("text_content=")[1]
            text_content = ast.literal_eval(text_content)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=6)
        if 'output_filename' in text_content:
            del text_content['output_filename']
        # Split the text into lines and add each line to the PDF
        for key, value in text_content.items():
            if key == "answer_key":
                pdf.cell(0, 10, txt=key, ln=True)
            for line in value.split('\n'):
                pdf.cell(0, 10, txt=line, ln=True)  # 0 for full width, 10 for line height, ln=True for new line
        pdf.output(op_file)

    def identify_num_questions(self, query):
        """
        Tool that can be used by LLM to identify how many questions should be generated as per the given query.
        :param query:
        :return: number of questions
        """
        llm = self.llm
        prompt = PromptTemplate(template=NUM_QUESTIONS_IDENTIFIER_PROMPT, input_variables=["input"])

        chain = prompt | llm | JsonOutputParser(pydantic_object=NumQuestions)

        num_questions = chain.invoke({"input": query})

        return num_questions.get("num_questions", 2)

    def identify_difficulty_level(self, query):
        """
        Tool that can be used by LLM to access difficulty level of questions to be generated as per given query
        :param query:
        :return: Difficulty level of questions to be generated
        """
        llm = self.llm
        prompt = PromptTemplate(template=DIFFICULTY_LEVEL_IDENTIFIER_PROMPT, input_variables=["input"]
                                )

        chain = prompt | llm | JsonOutputParser(pydantic_obj=DifficultyLevel)

        difficulty_level = chain.invoke({"input": query})
        return difficulty_level.get("difficulty_level", 'MEDIUM')

    def generate_quiz(self, docs, num_questions=5, difficulty_level='MEDIUM'):
        """
           Tool that can be used by the LLM to generate quiz questions with input document_content along with num_questions
           and difficulty_level
        """
        llm = self.llm

        prompt = PromptTemplate(template=GENERATE_QUIZ_PROMPT,
                                input_variables=["docs", "num_questions", "difficulty_level"],
                                )

        chain = prompt | llm | JsonOutputParser(pydantic_object=Quiz)

        quiz = chain.invoke({"docs": docs, "num_questions": num_questions, "difficulty_level": difficulty_level})
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
            description="Useful for generating multiple-choice quiz questions from provided document content.",
        )
        self.write_as_pdf_tool = Tool(
            name="create_pdf",
            func=self.write_to_pdf,
            description="Useful for generating pdf from provided quiz questions."
        )

        self.tools.extend(
            [self.retrieval_tool, self.generate_quiz_tool, self.write_as_pdf_tool])

    def create_agent(self):
        agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.tools, verbose=False,
                                                                 handle_parsing_errors=True)

    def invoke_agent(self, query, thread_id='1234', documents=None):

        self.num_questions = self.identify_num_questions(query=query)
        self.difficulty_level = self.identify_difficulty_level(query=query)
        if documents:
            response = self.agent_executor.invoke(
                {"input": query, "docs": documents, "num_questions": self.num_questions,
                 "difficulty_level": self.difficulty_level, "thread_id": thread_id})
        else:
            response = self.agent_executor.invoke({"input": query, "num_questions": self.num_questions,
                                                   "difficulty_level": self.difficulty_level, "thread_id": thread_id})
        return response["output"]
