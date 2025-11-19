from langchain_milvus import Milvus, BM25BuiltInFunction


def get_interim_retrievers(ip_embedding, target_collections=["ip_laws", "ip_laws_extended", "ip_laws_hindi"]
                           , uri="/Users/sourabpanchanan/PycharmProjects/lma-major-project-raggers/milvus_db.db",
                           num_docs=10):
    for collection_name in target_collections:
        yield Milvus(
            embedding_function=ip_embedding,
            builtin_function=BM25BuiltInFunction(),
            connection_args={"uri": uri},
            collection_name=collection_name,
            partition_key_field=None,
            vector_field=["dense", "sparse"],
        ).as_retriever(
            search_type="similarity",
            k=num_docs,
        )


def format_docs(docs):
    return "".join(doc.page_content for doc in docs)
