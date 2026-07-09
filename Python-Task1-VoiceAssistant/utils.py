"""
====================================================================
Project Name : Advanced AI Voice Assistant
Internship   : Oasis Infobyte Python Programming Internship
Task         : Task 1 - Voice Assistant
Description  : This module (utils.py) provides all the core utility
               functions required by the Voice Assistant, including
               text-to-speech, speech recognition, web search,
               website navigation, weather retrieval, Wikipedia
               search, email sending, Gemini AI integration,
               reminders, and general helper functions.
Author       : <Your Name Here>
====================================================================
"""

# =====================================================
# Imports
# =====================================================
import datetime
import threading
import time
import logging
import webbrowser
import os
import warnings

import requests
import pyttsx3
import queue
import speech_recognition as sr

try:
    import wikipedia
except ImportError:
    wikipedia = None

try:
    import google.genai as genai
except ImportError:
    old_filters = warnings.filters[:]
    try:
        warnings.simplefilter("ignore")
        import google.generativeai as genai
    finally:
        warnings.filters[:] = old_filters

import smtplib
import ssl
from email.message import EmailMessage

import config


# =====================================================
# Logging Configuration
# =====================================================
logging.basicConfig(
    filename=getattr(config, "LOG_FILE", "assistant.log"),
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def log_message(level: str, message: str) -> None:
    """
    Log a message at the specified logging level.

    Args:
        level (str): The logging level as a string
                      ("info", "warning", "error", "debug", "critical").
        message (str): The message to be logged.

    Returns:
        None
    """
    level = level.lower().strip()

    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    elif level == "debug":
        logging.debug(message)
    elif level == "critical":
        logging.critical(message)
    else:
        logging.info(message)


# =====================================================
# Text To Speech
# =====================================================
_tts_queue = None
_tts_thread = None
_tts_ready = None
_tts_watchdog_thread = None
engine = None  # kept for backward-compat; actual TTS runs in worker thread


def initialize_engine():
    """
    Initialize a dedicated TTS worker thread with its own pyttsx3 engine.
    Safe to call multiple times — only starts a new worker if one isn't running.
    """
    global _tts_queue, _tts_thread, _tts_ready, engine

    try:
        if _tts_queue is None:
            _tts_queue = queue.Queue()

        if _tts_ready is None:
            _tts_ready = threading.Event()

        # Check if worker is already alive — don't spawn duplicates
        if _tts_thread is not None and _tts_thread.is_alive():
            log_message("info", "Text-to-speech engine already running.")
            return engine

        # Reset the ready event for the new worker
        _tts_ready = threading.Event()

        def _tts_worker():
            # Signal ready immediately — engine is created fresh per utterance
            try:
                _tts_ready.set()
            except Exception:
                pass

            # On Windows, pyttsx3's SAPI5 driver can silently get stuck
            # after the first runAndWait() when reusing the same engine
            # instance. Fix: create a fresh engine for every utterance.
            # The ~100ms overhead per call is imperceptible to the user.
            while True:
                try:
                    text = _tts_queue.get()
                except Exception as e:
                    log_message("error", f"TTS queue get error: {e}")
                    time.sleep(0.1)
                    continue

                if text is None:
                    try:
                        _tts_queue.task_done()
                    except Exception:
                        pass
                    break

                try:
                    eng = pyttsx3.init()
                    eng.setProperty("rate", getattr(config, "VOICE_RATE", 170))
                    eng.setProperty("volume", getattr(config, "VOICE_VOLUME", 1.0))
                    voice_id   = getattr(config, "VOICE_ID", None)
                    voice_lang = getattr(config, "VOICE_LANGUAGE", None)
                    if voice_id or voice_lang:
                        target = (voice_id or voice_lang).lower()
                        for v in eng.getProperty("voices"):
                            if target in (v.id or "").lower() or target in (v.name or "").lower():
                                eng.setProperty("voice", v.id)
                                break
                    eng.say(text)
                    eng.runAndWait()
                    try:
                        eng.stop()
                    except Exception:
                        pass
                    log_message("info", f"Spoken response: {text}")
                except Exception as inner_err:
                    log_message("error", f"TTS speak error: {inner_err}")

                try:
                    _tts_queue.task_done()
                except Exception:
                    pass

        _tts_thread = threading.Thread(target=_tts_worker, daemon=True, name="TTS-Worker")
        _tts_thread.start()
        _tts_ready.wait(timeout=3.0)

        log_message("info", "Text-to-speech engine initialized successfully.")
        return engine

    except Exception as error:
        log_message("error", f"Failed to initialize text-to-speech engine: {error}")
        return None


def speak(text: str) -> None:
    """
    Enqueue text for speech on the dedicated TTS worker thread.
    Thread-safe — can be called from any thread.
    """
    if not text:
        log_message("warning", "speak() called with empty text.")
        return

    try:
        global _tts_queue, _tts_thread, _tts_ready

        # Re-initialize if the worker has died or was never started
        if _tts_queue is None or _tts_thread is None or not _tts_thread.is_alive():
            initialize_engine()

        print(f"Assistant: {text}")
        _tts_queue.put(text)
        log_message("info", f"Enqueued TTS text: {text}")

    except Exception as error:
        log_message("error", f"Error while speaking text: {error}")


# =====================================================
# Date & Time
# =====================================================
def get_current_time() -> str:
    """
    Retrieve the current system time in a human-readable 12-hour format.

    Returns:
        str: The current time, e.g. "03:45 PM".
    """
    try:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        log_message("info", f"Current time retrieved: {current_time}")
        return current_time

    except Exception as error:
        log_message("error", f"Error retrieving current time: {error}")
        return "Unable to retrieve current time."


def get_current_date() -> str:
    """
    Retrieve the current system date in a human-readable format.

    Returns:
        str: The current date, e.g. "Monday, July 07, 2026".
    """
    try:
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        log_message("info", f"Current date retrieved: {current_date}")
        return current_date

    except Exception as error:
        log_message("error", f"Error retrieving current date: {error}")
        return "Unable to retrieve current date."


# =====================================================
# Web Search
# =====================================================
def search_google(query: str) -> str:
    """
    Open the default web browser and perform a Google search
    for the given query.

    Args:
        query (str): The search term entered by the user.

    Returns:
        str: A success or failure message describing the outcome.
    """
    if not query:
        log_message("warning", "search_google() called with empty query.")
        return "No search query was provided."

    try:
        clean_query = clean_text(query)
        search_url = f"https://www.google.com/search?q={clean_query}"
        webbrowser.open(search_url)

        log_message("info", f"Performed Google search for: {clean_query}")
        return f"Here are the search results for {clean_query}."

    except Exception as error:
        log_message("error", f"Error performing Google search: {error}")
        return "Sorry, I was unable to complete the search."


# =====================================================
# Open Website
# =====================================================
def open_website(url: str) -> str:
    """
    Open a website in the default web browser. Automatically
    prepends "https://" to the URL if it is missing.

    Args:
        url (str): The website URL or domain name to open.

    Returns:
        str: A success or failure message describing the outcome.
    """
    if not url:
        log_message("warning", "open_website() called with empty URL.")
        return "No website URL was provided."

    try:
        url = url.strip()

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        webbrowser.open(url)
        log_message("info", f"Opened website: {url}")
        return f"Opening {url} now."

    except Exception as error:
        log_message("error", f"Error opening website '{url}': {error}")
        return "Sorry, I was unable to open that website."


# =====================================================
# Weather
# =====================================================
def _correct_city_spelling(city: str, api_key: str) -> str:
    if not city:
        return city

    try:
        geocode_url = "https://api.openweathermap.org/geo/1.0/direct"
        params = {"q": city, "limit": 1, "appid": api_key}
        response = requests.get(geocode_url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200 and isinstance(data, list) and data:
            corrected = data[0].get("name")
            if corrected:
                return corrected
    except Exception as error:
        log_message("warning", f"City correction via OpenWeather geocoding failed for '{city}': {error}")

    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": city,
            "format": "json",
            "srlimit": 1,
        }
        headers = {"User-Agent": "Mozilla/5.0 (VoiceAssistant/1.0)"}
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        data = response.json()
        search_results = data.get("query", {}).get("search", [])
        if search_results:
            title = search_results[0].get("title")
            if title:
                return title
    except Exception as error:
        log_message("warning", f"City correction via Wikipedia search failed for '{city}': {error}")

    return city


def _format_weather_report(data: dict, location_name: str) -> str:
    description = data["weather"][0]["description"].title()
    temperature = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]

    weather_report = (
        f"The weather in {location_name} is currently {description}. "
        f"The temperature is {temperature} degrees Celsius, "
        f"but it feels like {feels_like} degrees Celsius. "
        f"Humidity is at {humidity} percent, and wind speed is "
        f"{wind_speed} meters per second."
    )

    return weather_report


