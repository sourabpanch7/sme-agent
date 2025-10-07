from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ...services.rag_service import RAGService

router = APIRouter()

class QueryIn(BaseModel):
    query: str
    top_k: int = 5

@router.post('/query')
def query_rag(data: QueryIn):
    svc = RAGService()
    results = svc.query(data.query, top_k=data.top_k)
    return {'results': results}
