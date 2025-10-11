import logging
import warnings
from langchain_core.messages import AIMessage, HumanMessage
from app.services.embedding_service import VectorStore, PdfEmbeder
from app.services.rag_service import IpRAG
from app.services.llm_service import IpExpertLLM
from app.services.agent_service import IpAgent
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()


# from fastapi import FastAPI
# app = FastAPI()


class InteractIpExpert(PdfEmbeder, IpRAG, IpExpertLLM, VectorStore,IpAgent):
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
        # self.llm_obj = IpExpertLLM(retriever=self.rag_obj.relevant_doc, model="gemini-2.5-flash")
        self.agent = IpAgent(retriever=self.rag_obj.relevant_doc,model="gemini-2.0-flash")

    def chat(self, query):
        rsp = self.agent.invoke_agent(query=query)
        # print(rsp)
        # try:
        #     rsp = rsp.split("Answer:", 1)[1]
        #
        # except IndexError:
        #     pass
        rsp = rsp.strip()
        rsp = rsp.replace("\n", "")
        # logging.info(rsp)
        # self.llm_obj.chat_history.extend([HumanMessage(content=query), AIMessage(content=rsp)])
        resp_dict = {"IP_expert_response": rsp}
        return resp_dict


# items_db = {}
# item_id_counter = 0
#
#
# @app.get("/items/")
# async def read_all_items():
#     """
#     Retrieves all items in the database.
#     """
#     return items_db
#
#
# @app.post("/items/")
# async def create_item(item_data):
#     global item_id_counter
#     item_id_counter += 1
#     items_db[item_id_counter] = item_data
#     return {"message": "Item created successfully", "item_id": item_id_counter, "item": item_data}
#
#
# @app.get("/items/{item_id}")
# async def read_item(item_id: int):
#     if item_id in items_db:
#         return items_db[item_id]
#     else:
#         return {"message": "Item not found"}

#
#
if __name__ == "__main__":
    logging.getLogger().setLevel(level=logging.INFO)
    try:
        chat_obj = InteractIpExpert(milvus_uri="/Users/sourabpanchanan/PycharmProjects/SME_Agent/milvus_db.db",
                                    target_collection="ip_test", partition_key=None, search_key=None)
        chat_obj.create_chat_info()
        op = chat_obj.chat(query="What's an Ordinary Patent Application?")
        logging.info(op)
    except Exception as err_msg:
        logging.error(err_msg)
        raise err_msg
    finally:
        logging.info("DONE")
