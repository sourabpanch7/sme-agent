from fastapi import APIRouter
from pydantic import BaseModel
from ...agents.course_orchestrator import CourseOrchestrator

router = APIRouter()

class CourseRequest(BaseModel):
    topic: str
    target_audience: str = 'beginner'

@router.post('/create')
def create_course(req: CourseRequest):
    orchestrator = CourseOrchestrator()
    course = orchestrator.create_course(req.topic, req.target_audience)
    return course
