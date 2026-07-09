"""
=========================================================
Project : Advanced Voice Assistant
Internship : Oasis Infobyte - Python Programming
Task : Task 1 - Voice Assistant

File : config.py

Description:
This file stores all configurable settings used by the
Voice Assistant application, including GUI settings,
voice engine parameters, API keys, and application
constants.

Author : Ibrar Ahmad
=========================================================
"""

import os
from dotenv import load_dotenv

# -------------------------------------------------------
# Load Environment Variables
# -------------------------------------------------------

load_dotenv()

# -------------------------------------------------------
# Application Information
# -------------------------------------------------------

APP_NAME = "AI Voice Assistant"

ASSISTANT_NAME = "Nova"

VERSION = "1.0"

# -------------------------------------------------------
# GUI Settings
# -------------------------------------------------------

WINDOW_WIDTH = 900

WINDOW_HEIGHT = 700

WINDOW_TITLE = "Advanced AI Voice Assistant"

BACKGROUND_COLOR = "#1E293B"

CARD_COLOR = "#334155"

PRIMARY_COLOR = "#2563EB"

SUCCESS_COLOR = "#16A34A"

WARNING_COLOR = "#F59E0B"

ERROR_COLOR = "#DC2626"

TEXT_COLOR = "#FFFFFF"

SECONDARY_TEXT = "#CBD5E1"

FONT = ("Segoe UI", 11)

TITLE_FONT = ("Segoe UI", 20, "bold")

BUTTON_FONT = ("Segoe UI", 11, "bold")

# -------------------------------------------------------
# Voice Settings
# -------------------------------------------------------

VOICE_RATE = 175

VOICE_VOLUME = 1.0

VOICE_LANGUAGE = "en"
# Optional: specify a voice id or name to select a specific TTS voice
VOICE_ID = None

# -------------------------------------------------------
# Gemini API
# -------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-2.5-flash"

# -------------------------------------------------------
# Weather API
# -------------------------------------------------------

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# -------------------------------------------------------
# Email Configuration
# -------------------------------------------------------

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")

EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"

SMTP_PORT = 587

# -------------------------------------------------------
# Reminder Settings
# -------------------------------------------------------

DEFAULT_REMINDER_SOUND = True

# -------------------------------------------------------
# Speech Recognition
# -------------------------------------------------------

LISTEN_TIMEOUT = 5

PHRASE_TIME_LIMIT = 8

# -------------------------------------------------------
# Browser Search
# -------------------------------------------------------

DEFAULT_SEARCH_ENGINE = "https://www.google.com/search?q="

# -------------------------------------------------------
# Conversation Settings
# -------------------------------------------------------

MAX_CHAT_HISTORY = 100

# -------------------------------------------------------
# Logging
# -------------------------------------------------------

LOG_FILE = "assistant.log"


# -------------------------------------------------------
# Custom Commands
# -------------------------------------------------------
def load_custom_commands(path: str = "custom_commands.json") -> dict:
	"""Load user-defined custom commands from a JSON file.

	The file should map trigger phrases (lowercase) to either a
	response string or a dict with an action (e.g. {"open": "https://..."}).
	"""
	import json

	if not os.path.exists(path):
		# Create a template file for users
		template = {
			"hello assistant": "Hi! This is a custom response.",
			"open project site": {"open": "https://example.com"}
		}
		try:
			with open(path, "w", encoding="utf-8") as fh:
				json.dump(template, fh, indent=2)
		except Exception:
			pass
		return {}

	try:
		with open(path, "r", encoding="utf-8") as fh:
			data = json.load(fh)
			# normalize keys to lowercase
			return {k.lower(): v for k, v in data.items()}
	except Exception:
		return {}