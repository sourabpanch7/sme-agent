from pymilvus import Collection, MilvusClient, DataType

client = MilvusClient("/Users/sourabpanchanan/PycharmProjects/lma-major-project-raggers/milvus_db.db")

# Specify the name of the collection
collection_name = "ip_laws"

schema = client.create_schema(
    auto_id=True,
    enable_dynamic_schema=True,
)

schema.add_field(field_name="text", datatype=DataType.VARCHAR, default_value="xxx", max_length=65535)
schema.add_field(field_name="pk", datatype=DataType.INT64, is_primary=True, default_value=1)
schema.add_field(field_name="dense", datatype=DataType.FLOAT_VECTOR, dim=768)
schema.add_field(field_name="sparse", datatype=DataType.SPARSE_FLOAT_VECTOR, is_function_output=True)
schema.add_field(field_name="producer", datatype=DataType.VARCHAR, default_value="xxx", max_length=1000)
schema.add_field(field_name="creator", datatype=DataType.VARCHAR, default_value="xxx", max_length=1000)
schema.add_field(field_name="creationdate", datatype=DataType.VARCHAR, default_value="xxx", max_length=1000)
schema.add_field(field_name="author", datatype=DataType.VARCHAR, default_value="xxx", max_length=1000)
schema.add_field(field_name="moddate", datatype=DataType.VARCHAR, default_value="xxx", max_length=1000)
schema.add_field(field_name="source", datatype=DataType.VARCHAR, default_value="xxx", max_length=1000)
schema.add_field(field_name="total_pages", datatype=DataType.INT64, default_value=-1111111111111)
schema.add_field(field_name="page", datatype=DataType.INT64, default_value=-1111111111111)
schema.add_field(field_name="page_label", datatype=DataType.VARCHAR, default_value="xxx", max_length=1000)
schema.add_field(field_name="start_index", datatype=DataType.INT64, default_value=-1111111111111)

index_params = client.prepare_index_params()
index_params.add_index(field_name="dense", metric_type="COSINE", index_type="IVF_FLAT")
index_params.add_index(field_name="sparse", metric_type="BM25", index_type="SPARSE_INVERTED_INDEX")

client.create_collection(collection_name=collection_name, schema=schema, index_params=index_params)

print("Collection created Successfully")
