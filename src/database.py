import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

class QuantumLedgerDB:
    def __init__(self, collection_name="financial_intel"):
        self.collection_name = collection_name
        # Initialize client (defaults to local Docker/Binary if no URL provided)
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )

    def create_hybrid_collection(self, dense_dim=384):
        """
        Sets up the 2026 Hybrid Schema:
        - text-dense: For OpenAI/Gemini/Llama embeddings
        - text-sparse: For BM25/Keyword precision
        """
        if self.client.collection_exists(self.collection_name):
            print(f"Collection '{self.collection_name}' already exists. Skipping creation.")
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            # 1. Semantic Config (The 'Meaning' layer)
            vectors_config={
                "text-dense": models.VectorParams(
                    size=dense_dim,
                    distance=models.Distance.COSINE,
                    on_disk=True  # Keeps RAM usage low for large financial docs
                )
            },
            # 2. Lexical Config (The 'Keyword' layer)
            sparse_vectors_config={
                "text-sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(
                        on_disk=True,
                    )
                )
            }
        )
        
        # 3. Payload Indexing (Crucial for filtering by Ticker/Year)
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="metadata.source",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        print(f"✅ Collection '{self.collection_name}' initialized for Hybrid Search.")

if __name__ == "__main__":
    db = QuantumLedgerDB()
    db.create_hybrid_collection()