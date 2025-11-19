from pymilvus import Collection, MilvusClient, DataType

client = MilvusClient("./milvus_db.db")

# Assuming 'client' is an initialized MilvusClient instance

# Altering a field's property (e.g., setting a default value)
client.alter_collection_field(
    collection_name="ip_laws",
    field_name="author",
    # properties={"default_value": "NA"},
    field_params={'max_length': 65535}
)
