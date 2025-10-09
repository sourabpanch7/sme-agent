from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate


class IpAgent:
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self.prompt = PromptTemplate.from_template("""
        You are a helpful assistant. Answer the user's questions based on the provided context.
        If you don't know the answer, say you don't know.
        Question: {input}
        Context: {agent_scratchpad}
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
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def invoke_agent(self, query):
        response = self.agent_executor.invoke({"input": query})
        return response["output"]
