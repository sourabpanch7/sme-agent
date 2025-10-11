import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate


class IpAgent:
    def __init__(self, retriever, model):
        self.retriever = retriever
        self.llm = ChatGoogleGenerativeAI(
            model=model,  # Or another Gemma-based Gemini model like "gemma-3-27b-it"
            reasoning_effort="none",
            google_api_key=os.getenv('GEMINI_API_KEY')

        )
        self.prompt = PromptTemplate.from_template("""
        Answer the following questions as best you can. You have access to the following tools:

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
        self.tools = []

    def create_retrieval_tool(self):
        self.retrieval_tool = Tool(
            name="document_retriever",
            func=self.retriever.invoke,
            description="Useful for retrieving information from the document store."
        )

        self.tools.append(self.retrieval_tool)

    def create_agent(self):
        agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.tools, verbose=False,
                                                                 handle_parsing_errors=True)

    def invoke_agent(self, query):
        self.create_retrieval_tool()
        self.create_agent()
        response = self.agent_executor.invoke({"input": query})
        return response["output"]
