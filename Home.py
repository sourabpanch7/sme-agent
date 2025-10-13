import logging
import warnings
from app.services.embedding_service import VectorStore, PdfEmbeder
from app.services.rag_service import IpRAG
from app.services.agent_service import IpQuizAgent
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()


class InteractIpExpert(PdfEmbeder, IpRAG, VectorStore, IpQuizAgent):
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

    def create_chat_info(self):
        embedding = self.create_embeddings(model=self.embedding_model)
        self.get_vector_store(embedding=embedding, milvus_uri=self.milvus_uri, target_collection=self.target_collection,
                              partition_key=self.partition_key)
        self.rag_obj = IpRAG(retriever=self.vectorstore)
        self.rag_obj.get_retrieved_document(partition_column=self.partition_key,
                                            search_key=self.search_key, top_k=5)
        self.agent = IpQuizAgent(retriever=self.rag_obj.relevant_doc, model="gemini-2.0-flash")

    def chat(self, query):
        rsp = self.agent.invoke_agent(query=query)
        rsp = rsp.strip()
        return rsp


if __name__ == "__main_":
    logging.getLogger().setLevel(level=logging.INFO)
    try:
        chat_obj = InteractIpExpert(milvus_uri="/Users/sourabpanchanan/PycharmProjects/SME_Agent/milvus_db.db",
                                    target_collection="ip_test", partition_key=None, search_key=None)
        chat_obj.create_chat_info()
        op = chat_obj.chat(query="Generate quiz on Indian IP Laws")
        print(op)

    except Exception as err_msg:
        logging.error(str(err_msg))
        raise err_msg

    finally:
        logging.info("DONE")
