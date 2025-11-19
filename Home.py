import warnings
import uuid
import logging
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from app.services.llm_service import LLM
from app.services.embedding_service import Embedding
from app.services.agentic_workflow_service import IPAgenticWorkflow

logging.getLogger().setLevel(level=logging.INFO)

warnings.filterwarnings("ignore")
load_dotenv()

llm_obj = LLM(model_name="gemini-2.5-flash")
embedding_obj = Embedding()
flow_obj = IPAgenticWorkflow(llm=llm_obj.get_llm(),
                             embedding=embedding_obj.create_embeddings(embedding_model="models/text-embedding-004"))
flow = flow_obj.compile_workflow()

my_uuid = uuid.uuid4()

# Convert the UUID object to a string (hexadecimal representation without dashes)
user_id = f"user_id_{my_uuid.hex}"
msg_id = 0

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

if user_question := st.chat_input("What do you want to learn about today?"):
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        if "bye" in user_question.lower() or "exit" in user_question.lower() or "quit" in user_question.lower():
            st.write_stream(["Bye! have a great day ahead!!"])
            flow_obj.end_langgraph_session()
            st.session_state.clear()

        else:
            msg_id += 1
            message_id = str(msg_id).zfill(4)

            try:
                for event in flow.stream(
                        {"messages": [
                            {"role": "user",
                             "content": user_question}]},
                        flow_obj.config,
                        stream_mode="values"
                ):
                    response = flow_obj.interact(response=event, user_id=user_id, message_id=message_id)
                    txt = response["content"][0]["text"]
                    flow_obj.chat_history.extend(
                        [HumanMessage(user_question), AIMessage(txt)])

                response = st.write_stream([txt])
            except Exception as err_msg:
                logging.error(str(err_msg))
                response = st.write_stream(["Unable to process request right now. Please try after some time."])

            st.session_state.messages.append({"role": "assistant", "content": txt})
