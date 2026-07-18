"""
query.py

Quick way to test that your local knowledge base is actually retrievable.
Loads the persisted index (built by build_index.py) and lets you ask
questions from the terminal. Generation uses a local Ollama model too.

Usage:
    python query.py
    python query.py --model llama3.1:8b
"""

import argparse

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist-dir", default=DEFAULT_PERSIST_DIR)
    parser.add_argument("--chroma-dir", default=DEFAULT_CHROMA_DIR)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama generation model")
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()

    Settings.embed_model = OllamaEmbedding(model_name=DEFAULT_EMBED_MODEL, base_url=OLLAMA_BASE_URL)
    Settings.llm = Ollama(model=args.model, base_url=OLLAMA_BASE_URL, request_timeout=120.0)

    chroma_client = chromadb.PersistentClient(path=args.chroma_dir)
    chroma_collection = chroma_client.get_or_create_collection(args.collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=args.persist_dir)
    index = load_index_from_storage(storage_context)

    query_engine = index.as_query_engine(similarity_top_k=args.top_k)

    print("Local KB ready. Type a question (or 'exit').\n")
    while True:
        q = input("> ").strip()
        if q.lower() in ("exit", "quit"):
            break
        if not q:
            continue
        response = query_engine.query(q)
        print("\n" + str(response) + "\n")
        print("Sources:")
        for node in response.source_nodes:
            fname = node.metadata.get("file_name", "unknown")
            print(f"  - {fname} (score: {node.score:.3f})")
        print()


if __name__ == "__main__":
    main()
