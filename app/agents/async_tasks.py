from ..queue.worker import q

def enqueue_generate_course(topic, audience):
    job = q.enqueue('app.app.agents.course_orchestrator.CourseOrchestrator.create_course', topic, audience)
    return job.get_id()