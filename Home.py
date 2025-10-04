import logging
from langchain_core.messages import AIMessage, HumanMessage
from app.service.rag_service import IpRAG
from app.service.llm_service import IpExpertLLM


class InteractIpExpert(IpRAG, IpExpertLLM):
    def __init__(self, milvus_uri, collection, partition_key, search_key):
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
        self.llm_obj.chat_histort.extend([HumanMessage(content=query), AIMessage(content=rsp)])
        return {"IP_expert_response": rsp}


if __name__ == "__main__":
    try:
        chat_obj = InteractIpExpert(milvus_uri="", collection="", partition_key="", search_key="")
        chat_obj.create_chat_info()
        op = chat_obj.chat(query="")
        logging.info(op)
    except Exception as err_msg:
        logging.error(err_msg)
        raise err_msg
    finally:
        logging.info("DONE")