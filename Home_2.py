import logging
from langchain_core.messages import AIMessage, HumanMessage
from app.services.rag_service import IpRAG
from app.services.llm_service import IpExpertLLM
from fastapi import FastAPI

app = FastAPI()


class InteractIpExpert(IpRAG, IpExpertLLM):
    def __init__(self, partition_key, search_key):
        super().__init__()
        self.partition_key = partition_key
        self.search_key = search_key
        self.vectorstore = None
        self.rag_obj = None
        self.llm_obj = None

    def create_chat_info(self):
        self.rag_obj = IpRAG(retriever=self.vectorstore)
        self.rag_obj.get_retrieved_document(partition_column=self.partition_key,
                                            search_key=self.search_key, top_k=5)
        self.llm_obj = IpExpertLLM(retriever=self.rag_obj.relevant_doc, model="")

    def chat(self, query):
        rsp = self.llm_obj.invoke_llm(query=query)
        try:
            rsp = rsp.split("Answer:", 1)[1]

        except IndexError:
            pass
        rsp = rsp.strip()
        rsp = rsp.split(".")[0]
        logging.info(rsp)
        self.llm_obj.chat_history.extend([HumanMessage(content=query), AIMessage(content=rsp)])
        return {"IP_expert_response": rsp}


items_db = {}
item_id_counter = 0


@app.get("/items/")
async def read_all_items():
    """
    Retrieves all items in the database.
    """
    return items_db


@app.post("/items/")
async def create_item(item_data):
    global item_id_counter
    item_id_counter += 1
    items_db[item_id_counter] = item_data
    return {"message": "Item created successfully", "item_id": item_id_counter, "item": item_data}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id in items_db:
        return items_db[item_id]
    else:
        return {"message": "Item not found"}

#
#
# if __name__ == "__main__":
#     try:
#         chat_obj = InteractIpExpert(milvus_uri="", collection="", partition_key="", search_key="")
#         chat_obj.create_chat_info()
#         op = chat_obj.chat(query="")
#         logging.info(op)
#     except Exception as err_msg:
#         logging.error(err_msg)
#         raise err_msg
#     finally:
#         logging.info("DONE")
