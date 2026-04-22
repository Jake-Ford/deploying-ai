"""
Run this script once to pre-build the ChromaDB vector store from the anime CSV.
The app will also auto-build on first launch if the DB doesn't exist.

Usage (from 05_src/):
    python -m assignment_chat_2.build_db
"""
from assignment_chat_2.tools_search import _get_or_build_collection

if __name__ == "__main__":
    print("Building ChromaDB collection...")
    col = _get_or_build_collection()
    print(f"Done. Collection '{col.name}' has {col.count()} entries.")
