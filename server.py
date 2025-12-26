# server.py
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import requests
import html
import time

mcp = FastMCP("WeekendWizardTools")

# -------------------------
# Helper: retry + backoff
# -------------------------
def get_with_retry(url: str, params=None, retries: int = 3, timeout: int = 15):
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
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
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
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    )
    return r.json().get("current", {})

# -------------------------
# Book Recommendations
# -------------------------
@mcp.tool()
def book_recs(topic: str, limit: int = 5) -> Dict[str, Any]:
    """Book recommendations by topic (Open Library)."""
    r = get_with_retry(
        "https://openlibrary.org/search.json",
        params={"q": topic, "limit": limit},
    )

    docs = r.json().get("docs", [])
    results: List[Dict[str, Any]] = []

    for d in docs:
        results.append({
            "title": d.get("title"),
            "author": (d.get("author_name") or ["Unknown"])[0],
            "year": d.get("first_publish_year"),
        })

    return {"topic": topic, "results": results}

# -------------------------
# Joke
# -------------------------
@mcp.tool()
def random_joke() -> Dict[str, Any]:
    """Return a safe, one-liner joke."""
    r = get_with_retry(
        "https://v2.jokeapi.dev/joke/Any",
        params={"type": "single", "safe-mode": True},
    )
    return {"joke": r.json().get("joke", "No joke found")}

# -------------------------
# Dog Image
# -------------------------
@mcp.tool()
def random_dog() -> Dict[str, Any]:
    """Return a random dog image URL."""
    r = get_with_retry("https://dog.ceo/api/breeds/image/random")
    return r.json()

# -------------------------
# Trivia (Optional)
# -------------------------
@mcp.tool()
def trivia() -> Dict[str, Any]:
    """Return one multiple-choice trivia question."""
    r = get_with_retry(
        "https://opentdb.com/api.php",
        params={"amount": 1, "type": "multiple"},
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
