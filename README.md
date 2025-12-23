# Autonomous AI Agent with MCP Tools

An intelligent AI agent that autonomously decides when and which tools to use based on user requests. Built with Model Context Protocol (MCP) for tool integration and Ollama for local LLM inference.

## Features

✅ **Autonomous Tool Calling**: Agent decides by itself which tools to use - no keyword matching
✅ **Natural Conversation**: Combines LLM reasoning with tool outputs for comprehensive answers
✅ **Gradio UI**: Clean chat interface showing tools used and reasoning steps
✅ **MCP Integration**: Extensible tool framework with multiple pre-built tools
✅ **Local LLM**: Uses Ollama (llama3.2) for complete privacy

## Architecture

```
User Query → Agent (LLM) → Tool Decision → MCP Tools → Results → Final Answer
                ↑                                                        ↓
                └─────────── reasoning loop (up to 6 iterations) ───────┘
```

## Available Tools

The agent has access to these MCP tools:

1. **get_weather**(latitude, longitude) - Real-time weather data
2. **book_recs**(topic, limit) - Book recommendations from OpenLibrary
3. **random_joke**() - Get a safe joke
4. **random_dog**() - Random dog image (base64)
5. **trivia**() - Trivia question with multiple choice

## Setup

### Prerequisites

1. **Python 3.11+**
2. **Ollama** with llama3.2 model installed:
   ```bash
   ollama pull llama3.2
   ```

### Installation

```bash
# Install dependencies
pip install -e .

# Or manually:
pip install gradio mcp ollama requests
```

## Usage

### 1. Web UI (Recommended)

```bash
python app.py
```

Then open the URL shown in terminal (usually http://127.0.0.1:7860)

### 2. Command Line

```bash
python agent.py
```

## Test Prompts

Use these prompts to verify the agent is working correctly:

### Weather Tool
- "What's the weather like in San Francisco?" (should ask for or infer coordinates)
- "Tell me the weather at latitude 37.7749, longitude -122.4194"

### Book Recommendations
- "Recommend some science fiction books"
- "I want to read about artificial intelligence"
- "Suggest books on psychology"

### Joke Tool
- "Tell me a joke"
- "Make me laugh"
- "I need something funny"

### Dog Images
- "Show me a cute dog picture"
- "I want to see a random dog"

### Trivia
- "Give me a trivia question"
- "Test my knowledge"
- "Ask me something interesting"

### Multi-Tool Requests
- "Tell me the weather in NYC and then tell me a joke" (should use both tools)
- "Recommend a book and show me a dog picture"

### No-Tool Requests (Pure LLM)
- "What is the capital of France?"
- "Explain quantum physics"
- "Write a haiku about coding"

## How It Works

### Agent Decision Process

1. **Receives user message**
2. **LLM analyzes** and decides: need tool? Or can answer directly?
3. If tool needed:
   - Outputs `TOOL_CALL: {"tool": "name", "args": {...}}`
   - Executes tool via MCP
   - Adds result to conversation history
   - Loops back to step 2 (max 6 iterations)
4. When ready to answer:
   - Outputs `FINAL_ANSWER: natural language response`
5. **Returns** answer + tools used + reasoning steps

### Key Design Principles

- **No keyword matching**: LLM decides based on understanding, not hardcoded rules
- **Natural language first**: Agent speaks naturally, not in JSON
- **Tool transparency**: UI shows which tools were used
- **Reasoning visibility**: See the agent's thought process
- **Graceful degradation**: If tools fail, agent continues with available info

## File Structure

```
.
├── agent.py          # Core agent logic (CLI + run_agent_once function)
├── app.py            # Gradio web interface
├── server.py         # MCP server with tool definitions
├── pyproject.toml    # Dependencies
└── README.md         # This file
```

## Customization

### Adding New Tools

Edit [server.py](server.py) and add:

```python
@mcp.tool()
def my_tool(arg1: str, arg2: int) -> Dict[str, Any]:
    """Description of what this tool does"""
    # Implementation
    return {"status": "ok", "result": "..."}
```

The agent will automatically discover and use new tools!

### Changing the LLM

Edit [agent.py](agent.py):

```python
def llm_call(messages: List[Dict[str, str]], use_json: bool = False) -> str:
    params = {
        "model": "llama3.2",  # Change this
        "messages": messages,
        "options": {"temperature": 0.7},  # Adjust temperature
    }
```

Supported models: Any Ollama model (llama2, mistral, phi, etc.)

### Adjusting Agent Behavior

Edit the `SYSTEM` prompt in [agent.py](agent.py) to change:
- When agent should use tools
- Response style
- Reasoning approach

## Requirements Met

✅ Agent calls tools autonomously (no keyword matching)  
✅ LLM decides by itself what tool to use and when  
✅ UI shows chat interface with plain text output  
✅ Tools used are displayed to user  
✅ Output combines LLM reasoning + tool results  
✅ MCP tools work properly and give accurate answers  

## Troubleshooting

### "Ollama connection error"
- Make sure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`
- Pull if needed: `ollama pull llama3.2`

### "Tool not found"
- Verify server.py is in the same directory
- Check MCP server starts without errors: `python server.py`

### Agent doesn't use tools
- Check system prompt in agent.py
- Try more explicit requests
- Verify tools are listed at startup

### UI doesn't show reasoning steps
- This is normal if agent answers directly (1 iteration)
- Try multi-step requests to see reasoning

## Performance Notes

- First response may be slow (LLM initialization)
- Each tool call adds ~2-3 seconds
- Agent typically uses 1-3 iterations per request
- Max 6 iterations prevents infinite loops

## License

MIT

## Contributing

To add features:
1. New tools → edit server.py
2. UI improvements → edit app.py
3. Agent logic → edit agent.py

The agent will automatically adapt to new tools without code changes!
