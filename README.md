# Local Vector Knowledge Base (fully offline)

A local RAG pipeline: index a directory (e.g. a partition) into a vector
store using Ollama embeddings, query it via terminal or a browser UI, and
keep it auto-refreshed as files change. Nothing here ever calls out to the
internet at runtime.

## Files in this project

| File              | Purpose                                                        |
|-------------------|-----------------------------------------------------------------|
| `build_index.py`  | Builds/refreshes the vector index from a directory              |
| `watch_index.py`  | Watches the directory and auto-refreshes the index on changes   |
| `query.py`        | Terminal-based query tool                                       |
| `app.py`          | Browser UI (Streamlit) for querying                             |
| `run_app.bat`     | Windows launcher — double-click to start the browser UI         |
| `launcher.py`     | Entry point used to freeze the app into a standalone `.exe`     |
| `requirements.txt`| Python dependencies                                              |


# Bootstrapping 

## 1. Install Python 3.14 https://www.python.org/downloads/release/pymanager-263/

This python manager would ask to update settings, select all options y or Y. Use Python version 3.14 or above

## 2. Install Ollama
```
irm https://ollama.com/install.ps1 | iex
```

## 3. Install Ollama for python
```
pip install ollama
```
# Local Vector Knowledge Base (fully offline)

## 1. One-time setup

```powershell
# Pull the embedding model (only needs internet once, to download it — after this, fully offline)
ollama pull nomic-embed-text

# Also pull a generation model if you haven't already
ollama pull llama3.1:8b
```

**Recommended: use a virtual environment** so packages stay isolated:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> Always call pip as `python -m pip ...` rather than bare `pip ...` — it's
> more reliable on Windows since it doesn't depend on PATH being set up
> correctly for the `Scripts` folder.


#### Place the data files to your partition or specified dir on your local machine

## 2. Point it at your partition

Edit the defaults at the top of `build_index.py`, or just pass a flag:

```powershell
python build_index.py --kb-dir /path/to/your/partition_or_folder
```

First run: reads every file, embeds it, saves vectors to `./chroma_db` and
index metadata to `./storage`.

## 3. Refresh later (after adding/editing/removing files)

Run the exact same command again:

```powershell
python build_index.py --kb-dir /path/to/your/partition_or_folder
```

It hashes each file and only re-embeds what changed. Deleted files get
pruned from the index automatically. Safe to run as often as you like —
put it in a cron job if you want it to stay current automatically.

## 4. Auto-refresh on changes (optional)

Instead of manually re-running `build_index.py`, leave a watcher running
and it'll refresh automatically whenever files under `--kb-dir` are added,
edited, deleted, or moved:

```powershell
python watch_index.py --kb-dir "\path\to\your\partition_or_folder"
```

Debounced (default: 5s of quiet time after the last change) so a big batch
of edits triggers one refresh, not dozens. Leave it running in a terminal
if you want it always-on. Ctrl+C to stop.

Ask a question, and it'll show the answer plus which source files it pulled
from, so you can sanity-check retrieval quality.

## 5. Test retrieval (terminal)

```powershell
python query.py
```

Ask a question, and it'll show the answer plus which source files it pulled
from, so you can sanity-check retrieval quality.


## 6. Browser UI

```powershell
python -m streamlit run app.py
```

This opens a chat-style page (usually at `http://localhost:8501`) where you
can ask questions, see answers, and expand a "Sources" section per answer.
Fully local — Streamlit's dev server only binds to your machine by default.

Sidebar settings let you change the generation model, top-k, and which
index/collection to query, without touching code. Use "Reload index" if
you refreshed the index in another terminal and want the UI to pick up
the changes.

## 7. Launching via double-click (Windows)

**`run_app.bat`** — double-click to launch the browser UI without opening
a terminal manually. It:
- activates `venv` automatically if present in the same folder
- checks whether `streamlit` is installed, and installs dependencies if not
- launches the app via `python -m streamlit run app.py` (works regardless
  of PATH issues)
- stays open on error so you can read what went wrong

If `run_app.bat` closes instantly or you want to see output live, run it
from PowerShell instead of double-clicking:
```powershell
.\run_app.bat
```

### Optional: silent launch with no console window

Save as `run_app.vbs` in the same folder:
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "run_app.bat" & chr(34), 0
Set WshShell = Nothing
```
If double-clicking it opens VS Code instead of running it, that means
`.vbs` files are associated with VS Code, not the script host. Fix via
**Settings → Apps → Default apps → search `.vbs`** and set it to
**Windows Based Script Host**. Or just run it without needing the
association: `wscript.exe run_app.vbs`.

## Troubleshooting (PowerShell / Windows)

- **`python`/`pip` not recognized** — Python isn't on PATH. Try
  `py --version` instead; if that works, use `py` in place of `python`
  everywhere above.
- **`pip` not recognized but `python` works** — call pip through Python:
  `python -m pip install ...` instead of bare `pip ...`.
- **"running scripts is disabled on this system"** when activating a venv —
  PowerShell's execution policy is blocking it. Fix:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **`'streamlit' is not recognized as an internal or external command`** —
  either streamlit isn't installed in the active Python environment
  (`python -m pip install -r requirements.txt`), or it's installed but its
  `Scripts` folder isn't on PATH — use `python -m streamlit run app.py`
  instead of the bare `streamlit` command to sidestep this entirely.
- **`.vbs` opens in VS Code instead of running** — see the "silent launch"
  section above for the default-app fix.

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