def _resolve_city_coordinates(city: str, api_key: str):
    geocode_url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city,
        "limit": 1,
        "appid": api_key,
    }

    try:
        response = requests.get(geocode_url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200 and isinstance(data, list) and data:
            location_info = data[0]
            name = location_info.get("name", city)
            state = location_info.get("state")
            country = location_info.get("country")
            resolved_location = " ".join(part for part in [name, state, country] if part)
            return location_info.get("lat"), location_info.get("lon"), resolved_location
    except Exception as error:
        log_message("warning", f"Error resolving city coordinates for '{city}': {error}")

    if city:
        corrected = _correct_city_spelling(city, api_key)
        if corrected and corrected.lower() != city.lower():
            return _resolve_city_coordinates(corrected, api_key)

    return None


def _get_weather_by_coordinates(lat: float, lon: float, location_name: str, api_key: str) -> str | None:
    weather_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }

    try:
        response = requests.get(weather_url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200:
            return _format_weather_report(data, location_name)
        log_message("warning", f"Coordinate weather request returned status {response.status_code}: {data}")
    except Exception as error:
        log_message("warning", f"Weather lookup by coordinates failed for {location_name}: {error}")

    return None


def get_weather(city: str) -> str:
    """
    Retrieve current weather information for a given city using
    the OpenWeatherMap API.

    Args:
        city (str): The name of the city to retrieve weather for.

    Returns:
        str: A formatted string containing temperature, feels-like
             temperature, humidity, weather description, and wind
             speed, or an appropriate error message.
    """
    if not city:
        log_message("warning", "get_weather() called with empty city name.")
        return "No city name was provided."

    city = city.strip()
    api_key = getattr(config, "WEATHER_API_KEY", None)
    if not api_key:
        log_message("error", "Weather API key is missing in config.py.")
        return "Weather service is unavailable due to a missing API key."

    def _fetch(city_name: str) -> tuple[int, dict]:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city_name,
            "appid": api_key,
            "units": "metric",
        }
        response = requests.get(base_url, params=params, timeout=10)
        return response.status_code, response.json()

    try:
        status_code, data = _fetch(city)
        if status_code == 200:
            return _format_weather_report(data, city)

        if status_code == 401:
            log_message("error", "Invalid OpenWeatherMap API key.")
            return "Sorry, the weather API key appears to be invalid."

        if status_code == 404:
            corrected_city = _correct_city_spelling(city, api_key)
            if corrected_city and corrected_city.lower() != city.lower():
                status_code, data = _fetch(corrected_city)
                if status_code == 200:
                    log_message("info", f"Weather retrieved successfully for corrected city {corrected_city}.")
                    return _format_weather_report(data, corrected_city)

            coord_result = _resolve_city_coordinates(city, api_key)
            if coord_result:
                lat, lon, resolved_location = coord_result
                return _get_weather_by_coordinates(lat, lon, resolved_location, api_key) or f"Sorry, I could not find weather information for {city}."

            return f"Sorry, I could not find weather information for {city}."

        log_message("error", f"Unexpected weather API response: {data}")
        coord_result = _resolve_city_coordinates(city, api_key)
        if coord_result:
            lat, lon, resolved_location = coord_result
            return _get_weather_by_coordinates(lat, lon, resolved_location, api_key) or "Sorry, I was unable to retrieve the weather information."

        return "Sorry, I was unable to retrieve the weather information."

    except requests.exceptions.Timeout:
        log_message("error", "Weather API request timed out.")
        return "The weather service timed out. Please try again later."

    except requests.exceptions.ConnectionError:
        log_message("error", "Network error while retrieving weather data.")
        return "I could not connect to the weather service. Please check your internet connection."

    except Exception as error:
        log_message("error", f"Unexpected error retrieving weather: {error}")
        return "Sorry, an unexpected error occurred while retrieving the weather."


