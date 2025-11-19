import logging
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_milvus import Milvus, BM25BuiltInFunction
from app.services.service_interface import GenericEmbedder
from app.data_load.data_access_objects import PdfDAO
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()


class PdfEmbeder(GenericEmbedder, PdfDAO):
    def __init__(self, chunk_size=2500, chunk_overlap=1400):
        super().__init__()
        self.docs = None
        self.embedding = None
        self.vectorstore = None
        self.splitter = None
        self.texts = None
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def read_docs(self, **kwargs):
        self.docs = PdfDAO.read_data(self=self, pdf_path=kwargs["pdf_path"])
        logging.info("Created Documents")
        logging.info(self.status)
        return self.docs

    def create_embeddings(self, **kwargs):
        self.embedding = GoogleGenerativeAIEmbeddings(model=kwargs["model"], google_api_key=os.getenv('GEMINI_API_KEY'))
        return self.embedding

    def chunk(self, docs):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap,
                                                       length_function=len,
                                                       separators=["\n\n", "\n", " ", ""],
                                                       add_start_index=True)
        self.texts = self.splitter.split_documents(docs)
        return self.texts


class VectorStore:

    def __init__(self):
        self.vectorstore = None

    def insert_into_vector_store(self, **kwargs):
        dense_index_param = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
        }
        sparse_index_param = {
            "metric_type": "BM25",
            "index_type": "SPARSE_INVERTED_INDEX",
        }
        self.vectorstore = Milvus.from_documents(
            documents=kwargs["texts"],
            embedding=kwargs["embedding"],
            builtin_function=BM25BuiltInFunction(),
            vector_field=["dense", "sparse"],
            connection_args={"uri": kwargs["milvus_uri"]},
            collection_name=kwargs["target_collection"],
            drop_old=kwargs.get("drop_old", False),
            index_params=[dense_index_param, sparse_index_param],
            partition_key_field=kwargs["partition_key"]
        )
        logging.info("Embeddings written to Vector Store")

    def get_vector_store(self, **kwargs):
        self.vectorstore = Milvus(
            kwargs["embedding"],
            builtin_function=BM25BuiltInFunction(),
            connection_args={"uri": kwargs["milvus_uri"]},
            collection_name=kwargs["target_collection"],
            partition_key_field=kwargs["partition_key"],
            vector_field=["dense", "sparse"],
        )
        return self.vectorstore


class Embedding(GenericEmbedder):
    def __init__(self):
        super().__init__()

    def create_embeddings(self, **kwargs):
        return GoogleGenerativeAIEmbeddings(model=kwargs["embedding_model"], google_api_key=os.getenv('GEMINI_API_KEY'))
