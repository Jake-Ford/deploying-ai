"""Service 2: Semantic anime discovery via ChromaDB + sentence-transformers."""

import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.tools import tool
import pandas as pd
from utils.logger import get_logger

_logs = get_logger(__name__)

_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
_COLLECTION_NAME = "anime_synopses"
_MODEL_NAME = "all-MiniLM-L6-v2"
_CSV_PATH = os.path.join(os.path.dirname(__file__), "anime-dataset-2023.csv")
_TOP_N_TO_INDEX = 3000  # index top-N anime by member count to keep DB size manageable

_embedding_fn = SentenceTransformerEmbeddingFunction(model_name=_MODEL_NAME)


def _get_or_build_collection() -> chromadb.api.models.Collection.Collection:
    """Load the persistent ChromaDB collection, building it if it doesn't exist."""
    client = chromadb.PersistentClient(path=_DB_PATH)

    existing = [c.name for c in client.list_collections()]
    if _COLLECTION_NAME in existing:
        col = client.get_collection(name=_COLLECTION_NAME, embedding_function=_embedding_fn)
        if col.count() > 0:
            _logs.info(f"Loaded existing ChromaDB collection ({col.count()} entries).")
            return col

    _logs.info("Building ChromaDB collection from CSV — this only runs once...")
    col = client.get_or_create_collection(name=_COLLECTION_NAME, embedding_function=_embedding_fn)

    df = pd.read_csv(_CSV_PATH)
    df = df.dropna(subset=["Synopsis", "English name"])
    df["Members"] = pd.to_numeric(df["Members"], errors="coerce").fillna(0)
    df = df.sort_values("Members", ascending=False).head(_TOP_N_TO_INDEX)

    batch_size = 100
    docs, ids, metas = [], [], []

    for _, row in df.iterrows():
        anime_id = str(row["anime_id"])
        synopsis = str(row["Synopsis"]).strip()
        if not synopsis or synopsis.lower() == "nan":
            continue
        docs.append(synopsis)
        ids.append(anime_id)
        metas.append({
            "name": str(row.get("English name", row.get("Name", "Unknown"))),
            "score": float(row["Score"]) if str(row["Score"]).replace(".", "").isdigit() else 0.0,
            "genres": str(row.get("Genres", "")),
            "type": str(row.get("Type", "")),
            "episodes": str(row.get("Episodes", "")),
            "status": str(row.get("Status", "")),
        })

        if len(docs) >= batch_size:
            col.add(documents=docs, ids=ids, metadatas=metas)
            docs, ids, metas = [], [], []

    if docs:
        col.add(documents=docs, ids=ids, metadatas=metas)

    _logs.info(f"ChromaDB built with {col.count()} anime entries.")
    return col


_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        _collection = _get_or_build_collection()
    return _collection


@tool
def semantic_anime_search(query: str, n_results: int = 4) -> str:
    """
    Finds anime that match a description, mood, theme, or feeling using semantic search.
    Use this when the user describes what kind of anime experience they want rather than
    naming a specific title. Examples: 'sad anime about loss', 'funny slice-of-life',
    'space opera with deep characters', 'like Spirited Away but darker'.
    Returns a list of matching anime with descriptions.
    """
    _logs.info(f"Semantic search: {query}")
    col = _get_collection()

    results = col.query(query_texts=[query], n_results=min(n_results, col.count()))
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        return "I couldn't find any matching anime for that description."

    lines = [f"Here are {len(docs)} anime that match your vibe:\n"]
    for i, (doc, meta) in enumerate(zip(docs, metas), 1):
        name = meta.get("name", "Unknown")
        score = meta.get("score", 0.0)
        genres = meta.get("genres", "")
        anime_type = meta.get("type", "")
        episodes = meta.get("episodes", "?")
        snippet = doc[:300] + "..." if len(doc) > 300 else doc
        lines.append(
            f"{i}. **{name}** ({anime_type}, {episodes} ep) | Score: {score}/10\n"
            f"   Genres: {genres}\n"
            f"   {snippet}\n"
        )

    return "\n".join(lines)
