from ..services.rag_service import RAGService
from ..services.qwen_client import QWENClient

class CourseOrchestrator:
    def __init__(self):
        self.rag = RAGService()
        self.llm = QWENClient()

    def create_course(self, topic: str, target_audience: str = 'beginner'):
        # 1) Query RAG for topic materials
        docs = self.rag.query(f"create a syllabus for {topic} for {target_audience}")
        # 2) Use LLM to synthesize a course outline
        prompt = f"Based on the following documents:\n{docs['retrieved']}\n\nCreate a course outline for {topic} aimed at {target_audience}. Include modules, lessons, learning objectives, and estimated time per lesson."
        resp = self.llm.generate(prompt)
        # user should parse resp according to their LM output format
        return {
            'topic': topic,
            'audience': target_audience,
            'outline_raw': resp
        }
