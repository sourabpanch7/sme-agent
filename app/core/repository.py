import warnings
from datetime import datetime,timezone
import json
from langchain_core.messages import AIMessage, HumanMessage
from app.services.llm_service import IpExpertLLM
from app.services.embedding_service import VectorStore, PdfEmbeder
from app.services.rag_service import IpRAG
from app.services.agent_service import IpQuizAgent
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()


class IpQuizGenerator(PdfEmbeder, IpRAG, VectorStore, IpQuizAgent):
    def __init__(self, partition_key, search_key, milvus_uri, target_collection,
                 embedding_model="models/text-embedding-004"):
        super().__init__()
        self.partition_key = partition_key
        self.search_key = search_key
        self.embedding_model = embedding_model
        self.milvus_uri = milvus_uri
        self.target_collection = target_collection
        self.vectorstore = None
        self.rag_obj = None
        self.agent = None

    def create_quiz_info(self):
        embedding = self.create_embeddings(model=self.embedding_model)
        self.get_vector_store(embedding=embedding, milvus_uri=self.milvus_uri, target_collection=self.target_collection,
                              partition_key=self.partition_key)
        self.rag_obj = IpRAG(retriever=self.vectorstore)
        self.rag_obj.get_retrieved_document(partition_column=self.partition_key,
                                            search_key=self.search_key, top_k=5)
        self.agent = IpQuizAgent(retriever=self.rag_obj.relevant_doc, model="gemini-2.5-flash")

    def create_quiz(self, query):
        rsp = self.agent.invoke_agent(query=query)
        rsp = rsp.strip()
        return rsp


class InteractIpExpert(PdfEmbeder, IpRAG, IpExpertLLM, VectorStore):
    def __init__(self, partition_key, search_key, milvus_uri, target_collection,
                 embedding_model="models/text-embedding-004"):
        super().__init__()
        self.partition_key = partition_key
        self.search_key = search_key
        self.embedding_model = embedding_model
        self.milvus_uri = milvus_uri
        self.target_collection = target_collection
        self.vectorstore = None
        self.rag_obj = None
        self.llm_obj = None

    def create_chat_info(self):
        embedding = self.create_embeddings(model=self.embedding_model)
        self.get_vector_store(embedding=embedding, milvus_uri=self.milvus_uri, target_collection=self.target_collection,
                              partition_key=self.partition_key)
        self.rag_obj = IpRAG(retriever=self.vectorstore)
        self.rag_obj.get_retrieved_document(partition_column=self.partition_key,
                                            search_key=self.search_key, top_k=5)
        self.llm_obj = IpExpertLLM(retriever=self.rag_obj.relevant_doc, model="gemini-2.0-flash")

    def interact(self, query, user_id="", message_id=""):
        rsp = self.llm_obj.invoke_llm(query=query)
        try:
            rsp = rsp.split("Answer:", 1)[1]

        except IndexError:
            pass
        rsp = rsp.strip()
        rsp = rsp.replace("\n", "")
        self.llm_obj.chat_history.extend([HumanMessage(content=query), AIMessage(content=rsp)])
        rsp = json.dumps(rsp)
        text = json.loads(rsp)
        return {"user_id": user_id,
                "role": "assistant",
                "message_id": message_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "content": [
                    {"text": text,
                     "source_docs": []
                     }
                ]
                }
