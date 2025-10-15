from pydantic import BaseModel, Field
class Quiz(BaseModel):
    Questions: str = Field(description="Multiple-choice Quiz questions")
    Answer_Key: str = Field(description="Answer Key for generated questions")