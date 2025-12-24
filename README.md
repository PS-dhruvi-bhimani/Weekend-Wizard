# 🌈 Weekend Wizard

Weekend Wizard is an **agentic AI assistant** that helps you plan the perfect weekend based on your mood, location, and preferences.

It is built using a **local LLM + MCP (Model Context Protocol) tools**, following a clean agent–tool separation and production-grade design.

---

## ✨ Features

- 🧠 Autonomous AI agent that decides when to call tools  
- 🛠 MCP-based tool integration (weather, places, images, etc.)
- ⚡ Local LLM inference (Ollama / Groq support)
- 🎨 Clean Gradio chat UI
- 🔐 Secure handling of environment variables
- 🧩 Modular and extensible agent architecture

---

## 🏗 Architecture Overview

- **Agent Layer**  
  Decides *what to do* (answer directly or call tools)

- **Tool Layer (MCP Servers)**  
  Provides real-world capabilities like weather, city info, images

- **UI Layer**  
  Gradio-based conversational interface

---

## 🚀 Tech Stack

- Python 3.10+
- MCP (Model Context Protocol)
- Ollama / Groq LLMs
- Gradio
- uv (Python package manager)

---

## 📦 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/PS-dhruvi-bhimani/Weekend-Wizard.git
cd Weekend-Wizard

### 2. Create a virtual environment & install dependencies

Using uv (recommended):

uv venv
uv pip install -r requirements.txt


If you don’t have uv:

pip install uv

### 3️. Configure environment variables

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key_here
### 4. Run the Gradio UI

python app.py 

Gradio will start a local server 
http://127.0.0.1:7860

💬 Example Prompts

Try prompts like:

“Plan a cozy Saturday in Bangalore”

“I feel tired, suggest a relaxing Sunday”

“Plan a fun weekend with friends if the weather is good”

  “Show me a dog image and suggest a nearby place to visit”

The agent will automatically decide when to call tools.
