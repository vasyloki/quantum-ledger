from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
client.delete_collection("financial_intel")
print("Dropped old collection.")