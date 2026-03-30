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
    company_filter = st.selectbox("Focus Analysis On:", ["All", "NVIDIA", "Meta", "Alphabet"])
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

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
            # Set company context
            target_company = None if company_filter == "All" else company_filter.lower()
            
            # Get response from your existing engine
            response = engine.ask(prompt, company=target_company)
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})