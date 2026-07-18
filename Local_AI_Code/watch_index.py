"""
watch_index.py

Watches your knowledge base directory and automatically re-runs the
index refresh whenever files are added, changed, deleted, or moved.

Debounced: if you save 10 files in 2 seconds (e.g. editing, copying a
folder in), it waits for things to go quiet before refreshing once,
rather than re-embedding on every single event.

Usage:
    python watch_index.py --kb-dir /path/to/your/partition_or_folder

Leave this running in a terminal (or as a background service) and the
index will stay current automatically. Ctrl+C to stop.
"""

import argparse
import threading
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from build_index import (
    build_or_refresh,
    DEFAULT_KB_DIR,
    DEFAULT_PERSIST_DIR,
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION,
)

DEBOUNCE_SECONDS = 5.0  # quiet period after last change before refreshing


class DebouncedRefreshHandler(FileSystemEventHandler):
    def __init__(self, kb_dir, persist_dir, chroma_dir, collection, debounce_seconds):
        self.kb_dir = kb_dir
        self.persist_dir = persist_dir
        self.chroma_dir = chroma_dir
        self.collection = collection
        self.debounce_seconds = debounce_seconds
        self._timer = None
        self._lock = threading.Lock()

    def _trigger_refresh(self):
        print("\n[watch] Change detected -> refreshing index...")
        try:
            build_or_refresh(self.kb_dir, self.persist_dir, self.chroma_dir, self.collection)
        except Exception as e:
            # Never let the watcher die because one refresh failed
            # (e.g. a file was mid-write when we tried to read it).
            print(f"[watch] Refresh failed, will retry on next change: {e}")
        print("[watch] Watching for further changes...\n")

    def _schedule_refresh(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_seconds, self._trigger_refresh)
            self._timer.daemon = True
            self._timer.start()

    def on_any_event(self, event):
        # Ignore directory-level events and Chroma/storage's own writes
        # (in case persist dirs happen to live inside the watched tree).
        if event.is_directory:
            return
        if self.persist_dir in event.src_path or self.chroma_dir in event.src_path:
            return
        self._schedule_refresh()


def main():
    parser = argparse.ArgumentParser(description="Auto-refresh the local vector index on file changes.")
    parser.add_argument("--kb-dir", default=DEFAULT_KB_DIR)
    parser.add_argument("--persist-dir", default=DEFAULT_PERSIST_DIR)
    parser.add_argument("--chroma-dir", default=DEFAULT_CHROMA_DIR)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--debounce", type=float, default=DEBOUNCE_SECONDS,
                         help="Seconds of inactivity to wait before refreshing")
    args = parser.parse_args()

    # Do an initial build/refresh before we start watching, so the index
    # is current the moment the watcher comes up.
    print("[watch] Running initial index build/refresh...")
    build_or_refresh(args.kb_dir, args.persist_dir, args.chroma_dir, args.collection)

    handler = DebouncedRefreshHandler(
        args.kb_dir, args.persist_dir, args.chroma_dir, args.collection, args.debounce
    )
    observer = Observer()
    observer.schedule(handler, args.kb_dir, recursive=True)
    observer.start()

    print(f"[watch] Watching {args.kb_dir} for changes (debounce: {args.debounce}s). Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
