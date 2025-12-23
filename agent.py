# agent.py
import asyncio
import json
import os
import base64
import re
from contextlib import AsyncExitStack
from typing import Dict, Any, List

from dotenv import load_dotenv
from groq import Groq

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# -------------------------------------------------
# ENV + GROQ SETUP
# -------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found. Make sure it exists in your .env file."
    )

groq_client = Groq(api_key=GROQ_API_KEY)

# -------------------------------------------------
# SYSTEM PROMPT (CLEAN + PRODUCTION GRADE)
# -------------------------------------------------
SYSTEM = """
You are an autonomous AI agent with access to tools. Always respond in JSON format.

Rules:
- Carefully analyze the user's request. If they ask for multiple things or specific quantities, identify EXACTLY what they need.
- Examples:
  * "two dog images" = call random_dog tool EXACTLY 2 times
  * "a joke and a dog image" = call random_joke once, then random_dog once
  * "3 book recommendations" = call book_recs with limit=3 once
- Call tools ONE AT A TIME: respond with JSON: {"action":"tool_name","args":{...}}
- ONLY use tools from the available tools list - NEVER make up tool names.
- After receiving each tool result, count what you've completed and decide:
  * If you need to call the SAME tool again (e.g., for multiple images) → call it again
  * If there are MORE different tasks → call the next different tool
  * If ALL tasks are complete (exact quantity met) → provide the final answer
- When giving the final answer, respond with JSON: {"action":"final","answer":"..."}

For the final answer:
- Present each result naturally and separately
- If user asked for multiple of the same thing (like 2 dog images), show each one
- DO NOT combine unrelated results into one paragraph
- Be natural and conversational
- DO NOT mention tool names or say 'I used a tool'
- DO NOT include any technical terms like 'IMAGE_PLACEHOLDER', 'Tool result', or similar
- Just deliver the information the user requested in a friendly way
"""

# -------------------------------------------------
# LLM CALL (GROQ) - CONFIGURABLE PARAMETERS
# -------------------------------------------------
def llm_call(messages: List[Dict[str, str]], temperature: float = 0.5, top_p: float = 0.9) -> str:
    """
    Call Groq LLM with configurable parameters.
    
    Args:
        temperature: Controls randomness (0.0-2.0). Lower = more focused, higher = more creative.
        top_p: Controls diversity via nucleus sampling (0.0-1.0).
    """
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


# -------------------------------------------------
# SINGLE-TURN AGENT (USED BY UI)
# -------------------------------------------------
async def run_agent_once(user_message: str) -> Dict[str, Any]:
    server_path = "server.py"

    tools_used: List[str] = []
    history: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_message},
    ]

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

        tool_list = "\n".join([f"- {t.name}: {t.description}" for t in tools])
        history[0]["content"] += f"\n\nAvailable tools:\n{tool_list}"
        
        # Track tool results with their names for structured output
        tool_results = []

        for iteration in range(12):  # Increased to handle more multiple requests
            # Before each decision, add summary of pending tool results if this is not the first iteration
            if iteration > 0 and tool_results:
                # Count how many times each tool was called
                tool_counts = {}
                for tr in tool_results:
                    tool_counts[tr['name']] = tool_counts.get(tr['name'], 0) + 1
                
                completed_summary = [f"{name} ({count}x)" if count > 1 else name 
                                    for name, count in tool_counts.items()]
                
                history.append({
                    "role": "system",
                    "content": f"Tools completed: {', '.join(completed_summary)}. Total calls: {len(tool_results)}. Check if the exact quantity requested by the user is met. If not, continue."
                })
            
            response_text = llm_call(history)
            
            # Parse JSON and handle list or dict responses
            try:
                decision = json.loads(response_text)
                
                # Handle if response is a list - take first element
                if isinstance(decision, list):
                    if len(decision) > 0:
                        decision = decision[0]
                    else:
                        decision = {"action": "final", "answer": "No response generated"}
                
                # Ensure it's a dict
                if not isinstance(decision, dict):
                    decision = {"action": "final", "answer": str(decision)}
                    
            except json.JSONDecodeError as e:
                return {
                    "answer": f"Error: Could not parse response. {str(e)}",
                    "tools_used": tools_used,
                }

            # ✅ FINAL ANSWER
            if decision.get("action") == "final":
                answer = decision.get("answer", "")
                
                # Append any images that are NOT already in the answer
                for tool_info in tool_results:
                    # Check if this is an image
                    is_image = (
                        tool_info["name"] == "random_dog" or 
                        "![" in tool_info["content"] or 
                        "data:image" in tool_info["content"]
                    )
                    
                    if is_image:
                        # Only append this specific image if it's not already in the answer
                        if tool_info["content"] not in answer:
                            answer += f"\n\n{tool_info['content']}"
                
                # Append tools used at the end
                if tools_used:
                    answer += f"\n\n---\n🛠️ Tools used: {', '.join(tools_used)}"
                
                return {
                    "answer": answer,
                    "tools_used": tools_used,
                }

            # 🔧 TOOL CALL
            tool_name = decision.get("action")
            tool_args = decision.get("args", {})

            # 🚫 BLOCK HALLUCINATED TOOLS
            if tool_name not in valid_tool_names:
                history.append({
                    "role": "system",
                    "content": f"ERROR: Tool '{tool_name}' does not exist. Available tools: {', '.join(valid_tool_names)}. Use an available tool or provide final answer."
                })
                continue

            # ✅ REAL TOOL CALL
            tools_used.append(tool_name)

            result = await session.call_tool(tool_name, tool_args)
            payload = (
                result.content[0].text
                if result.content
                else result.model_dump_json()
            )
            
            # Parse JSON payload to check for images
            try:
                result_data = json.loads(payload)
                # Check if this is an image result
                if isinstance(result_data, dict) and "image_base64" in result_data:
                    # Store the image data separately for the final answer
                    image_b64 = result_data["image_base64"]
                    mime_type = result_data.get("mime_type", "image/jpeg")
                    
                    # Store formatted image content
                    image_markdown = f"![Dog Image](data:{mime_type};base64,{image_b64})"
                    tool_results.append({
                        "name": tool_name,
                        "content": image_markdown
                    })
                    
                    # Tell the LLM an image is ready to display
                    history.append({
                        "role": "assistant",
                        "content": f"Tool result: Dog image received successfully.",
                    })
                else:
                    # Store regular tool result
                    tool_results.append({
                        "name": tool_name,
                        "content": payload
                    })
                    history.append({
                        "role": "assistant",
                        "content": f"Tool result: {payload}",
                    })
            except:
                # Store unparsed result
                tool_results.append({
                    "name": tool_name,
                    "content": payload
                })
                history.append({
                    "role": "assistant",
                    "content": f"Tool result: {payload}",
                })

        return {
            "answer": "I couldn’t complete the request.",
            "tools_used": tools_used,
        }

if __name__ == "__main__":
    asyncio.run(main())

