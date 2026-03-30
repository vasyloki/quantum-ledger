import os
from dotenv import load_dotenv
from anthropic import Anthropic
from retriever import QuantumRetriever

load_dotenv()

class QuantumEngine:
    def __init__(self):
        self.retriever = QuantumRetriever()
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def ask(self, question, company=None):
        # 1. RETRIEVAL: Get the "Quantum" facts
        print(f"🔍 Searching the Ledger for: {company if company else 'All Companies'}...")
        hits = self.retriever.search(question, company=company, limit=5)
        
        # 2. CONTEXT ASSEMBLY: Format snippets for Claude
        context_text = ""
        for i, hit in enumerate(hits):
            source = hit.payload['metadata']['source']
            content = hit.payload['page_content']
            context_text += f"\n---\n[Document: {source}]\n{content}\n"

        # 3. SYSTEM PROMPT: Set the "Financial Analyst" persona
        system_msg = (
            "You are a Senior Financial Analyst for 'The Quantum Ledger'. "
            "Use the provided context from 2025-2026 financial reports to answer the query. "
            "If the answer isn't in the context, state that you don't have that specific data. "
            "Always cite your sources (e.g., 'According to the NVIDIA 10-K...')."
        )

        # 4. GENERATION: Claude's Reasoning
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_msg,
            messages=[
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}
            ]
        )

        return message.content[0].text

if __name__ == "__main__":
    engine = QuantumEngine()
    
    # TEST: Ask about the Blackwell ramp or Meta's CapEx
    query = "What is the production outlook for Blackwell GPUs and what are the primary risks mentioned?"
    
    response = engine.ask(query, company="nvidia")
    print("\n📊 QUANTUM ANALYSIS:\n")
    print(response)