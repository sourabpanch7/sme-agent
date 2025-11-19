import logging
import argparse
from app.services.embedding_service import PdfEmbeder, VectorStore


class DataEmbedding(PdfEmbeder, VectorStore):
    def __init__(self, pdf_path, milvus_uri, target_collection, chunk_size=2500, chunk_overlap=1400,
                 embedding_model="models/text-embedding-004",
                 search_key=None, partition_key=None):
        super().__init__()
        logging.info("Starting Embedding creation")
        self.pdf_path = pdf_path
        self.milvus_uri = milvus_uri
        self.milvus_collection = target_collection
        self.partition_key = partition_key
        self.search_key = search_key
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_obj = None

    def insert_vector_data(self):
        self.embedding_obj = PdfEmbeder(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        docs = self.embedding_obj.read_docs(pdf_path=self.pdf_path)
        texts = self.chunk(docs)
        embedding = self.create_embeddings(model=self.embedding_model, texts=texts)
        self.insert_into_vector_store(texts=texts, embedding=embedding, milvus_uri=self.milvus_uri,
                                      target_collection=self.milvus_collection,
                                      partition_key=self.partition_key)


if __name__ == "__main__":
    logging.getLogger().setLevel(level=logging.INFO)
    parser = argparse.ArgumentParser(description="A simple script demonstrating argparse.")
    parser.add_argument("--milvus_uri", help="Milvus URI", default="./milvus_db.db")
    parser.add_argument("--doc_path", help="Path of the document to load",
                        default="resources/ip_laws/Manual_for_Patent_Office_Practice_and_Procedure_.pdf")
    parser.add_argument("--target_collection", help="Milvus target collection",
                        default="ip_laws")
    parser.add_argument("--embedding_model", help="Text embedding model to be used",
                        default="models/gemini-embedding-001")
    parser.add_argument("--chunk_size", help="Chunk Size to be used",
                        default=2500)
    parser.add_argument("--chunk_overlap", help="Chunk overlap to be used",
                        default=1400)
    args = parser.parse_args()
    try:
        data_load_obj = DataEmbedding(
            pdf_path=args.doc_path,
            milvus_uri=args.milvus_uri,
            target_collection=args.target_collection
        )
        data_load_obj.insert_vector_data()
    except Exception as err_msg:
        logging.error(err_msg)
        raise err_msg
    finally:
        logging.info("DONE")
