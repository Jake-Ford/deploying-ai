"""Service 1: Anime information via the Jikan REST API (api.jikan.moe/v4)."""

import requests
import json
from langchain.tools import tool
from utils.logger import get_logger

_logs = get_logger(__name__)

JIKAN_BASE = "https://api.jikan.moe/v4"


def _search_anime(name: str) -> dict | None:
    """Returns the top search result for the given anime name."""
    url = f"{JIKAN_BASE}/anime"
    params = {"q": name, "limit": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data[0] if data else None
    except Exception as e:
        _logs.error(f"Jikan search error: {e}")
        return None


def _get_anime_by_id(mal_id: int) -> dict | None:
    url = f"{JIKAN_BASE}/anime/{mal_id}/full"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json().get("data")
    except Exception as e:
        _logs.error(f"Jikan fetch error: {e}")
        return None


def _format_anime_details(data: dict) -> str:
    """Converts raw Jikan anime data into a readable summary string."""
    title = data.get("title_english") or data.get("title", "Unknown")
    jp_title = data.get("title")
    score = data.get("score", "N/A")
    rank = data.get("rank", "N/A")
    popularity = data.get("popularity", "N/A")
    episodes = data.get("episodes", "?")
    status = data.get("status", "Unknown")
    aired = data.get("aired", {}).get("string", "Unknown")
    synopsis = data.get("synopsis", "No synopsis available.")
    genres = ", ".join(g["name"] for g in data.get("genres", []))
    themes = ", ".join(t["name"] for t in data.get("themes", []))
    studios = ", ".join(s["name"] for s in data.get("studios", []))
    rating = data.get("rating", "Unknown")
    anime_type = data.get("type", "Unknown")
    duration = data.get("duration", "Unknown")
    source = data.get("source", "Unknown")
    favorites = data.get("favorites", 0)
    members = data.get("members", 0)

    parts = [
        f"**{title}**" + (f" ({jp_title})" if jp_title and jp_title != title else ""),
        f"Type: {anime_type} | Episodes: {episodes} | Duration: {duration}",
        f"Score: {score}/10 | Rank: #{rank} | Popularity: #{popularity}",
        f"Genres: {genres}" + (f" | Themes: {themes}" if themes else ""),
        f"Studios: {studios}" if studios else "",
        f"Source: {source} | Rating: {rating}",
        f"Aired: {aired} | Status: {status}",
        f"Favorites: {favorites:,} | Members: {members:,}",
        "",
        f"Synopsis: {synopsis[:800]}{'...' if len(synopsis) > 800 else ''}",
    ]
    return "\n".join(p for p in parts if p or p == "")


@tool
def get_anime_details(anime_name: str) -> str:
    """
    Looks up detailed information about an anime by its name using the Jikan (MyAnimeList) API.
    Returns score, episodes, genres, studios, synopsis, and more.
    Use this when the user asks about a specific anime title.
    """
    _logs.info(f"Jikan lookup: {anime_name}")
    anime = _search_anime(anime_name)
    if not anime:
        return f"I couldn't find any anime matching '{anime_name}' in the database."

    mal_id = anime.get("mal_id")
    full_data = _get_anime_by_id(mal_id) if mal_id else anime
    if not full_data:
        full_data = anime

    return _format_anime_details(full_data)
