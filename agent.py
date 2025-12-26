import asyncio
import json
import sys
import os
import re
from typing import Dict, Any, List
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from mistralai import Mistral

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise RuntimeError("MISTRAL_API_KEY not found.")

mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# -----------------------------
# CONFIG
# -----------------------------
MODEL = "mistral-small-latest"  # Fast Mistral model
TEMPERATURE = 0.2
MAX_STEPS = 8
MAX_PROMPT_CHARS = 8000

PREF_FILE = "preferences.json"

# -----------------------------
# SYSTEM PROMPT (LARGE-PROMPT SAFE)
# -----------------------------
SYSTEM = """
You are an autonomous weekend-planning AI agent with access to external tools via MCP.
You MUST always respond in valid JSON.

========================
CORE BEHAVIOR
========================
- Be friendly, concise, and accurate.
- Handle very large or complex prompts calmly.
- If real-world, dynamic, or factual data is required, you MUST call a tool.
- NEVER hallucinate tool data.

========================
MANDATORY TOOL USAGE
========================
You MUST call a tool if the user asks for:
- Weather, temperature, wind, outdoor conditions → get_weather
- City names without coordinates → city_to_coords
- Book recommendations or genres → book_recs
- Jokes or humor → random_joke
- Images, dog photos → random_dog
- Trivia → trivia

========================
TOOL RULES
========================
- Call ONE tool at a time.
- You MUST identify which tools are REQUIRED to fully satisfy the user's request.
- For every REQUIRED tool, you MUST call it exactly once.
- NEVER repeat a tool that has already completed.
- NEVER invent tool names or arguments.
- Always use actual tool output values in your answer.
- You are NOT allowed to finalize until ALL REQUIRED tools have been successfully called.

Tool call format (JSON ONLY):
{"action":"tool_name","args":{...}}

========================
FINAL OUTPUT
========================
When finished, respond ONLY with:

{
  "action": "final",
  "answer": "A friendly response that references specific tool data"
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
    genres = [
        "sci-fi", "science fiction", "fantasy", "romance",
        "mystery", "thriller", "history", "philosophy"
    ]
    for g in genres:
        if g in text.lower():
            return g
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
            temperature=0.1,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return user_message[:MAX_PROMPT_CHARS]

def contains_lat_long(text: str) -> bool:
    return bool(re.search(r"-?\d{1,3}\.\d+\s*,\s*-?\d{1,3}\.\d+", text))

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
# Infer Required Tools (LLM-driven)
# -----------------------------
def infer_required_tools(user_message: str, valid_tool_names: set[str]) -> set[str]:
    """Use LLM to determine which tools are STRICTLY REQUIRED for the user's request."""
    response = mistral_client.chat.complete(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "From the user's request, determine which tools are STRICTLY REQUIRED "
                    "to answer it. Do NOT include optional or enrichment tools.\n\n"
                    "Return JSON in this format:\n"
                    '{ "required_tools": ["tool1", "tool2"] }'
                )
            },
            {
                "role": "user",
                "content": f"User request:\n{user_message}\n\nAvailable tools:\n{', '.join(valid_tool_names)}"
            }
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)
    return set(data.get("required_tools", []))

# -----------------------------
# MAIN AGENT LOOP (UI-safe)
# -----------------------------
async def run_agent_once(user_message: str) -> Dict[str, Any]:
    server_path = "server.py"

    original_user_query = user_message
    user_message = compress_large_input(user_message)

    tools_used: List[str] = []
    prefs = load_prefs()

    history: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM},
    ]

    # Preference learning
    genre = extract_genre(user_message)
    if genre:
        prefs["favorite_genre"] = genre
        save_prefs(prefs)

    if "favorite_genre" in prefs and "book" in user_message.lower():
        history.append({
            "role": "system",
            "content": f"User prefers {prefs['favorite_genre']} books."
        })

    history.append({"role": "user", "content": user_message})

    if contains_lat_long(user_message):
        history.append({
            "role": "system",
            "content": "Coordinates detected. Weather data is required."
        })

    async with AsyncExitStack() as stack:
        stdio = await stack.enter_async_context(
            stdio_client(
                StdioServerParameters(command="python", args=[server_path])
            )
        )
        r_in, w_out = stdio
        session = await stack.enter_async_context(ClientSession(r_in, w_out))
        await session.initialize()

        tools = (await session.list_tools()).tools
        valid_tool_names = {t.name for t in tools}

        # Compute required tools using LLM (model-driven, not hardcoded)
        required_tools = infer_required_tools(user_message, valid_tool_names)

        history.insert(1, {
            "role": "system",
            "content": f"Available tools: {', '.join(valid_tool_names)}"
        })

        for _ in range(MAX_STEPS):
            decision = llm_json(history)
            action = decision.get("action")

            # ---------- FINAL ----------
            if action == "final":
                final_answer = decision.get("answer", "")
                break

            # ---------- INVALID ACTION ----------
            if not action:
                history.append({
                    "role": "system",
                    "content": "You must either call a valid tool or finalize."
                })
                continue

            if action not in valid_tool_names:
                history.append({
                    "role": "system",
                    "content": f"'{action}' is not a valid tool. Choose from the available tools."
                })
                continue

            if action not in required_tools:
                history.append({
                    "role": "system",
                    "content": (
                        f"Tool '{action}' is NOT required for this request. "
                        f"Only these tools are allowed: {', '.join(required_tools)}."
                    )
                })
                continue

            if action in tools_used:
                history.append({
                    "role": "system",
                    "content": f"Tool '{action}' already completed. Choose another tool or finalize."
                })
                continue

            # ---------- TOOL CALL ----------
            result = await session.call_tool(action, decision.get("args", {}))
            payload = result.content[0].text if result.content else "{}"

            tools_used.append(action)

            history.append({
                "role": "system",
                "content": f"Tool '{action}' result (may be partial): {payload}"
            })
            history.append({
                "role": "system",
                "content": (
                    "Continue calling required tools if more information is needed. "
                    "Only finalize when all necessary tools are completed."
                )
            })

        # If MAX_STEPS hit, force final safely
        if 'final_answer' not in locals():
            history.append({
                "role": "system",
                "content": (
                    "Now generate the FINAL answer.\n\n"
                    f"User's original request:\n{original_user_query}\n\n"
                    "Use ALL relevant tool outputs above.\n"
                    "Ignore any tool failures unless they block the request.\n"
                    "Do NOT apologize unless the entire request is impossible.\n"
                    "Focus on fulfilling the user's original intent."
                )
            })
            decision = llm_json(history)
            final_answer = decision.get("answer", "")

        return {
            "action": "final",
            "answer": final_answer if 'final_answer' in locals() else "",
            "tools_used": tools_used,
        }

if __name__ == "__main__":
    pass