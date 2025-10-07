from fastapi import FastAPI
from .core.config import settings
from .db.session import engine, SessionLocal
from .api.routes import register_routes

app = FastAPI(title="QWEN Agentic System")
register_routes(app)

@app.on_event("startup")
async def startup():
    # create DB tables if needed
    from . import models
    models.Base.metadata.create_all(bind=engine)
    # warm-up connections if needed
    print("Startup: connections initialized")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}