class GenericEmbedder:
    def __init__(self):
        self.status = True

    def read_docs(self, **kwargs):
        return self.status

    def create_embeddings(self, **kwargs):
        return self.status

    def create_vector_store(self, **kwargs):
        return self.status


class GenericRAG:
    def __init__(self, retriever):
        self.status = True
        self.retriever = retriever
        self.relevant_doc = None

    def get_retrieved_document(self):
        return self.relevant_doc


class GenericLLM:
    def __init__(self, model, temperature, retriever):
        self.model = model
        self.temperature = temperature
        self.retriever = retriever
        self.examples = None
        self.example_prompt = None
        self.few_shot_prompt = None
        self.prompt = None
        self.query = None
        self.rag_chain = None

    def build_rag_chain(self):
        return self.rag_chain

    def invoke_llm(self, query):
        self.query = query
        return self.rag_chain.invoke(self.query)


class GenericAgent:
    def __init__(self):
        self.status = True

    def create_tools(self):
        return self.status

    def create_agent(self):
        return self.status

    def invoke_agent(self, query):
        return self.status
