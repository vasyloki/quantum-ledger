import streamlit as st
from src.engine import QuantumEngine

# Page Config
st.set_page_config(page_title="The Quantum Ledger", page_icon="🌌", layout="wide")

# Initialize the Engine (cached so it doesn't reload on every click)
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
    
    # 1. Filters and Controls (Keep these at the top)
    company_filter = st.selectbox("Focus Analysis On:", ["All", "NVIDIA", "Meta", "Alphabet"])
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        # Clear sources too when clearing chat
        if "last_sources" in st.session_state:
            del st.session_state.last_sources
        st.rerun()

    st.divider()
    st.subheader("🎯 Retrieval Metadata")

    # 2. THE DASHBOARD LOGIC (This was missing)
    if "last_sources" in st.session_state and st.session_state.last_sources:
        # Show a high-level metric
        st.metric("Quantum Hits", len(st.session_state.last_sources))
        
        # Loop through each hit saved in session_state
        for i, doc in enumerate(st.session_state.last_sources):
            with st.expander(f"Source {i+1}: {doc['source']}"):
                # Display the "Quantum" similarity score
                st.caption(f"Similarity Score: {doc['score']:.4f}")
                # Display the actual text chunk used by Claude
                st.write(doc['content'])
    else:
        st.info("Ask a question to see the underlying 'Quantum' data.")
        
st.title("🌌 The Quantum Ledger")
st.markdown("*Grounded Financial Intelligence for the 2026 Fiscal Landscape*")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about Blackwell yield, Meta's CapEx, etc..."):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Consulting the Ledger..."):
            target_company = None if company_filter == "All" else company_filter.lower()
            
            response, sources = engine.ask(prompt, company=target_company)
            
            # Save to session state so the sidebar can find it
            st.session_state.last_sources = sources
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Force a rerun so the sidebar updates immediately with the new data
            st.rerun()