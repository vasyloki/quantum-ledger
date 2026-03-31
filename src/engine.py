import os
from dotenv import load_dotenv
from anthropic import Anthropic
# Ensure these are imported for the Retriever to use
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from src.retriever import QuantumRetriever

load_dotenv()

class QuantumEngine:
    def __init__(self):
        # 1. Initialize Retriever
        self.retriever = QuantumRetriever()
        
        # 🛠️ REQUIRED CHANGE: Initialize Docling tools directly on the retriever
        # This allows app.py to access them for 'Hot-Ingestion'
        self.retriever.converter = DocumentConverter()
        self.retriever.chunker = HybridChunker()
        
        # 2. Initialize LLM Client
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def ask(self, question, company=None):
        # 1. RETRIEVAL: Get the "Quantum" facts
        print(f"🔍 Searching the Ledger for: {company if company else 'All Companies'}...")
        
        # Use the search method from your QuantumRetriever
        hits = self.retriever.search(question, company=company, limit=5)
        
        # 2. CONTEXT ASSEMBLY: Format snippets for Claude and metadata for UI
        context_text = ""
        sources_metadata = []
        
        for hit in hits:
            # Extract data from the Qdrant hit
            source = hit.payload.get('metadata', {}).get('source', 'Unknown Source')
            content = hit.payload.get('page_content', '')
            score = hit.score 
            
            # Build the text block for the LLM
            context_text += f"\n---\n[Document: {source}]\n{content}\n"
            
            # Build the structured list for the Sidebar Dashboard
            sources_metadata.append({
                "source": source,
                "score": score,
                "content": content
            })

        # 3. SYSTEM PROMPT
        system_msg = (
            "You are a Senior Financial Analyst for 'The Quantum Ledger'. "
            "Use the provided context from 2025-2026 financial reports to answer the query. "
            "If the answer isn't in the context, state that you don't have that specific data. "
            "Always cite your sources (e.g., 'According to the NVIDIA 10-K...')."
        )

        # 4. GENERATION
        # Note: Updated model name to a standard Anthropic identifier
        message = self.client.messages.create(
            model="claude-sonnet-4-6", 
            max_tokens=1024,
            system=system_msg,
            messages=[
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}
            ]
        )

        return message.content[0].text, sources_metadata

if __name__ == "__main__":
    engine = QuantumEngine()
    
    # TEST: Ask about the Blackwell ramp
    query = "What is the production outlook for Blackwell GPUs and what are the primary risks mentioned?"
    
    response, sources = engine.ask(query, company="nvidia")
    print("\n📊 QUANTUM ANALYSIS:\n")
    print(response)