from fastapi import APIRouter
from pydantic import BaseModel
from ...agents.quiz_head import QuizHead
from ...agents.assessment_head import AssessmentHead

router = APIRouter()

class QuizReq(BaseModel):
    course_id: str
    num_questions: int = 10

@router.post('/generate')
def generate_quiz(req: QuizReq):
    q = QuizHead()
    quiz = q.create_quiz(req.course_id, req.num_questions)
    return quiz

class AssessReq(BaseModel):
    quiz_id: str
    answers: dict

@router.post('/assess')
def assess(req: AssessReq):
    a = AssessmentHead()
    result = a.assess(req.quiz_id, req.answers)
    return result
