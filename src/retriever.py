import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

load_dotenv()

class QuantumRetriever:
    def __init__(self, collection_name="financial_intel"):
        self.collection_name = collection_name
        # Must match the model used in ingest.py
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

    def search(self, question, company=None, limit=3):
        # 1. Vectorize the user's question
        query_vector = self.model.encode(question).tolist()

        # 2. Setup metadata filtering (The 'Senior' move)
        search_filter = None
        if company:
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.company",
                        match=models.MatchValue(value=company)
                    )
                ]
            )

        # 3. Query the Ledger
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            using="text-dense"
        ).points

        return results

if __name__ == "__main__":
    retriever = QuantumRetriever()
    
    # Let's test it with a real financial query
    query = "What is the outlook for Blackwell GPU shipments?"
    print(f"\n🔍 Querying the Ledger: '{query}'")
    
    hits = retriever.search(query, company="nvidia")
    
    for i, hit in enumerate(hits):
        source = hit.payload['metadata']['source']
        content = hit.payload['page_content'][:400] # Show a snippet
        print(f"\n[Result {i+1}] Source: {source}")
        print(f"Content: {content}...")
        print("-" * 50)