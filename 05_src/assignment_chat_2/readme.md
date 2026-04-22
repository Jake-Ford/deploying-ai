# Otaku Oracle — Assignment 2 Chat Client

## Overview

**Otaku Oracle** is an anime expert chat assistant powered by GPT-4o-mini and LangGraph.
It has a passionate, enthusiastic personality and answers questions about anime using three
distinct backend services. The interface is built with Gradio and maintains conversation memory.

---

## Services

### Service 1: Anime Lookup via Jikan API (`tools_api.py`)

Uses the **Jikan REST API** (`https://api.jikan.moe/v4`) — a free, public API backed by
MyAnimeList data. When a user asks about a specific anime title, the agent calls `get_anime_details`,
which searches the API and returns score, genres, synopsis, studios, episode count, and more.
The raw JSON is transformed into natural language before being returned.

> **Note:** The assignment referenced `https://chandan-02.github.io/anime-facts-rest-api/` but
> that service's Heroku backend has been decommissioned (Heroku removed free dynos in 2022).
> Jikan is the standard replacement for public anime data — it is actively maintained and free.

### Service 2: Semantic Anime Discovery (`tools_search.py`)

A **ChromaDB vector store** (file-persistent) backed by the `anime-dataset-2023.csv` dataset
(~24,900 anime). The top 3,000 most-popular anime are indexed by synopsis using the
`all-MiniLM-L6-v2` sentence-transformer model (local, no API key required).

When a user describes a mood, theme, or feeling ("something dark like Evangelion", "a cozy
slice-of-life"), the `semantic_anime_search` tool queries the collection and returns the closest
semantic matches with genre and score metadata.

**Embedding process:**
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, runs locally)
- Subset: top 3,000 anime by `Members` count (most culturally significant titles)
- The DB is built automatically on first launch and persisted to `chroma_db/`
- Subsequent launches load instantly from disk

### Service 3: Structured Database Filter via Function Calling (`tools_functions.py`)

Uses **OpenAI function calling** (via LangGraph's tool node) to execute structured queries
over the anime CSV with `pandas`. The `query_anime_database` tool accepts typed parameters
(genre, score range, type, status, sort order) that the LLM populates from natural language.
This satisfies the Function Calling requirement — the LLM calls this tool with precise typed
arguments rather than freeform text.

---

## Architecture

```
User message → Gradio UI → LangGraph agent (GPT-4o-mini)
                                   │
               ┌───────────────────┼──────────────────────┐
               ▼                   ▼                        ▼
     get_anime_details   semantic_anime_search   query_anime_database
       (Jikan API)          (ChromaDB)            (pandas + CSV)
```

The agent uses a **sliding window** of the last 20 messages to manage context length.

---

## Guardrails

- System prompt cannot be revealed or modified by the user
- Restricted topics (cats/dogs, horoscopes/zodiac, Taylor Swift) are politely declined
- Guardrails are enforced via the system prompt — the agent refuses to engage and redirects

---

## Running the App

From the `05_src/` directory:

```bash
python -m assignment_chat_2.app
```

**First launch** will auto-build the ChromaDB (downloads the sentence-transformer model ~90 MB,
then embeds ~3,000 anime synopses — takes 1-3 minutes). All subsequent launches load instantly.

To pre-build the DB manually:
```bash
python -m assignment_chat_2.build_db
```

Requires an `OPENAI_API_KEY` in `.secrets`.

---

## Dataset

`anime-dataset-2023.csv` — 24,905 anime entries with title, synopsis, genres, score, type,
episode count, and more. Source: Kaggle (anime-dataset-2023).
File size: ~15 MB (within the 40 MB GitHub limit).
