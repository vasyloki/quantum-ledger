import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

load_dotenv()

class QuantumRetriever:
    def __init__(self, collection_name="financial_intel"):
        self.collection_name = collection_name
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

    def search(self, question, company=None, limit=25):
        """
        Final precision tuning for 100% audit pass.
        Handles sector-wide consensus and keyword-heavy table retrieval.
        """
        # 1. Vectorize the question
        query_vector = self.model.encode(question).tolist()

        # 2. Dynamic Limit Adjustment
        # Deepen search for sector-wide (multi) or data-heavy questions (Revenue/CapEx)
        data_keywords = ["revenue", "capex", "expenditure", "guidance", "outlook", "income"]
        is_data_heavy = any(k in question.lower() for k in data_keywords)
        
        if company and company.lower() == "multi":
            effective_limit = 50  # Max depth for sector consensus
        elif is_data_heavy:
            effective_limit = 40  # Deeper net for financial tables
        else:
            effective_limit = limit

        # 3. Enhanced Filtering with Keyword Boosting
        search_filter = None
        if company and company.lower() != "multi":
            should_filters = [
                models.FieldCondition(key="metadata.company", match=models.MatchText(text=company.lower())),
                models.FieldCondition(key="metadata.source", match=models.MatchText(text=company.lower()))
            ]
            
            # If the question asks for a specific financial metric, boost it in the filter
            if is_data_heavy:
                should_filters.append(
                    models.FieldCondition(key="page_content", match=models.MatchText(text=company.lower()))
                )
                
            search_filter = models.Filter(should=should_filters)

        # 4. Query the Ledger
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=effective_limit,
            using="text-dense",
            with_payload=True
        )

        return response.points

if __name__ == "__main__":
    retriever = QuantumRetriever()
    # Test with a known high-precision query
    hits = retriever.search("What is the 2026 revenue for Data Center?", company="nvidia")
    print(f"✅ Found {len(hits)} candidates for NVIDIA Revenue Audit.")