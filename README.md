# 🌈 Weekend Wizard

Weekend Wizard is an **agentic AI assistant** that helps you plan the perfect weekend based on your mood, location, and preferences.

It is built using a **local LLM + MCP (Model Context Protocol) tools**, following a clean agent–tool separation and production-grade design.

---

## ✨ Features

- 🧠 Autonomous AI agent powered by Cerebras API that decides when to call tools  
- 🛠 MCP-based tool integration (weather, books, jokes, dog images, trivia)
- ⚡ Fast inference with qwen-3-32b model
- 🎨 Clean Gradio chat UI
- 🔐 Secure handling of API keys via environment variables
- 🧩 Modular and extensible agent architecture
- 📚 Smart preference learning for book recommendations

---

## 🏗 Architecture Overview

- **Agent Layer**  
  Decides *what to do* using Cerebras AI (call tools or provide final answer)

- **Tool Layer (MCP Servers)**  
  Provides real-world capabilities:
  - Weather data (Open-Meteo API)
  - City coordinates (Open-Meteo Geocoding)
  - Book recommendations (Project Gutenberg)
  - Random jokes (JokeAPI)
  - Dog images (Dog CEO API)
  - Trivia questions (Open Trivia DB)

- **UI Layer**  
  Gradio-based conversational interface with tool usage display

---

## 🚀 Tech Stack

- Python 3.11+
- Cerebras AI API (qwen-3-32b)
- MCP (Model Context Protocol)
- Gradio 6.0+
- FastMCP for tool server
- Requests for API calls
- Python-dotenv for environment management

---

## 📦 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/PS-dhruvi-bhimani/Weekend-Wizard.git
cd Weekend-Wizard

### 2. Create a virtual environment & install dependencies

Using uv (recommended):

```bash
uv venv
uv pip install -r requirements.txt
```

Or using pip:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Then edit `.env` and add your Cerebras API key:

```env
CEREBRAS_API_KEY=your_cerebras_api_key_here
```

Get your Cerebras API key from: https://cloud.cerebras.ai/

The `.env.example` file contains all available configuration options with documentation. You can customize:
- Model settings (temperature, max steps, etc.)
- API endpoints and retry settings
- UI appearance and text
- Tool behavior and parameters
- Logging preferences

All hard-coded values have been moved to the configuration system for easy customization!
### 4. Run the Gradio UI

python app.py 

Gradio will start a local server 
http://127.0.0.1:7860

💬 Example Prompts

Try prompts like:

- "Plan a cozy Saturday in New York at (40.7128, -74.0060). Include the current weather, 2 book ideas about mystery, one joke, and a dog pic"
- "What's the weather like in Paris? Also suggest a good sci-fi book"
- "Tell me a joke and show me a cute dog picture"
- "Give me a trivia question and recommend a fantasy book"
- "Suggest books about philosophy and tell me a joke"

The agent will automatically:
- Determine which tools are needed
- Call them in the correct order
- Provide a comprehensive answer using all tool outputs

🛠️ The UI shows which tools were used at the bottom of each response.
