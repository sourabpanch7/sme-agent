import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate


class IpQuizAgent:
    def __init__(self, retriever, model):
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
        3. Present the quiz to the user. 
        You have access to the following tools:

        {tools}

        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat 5 times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        Begin!

        Question: {input}
        Thought:{agent_scratchpad}
        """)
        self.retrieval_tool = None
        self.agent_executor = None
        self.generate_quiz_tool = None
        self.tools = []

    def generate_quiz(self, docs):
        # Logic to prompt LLM with document_content to generate quiz questions
        llm = self.llm  # or your preferred LLM
        prompt = f"Generate 2 multiple-choice quiz questions from the following text:\n\n{docs}"
        quiz = llm.invoke(prompt)
        return quiz.content

    def create_tools(self):
        self.retrieval_tool = Tool(
            name="document_retriever",
            func=self.retriever.invoke,
            description="Useful for retrieving information from the document store."
        )
        self.generate_quiz_tool = Tool(
            name="generate_quiz",
            func=self.generate_quiz,
            description="Useful for generating quiz questions from provided document content."
        )

        self.tools.append(self.retrieval_tool)

    def create_agent(self):
        agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.tools, verbose=False,
                                                                 handle_parsing_errors=True)

    def invoke_agent(self, query):
        self.create_tools()
        self.create_agent()
        response = self.agent_executor.invoke({"input": query})
        return response["output"]
