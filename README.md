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
