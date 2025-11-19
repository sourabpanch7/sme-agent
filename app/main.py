from fastapi import FastAPI
from app.routers.chat_routes import router as chat_router

app = FastAPI(title="IP Agent API (Modular)", version="2.0")

app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "IP Tutor API running 🚀"}
