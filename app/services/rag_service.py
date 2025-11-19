import logging
from app.services.service_interface import GenericRAG


class IpRAG(GenericRAG):
    def __init__(self, retriever):
        super().__init__(retriever=retriever)
        self.compressor = None
        self.compression_retriever = None

    def get_retrieved_document(self, **kwargs):
        return self.retriever.as_retriever(
            search_type="similarity",
            k=kwargs.get("top_k", 10),
        )
