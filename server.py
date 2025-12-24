# server_fun.py
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import requests
import html
import base64
import json
import time
import os
from pathlib import Path

mcp = FastMCP("FunTools")

# -------------------------------------------------
# HELPER: RETRY LOGIC WITH BACKOFF
# -------------------------------------------------
def fetch_with_retry(url: str, params: dict = None, timeout: int = 15, max_retries: int = 3) -> requests.Response:
    """Fetch URL with exponential backoff retry on rate limits or transient errors."""
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            # Handle rate limiting (429) or server errors (5xx)
            if r.status_code == 429 or r.status_code >= 500:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                    time.sleep(wait_time)
                    continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)
                continue
            raise e
    raise Exception("Max retries exceeded")

# -------------------------------------------------
# USER PREFERENCES MANAGEMENT
# -------------------------------------------------
PREFS_FILE = Path("user_preferences.json")

def load_preferences() -> Dict[str, Any]:
    """Load user preferences from JSON file."""
    if PREFS_FILE.exists():
        try:
            with open(PREFS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_preferences(prefs: Dict[str, Any]) -> None:
    """Save user preferences to JSON file."""
    with open(PREFS_FILE, 'w') as f:
        json.dump(prefs, f, indent=2)

# ---------- City to Coordinates ----------
@mcp.tool()
def city_to_coords(city: str) -> Dict[str, Any]:
    """
    Convert city name to latitude and longitude coordinates using Open-Meteo geocoding.
    Returns the coordinates for the city.
    """
    try:
        r = fetch_with_retry(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10
        )
        data = r.json()
        
        if "results" not in data or len(data["results"]) == 0:
            return {"status": "error", "message": f"City '{city}' not found"}
        
        result = data["results"][0]
        return {
            "status": "ok",
            "city": result.get("name"),
            "country": result.get("country"),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------- Weather ----------
@mcp.tool()
def get_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Get current weather for given latitude and longitude.
    Returns temperature, wind speed, and weather code.
    """
    try:
        r = fetch_with_retry(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=15
        )
        return {"status": "ok", "data": r.json().get("current", {})}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------- Book Recommendations ----------
@mcp.tool()
def book_recs(topic: str, limit: int = 1, save_preference: bool = False) -> Dict[str, Any]:
    """
    Recommend books related to a topic. Can save topic as user preference.
    """
    try:
        # Save preference if requested
        if save_preference:
            prefs = load_preferences()
            if "favorite_genres" not in prefs:
                prefs["favorite_genres"] = []
            if topic not in prefs["favorite_genres"]:
                prefs["favorite_genres"].append(topic)
            save_preferences(prefs)
        
        r = fetch_with_retry(
            "https://openlibrary.org/search.json",
            params={"q": topic, "limit": limit},
            timeout=15
        )
        docs = r.json().get("docs", [])

        results: List[Dict[str, Any]] = []
        for d in docs[:limit]:
            results.append({
                "title": d.get("title", "Unknown"),
                "author": (d.get("author_name") or ["Unknown"])[0],
                "year": d.get("first_publish_year"),
            })

        return {"status": "ok", "topic": topic, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_user_preferences() -> Dict[str, Any]:
    """
    Get saved user preferences including favorite genres.
    """
    try:
        prefs = load_preferences()
        return {"status": "ok", "preferences": prefs}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------- Joke ----------
@mcp.tool()
def random_joke() -> Dict[str, Any]:
    """
    Get a safe one-line joke.
    """
    try:
        r = fetch_with_retry(
            "https://v2.jokeapi.dev/joke/Any?type=single&safe-mode",
            timeout=10
        )
        return {"status": "ok", "joke": r.json().get("joke")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------- Dog Image ----------

@mcp.tool()
def random_dog() -> Dict[str, Any]:
    """
    Returns a random dog image as base64-encoded data.
    """
    try:
        # Step 1: Get image URL
        meta = fetch_with_retry(
            "https://dog.ceo/api/breeds/image/random",
            timeout=10
        )
        image_url = meta.json()["message"]

        # Step 2: Download image with retry
        img = fetch_with_retry(image_url, timeout=15)

        # Step 3: Encode image
        encoded = base64.b64encode(img.content).decode("utf-8")

        return {
            "status": "ok",
            "mime_type": "image/jpeg",
            "image_base64": encoded
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------- Trivia ----------
@mcp.tool()
def trivia() -> Dict[str, Any]:
    """
    Get one multiple-choice trivia question.
    """
    try:
        r = fetch_with_retry(
            "https://opentdb.com/api.php?amount=1&type=multiple",
            timeout=15
        )
        q = r.json()["results"][0]
        return {
            "status": "ok",
            "question": html.unescape(q["question"]),
            "options": [html.unescape(x) for x in q["incorrect_answers"]] +
                       [html.unescape(q["correct_answer"])],
            "answer": html.unescape(q["correct_answer"]),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    mcp.run()
