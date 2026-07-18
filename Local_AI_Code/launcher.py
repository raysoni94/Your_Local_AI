"""
launcher.py

Entry point for building a standalone .exe with PyInstaller.
Spawns `streamlit run app.py` as a subprocess and waits.

This file is NOT meant to be run directly with `python launcher.py`
during normal development -- just use `streamlit run app.py` for that.
This is only the entry point for the frozen .exe build.
"""

import os
import sys
import subprocess


def resource_path(relative_path):
    """Get absolute path to a bundled resource, works for dev and for PyInstaller's onefile mode."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def main():
    app_path = resource_path("app.py")
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless=false",
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
