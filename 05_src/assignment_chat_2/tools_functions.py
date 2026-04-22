"""Service 3: Structured anime database queries via OpenAI function calling over the CSV."""

import os
import pandas as pd
from langchain.tools import tool
from utils.logger import get_logger

_logs = get_logger(__name__)

_CSV_PATH = os.path.join(os.path.dirname(__file__), "anime-dataset-2023.csv")
_df: pd.DataFrame | None = None


def _get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        _logs.info("Loading anime CSV for structured queries...")
        df = pd.read_csv(_CSV_PATH)
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
        df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
        df["Episodes"] = pd.to_numeric(df["Episodes"], errors="coerce")
        df["Members"] = pd.to_numeric(df["Members"], errors="coerce")
        df["Favorites"] = pd.to_numeric(df["Favorites"], errors="coerce")
        _df = df
    return _df


def _row_to_summary(row: pd.Series) -> str:
    name = row.get("English name") or row.get("Name", "Unknown")
    score = row.get("Score", "N/A")
    genres = row.get("Genres", "")
    anime_type = row.get("Type", "")
    episodes = row.get("Episodes", "?")
    status = row.get("Status", "")
    rank = row.get("Rank", "N/A")
    score_str = f"{score:.2f}" if isinstance(score, float) else str(score)
    rank_str = f"#{int(rank)}" if pd.notna(rank) else "N/A"
    ep_str = str(int(episodes)) if pd.notna(episodes) else "?"
    return (
        f"**{name}** ({anime_type}, {ep_str} ep) | Score: {score_str}/10 | Rank: {rank_str}\n"
        f"   Genres: {genres} | Status: {status}"
    )


@tool
def query_anime_database(
    genre: str = "",
    min_score: float = 0.0,
    max_score: float = 10.0,
    anime_type: str = "",
    status: str = "",
    sort_by: str = "score",
    limit: int = 5,
) -> str:
    """
    Queries the anime database with structured filters. Use this for requests like:
    - 'top-rated action anime'
    - 'finished mecha shows with score above 8'
    - 'most popular romance TV anime'
    - 'show me some short OVA anime'

    Parameters:
    - genre: filter by genre keyword (e.g. 'Action', 'Romance', 'Horror', 'Sci-Fi')
    - min_score: minimum score (0.0 - 10.0)
    - max_score: maximum score (0.0 - 10.0)
    - anime_type: filter by type — 'TV', 'Movie', 'OVA', 'ONA', 'Special', 'Music'
    - status: filter by airing status — 'Finished Airing', 'Currently Airing', 'Not yet aired'
    - sort_by: sort results by 'score', 'rank', 'popularity', or 'favorites'
    - limit: number of results to return (max 10)
    """
    _logs.info(
        f"DB query: genre={genre!r}, score={min_score}-{max_score}, "
        f"type={anime_type!r}, status={status!r}, sort={sort_by}, limit={limit}"
    )
    df = _get_df().copy()

    if genre:
        df = df[df["Genres"].str.contains(genre, case=False, na=False)]
    if anime_type:
        df = df[df["Type"].str.lower() == anime_type.lower()]
    if status:
        df = df[df["Status"].str.lower().str.contains(status.lower(), na=False)]

    df = df[df["Score"].between(min_score, max_score, inclusive="both")]

    sort_col_map = {
        "score": "Score",
        "rank": "Rank",
        "popularity": "Popularity",
        "favorites": "Favorites",
    }
    sort_col = sort_col_map.get(sort_by.lower(), "Score")
    ascending = sort_col == "Rank"
    df = df.sort_values(sort_col, ascending=ascending, na_position="last")

    limit = min(max(1, limit), 10)
    top = df.head(limit)

    if top.empty:
        return "No anime found matching those criteria. Try relaxing the filters a bit!"

    header_parts = []
    if genre:
        header_parts.append(genre)
    if anime_type:
        header_parts.append(anime_type)
    label = " ".join(header_parts) or "anime"
    lines = [f"Here are the top {len(top)} {label} results (sorted by {sort_by}):\n"]
    for i, (_, row) in enumerate(top.iterrows(), 1):
        lines.append(f"{i}. {_row_to_summary(row)}")

    return "\n".join(lines)
