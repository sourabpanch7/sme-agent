import logging

from app.services.embedding_service import PdfEmbeder, VectorStore


class DataEmbedding(PdfEmbeder, VectorStore):
    def __init__(self, pdf_path, milvus_uri, target_collection, embedding_model="models/text-embedding-004",
                 search_key=None, partition_key=None):
        super().__init__()
        logging.info("Starting Embedding creation")
        self.pdf_path = pdf_path
        self.milvus_uri = milvus_uri
        self.milvus_collection = target_collection
        self.partition_key = partition_key
        self.search_key = search_key
        self.embedding_model = embedding_model
        self.embedding_obj = None

    def insert_vector_data(self):
        self.embedding_obj = PdfEmbeder(chunk_size=2500, chunk_overlap=1400)
        docs = self.embedding_obj.read_docs(pdf_path=self.pdf_path)
        texts = self.chunk(docs)
        embedding = self.create_embeddings(model=self.embedding_model, texts=texts)
        self.insert_into_vector_store(texts=texts, embedding=embedding, milvus_uri=self.milvus_uri,
                                      target_collection=self.milvus_collection,
                                      partition_key=self.partition_key)


if __name__ == "__main__":
    logging.getLogger().setLevel(level=logging.INFO)
    try:
        data_load_obj = DataEmbedding(
            pdf_path="/Users/sourabpanchanan/PycharmProjects/SME_Agent/resources/Manual_for_Patent_Office_Practice_and_Procedure_.pdf",
            milvus_uri="/Users/sourabpanchanan/PycharmProjects/SME_Agent/milvus_db.db",
            target_collection="ip_test"
        )
        data_load_obj.insert_vector_data()
    except Exception as err_msg:
        logging.error(err_msg)
        raise err_msg
    finally:
        logging.info("DONE")
