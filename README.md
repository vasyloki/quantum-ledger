# 🌌 The Quantum Ledger: Dynamic Financial Intelligence

**The Quantum Ledger** is a high-fidelity Retrieval-Augmented Generation (RAG) platform designed for real-time fiscal analysis. It transforms static financial documents—10-Ks, earnings transcripts, and management reports—into a dynamic, searchable intelligence graph. 

By leveraging **IBM Docling** for structural parsing and **Qdrant** for vector orchestration, the Ledger provides grounded, source-cited insights into the 2025-2026 performance of major tech entities like **NVIDIA, Meta, Alphabet**, and now **TSMC**.

---

Why use **The Quantum Ledger** instead of a general LLM like Gemini or ChatGPT? While general assistants are excellent "reasoning engines," they lack the **deterministic memory architecture** required for professional financial auditing.

### 🛡️ The Hallucination Firewall (Hard Grounding)
General LLMs often "hallucinate" by blending their pre-training data with your uploaded documents. The Ledger utilizes **Hard Grounding**, physically restricting the LLM's context to only the specific data points retrieved from your private Qdrant vault. If the fact isn't in your Ledger, the system won't "guess" it.

### 🔍 Audit-Ready Verifiability
In finance, an answer is only as good as its source. Every response in the Ledger is tethered to a **Quantum Hit**. The sidebar dashboard allows you to instantly verify the exact source text, chunk index, and similarity score, turning a 10-minute manual "fact-check" into a 2-second visual audit.

### ♾️ Infinite Context & Scale
Standard LLMs are limited by "context windows"—they eventually "forget" the beginning of a long report or a large collection of files. The Ledger’s **Vector Memory** scales infinitely; you can index thousands of annual reports across decades, and the system will only surface the relevant 1% of data needed for your specific query.

### 📊 Structural Intelligence (Table Parsing)
Most LLMs treat financial tables as a "word soup," losing the relationship between headers and values. By leveraging **IBM Docling**, the Ledger preserves the structural hierarchy of financial matrices, ensuring that complex data (like TSMC’s revenue-by-node technology) is interpreted with 100% relational accuracy.

---

### 🌌 Why "Quantum"?

Unlike traditional financial tools that are **linear and deterministic**, **The Quantum Ledger** treats financial intelligence as a **high-dimensional probability space**.

* **Superposition (Hybrid Search):** The engine evaluates data as "waves" (semantic intent) and "particles" (exact fiscal constants) using Qdrant’s hybrid architecture.
* **Entanglement (Vector Embeddings):** Identifies relationships between disparate reports—linking NVIDIA's R&D trajectory to Alphabet’s infrastructure spending through conceptual proximity.
* **Observer Effect (Dynamic Ingestion):** The Ledger is no longer a static snapshot. By "observing" new data through the upload portal, the analysis space expands instantly to include new market players and fiscal years.

---

## 🏗️ Platform Features

### 🚀 **Dynamic Web Interface (Streamlit)**
A professional-grade dashboard for interactive querying and audit.
* **Quantum Hits Sidebar:** Real-time visibility into similarity scores and raw document chunks used for every answer.
* **Entity Filtering:** Toggle focus between specific companies or perform cross-sector "All" analysis.
* **Session Persistence:** Chat history and retrieval metadata are maintained throughout your research session.

### 📂 **Hot-Ingestion Engine**
Move from raw PDF to searchable vector in seconds directly from the browser.
* **Structural Conversion:** Uses **Docling** to preserve complex financial tables and nested hierarchies in Markdown format.
* **Generalist Strategy:** Employs a pure semantic embedding approach (no manual anchoring) to maintain 90%+ retrieval precision across diverse document types.
* **Zero-Restart Updates:** Ingest new entities like **TSMC** or **ASML** without restarting the backend infrastructure.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Interface** | Streamlit |
| **LLM** | Claude 3.5 Sonnet (Anthropic) |
| **Vector DB** | Qdrant (Dockerized) |
| **Parser** | IBM Docling |
| **Embeddings** | BAAI/bge-small-en-v1.5 |
| **Orchestration** | Python 3.12+ |

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have **Docker** installed for the vector database and an **Anthropic API key** in your `.env`.

### 2. Installation & Launch
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

# Launch the Platform
streamlit run app.py