import asyncio
import json
import sys
import os
import re
from typing import Dict, Any, List
from contextlib import AsyncExitStack

from cerebras.cloud.sdk import Cerebras

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import configuration
from config import (
    CEREBRAS_API_KEY,
    MODEL,
    TEMPERATURE,
    COMPRESSION_TEMPERATURE,
    MAX_STEPS,
    MAX_PROMPT_CHARS,
    MAX_COMPRESSION_TOKENS,
    SERVER_PATH,
    SERVER_COMMAND,
    validate_config,
    load_system_prompt
)

# Validate configuration on startup
validate_config()

cerebras_client = Cerebras(api_key=CEREBRAS_API_KEY)

# Load system prompt from configuration
SYSTEM = load_system_prompt()

# -----------------------------
# Large prompt compression
# -----------------------------
def compress_large_input(user_message: str) -> str:
    if len(user_message) <= MAX_PROMPT_CHARS:
        return user_message

    try:
        response = cerebras_client.chat.completions.create(
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
# LLM JSON helper (Cerebras)
# -----------------------------
def llm_json(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    try:
        response = cerebras_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if content is None:
            print("[DEBUG] LLM returned None content")
            print(f"[DEBUG] Response: {response}")
            return {"action": "final", "answer": "I apologize, but I encountered an issue processing your request."}
        
        # Try to parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError as je:
            print(f"[DEBUG] JSON decode error: {je}")
            print(f"[DEBUG] Content was: {content}")
            return {"action": "final", "answer": "I apologize, but I encountered an issue processing your request."}
    except Exception as e:
        print(f"[DEBUG] LLM call exception: {e}")
        return {"action": "final", "answer": f"I apologize, but I encountered an error: {str(e)}"}

# -----------------------------
# MAIN AGENT LOOP (UI-safe)
# -----------------------------
async def run_agent_once(user_message: str) -> Dict[str, Any]:
    server_path = SERVER_PATH

    original_user_query = user_message
    user_message = compress_large_input(user_message)

    tools_used: List[str] = []

    history: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_message},
    ]

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

        # Create tool descriptions for the LLM
        tool_descriptions = []
        for tool in tools:
            tool_info = f"{tool.name}"
            if tool.description:
                tool_info += f": {tool.description}"
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                if 'properties' in schema:
                    args = []
                    for prop_name, prop_info in schema['properties'].items():
                        arg_desc = prop_name
                        if isinstance(prop_info, dict) and 'description' in prop_info:
                            arg_desc += f" ({prop_info['description']})"
                        args.append(arg_desc)
                    if args:
                        tool_info += f" - args: {', '.join(args)}"
            tool_descriptions.append(tool_info)
        
        # Add tool info to history
        history.insert(1, {
            "role": "user",
            "content": f"Available tools:\n" + "\n".join(f"- {desc}" for desc in tool_descriptions)
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
                    "role": "assistant",
                    "content": json.dumps(decision)
                })
                history.append({
                    "role": "user",
                    "content": "You must either call a valid tool or finalize."
                })
                continue

            if action not in valid_tool_names:
                history.append({
                    "role": "assistant",
                    "content": json.dumps(decision)
                })
                history.append({
                    "role": "user",
                    "content": f"'{action}' is not a valid tool. Available tools: {', '.join(valid_tool_names)}"
                })
                continue

            if action in tools_used:
                history.append({
                    "role": "assistant",
                    "content": json.dumps(decision)
                })
                history.append({
                    "role": "user",
                    "content": f"Tool '{action}' already used. Choose another tool or finalize."
                })
                continue

            # ---------- TOOL CALL ----------
            args = decision.get("args", {})
            try:
                result = await session.call_tool(action, args)
                payload = normalize_tool_result(result)
                tools_used.append(action)
                
                # Debug: print what we got
                print(f"[DEBUG] Tool '{action}' called with args: {args}")
                print(f"[DEBUG] Tool result payload: {payload[:200]}...")
                
                # Add assistant acknowledgment, then user with tool result
                history.append({
                    "role": "assistant",
                    "content": json.dumps({"action": action, "args": args})
                })
                history.append({
                    "role": "user",
                    "content": f"Tool '{action}' returned: {payload}\n\nNow either call another tool or provide the final answer."
                })
            except Exception as e:
                error_msg = f"Error calling tool '{action}': {str(e)}"
                print(f"[DEBUG] {error_msg}")
                history.append({
                    "role": "assistant",
                    "content": json.dumps({"action": action, "args": args})
                })
                history.append({
                    "role": "user",
                    "content": error_msg + "\n\nChoose a different tool or provide final answer."
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