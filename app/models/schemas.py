from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class NumQuestions(BaseModel):
    num_questions: int = Field(description="Number of questions to be generated")


class DifficultyLevel(BaseModel):
    difficulty_level: str = Field(description="Difficulty level of the quiz to be generated")


class RelevantDocsExists(BaseModel):
    relevant_docs_exist: bool = Field(description="Flag for checking if relevant documents exists")


class Quiz(BaseModel):
    questions: str = Field(description="Multiple-choice Quiz questions")
    answer_key: str = Field(description="Answer Key for generated questions")


class GenerateContextualizedQuiz(BaseModel):
    generate_contextualized_quiz: bool = Field(
        description="Flag for checking if contextualized quiz can be generated or not")


class ChatRequest(BaseModel):
    user_id: str
    query: str
    message_id: str


class SourceDoc(BaseModel):
    id: str
    text: str
    meta: Optional[Dict[str, Any]] = None


class ContentItem(BaseModel):
    text: str
    source_docs: List[str]


class QuizItem(BaseModel):
    status: str
    uri: str
    meta: Optional[Dict[str, Any]] = None


class QuizResponse(BaseModel):
    user_id: str
    role: str = Field("assistant", Literal=True)
    message_id: str
    timestamp: str
    content: List[QuizItem]


class ChatResponse(BaseModel):
    user_id: str
    role: str = Field("assistant", Literal=True)
    message_id: str
    timestamp: str
    content: List[ContentItem]


class QuestionValidator(BaseModel):
    valid_question: bool = Field(description="Flag for marking if question is valid or not")


class QuizTopicValidator(BaseModel):
    valid_quiz_topic: bool = Field(description="Flag for marking if quiz topic is valid or not")


class WebSearchRequired(BaseModel):
    web_search_required: bool = Field(description="Flag for marking if web-search is valid or not")
