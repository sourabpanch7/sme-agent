from ..services.qwen_client import QWENClient

class QuizHead:
    def __init__(self):
        self.llm = QWENClient()

    def create_quiz(self, course_id: str, num_questions: int = 10):
        prompt = f"Create {num_questions} quiz questions (multiple choice with 4 choices and an answer key) for the course id: {course_id}. Provide JSON output with fields: question, options, answer, difficulty."
        resp = self.llm.generate(prompt, max_tokens=1024)
        return resp
