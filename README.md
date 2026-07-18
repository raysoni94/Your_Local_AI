# Your_Local_AI

# Bootstapping 

## 1. Install Python 3.14 https://www.python.org/downloads/release/pymanager-263/

This python manager would ask to update settings, select all options y or Y. Use Python version 3.14 or above

## 2. Install Ollama
```
function test() {
  console.log("irm https://ollama.com/install.ps1 | iex");
}
```

## 3. Install Ollama for python

pip install ollama

# Local Vector Knowledge Base (fully offline)

## 1. One-time setup

```bash
# Pull the embedding model (only needs internet once, to download it — after this, fully offline)
ollama pull nomic-embed-text

# Also pull a generation model if you haven't already
ollama pull llama3.1:8b

# Install python deps
pip install -r requirements.txt
```

## 2. Point it at your partition

Edit the defaults at the top of `build_index.py`, or just pass a flag:

```bash
python build_index.py --kb-dir /path/to/your/partition_or_folder
```

First run: reads every file, embeds it, saves vectors to `./chroma_db` and
index metadata to `./storage`.

## 3. Refresh later (after adding/editing/removing files)

Run the exact same command again:

```bash
python build_index.py --kb-dir /path/to/your/partition_or_folder
```

It hashes each file and only re-embeds what changed. Deleted files get
pruned from the index automatically. Safe to run as often as you like —
put it in a cron job if you want it to stay current automatically.

## 4. Test retrieval

```bash
python query.py
```

Ask a question, and it'll show the answer plus which source files it pulled
from, so you can sanity-check retrieval quality.

## Notes

- `base_url` is pinned to `http://localhost:11434` everywhere so nothing
  ever reaches out past your machine.
- `filename_as_id=True` is what makes incremental refresh possible —
  don't remove it.
- If retrieval quality feels off, the two easiest knobs are chunk size
  (set via `Settings.chunk_size`, default 1024) and `--top-k` in query.py.
- Supported file types out of the box: .txt, .md, .pdf, .docx, .csv, .json,
  and several more. For a partition full of code or unusual formats, let
  me know and I'll add a custom reader.


wget -uri https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py
python get-pip.py   
