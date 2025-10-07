from fastapi import FastAPI
from .auth import router as auth_router
from .rag import router as rag_router
from .course import router as course_router
from .quiz import router as quiz_router


def register_routes(app: FastAPI):
    app.include_router(auth_router, prefix="/auth")
    app.include_router(rag_router, prefix="/rag")
    app.include_router(course_router, prefix="/course")
    app.include_router(quiz_router, prefix="/quiz")