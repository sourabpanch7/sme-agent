import logging
import warnings
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from app.services.embedding_service import VectorStore, PdfEmbeder
from app.services.rag_service import IpRAG
from app.services.llm_service import IpExpertLLM
from app.services.agent_service import IpQuizAgent
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()


# from fastapi import FastAPI
# app = FastAPI()


class InteractIpExpert(PdfEmbeder, IpRAG, IpExpertLLM, VectorStore, IpQuizAgent):
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
        # self.llm_obj=None
        self.agent = None

    def create_chat_info(self):
        embedding = self.create_embeddings(model=self.embedding_model)
        self.get_vector_store(embedding=embedding, milvus_uri=self.milvus_uri, target_collection=self.target_collection,
                              partition_key=self.partition_key)
        self.rag_obj = IpRAG(retriever=self.vectorstore)
        self.rag_obj.get_retrieved_document(partition_column=self.partition_key,
                                            search_key=self.search_key, top_k=5)
        self.llm_obj = IpExpertLLM(retriever=self.rag_obj.relevant_doc, model="gemini-2.0-flash")
        # self.agent = IpQuizAgent(retriever=self.rag_obj.relevant_doc,model="gemini-2.0-flash")

    def chat(self, query):
        # rsp = self.agent.invoke_agent(query=query)
        rsp = self.llm_obj.invoke_llm(query=query)
        try:
            rsp = rsp.split("Answer:", 1)[1]

        except IndexError:
            pass
        rsp = rsp.strip()
        rsp = rsp.replace("\n", "")
        logging.info(rsp)
        self.llm_obj.chat_history.extend([HumanMessage(content=query), AIMessage(content=rsp)])
        resp_dict = {"IP_expert_response": rsp}
        return resp_dict


st.set_page_config(
    layout="wide",
    page_title="Indian Intellectual Property Laws Tutor - Home",
    initial_sidebar_state="collapsed"
)

chat_obj = InteractIpExpert(milvus_uri="/Users/sourabpanchanan/PycharmProjects/SME_Agent/milvus_db.db",
                            target_collection="ip_test", partition_key=None, search_key=None)
chat_obj.create_chat_info()

st.header("""Intellectual Property Tutor: 
Gen-AI powered Tutor for Indian Intellectual Property Laws Tutor""")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": """
    Hello !! I am your tutor for Indian Intellectual Property Laws. Hope you are doing good today!!
    """}
        , {"role": "assistant", "content": """
    Let's try to talk about one topic at a time.
    If you want to talk about something new, just say bye, we can restart our conversation"""}
        , {"role": "assistant", "content": """
    Whenever you want to stop our conversation, just say bye!"""}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_question := st.chat_input("What do you want to lear about today?"):
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        if "bye" in user_question.lower():
            st.write_stream(["Bye! have a great day ahead!!"])
            st.session_state.clear()

        else:
            try:
                op = chat_obj.chat(query=user_question)
                response = st.write_stream([op.get("IP_expert_response", "Sorry,I'm unable to answer that right now.")])
            except Exception:
                response = st.write_stream(["Unable to answer right now. Please try after some time."])

            st.session_state.messages.append({"role": "assistant", "content": response})
