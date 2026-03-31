import streamlit as st
import tempfile
from pathlib import Path
from src.engine import QuantumEngine
from qdrant_client import models 

# Page Config
st.set_page_config(page_title="The Quantum Ledger", page_icon="🌌", layout="wide")

# Initialize the Engine
@st.cache_resource
def get_engine():
    return QuantumEngine()

engine = get_engine()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for controls
with st.sidebar:
    st.title("🌌 Ledger Settings")
    
    # 📂 DATA MANAGEMENT (Perfectly mirrored to your ingest.py)
    st.subheader("📂 Data Management")
    with st.expander("Upload New Company Docs"):
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")
        # Ingest.py uses the folder name as company_name; here we use a text input
        new_company = st.text_input("Company Name", value="tsmc").lower()
        
        if st.button("🚀 Process & Ingest") and uploaded_file:
            with st.spinner(f"Ingesting {uploaded_file.name}..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = Path(tmp_file.name)

                try:
                    r = engine.retriever 
                    
                    # 1. Structural Conversion (Docling)
                    result = r.converter.convert(tmp_path).document
                    doc_chunks = r.chunker.chunk(result)
                    
                    points = []
                    for i, chunk in enumerate(doc_chunks):
                        text_content = r.chunker.contextualize(chunk)
                        
                        if len(text_content) < 40:
                            continue

                        # Embedding the raw text content (No Year/Company Anchoring)
                        vector = r.model.encode(text_content).tolist()
                        point_id = hash(f"{uploaded_file.name}_{i}") & 0xFFFFFFFFFFFFFFFF
                        
                        # 2. Payload Construction (Matches your ingest.py exactly)
                        points.append(models.PointStruct(
                            id=point_id,
                            vector={"text-dense": vector},
                            payload={
                                "page_content": text_content,
                                "metadata": {
                                    "source": uploaded_file.name,
                                    "company": new_company, 
                                    "chunk_index": i
                                }
                            }
                        ))

                    # 3. Upsert to Qdrant
                    if points:
                        r.client.upsert(
                            collection_name=r.collection_name, 
                            points=points
                        )
                        st.success(f"✅ Successfully indexed {len(points)} chunks for {new_company.upper()}!")
                    
                    st.rerun() 
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")
                finally:
                    if tmp_path.exists():
                        tmp_path.unlink()

    st.divider()

    # Dynamic Filter logic
    default_companies = ["All", "NVIDIA", "Meta", "Alphabet"]
    if new_company.upper() not in default_companies:
        display_options = default_companies + [new_company.upper()]
    else:
        display_options = default_companies
        
    company_filter = st.selectbox("Focus Analysis On:", display_options)
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        if "last_sources" in st.session_state:
            del st.session_state.last_sources
        st.rerun()

    st.divider()
    st.subheader("🎯 Retrieval Metadata")

    if "last_sources" in st.session_state and st.session_state.last_sources:
        st.metric("Quantum Hits", len(st.session_state.last_sources))
        for i, doc in enumerate(st.session_state.last_sources):
            with st.expander(f"Source {i+1}: {doc['source']}"):
                st.caption(f"Similarity Score: {doc['score']:.4f}")
                st.write(doc['content'])
        
st.title("🌌 The Quantum Ledger")
st.markdown("*Grounded Financial Intelligence for the 2026 Fiscal Landscape*")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about Blackwell yield, TSMC N3 ramp, etc..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consulting the Ledger..."):
            target_company = None if company_filter == "All" else company_filter.lower()
            
            response, sources = engine.ask(prompt, company=target_company)
            st.session_state.last_sources = sources
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()