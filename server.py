# server.py
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import requests
import html
import time

from config import (
    MCP_SERVER_NAME,
    TOOL_RETRY_COUNT,
    TOOL_TIMEOUT,
    GEOCODING_API_URL,
    GEOCODING_COUNT,
    WEATHER_API_URL,
    WEATHER_CURRENT_PARAMS,
    WEATHER_TIMEZONE,
    BOOKS_API_URL,
    BOOK_RECS_LIMIT,
    DOG_API_URL,
    TRIVIA_API_URL,
    TRIVIA_AMOUNT,
    TRIVIA_TYPE
)

mcp = FastMCP(MCP_SERVER_NAME)

# -------------------------
# Helper: retry + backoff
# -------------------------
def get_with_retry(url: str, params=None, retries: int = None, timeout: int = None):
    if retries is None:
        retries = TOOL_RETRY_COUNT
    if timeout is None:
        timeout = TOOL_TIMEOUT
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2 ** i)

# -------------------------
# City → Coordinates
# -------------------------
@mcp.tool()
def city_to_coords(city: str) -> Dict[str, Any]:
    """Convert city name to latitude and longitude (Open-Meteo Geocoding)."""
    r = get_with_retry(
        GEOCODING_API_URL,
        params={"name": city, "count": GEOCODING_COUNT},
    )

    results = r.json().get("results")
    if not results:
        return {"error": f"No coordinates found for {city}"}

    c = results[0]
    return {
        "city": c.get("name"),
        "country": c.get("country"),
        "latitude": c.get("latitude"),
        "longitude": c.get("longitude"),
    }

# -------------------------
# Weather
# -------------------------
@mcp.tool()
def get_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """Current weather at coordinates via Open-Meteo."""
    r = get_with_retry(
        WEATHER_API_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": WEATHER_CURRENT_PARAMS,
            "timezone": WEATHER_TIMEZONE,
        },
    )
    return r.json().get("current", {})

# -------------------------
# Book Recommendations
# -------------------------
@mcp.tool()
def book_recs(topic: str, limit: int = None) -> Dict[str, Any]:
    """Book recommendations by topic (Google Books API)."""
    if limit is None:
        limit = BOOK_RECS_LIMIT

    try:
        r = get_with_retry(
            BOOKS_API_URL,
            params={"q": topic, "maxResults": limit},
        )

        data = r.json()
        
        # Check for API errors
        if "error" in data:
            return {"error": f"Google Books API error: {data['error']}", "topic": topic}
        
        items = data.get("items", [])
        
        # Handle case when no items found
        if not items:
            return {
                "topic": topic,
                "results": [],
                "message": f"No books found for topic '{topic}'. Try a different search term."
            }

        results: List[Dict[str, Any]] = []

        for item in items[:limit]:
            info = item.get("volumeInfo", {})

            results.append({
                "title": info.get("title", "Unknown Title"),
                "authors": info.get("authors", ["Unknown"]),
                "published_year": info.get("publishedDate", "Unknown"),
                "description": info.get("description", "No description available"),
                "preview_link": info.get("previewLink", ""),
            })

        return {
            "topic": topic,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch book recommendations: {str(e)}",
            "topic": topic
        }

# -------------------------
# Dog Image
# -------------------------
@mcp.tool()
def random_dog() -> Dict[str, Any]:
    """Return a random dog image URL."""
    r = get_with_retry(DOG_API_URL)
    return r.json()

# -------------------------
# Trivia (Optional)
# -------------------------
@mcp.tool()
def trivia() -> Dict[str, Any]:
    """Return one multiple-choice trivia question."""
    r = get_with_retry(
        TRIVIA_API_URL,
        params={"amount": TRIVIA_AMOUNT, "type": TRIVIA_TYPE},
    )

    data = r.json().get("results")
    if not data:
        return {"error": "No trivia found"}

    q = data[0]
    return {
        "category": q["category"],
        "difficulty": q["difficulty"],
        "question": html.unescape(q["question"]),
        "correct_answer": html.unescape(q["correct_answer"]),
        "incorrect_answers": [
            html.unescape(x) for x in q["incorrect_answers"]
        ],
    }

# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    mcp.run()  # stdio MCP server