# =====================================================
# Wikipedia
# =====================================================
def _fetch_wikipedia_summary_from_rest(title: str) -> str:
    encoded_title = requests.utils.quote(title.replace(" ", "_"))
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
    headers = {"User-Agent": "Mozilla/5.0 (VoiceAssistant/1.0)"}

    response = requests.get(summary_url, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        extract = data.get("extract")
        if extract:
            return extract
        raise ValueError("Wikipedia summary response did not contain an extract.")

    if response.status_code == 404:
        raise wikipedia.exceptions.PageError(title)

    response.raise_for_status()


def _search_wikipedia_title(query: str) -> str | None:
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 1,
    }
    headers = {"User-Agent": "Mozilla/5.0 (VoiceAssistant/1.0)"}

    response = requests.get(search_url, params=params, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        search_results = data.get("query", {}).get("search", [])
        if search_results:
            return search_results[0].get("title")

    return None


def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for the given query and return a brief summary.

    Args:
        query (str): The topic to search for on Wikipedia.

    Returns:
        str: A three-sentence summary of the topic, or an
             appropriate error message.
    """
    if not query:
        log_message("warning", "search_wikipedia() called with empty query.")
        return "No search query was provided."

    clean_query = clean_text(query)
    if not clean_query:
        log_message("warning", "search_wikipedia() called with empty cleaned query.")
        return "No search query was provided."

    try:
        if wikipedia is not None:
            summary = wikipedia.summary(clean_query, sentences=3)
            log_message("info", f"Wikipedia summary retrieved for: {clean_query}")
            return summary
        raise RuntimeError("Local wikipedia package unavailable")

    except Exception as error:
        error_name = type(error).__name__
        log_message("warning", f"Primary Wikipedia lookup failed for '{clean_query}': ({error_name}) {error}")

        if wikipedia is not None and hasattr(wikipedia, 'exceptions'):
            if isinstance(error, wikipedia.exceptions.DisambiguationError):
                options = ", ".join(error.options[:5])
                return f"Your query is ambiguous. Did you mean: {options}?"

            if isinstance(error, wikipedia.exceptions.PageError):
                log_message("warning", f"Wikipedia page not found for query: {clean_query}. Trying REST fallback.")
                try:
                    return _fetch_wikipedia_summary_from_rest(clean_query)
                except Exception as rest_error:
                    log_message("warning", f"Wikipedia REST fallback failed for query '{clean_query}': {rest_error}")
                    title = _search_wikipedia_title(clean_query)
                    if title:
                        try:
                            return _fetch_wikipedia_summary_from_rest(title)
                        except Exception as final_error:
                            log_message("error", f"Final Wikipedia fallback failed for title '{title}': {final_error}")
                    return f"Sorry, I could not find any Wikipedia page for {query}."

        try:
            return _fetch_wikipedia_summary_from_rest(clean_query)
        except Exception as final_error:
            log_message("error", f"Wikipedia REST fallback also failed for '{clean_query}': {final_error}")
            title = _search_wikipedia_title(clean_query)
            if title:
                try:
                    return _fetch_wikipedia_summary_from_rest(title)
                except Exception as final_error2:
                    log_message("error", f"Final Wikipedia fallback failed for title '{title}': {final_error2}")
            return "Sorry, an unexpected error occurred while searching Wikipedia."


# =====================================================
# Email
# =====================================================
def send_email(receiver: str, subject: str, body: str) -> str:
    """
    Send an email using Gmail's SMTP server with credentials
    stored in config.py.

    Args:
        receiver (str): The recipient's email address.
        subject (str): The subject line of the email.
        body (str): The main content/body of the email.

    Returns:
        str: A success or failure message describing the outcome.
    """
    if not receiver or not subject or not body:
        log_message("warning", "send_email() called with missing parameters.")
        return "Email details are incomplete. Please provide receiver, subject, and body."

    try:
        sender_email = getattr(config, "EMAIL_ADDRESS", None)
        sender_password = getattr(config, "EMAIL_PASSWORD", None)

        if not sender_email or not sender_password:
            log_message("error", "Email credentials are missing in config.py.")
            return "Email service is unavailable due to missing credentials."

        message = EmailMessage()
        message["From"] = sender_email
        message["To"] = receiver
        message["Subject"] = subject
        message.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)

        log_message("info", f"Email sent successfully to {receiver}.")
        return f"Email has been sent successfully to {receiver}."

    except smtplib.SMTPAuthenticationError:
        log_message("error", "SMTP authentication failed. Check email credentials.")
        return "Failed to send email due to an authentication error. Please check your credentials."

    except smtplib.SMTPException as error:
        log_message("error", f"SMTP error while sending email: {error}")
        return "Sorry, an error occurred while sending the email."

    except Exception as error:
        log_message("error", f"Unexpected error sending email: {error}")
        return "Sorry, an unexpected error occurred while sending the email."


# =====================================================
# Gemini AI
# =====================================================
try:
    GEMINI_API_KEY = getattr(config, "GEMINI_API_KEY", None)
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except Exception as configuration_error:
    log_message("error", f"Error configuring Gemini AI: {configuration_error}")


def ask_gemini(prompt: str) -> str:
    """
    Send a prompt to the Gemini AI model and return its text response.

    Args:
        prompt (str): The user's question or prompt for the AI model.

    Returns:
        str: The AI-generated text response, or an appropriate
             error message.
    """
    if not prompt:
        log_message("warning", "ask_gemini() called with empty prompt.")
        return "No prompt was provided to Gemini AI."

    try:
        api_key = getattr(config, "GEMINI_API_KEY", None)

        if not api_key:
            log_message("error", "Gemini API key is missing in config.py.")
            return "Gemini AI is unavailable due to a missing API key."

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        if response and hasattr(response, "text") and response.text:
            log_message("info", f"Gemini AI response generated for prompt: {prompt}")
            return response.text.strip()

        log_message("warning", "Gemini AI returned an empty response.")
        return "Gemini AI did not return a valid response."

    except requests.exceptions.ConnectionError:
        log_message("error", "Network error while contacting Gemini AI.")
        return "I could not connect to Gemini AI. Please check your internet connection."

    except Exception as error:
        log_message("error", f"Error communicating with Gemini AI: {error}")
        return "Sorry, an error occurred while contacting Gemini AI."


# =====================================================
# Reminder
# =====================================================
def set_reminder(seconds: int, message: str) -> str:
    """
    Set a reminder that speaks and logs a message after a
    specified number of seconds. The reminder runs in a
    separate background thread so it does not block execution.

    Args:
        seconds (int): The delay in seconds before the reminder triggers.
        message (str): The reminder message to be spoken and logged.

    Returns:
        str: A confirmation message that the reminder has been set.
    """
    if seconds is None or seconds < 0:
        log_message("warning", "set_reminder() called with invalid duration.")
        return "Please provide a valid duration for the reminder."

    if not message:
        log_message("warning", "set_reminder() called with empty message.")
        return "Please provide a reminder message."

    def reminder_task():
        """Internal task executed in a separate thread after the delay."""
        try:
            time.sleep(seconds)
            speak(f"Reminder: {message}")
            log_message("info", f"Reminder triggered: {message}")
        except Exception as error:
            log_message("error", f"Error while triggering reminder: {error}")

    try:
        reminder_thread = threading.Thread(target=reminder_task, daemon=True)
        reminder_thread.start()

        log_message("info", f"Reminder set for {seconds} seconds: {message}")
        return f"Reminder set for {seconds} seconds from now."

    except Exception as error:
        log_message("error", f"Error setting reminder: {error}")
        return "Sorry, I was unable to set the reminder."


# =====================================================
# Listening
# =====================================================
def listen() -> str:
    """
    Listen for audio input through the microphone and convert
    it to lowercase text using Google's speech recognition API.

    Returns:
        str: The recognized speech converted to lowercase text,
             or an empty string if recognition fails.
    """
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            log_message("info", "Listening for user input...")
            print("Listening...")

            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

        try:
            recognized_text = recognizer.recognize_google(audio)
            recognized_text = recognized_text.lower()

            log_message("info", f"Recognized speech: {recognized_text}")
            return recognized_text

        except sr.UnknownValueError:
            log_message("warning", "Speech recognition could not understand audio.")
            return ""

        except sr.RequestError as error:
            log_message("error", f"Speech recognition request error: {error}")
            return ""

    except sr.WaitTimeoutError:
        log_message("warning", "Listening timed out while waiting for speech.")
        return ""

    except OSError as error:
        log_message("error", f"Microphone unavailable: {error}")
        return ""

    except Exception as error:
        log_message("error", f"Unexpected error during listening: {error}")
        return ""


# =====================================================
# Helpers
# =====================================================
def clean_text(text: str) -> str:
    """
    Clean and normalize a given text string by removing
    unnecessary leading, trailing, and duplicate whitespace.

    Args:
        text (str): The raw text to be cleaned.

    Returns:
        str: The cleaned and normalized text.
    """
    if not text:
        return ""

    try:
        cleaned = " ".join(text.strip().split())
        return cleaned

    except Exception as error:
        log_message("error", f"Error cleaning text: {error}")
        return text


# =====================================================
# YouTube Auto-Play (Selenium) — Persistent Session
# =====================================================

# Module-level driver reference so the browser stays alive
# between the play call and a later stop/back/cancel command.
_yt_driver = None


def _find_chromedriver() -> str:
    """
    Locate chromedriver.exe on this machine.
    Tries webdriver-manager first, then common install locations,
    then a recursive search under ~/.wdm.
    Returns the full path to chromedriver.exe, or empty string if not found.
    """
    import os, glob

    # 1. Try webdriver-manager — but resolve to the actual .exe, not metadata files
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        raw = ChromeDriverManager().install()
        # webdriver-manager sometimes returns a metadata/text file path — walk up to find .exe
        candidate_dir = os.path.dirname(raw)
        for root, _, files in os.walk(candidate_dir):
            for f in files:
                if f.lower() == "chromedriver.exe":
                    return os.path.join(root, f)
    except Exception as e:
        log_message("warning", f"webdriver-manager lookup failed: {e}")

    # 2. Search the entire ~/.wdm/drivers/chromedriver tree
    wdm_root = os.path.join(os.path.expanduser("~"), ".wdm", "drivers", "chromedriver")
    if os.path.isdir(wdm_root):
        for exe in glob.glob(os.path.join(wdm_root, "**", "chromedriver.exe"), recursive=True):
            return exe

    # 3. Common manual install locations
    common = [
        r"C:\chromedriver\chromedriver.exe",
        r"C:\Program Files\chromedriver\chromedriver.exe",
        r"C:\Program Files (x86)\chromedriver\chromedriver.exe",
        os.path.join(os.path.expanduser("~"), "chromedriver.exe"),
    ]
    for path in common:
        if os.path.isfile(path):
            return path

    # 4. Check PATH
    import shutil
    found = shutil.which("chromedriver")
    if found:
        return found

    return ""


def play_youtube_video(query: str) -> str:
    """
    Search YouTube for the query and auto-play the first video result
    using a persistent Selenium WebDriver session.

    The browser stays open until stop_youtube_video() is called.
    Calling play_youtube_video() again reuses the same browser window.

    Args:
        query (str): The search term, e.g. "shape of you" or "lofi music".

    Returns:
        str: Success message ("Now playing …") or empty string on failure.
    """
    global _yt_driver
    import time

    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        log_message("error", "Selenium not installed.")
        return ""

    log_message("info", f"Launching Selenium to play YouTube: '{query}'")

    # ── Reuse existing driver if still alive, otherwise create a new one ──
    if _yt_driver is not None:
        try:
            # Quick check — accessing window_handles throws if driver is dead
            _ = _yt_driver.window_handles
        except Exception:
            log_message("info", "Previous YouTube driver was closed; starting a new one.")
            _yt_driver = None

    if _yt_driver is None:
        driver_path = _find_chromedriver()
        if not driver_path:
            log_message("error", "chromedriver.exe not found.")
            return ""

        log_message("info", f"Using chromedriver at: {driver_path}")

        opts = Options()
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--autoplay-policy=no-user-gesture-required")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        try:
            service    = Service(executable_path=driver_path)
            _yt_driver = webdriver.Chrome(service=service, options=opts)
        except Exception as e:
            log_message("error", f"Chrome failed to launch: {e}")
            return ""

    # ── Navigate and play ──────────────────────────────────────────────
    try:
        import urllib.parse
        search_url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote(query)
        )
        _yt_driver.get(search_url)
        log_message("info", f"Opened YouTube search: {search_url}")

        wait        = WebDriverWait(_yt_driver, 15)
        first_video = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#video-title"))
        )
        video_title = first_video.get_attribute("title") or query
        first_video.click()
        log_message("info", f"Clicked video: {video_title}")

        # Wait for video player to appear (don't use a fixed sleep that can
        # race with YouTube's autoplay detection)
        try:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "video.html5-main-video"))
            )
        except Exception:
            time.sleep(3)

        # Only click play if the video is genuinely paused (not if it is
        # already playing). Checking "pause" in aria-label means it IS
        # currently playing, so we leave it alone.
        try:
            play_btn = _yt_driver.find_element(
                By.CSS_SELECTOR, "button.ytp-play-button"
            )
            aria = (play_btn.get_attribute("aria-label") or "").lower()
            # aria-label is "Pause (k)" when playing, "Play (k)" when paused
            if "play" in aria and "pause" not in aria:
                play_btn.click()
                log_message("info", "Clicked play button to resume")
            else:
                log_message("info", "Video is already playing, skipping play-button click")
        except Exception:
            pass  # Player controls not found — video likely already playing

        log_message("info", f"Now playing: {video_title}")
        # Driver intentionally NOT closed here — browser stays open
        return f"Now playing '{video_title}' on YouTube."

    except Exception as e:
        log_message("error", f"Selenium playback error: {e}")
        # On error, clean up so next call starts fresh
        try:
            _yt_driver.quit()
        except Exception:
            pass
        _yt_driver = None
        return ""


def stop_youtube_video() -> str:
    """
    Close the persistent YouTube browser window and clean up the driver.
    Called when the user says "stop", "back", "cancel", "close youtube", etc.

    Returns:
        str: Confirmation message.
    """
    global _yt_driver
    if _yt_driver is None:
        return "Nothing is currently playing."
    try:
        _yt_driver.quit()
        log_message("info", "YouTube browser closed by user command.")
        return "Stopped. YouTube is closed."
    except Exception as e:
        log_message("error", f"stop_youtube_video error: {e}")
        return "Stopped."
    finally:
        _yt_driver = None
