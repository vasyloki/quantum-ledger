import os
import re
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
        # 1. Vectorize the question
        query_vector = self.model.encode(question).tolist()

        # 2. Advanced Intent & Segment Detection
        q_lower = question.lower()
        years = re.findall(r"202[4-7]", question)
        
        # Segment & Specific Metric Anchors (Crucial for Q6 & Q7)
        segments = ["gaming", "data center", "cloud", "reality labs", "search"]
        metrics = ["revenue", "capex", "margin", "inventory", "repurchase", "buyback", "authorization"]
        
        found_segments = [s for s in segments if s in q_lower]
        found_metrics = [m for m in metrics if m in q_lower]
        architectures = ["blackwell", "hopper", "h100", "b200"]
        found_arch = [a for a in architectures if a in q_lower]

        # 3. Dynamic Depth Adjustment
        # We increase limit significantly for segment revenue tables which are often buried
        if company and company.lower() == "multi":
            effective_limit = 60
        elif found_segments or "revenue" in q_lower or "repurchase" in q_lower:
            effective_limit = 55 
        else:
            effective_limit = 50 if (found_metrics or years or found_arch) else limit

        # 4. Hybrid Filtering with Synonym & Table Anchoring
        company_synonyms = {
            "alphabet": ["alphabet", "google", "goog"],
            "nvidia": ["nvidia", "nvda"],
            "meta": ["meta", "facebook"]
        }
        search_terms = company_synonyms.get(company.lower(), [company.lower()]) if company else []

        should_filters = []
        if company and company.lower() != "multi":
            for term in search_terms:
                should_filters.append(models.FieldCondition(key="metadata.company", match=models.MatchText(text=term)))
                should_filters.append(models.FieldCondition(key="metadata.source", match=models.MatchText(text=term)))
            
            # ANCHOR: Table & Fiscal Year Summary (Fix for Q6)
            # If asking for revenue, prioritize chunks that mention 'Fiscal Year' or 'Segment'
            if "revenue" in q_lower:
                should_filters.append(models.FieldCondition(key="page_content", match=models.MatchText(text="fiscal year")))
                should_filters.append(models.FieldCondition(key="page_content", match=models.MatchText(text="segment")))

            # ANCHOR: Repurchase Logic (Fix for Q7)
            if "repurchase" in q_lower or "buyback" in q_lower:
                should_filters.append(models.FieldCondition(key="page_content", match=models.MatchText(text="authorization")))
                should_filters.append(models.FieldCondition(key="page_content", match=models.MatchText(text="remaining")))

            # Existing Temporal & Architecture Anchors
            for year in years:
                should_filters.append(models.FieldCondition(key="page_content", match=models.MatchText(text=year)))
            for arch in found_arch:
                should_filters.append(models.FieldCondition(key="page_content", match=models.MatchText(text=arch)))
            if "inventory" in q_lower:
                should_filters.append(models.FieldCondition(key="page_content", match=models.MatchText(text="provision")))

        search_filter = models.Filter(should=should_filters) if should_filters else None

        # 5. Execute Query
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=effective_limit,
            using="text-dense",
            with_payload=True
        )

        return response.points