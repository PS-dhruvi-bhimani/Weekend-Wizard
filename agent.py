import asyncio
import json
import sys
import os
import re
from typing import Dict, Any, List
from contextlib import AsyncExitStack

from mistralai import Mistral

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import configuration
from config import (
    MISTRAL_API_KEY,
    MODEL,
    TEMPERATURE,
    COMPRESSION_TEMPERATURE,
    MAX_STEPS,
    MAX_PROMPT_CHARS,
    MAX_COMPRESSION_TOKENS,
    PREF_FILE,
    SERVER_PATH,
    SERVER_COMMAND,
    DETECTED_GENRES,
    validate_config
)

# Validate configuration on startup
validate_config()

mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# -----------------------------
# SYSTEM PROMPT (LARGE-PROMPT SAFE)
# -----------------------------
SYSTEM = """
You are an autonomous AI agent with access to external tools via MCP.
You MUST always respond in valid JSON format.

========================
CORE BEHAVIOR
========================
- Be friendly, concise, and accurate
- If real-world, dynamic, or factual data is required, call the appropriate tool
- NEVER hallucinate or make up tool results
- Use actual tool output values in your final answer

========================
TOOL RULES
========================
- Call ONE tool at a time
- NEVER repeat a tool that has already been called
- NEVER invent tool names or arguments
- Use tools when you need real-time data (weather, books, jokes, trivia, etc.)
- When a user asks for book recommendations, use the book_recs tool with the topic

Tool call format:
{"action":"tool_name","args":{...}}

========================
FINAL OUTPUT
========================
When you have all the information needed, respond with:

{
  "action": "final",
  "answer": "Your response using the tool data"
}
"""

# -----------------------------
# Preferences helpers
# -----------------------------
def load_prefs() -> Dict[str, Any]:
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_prefs(prefs: Dict[str, Any]):
    with open(PREF_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)

def extract_genre(text: str) -> str | None:
    for g in DETECTED_GENRES:
        if g.strip() in text.lower():
            return g.strip()
    return None

# -----------------------------
# Large prompt compression
# -----------------------------
def compress_large_input(user_message: str) -> str:
    if len(user_message) <= MAX_PROMPT_CHARS:
        return user_message

    try:
        response = mistral_client.chat.complete(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract only the actionable request:\n{user_message[:MAX_PROMPT_CHARS]}"
                }
            ],
            temperature=COMPRESSION_TEMPERATURE,
            max_tokens=MAX_COMPRESSION_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return user_message[:MAX_PROMPT_CHARS]

def contains_lat_long(text: str) -> bool:
    return bool(re.search(r"-?\d{1,3}\.\d+\s*,\s*-?\d{1,3}\.\d+", text))

# -----------------------------
# Tool result normalization
# -----------------------------
def normalize_tool_result(result) -> str:
    """Extract JSON data from MCP tool result."""
    try:
        # Try .json() method first
        if hasattr(result, 'json') and callable(result.json):
            return json.dumps(result.json())
        # Try .json attribute
        if hasattr(result, 'json') and not callable(result.json):
            return json.dumps(result.json)
        # Try content[0].text
        if hasattr(result, 'content') and result.content:
            return result.content[0].text if result.content[0].text else "{}"
        # Fallback: try to convert to string
        return str(result)
    except Exception:
        return "{}"

# -----------------------------
# LLM JSON helper (Mistral)
# -----------------------------
def llm_json(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    response = mistral_client.chat.complete(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

# -----------------------------
# MAIN AGENT LOOP (UI-safe)
# -----------------------------
async def run_agent_once(user_message: str) -> Dict[str, Any]:
    server_path = SERVER_PATH

    original_user_query = user_message
    user_message = compress_large_input(user_message)

    tools_used: List[str] = []
    prefs = load_prefs()

    history: List[Dict[str, str]] = [
        {"role": "user", "content": SYSTEM},
    ]

    # Preference learning
    genre = extract_genre(user_message)
    if genre:
        prefs["favorite_genre"] = genre
        save_prefs(prefs)

    if "favorite_genre" in prefs and "book" in user_message.lower():
        history.append({
            "role": "user",
            "content": f"Note: User prefers {prefs['favorite_genre']} books."
        })

    history.append({"role": "user", "content": user_message})

    if contains_lat_long(user_message):
        history.append({
            "role": "user",
            "content": "Hint: Coordinates detected in the query - you may need weather data."
        })

    async with AsyncExitStack() as stack:
        stdio = await stack.enter_async_context(
            stdio_client(
                StdioServerParameters(command=SERVER_COMMAND, args=[server_path])
            )
        )
        r_in, w_out = stdio
        session = await stack.enter_async_context(ClientSession(r_in, w_out))
        await session.initialize()

        tools = (await session.list_tools()).tools
        valid_tool_names = {t.name for t in tools}

        history.insert(1, {
            "role": "user",
            "content": f"Available tools: {', '.join(valid_tool_names)}"
        })

        for _ in range(MAX_STEPS):
            decision = llm_json(history)
            action = decision.get("action")

            # ---------- FINAL ----------
            if action == "final":
                return {
                    "action": "final",
                    "answer": decision.get("answer", ""),
                    "tools_used": tools_used,
                }

            # ---------- INVALID ACTION ----------
            if not action:
                history.append({
                    "role": "user",
                    "content": "You must either call a valid tool or finalize."
                })
                continue

            if action not in valid_tool_names:
                history.append({
                    "role": "user",
                    "content": f"'{action}' is not a valid tool. Choose from the available tools."
                })
                continue

            if action in tools_used:
                history.append({
                    "role": "user",
                    "content": f"Tool '{action}' already completed. Choose another tool or finalize."
                })
                continue

            # ---------- TOOL CALL ----------
            result = await session.call_tool(action, decision.get("args", {}))
            payload = normalize_tool_result(result)

            tools_used.append(action)

            history.append({
                "role": "user",
                "content": f"Tool '{action}' result: {payload}"
            })

        # If MAX_STEPS hit, force final safely
        history.append({
            "role": "user",
            "content": (
                "Now generate the FINAL answer.\n\n"
                f"User's original request:\n{original_user_query}\n\n"
                "Use ALL relevant tool outputs above."
            )
        })
        decision = llm_json(history)
        return {
            "action": "final",
            "answer": decision.get("answer", ""),
            "tools_used": tools_used,
        }

if __name__ == "__main__":
    pass