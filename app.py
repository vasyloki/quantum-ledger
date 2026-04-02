import streamlit as st
import tempfile
import time
import base64
import os
from pathlib import Path
from src.engine import QuantumEngine
from src.search_service import SECSearchService
from qdrant_client import models 
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="The Quantum Ledger", 
    page_icon="🌌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- HELPER: BASE64 IMAGE ENCODER ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- DEFINE ASSETS & ENCODE ---
IMAGE_PATH = "Agape’s Song.png" 
img_base64 = get_base64_image(IMAGE_PATH)

# --- MIDNIGHT GLOW UI INJECTION ---
if img_base64:
    bg_style = f"""
        background-image: linear-gradient(rgba(5, 5, 5, 0.92), rgba(15, 15, 15, 0.95)), 
        url("data:image/png;base64,{img_base64}");
    """
else:
    bg_style = "background: linear-gradient(135deg, #050505 0%, #111111 100%);"

st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Almendra:wght@400;700&family=Cinzel+Decorative:wght@400;700&family=Spectral:ital,wght@0,200;1,200;1,300&display=swap');

        :root {{
            --primary-color: #FFFFFF !important; 
            --secondary-background-color: rgba(30, 30, 30, 0.6) !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}
        
        .stApp {{
            {bg_style}
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #FFFFFF !important; 
            font-family: 'Spectral', serif;
            font-weight: 300;
            letter-spacing: 1px;
            text-shadow: 0px 0px 8px rgba(255, 255, 255, 0.4);
        }}

        input:focus, textarea:focus {{
            border-color: #FFFFFF !important;
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.5) !important;
        }}

        [data-testid="stSidebar"] {{
            background-color: #050505 !important;
            backdrop-filter: blur(25px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}

        h1 {{
            font-family: 'Cinzel Decorative', cursive;
            font-weight: 700;
            color: #FFFFFF !important;
            letter-spacing: 5px;
            text-transform: none !important;
            text-shadow: 0px 0px 15px rgba(255, 255, 255, 0.6);
        }}

        h2, h3, .st-emotion-cache-10trblm, label, p, span {{
            font-family: 'Spectral', serif;
            font-style: italic;
            font-weight: 400;
            color: #FFFFFF !important;
            letter-spacing: 1px;
            text-transform: none !important;
        }}

        div.stButton > button {{
            background: rgba(255, 255, 255, 0.05) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 40px !important; 
            padding: 0.6rem 2rem !important;
            transition: all 0.5s ease;
            width: 100%;
            text-transform: none !important;
            font-family: 'Spectral', serif;
            font-style: italic;
        }}
        
        div.stButton > button:hover {{
            background-color: rgba(255, 255, 255, 0.15) !important;
            border-color: #FFFFFF !important;
            box-shadow: 0px 0px 20px rgba(255, 255, 255, 0.2);
        }}

        .quantum-card {{
            background-color: rgba(255, 255, 255, 0.03);
            border-left: 2px solid rgba(255, 255, 255, 0.4);
            padding: 1.8rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}

        [data-testid="stChatMessage"] {{
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 20px;
            padding: 25px;
        }}

        div[data-testid="stStatus"] {{
            background-color: #0A0A0A !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 40px !important;
        }}

        .stProgress > div > div > div > div {{
            background-color: rgba(255, 255, 255, 0.7) !important;
        }}
        
        .stChatInput textarea {{
            background-color: rgba(15, 15, 15, 0.8) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- ENGINE & HELPERS ---
@st.cache_resource
def get_engine():
    return QuantumEngine()

engine = get_engine()

def get_ingested_tickers(engine):
    """PRO FEATURE: Dynamic ticker list from Qdrant metadata."""
    try:
        results, _ = engine.retriever.client.scroll(
            collection_name=engine.retriever.collection_name,
            with_payload=True,
            with_vectors=False,
            limit=1000
        )
        tickers = set(
            point.payload['metadata']['company'].upper() 
            for point in results if 'metadata' in point.payload and 'company' in point.payload['metadata']
        )
        return sorted(list(tickers))
    except Exception:
        return []

if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

def process_and_vectorize(file_path, company_name, source_name):
    r = engine.retriever 
    conv_result = r.converter.convert(file_path)
    whole_text = conv_result.document.export_to_markdown()
    safety_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100, separators=["\n\n", "\n", " ", ""])
    final_chunks = safety_splitter.split_text(whole_text)
    points = []
    for i, text_segment in enumerate(final_chunks):
        clean_text = text_segment.strip()
        if len(clean_text) < 40: continue
        vector = r.model.encode(clean_text).tolist()
        point_id = hash(f"{source_name}_{i}_{company_name}") & 0xFFFFFFFFFFFFFFFF
        points.append(models.PointStruct(id=point_id, vector={"text-dense": vector}, payload={"page_content": clean_text, "metadata": {"source": source_name, "company": company_name.lower()}}))
    if points:
        r.client.upsert(collection_name=r.collection_name, points=points)
        return len(points)
    return 0
        
# --- SIDEBAR ---
with st.sidebar:
    st.title("Currents")
    ticker_input = st.text_input("Entity Ticker", value="NVDA").upper()
    
    if st.button("Query Archive", use_container_width=True):
        st.session_state.search_results = []
        with st.status("Listening to the Void...", expanded=False):
            try:
                search_service = SECSearchService()
                results = search_service.get_filing_list(ticker_input)
                if results:
                    st.session_state.search_results = results
                    st.rerun() 
                else:
                    st.warning("No echoes returned.")
            except Exception as e:
                st.error("Signal lost.")

    if st.session_state.search_results:
        st.write("---")
        for filing in st.session_state.search_results:
            with st.expander(f"{filing['type']} | {filing['date']}"):
                if st.button("Synchronize Artifact", key=f"btn_{filing['url']}"):
                    prog = st.progress(0)
                    with st.spinner("Extracting..."):
                        search_service = SECSearchService()
                        path = search_service.download_filing(filing)
                        if path:
                            count = process_and_vectorize(path, ticker_input, f"{ticker_input}-{filing['type']}")
                            prog.progress(100)
                            st.toast(f"Synchronized {count} fragments")
                            time.sleep(1)
                            prog.empty()
                            st.rerun()

    st.divider()
    uploaded_file = st.file_uploader("Upload Artifact", type=["pdf", "html"])
    manual_tag = st.text_input("Entity ID", value=ticker_input.lower())
    if st.button("Index Supplement", key="manual_ingest") and uploaded_file:
        with st.spinner("Manifesting..."):
            ext = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = Path(tmp.name)
            count = process_and_vectorize(tmp_path, manual_tag, uploaded_file.name)
            st.toast(f"Manifested {count} fragments")
            st.rerun()

    live_tickers = get_ingested_tickers(engine)
    focus_options = ["Global Markets"] + live_tickers
    company_filter = st.selectbox("Focus Area", focus_options, index=0)

    if st.button("Reset Memory", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_sources = []
        st.rerun()

# --- MAIN AREA ---
col_head, col_badge = st.columns([5, 1])
with col_head:
    st.title("The Quantum Ledger")
    st.caption(f"Analyzing {ticker_input if ticker_input else 'Aggregate Market Data'}")

tab_chat, tab_sources = st.tabs(["Analysis Terminal", "Grounded Citations"])

with tab_chat:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("Input Fiscal Inquiry..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Synthesizing..."):
                target_company = None if company_filter == "Global Markets" else company_filter.lower()
                response, sources = engine.ask(prompt, company=target_company)
                
                # Commit flattened source dictionaries to state
                st.session_state.last_sources = sources
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.markdown(response)
                st.rerun()

with tab_sources:
    if st.session_state.get("last_sources"):
        for i, doc in enumerate(st.session_state.last_sources):
            # Accessing the flattened dictionary keys defined in engine.py
            source_name = doc.get("source", "Archive Record")
            content = doc.get("content", "Fragment missing...")
            score = doc.get("score", 0.0)
            
            st.markdown(f'''
                <div class="quantum-card">
                    <strong style="color:#9370DB">Source Entry {i+1} | {source_name}</strong>
                    <br><small style="color: rgba(255,255,255,0.6)">Relevance Score: {score:.4f}</small>
                </div>
            ''', unsafe_allow_html=True)
            
            with st.expander("Examine Fragment"): 
                st.write(content)
    else:
        st.info("The ledger is silent.")