from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from app.services.service_interface import GenericLLM


class IpExpertLLM(GenericLLM):
    def __init__(self, retriever, model, temperature=0):
        super().__init__(model=model, temperature=temperature, retriever=retriever)
        self.llm = model
        self.compressor = None
        self.query = None
        self.compression_retriever = None
        self.examples = [{"question": ""
                             , "answer": ""}]
        self.example_prompt = ChatPromptTemplate.from_messages([
            ("human", "{question}"),
            ("ai", "{answer}")
        ])

        self.few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=self.example_prompt,
            examples=self.examples
        )
        self.prompt = ChatPromptTemplate.from_messages([("system", """
        Question:
        Thought:
        Action:
        Action Input:
        Observation:
        Thought:
        Answer:
        Assistant:
        """), ("placeholder", "{chat_history}"), self.few_shot_prompt, ("human", "{question}")
                                                        ])
        self.prompt.input_variables = ["context", "question"]
        self.compressor = FlashrankRerank()
        self.retriever = retriever
        self.rag_chain = None
        self.history_chain = None

        self.contextualize_system_prompt = """
        Given a chat history...
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
