# 🌌 The Quantum Ledger: Agentic Financial RAG

**The Quantum Ledger** is an advanced Retrieval-Augmented Generation (RAG) system designed to perform high-fidelity fiscal analysis. It ingests complex financial documents—including 10-K filings, earnings call transcripts, and CFO commentaries—to provide grounded, source-cited insights into the 2025-2026 performance of major tech entities like **NVIDIA, Meta, and Alphabet**.

### 🌌 Why "Quantum"?

Unlike traditional financial ledgers that are **linear and deterministic** (row-by-row, keyword-based), **The Quantum Ledger** treats financial intelligence as a **high-dimensional probability space**.

* **Superposition (Hybrid Search):** The engine simultaneously evaluates data as "waves" (semantic context/intent) and "particles" (exact fiscal constants and hard numbers) using Qdrant’s hybrid search architecture.
* **Entanglement (Vector Embeddings):** By mapping every document chunk into a 384-dimensional vector space, the system identifies "entangled" relationships between disparate reports—linking NVIDIA's R&D trajectory to Alphabet’s infrastructure spending even when they don't share common keywords.
* **Dimensionality:** It moves beyond flat text into a mathematical manifold where financial concepts are clustered by their conceptual "proximity," allowing for a non-linear, global understanding of the 2026 fiscal landscape.

---

## 🏗️ System Architecture

The pipeline is built on a modular "Research-First" architecture:

1. **High-Fidelity Ingestion:** Uses [Docling](https://github.com/DS4SD/docling) to parse complex PDF/HTML structures, ensuring financial tables and nested hierarchies are preserved.
2. **Vector Orchestration:** Powered by [Qdrant](https://qdrant.tech/) running in Docker. It utilizes metadata filtering to prevent "cross-talk" between different corporate entities during retrieval.
3. **Semantic Mapping:** Employs the `BAAI/bge-small-en-v1.5` model for local embedding generation, providing a 384-dimensional dense vector space.
4. **Reasoning Engine:** Integrated with [Claude 3.5 Sonnet](https://www.anthropic.com/) to synthesize retrieved "facts" into professional-grade financial analysis.



---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **LLM** | Claude 3.5 Sonnet |
| **Vector DB** | Qdrant |
| **Parser** | IBM Docling |
| **Embeddings** | Sentence-Transformers (BGE) |
| **Orchestration** | Python 3.12+ / Dotenv |

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Docker running for the vector database and an Anthropic API key.

### 2. Installation
```bash
# Clone the repository
git clone [https://github.com/vasyloki/quantum-ledger.git](https://github.com/vasyloki/quantum-ledger.git)
cd quantum-ledger

# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Spin up the Qdrant engine
docker run -p 6333:6333 qdrant/qdrant

# Run the pipeline
python3 src/database.py  # Initialize Collection
python3 src/ingest.py    # Process & Vectorize Data
python3 src/engine.py    # Query the Ledger
```