"""
build_index.py

Point this at a directory (e.g. your mounted partition, or a folder on it),
and it will:
  - On first run: read every file, chunk it, embed it locally via Ollama,
    and persist the vectors to disk in Chroma.
  - On every later run: detect which files were added / changed / deleted
    since last time, and only re-embed those. Unchanged files are skipped.

Everything happens on localhost. No file ever leaves your machine.

Usage:
    python build_index.py
    python build_index.py --kb-dir /mnt/my_partition/notes --refresh
"""

import argparse
import os
import sys

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
    load_index_from_storage,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# ---------------------------------------------------------------------------
# Config — edit these or override via CLI flags
# ---------------------------------------------------------------------------

DEFAULT_KB_DIR = "./docs"       # directory to index (your partition/folder)
DEFAULT_PERSIST_DIR = "./storage"         # where the index metadata is saved
DEFAULT_CHROMA_DIR = "./chroma_db"        # where the vector DB itself is saved
DEFAULT_COLLECTION = "local_kb"
DEFAULT_EMBED_MODEL = "nomic-embed-text"  # must be pulled in ollama already
OLLAMA_BASE_URL = "http://localhost:11434"

# File types LlamaIndex's default reader handles out of the box.
# (pdf, docx, txt, md, csv, and more are supported natively)
REQUIRED_EXTS = None  # None = let it read everything it recognizes


def get_embed_model():
    # base_url is pinned to localhost explicitly — this will never
    # reach out to the internet, even if ollama's client defaults change.
    return OllamaEmbedding(
        model_name=DEFAULT_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )


def build_or_refresh(kb_dir: str, persist_dir: str, chroma_dir: str, collection: str):
    if not os.path.isdir(kb_dir):
        print(f"ERROR: knowledge base directory not found: {kb_dir}")
        sys.exit(1)

    Settings.embed_model = get_embed_model()
    # No LLM needed just to build the index — keep it None so nothing
    # tries to reach a generation endpoint at index-build time.
    Settings.llm = None

    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    chroma_collection = chroma_client.get_or_create_collection(collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    print(f"Scanning: {kb_dir}")
    documents = SimpleDirectoryReader(
        kb_dir,
        recursive=True,
        required_exts=REQUIRED_EXTS,
        filename_as_id=True,   # important: lets refresh_ref_docs track files by path
    ).load_data()
    print(f"Found {len(documents)} file(s) to consider.")

    if os.path.exists(persist_dir):
        # Existing index found -> load it and refresh incrementally.
        print("Existing index found. Loading and checking for changes...")
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store, persist_dir=persist_dir
        )
        index = load_index_from_storage(storage_context)

        # refresh_ref_docs compares content hashes per file:
        #  - new file  -> inserted
        #  - changed file -> old chunks deleted, new chunks inserted
        #  - unchanged file -> skipped entirely (no re-embedding cost)
        refreshed_flags = index.refresh_ref_docs(documents)
        changed_count = sum(refreshed_flags)
        print(f"Refreshed {changed_count} file(s); {len(documents) - changed_count} unchanged.")
    else:
        print("No existing index. Building from scratch (this embeds everything once)...")
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, show_progress=True
        )

    index.storage_context.persist(persist_dir=persist_dir)
    print(f"Done. Index persisted to: {persist_dir}")
    print(f"Vector data persisted to: {chroma_dir} (collection: {collection})")


def main():
    parser = argparse.ArgumentParser(description="Build/refresh a local vector index from a directory.")
    parser.add_argument("--kb-dir", default=DEFAULT_KB_DIR, help="Directory to index")
    parser.add_argument("--persist-dir", default=DEFAULT_PERSIST_DIR, help="Where to store index metadata")
    parser.add_argument("--chroma-dir", default=DEFAULT_CHROMA_DIR, help="Where to store the Chroma DB")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Chroma collection name")
    args = parser.parse_args()

    build_or_refresh(args.kb_dir, args.persist_dir, args.chroma_dir, args.collection)


if __name__ == "__main__":
    main()
