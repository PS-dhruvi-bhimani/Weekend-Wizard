"""
Configuration module for Weekend Wizard Agent
Centralizes all configuration values to avoid hard-coding
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Model Configuration
MODEL = os.getenv("MODEL", "mistral-small-latest")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
COMPRESSION_TEMPERATURE = float(os.getenv("COMPRESSION_TEMPERATURE", "0.1"))

# Agent Configuration
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
MAX_COMPRESSION_TOKENS = int(os.getenv("MAX_COMPRESSION_TOKENS", "300"))

# File Paths
PREF_FILE = os.getenv("PREF_FILE", "preferences.json")
SERVER_PATH = os.getenv("SERVER_PATH", "server.py")

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
    if not MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY not found in environment variables.")
    return True
