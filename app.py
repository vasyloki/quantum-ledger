import streamlit as st
import tempfile
from pathlib import Path
from src.engine import QuantumEngine
from src.search_service import SECSearchService
from qdrant_client import models 
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Page Config
st.set_page_config(page_title="The Quantum Ledger", page_icon="🌌", layout="wide")

# Initialize Engine
@st.cache_resource
def get_engine():
    return QuantumEngine()

engine = get_engine()

# Initialize State
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

# --- REUSABLE INGESTION HELPER ---
def process_and_vectorize(file_path, company_name, source_name):
    r = engine.retriever 
    conv_result = r.converter.convert(file_path)
    whole_text = conv_result.document.export_to_markdown()
    
    safety_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, 
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""] 
    )
    
    final_chunks = safety_splitter.split_text(whole_text)
    
    points = []
    for i, text_segment in enumerate(final_chunks):
        clean_text = text_segment.strip()
        if len(clean_text) < 40: continue
        
        if len(clean_text) > 2000:
            clean_text = clean_text[:2000]

        vector = r.model.encode(clean_text).tolist()
        point_id = hash(f"{source_name}_{i}_{company_name}") & 0xFFFFFFFFFFFFFFFF
        
        points.append(models.PointStruct(
            id=point_id,
            vector={"text-dense": vector},
            payload={
                "page_content": clean_text,
                "metadata": {"source": source_name, "company": company_name.lower()}
            }
        ))

    if points:
        r.client.upsert(collection_name=r.collection_name, points=points)
        return len(points)
    return 0
        
# Sidebar for controls
with st.sidebar:
    st.title("🌌 Ledger Settings")
    
    # --- 🔍 THE "GOLDEN TRIO" SCOUT ---
    st.subheader("🌐 Financial Artifact Scout")
    ticker_input = st.text_input("Enter Ticker", value="NVDA").upper()
    
    if st.button("🔍 Scout Trio"):
        st.session_state.search_results = []
        with st.spinner(f"Hunting for the Golden Trio for {ticker_input}..."):
            try:
                search_service = SECSearchService()
                results = search_service.get_filing_list(ticker_input)
                if results:
                    st.session_state.search_results = results
                    st.rerun() 
                else:
                    st.warning("No filings found in the Trio category.")
            except Exception as e:
                st.error(f"Scout failed: {e}")

    # DISPLAY TARGETED RESULTS
    if st.session_state.search_results:
        st.write("### 📥 Grounding Package")
        for filing in st.session_state.search_results:
            icon = "📄" if "10-K" in filing['type'] else "🎙️" if "8-K" in filing['type'] else "🌐"
            with st.expander(f"{icon} {filing['type']} | {filing['date']}"):
                st.write(f"**{filing['title']}**")
                
                # CRITICAL EDIT: Use unique key for the button
                if st.button("📥 Ingest to Ledger", key=f"btn_{filing['url']}"):
                    with st.spinner("Refining data..."):
                        search_service = SECSearchService()
                        
                        # --- THE FIX: PASS THE WHOLE FILING DICT ---
                        # This allows download_filing to access both the URL and the Ticker
                        path = search_service.download_filing(filing)
                        
                        if path:
                            count = process_and_vectorize(path, ticker_input, f"{ticker_input}-{filing['type']}")
                            st.success(f"Grounded {count} chunks!")
                        else:
                            st.error("Document retrieval failed. Check logs for 404 hints.")

    st.divider()

    # --- 📂 LOCAL OVERRIDE ---
    st.subheader("📂 Supplemental Upload")
    with st.expander("Upload CFO Commentary/IR PDF"):
        uploaded_file = st.file_uploader("Choose file", type=["pdf", "html"])
        manual_tag = st.text_input("Company Tag", value=ticker_input.lower())
        if st.button("🚀 Ingest Manual File", key="manual_ingest") and uploaded_file:
            ext = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = Path(tmp.name)
            try:
                count = process_and_vectorize(tmp_path, manual_tag, uploaded_file.name)
                st.success(f"Indexed {count} chunks!")
            finally:
                if tmp_path.exists(): tmp_path.unlink()

    st.divider()
    company_filter = st.selectbox("Focus Analysis On:", ["All", "NVIDIA", "Meta", "Alphabet", "TSM"])
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_sources = []
        st.rerun()

    # --- 🎯 IMPROVED METADATA VIEW ---
    st.divider()
    st.subheader("🎯 Retrieval Metadata")
    if st.session_state.last_sources:
        for i, doc in enumerate(st.session_state.last_sources):
            meta = doc.get('metadata', {}) if isinstance(doc, dict) else getattr(doc, 'metadata', {})
            source_label = meta.get('source', 'Unknown Source')
            content = doc.get('page_content', '') if isinstance(doc, dict) else getattr(doc, 'page_content', '')
            
            with st.expander(f"Source {i+1}: {source_label}"):
                st.caption(f"Company: {meta.get('company', 'N/A')}")
                st.write(content[:1000] + "..." if len(content) > 1000 else content)

st.title("🌌 The Quantum Ledger")
st.markdown(f"*Currently Grounded in: **{ticker_input}** 2026 Fiscal Data*")

# Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]): 
        st.markdown(message["content"])

# Assistant Interaction
if prompt := st.chat_input("Analyze Blackwell vs Hopper margins..."):
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