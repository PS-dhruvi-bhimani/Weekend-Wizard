"""
Configuration module for Weekend Wizard Agent
Centralizes all configuration values to avoid hard-coding
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# Model Configuration
MODEL = os.getenv("MODEL", "qwen-3-32b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
COMPRESSION_TEMPERATURE = float(os.getenv("COMPRESSION_TEMPERATURE", "0.1"))

# Agent Configuration
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
MAX_COMPRESSION_TOKENS = int(os.getenv("MAX_COMPRESSION_TOKENS", "300"))

# File Paths
PREF_FILE = os.getenv("PREF_FILE", "preferences.json")
SERVER_PATH = os.getenv("SERVER_PATH", "server.py")
SYSTEM_PROMPT_FILE = os.getenv("SYSTEM_PROMPT_FILE", "system_prompt.txt")

# Server Configuration
SERVER_COMMAND = os.getenv("SERVER_COMMAND", "python")

# Tool Configuration - Retry Settings
TOOL_RETRY_COUNT = int(os.getenv("TOOL_RETRY_COUNT", "3"))
TOOL_TIMEOUT = int(os.getenv("TOOL_TIMEOUT", "15"))

# Tool Configuration - API Endpoints
GEOCODING_API_URL = os.getenv("GEOCODING_API_URL", "https://geocoding-api.open-meteo.com/v1/search")
WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
BOOKS_API_URL = os.getenv("BOOKS_API_URL", "https://www.googleapis.com/books/v1/volumes")
DOG_API_URL = os.getenv("DOG_API_URL", "https://dog.ceo/api/breeds/image/random")
TRIVIA_API_URL = os.getenv("TRIVIA_API_URL", "https://opentdb.com/api.php")

# Tool Configuration - API Parameters
GEOCODING_COUNT = int(os.getenv("GEOCODING_COUNT", "1"))
BOOK_RECS_LIMIT = int(os.getenv("BOOK_RECS_LIMIT", "5"))
TRIVIA_AMOUNT = int(os.getenv("TRIVIA_AMOUNT", "1"))
TRIVIA_TYPE = os.getenv("TRIVIA_TYPE", "multiple")

# Weather API Parameters
WEATHER_CURRENT_PARAMS = os.getenv("WEATHER_CURRENT_PARAMS", "temperature_2m,weather_code,wind_speed_10m")
WEATHER_TIMEZONE = os.getenv("WEATHER_TIMEZONE", "auto")

# MCP Server Configuration
MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "WeekendWizardTools")

# User Preferences - Genre Detection
DETECTED_GENRES = os.getenv("DETECTED_GENRES", "sci-fi,science fiction,fantasy,romance,mystery,thriller,history,philosophy").split(",")

# Gradio UI Configuration
GRADIO_THEME = os.getenv("GRADIO_THEME", "Soft")
GRADIO_CHATBOT_HEIGHT = int(os.getenv("GRADIO_CHATBOT_HEIGHT", "420"))
GRADIO_TEXTBOX_SCALE = int(os.getenv("GRADIO_TEXTBOX_SCALE", "7"))

# UI Text Configuration
UI_TITLE = os.getenv("UI_TITLE", "weekend - wizard")
UI_PLACEHOLDER = os.getenv("UI_PLACEHOLDER", "Tell me how you're feeling or what you need...")
UI_SUBMIT_BUTTON = os.getenv("UI_SUBMIT_BUTTON", "✨ Ask")

# Greeting Configuration
GREETING_MORNING = os.getenv("GREETING_MORNING", "Good Morning ☀️")
GREETING_AFTERNOON = os.getenv("GREETING_AFTERNOON", "Good Afternoon 🌤️")
GREETING_EVENING = os.getenv("GREETING_EVENING", "Good Evening ✨")
MORNING_HOUR_CUTOFF = int(os.getenv("MORNING_HOUR_CUTOFF", "12"))
AFTERNOON_HOUR_CUTOFF = int(os.getenv("AFTERNOON_HOUR_CUTOFF", "17"))

# Logging Configuration
LOG_SEPARATOR_WIDTH = int(os.getenv("LOG_SEPARATOR_WIDTH", "60"))
LOG_MESSAGE_PREVIEW_LENGTH = int(os.getenv("LOG_MESSAGE_PREVIEW_LENGTH", "80"))
LOG_RESPONSE_PREVIEW_LENGTH = int(os.getenv("LOG_RESPONSE_PREVIEW_LENGTH", "100"))

# Validation
def validate_config():
    """Validate required configuration values"""
    if not CEREBRAS_API_KEY:
        raise RuntimeError("CEREBRAS_API_KEY not found in environment variables.")
    return True

def load_system_prompt():
    """Load system prompt from file or use default"""
    if os.path.exists(SYSTEM_PROMPT_FILE):
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    # Default prompt if file doesn't exist
    return """You are an autonomous AI agent with access to external tools via MCP.
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
- When coordinates (latitude, longitude) are provided in the format (lat, long) or "lat, long", extract them and use get_weather tool directly
- For city names, use city_to_coords first, then get_weather with the returned coordinates

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
