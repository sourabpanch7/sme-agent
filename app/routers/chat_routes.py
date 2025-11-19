import logging
from fastapi import APIRouter
from app.models.schemas import ChatResponse, ChatRequest
from app.services.llm_service import LLM
from langchain_core.messages import AIMessage, HumanMessage
from app.services.embedding_service import Embedding
from app.services.agentic_workflow_service import IPAgenticWorkflow

logging.getLogger().setLevel(level=logging.INFO)

router = APIRouter(prefix="/chat", tags=["chat"])
llm_obj = LLM(model_name="gemini-2.0-flash")
embedding_obj = Embedding()
flow_obj = IPAgenticWorkflow(llm=llm_obj.get_llm(),
                             embedding=embedding_obj.create_embeddings(embedding_model="models/text-embedding-004"))
flow = flow_obj.compile_workflow()


def generate_response(query, user_id, message_id):
    response = {}
    if "bye" in query.lower() or "exit" in query.lower() or "quit" in query.lower():
        resp = {"generation": "Bye! have a great day ahead!!"}
        response = flow_obj.interact(response=resp, user_id=user_id, message_id=message_id)
        flow_obj.end_langgraph_session()
    else:
        for event in flow.stream(
                {"messages": [
                    {"role": "user",
                     "content": query}]},
                flow_obj.config,
                stream_mode="values"
        ):
            response = flow_obj.interact(response=event, user_id=user_id, message_id=message_id)
            flow_obj.chat_history.extend([HumanMessage(query), AIMessage(response["content"][0]["text"])])

    return response


@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest):
    generated_response = generate_response(query=req.query, user_id=req.user_id, message_id=req.message_id)
    return ChatResponse(**generated_response)
