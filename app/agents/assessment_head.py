from app.services.llm_service import IpExpertLLM

class AssessmentHead:
    def __init__(self):
        self.llm = IpExpertLLM()

    def assess(self, quiz_id: str, answers: dict):
        # Load quiz from storage (omitted here), then grade
        prompt = f"Grade these answers for quiz {quiz_id}. Quiz: <load from DB>. Answers: {answers}. Provide score and feedback per question in JSON."
        resp = self.llm.generate(prompt, max_tokens=512)
        return resp