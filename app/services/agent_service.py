from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate



retrieval_tool = Tool(
        name="document_retriever",
        func=retriever.invoke,
        description="Useful for retrieving information from the document store."
    )

tools = [retrieval_tool]


prompt = PromptTemplate.from_template("""
You are a helpful assistant. Answer the user's questions based on the provided context.
If you don't know the answer, say you don't know.
Question: {input}
Context: {agent_scratchpad}
""")

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

response = agent_executor.invoke({"input": "What is discussed in the document about X?"})
print(response["output"])