"""
app.py

Browser-based UI for querying your local knowledge base.
Runs entirely on localhost — no internet involved.

Usage:
    streamlit run app.py

Then open the URL it prints (usually http://localhost:8501) in your browser.
"""

import streamlit as st

from llama_index.core import StorageContext, Settings, load_index_from_storage
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from build_index import (
    DEFAULT_PERSIST_DIR,
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION,
    DEFAULT_EMBED_MODEL,
    OLLAMA_BASE_URL,
)

st.set_page_config(page_title="Your Local AI", page_icon="🗂️", layout="centered")


@st.cache_resource(show_spinner=False)
def load_query_engine(persist_dir, chroma_dir, collection, gen_model, top_k):
    Settings.embed_model = OllamaEmbedding(model_name=DEFAULT_EMBED_MODEL, base_url=OLLAMA_BASE_URL)
    Settings.llm = Ollama(model=gen_model, base_url=OLLAMA_BASE_URL, request_timeout=180.0)

    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    chroma_collection = chroma_client.get_or_create_collection(collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=persist_dir)
    index = load_index_from_storage(storage_context)
    return index.as_query_engine(similarity_top_k=top_k)


# --- Sidebar: settings ---
with st.sidebar:
    st.header("Settings")
    gen_model = st.text_input("Ollama generation model", value="llama3.1:8b")
    top_k = st.slider("Chunks to retrieve (top-k)", min_value=1, max_value=10, value=4)
    persist_dir = st.text_input("Index dir", value=DEFAULT_PERSIST_DIR)
    chroma_dir = st.text_input("Chroma dir", value=DEFAULT_CHROMA_DIR)
    collection = st.text_input("Collection", value=DEFAULT_COLLECTION)

    if st.button("Reload index"):
        load_query_engine.clear()
        st.success("Index cache cleared — will reload on next question.")

st.title("🗂️ Your Local AI")
st.caption("Fully offline — queries never leave this machine.")

# --- Chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.markdown(f"- **{s['file']}** (score: {s['score']:.3f})")

# --- Chat input ---
question = st.chat_input("Ask something about your files...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching and generating..."):
                query_engine = load_query_engine(persist_dir, chroma_dir, collection, gen_model, top_k)
                response = query_engine.query(question)

            answer = str(response)
            st.markdown(answer)

            sources = [
                {"file": node.metadata.get("file_name", "unknown"), "score": node.score or 0.0}
                for node in response.source_nodes
            ]
            if sources:
                with st.expander("Sources"):
                    for s in sources:
                        st.markdown(f"- **{s['file']}** (score: {s['score']:.3f})")

            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
        except Exception as e:
            error_msg = f"Something went wrong: {e}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
