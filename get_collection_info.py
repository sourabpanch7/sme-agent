from pymilvus import MilvusClient

# Connect to your Milvus instance (e.g., Milvus Lite)
client = MilvusClient(
    "/Users/sourabpanchanan/PycharmProjects/lma-major-project-raggers/milvus_db.db")  # Replace with your Milvus Lite file or connection details

collection_name = "ip_laws"  # Replace with the actual name of your collection

try:
    collection_info = client.describe_collection(collection_name=collection_name)
    print(collection_info)
    for field in collection_info["fields"]:
        print(field.get("name"), field["type"])
except Exception as e:
    print(f"Error describing collection '{collection_name}': {e}")
