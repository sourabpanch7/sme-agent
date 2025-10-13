import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain.agents.format_scratchpad.tools import format_to_tool_messages
from langchain.agents.output_parsers.tools import ToolsAgentOutputParser
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


class IpQuizAgent:
    def __init__(self, retriever, model):
        self.retriever = retriever
        self.llm = ChatGoogleGenerativeAI(
            model=model,  # Or another Gemma-based Gemini model like "gemma-3-27b-it"
            reasoning_effort="none",
            google_api_key=os.getenv('GEMINI_API_KEY')

        )
        self.prompt = ChatPromptTemplate.from_messages([("system", """"
        You are an AI assistant designed to create quizzes from documents related to Indian Intellectual Property Laws.
        When a user asks for a quiz on a specific topic, you should:
        1. Use the 'document_retriever' tool to find relevant information in the vector database.
        2. Use the 'generate_quiz' tool to create quiz questions from the retrieved content.
        3. Present the quiz to the user. 

        Use the following format:
        
        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of ['document_retriever','generate_quiz']
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat 1 time)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question
        
        Begin!
        
        Question: {input}
        Thought:{agent_scratchpad}
        """), ("placeholder", "{chat_history}"),
                                                        ("human", "{input}"),
                                                        ("placeholder", "{agent_scratchpad}")])
        self.retrieval_tool = None
        self.agent_with_chat_history = None
        self.generate_quiz_tool = None
        self.tools = []

    def generate_quiz(self, docs):
        # Logic to prompt LLM with document_content to generate quiz questions
        llm = self.llm  # or your preferred LLM
        prompt = (f"""Generate 2 multiple-choice quiz questions from the following text enclosed in the 
                    <text> tags".
                    Do NOT provide answers.
                    Do NOT provide questions that you are enable to find in the documents enclosed in the <text> tags.
                    Turn down such requests, politely.
                    You can create the test at EASY, MEDIUM or HARD difficulty.
                    By default create a MEDIUM difficulty quiz.
                   <text> 
                  :\n\n{docs}
                  </text>

""")
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
        llm_with_tools = self.llm.bind_tools(self.tools, tool_choice=True)
        agent = (
                RunnablePassthrough.assign(agent_scratchpad=lambda x: format_to_tool_messages(x["intermediate_steps"]))
                | self.prompt
                | llm_with_tools
                | ToolsAgentOutputParser()
        )

        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.tools)

        message_history = ChatMessageHistory()
        self.agent_with_chat_history = RunnableWithMessageHistory(
            runnable=agent_executor,  # type: ignore[arg-type]
            get_session_history=lambda _: message_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def invoke_agent(self, query):
        self.create_tools()
        self.create_agent()
        response = self.agent_with_chat_history.invoke({"input": query},
                                                       {"configurable": {"session_id": "NA"}})
        print(response["output"])
        return response["output"]
