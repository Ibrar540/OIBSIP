"""
=========================================================
Project      : Advanced AI Voice Assistant
Internship   : Oasis Infobyte - Python Programming Internship
Task         : Task 1 - Voice Assistant
Description  : Command Dispatcher — the brain of the assistant.

               Architecture:
                 User Input
                     │
                 Normalize Text
                     │
                 Intent Detection  ←── pattern-based, no Gemini
                     │
              ┌──────┴───────┐
         Local Intent?     Unknown
              │                │
         Execute Handler   Gemini AI (last resort)
              │
          Return Result

               Gemini is NEVER called for actions that Python can
               perform locally (time, date, web search, open sites,
               weather, reminders, Wikipedia, email, etc.).
Author       : <Your Name Here>
=========================================================
"""

# =========================================================
# Imports
# =========================================================
import re
import datetime
import webbrowser

import config

from utils import (
    listen,
    get_current_time,
    get_current_date,
    search_google,
    open_website,
    search_wikipedia,
    get_weather,
    send_email,
    ask_gemini,
    set_reminder,
    log_message,
    play_youtube_video,
    stop_youtube_video,
)


# =========================================================
# Intent Constants
# =========================================================
class Intent:
    GREETING    = "GREETING"
    TIME        = "TIME"
    DATE        = "DATE"
    WEATHER     = "WEATHER"
    SEARCH      = "SEARCH"
    OPEN        = "OPEN"
    PLAY_MEDIA  = "PLAY_MEDIA"
    STOP_MEDIA  = "STOP_MEDIA"
    WIKIPEDIA   = "WIKIPEDIA"
    REMINDER    = "REMINDER"
    EMAIL       = "EMAIL"
    HELP        = "HELP"
    SELF_QUERY  = "SELF_QUERY"
    CUSTOM      = "CUSTOM"
    EXIT        = "EXIT"
    AI_FALLBACK = "AI_FALLBACK"


# =========================================================
# Command Processor Class
# =========================================================
class CommandProcessor:
    """
    CommandProcessor is the central command dispatcher for the Voice
    Assistant. Every user command passes through the intent detector
    before a handler is invoked. Gemini is called ONLY when no local
    handler matches — it is the last fallback, never the first stop.
    """

    def __init__(self, assistant_name: str = "Assistant") -> None:
        self.assistant_name: str = getattr(config, "ASSISTANT_NAME", assistant_name)
        self.configuration = config
        self.conversation_history: list = []
        self.max_history_length: int = 100

        # Load custom commands
        try:
            self.custom_commands = getattr(config, "load_custom_commands", lambda: {})()
        except Exception:
            self.custom_commands = {}

        # Website map for "open <site>" commands
        self.website_map: dict = {
            "youtube":       "https://www.youtube.com",
            "github":        "https://www.github.com",
            "google":        "https://www.google.com",
            "linkedin":      "https://www.linkedin.com",
            "gmail":         "https://mail.google.com",
            "chatgpt":       "https://chat.openai.com",
            "stackoverflow": "https://stackoverflow.com",
            "twitter":       "https://www.twitter.com",
            "facebook":      "https://www.facebook.com",
            "instagram":     "https://www.instagram.com",
            "reddit":        "https://www.reddit.com",
            "wikipedia":     "https://www.wikipedia.org",
            "whatsapp":      "https://web.whatsapp.com",
            "amazon":        "https://www.amazon.com",
            "netflix":       "https://www.netflix.com",
            "spotify":       "https://open.spotify.com",
            "gmail":         "https://mail.google.com",
            "maps":          "https://maps.google.com",
            "google maps":   "https://maps.google.com",
            "drive":         "https://drive.google.com",
            "google drive":  "https://drive.google.com",
            "docs":          "https://docs.google.com",
        }

        # Browser / app map — Key = what the user says, Value = executable/path
        # Includes Windows registry paths for browsers that aren't on PATH
        self.app_map: dict = {
            "chrome":          self._resolve_app("chrome", [
                                   r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                   r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                               ]),
            "google chrome":   self._resolve_app("chrome", [
                                   r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                   r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                               ]),
            "firefox":         self._resolve_app("firefox", [
                                   r"C:\Program Files\Mozilla Firefox\firefox.exe",
                                   r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                               ]),
            "mozilla firefox": self._resolve_app("firefox", [
                                   r"C:\Program Files\Mozilla Firefox\firefox.exe",
                               ]),
            "edge":            self._resolve_app("msedge", [
                                   r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                                   r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                               ]),
            "microsoft edge":  self._resolve_app("msedge", [
                                   r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                               ]),
            "brave":           self._resolve_app("brave", [
                                   r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                               ]),
            "opera":           self._resolve_app("opera", [
                                   r"C:\Program Files\Opera\opera.exe",
                               ]),
            "browser":         self._resolve_app("chrome", [
                                   r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                   r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                               ]),
            "notepad":         "notepad",
            "calculator":      "calc",
            "paint":           "mspaint",
            "word":            "winword",
            "excel":           "excel",
            "powerpoint":      "powerpnt",
            "vlc":             self._resolve_app("vlc", [
                                   r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                                   r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
                               ]),
            "file explorer":   "explorer",
            "explorer":        "explorer",
            "task manager":    "taskmgr",
            "control panel":   "control",
            "settings":        "ms-settings:",
        }

        log_message("info", f"CommandProcessor initialized for assistant '{self.assistant_name}'.")

    # =========================================================
    # Public Entry Point
    # =========================================================
    def process_command(self, command: str) -> str:
        """
        Main entry point.  Every user utterance flows through here.

        Flow:
            1. Normalize text.
            2. Detect intent deterministically (regex / keyword rules).
            3. Dispatch to the matching local handler.
            4. If no local handler matches → send to Gemini AI.

        Args:
            command (str): Raw user text / speech.

        Returns:
            str: The assistant's response text.
        """
        if not command or not command.strip():
            log_message("warning", "process_command() received empty input.")
            return "I did not receive any command. Please try again."

        normalized = self._normalize(command)
        response = ""

        try:
            intent, params = self._detect_intent(normalized)
            log_message("info", f"Intent: {intent} | Params: {params} | Input: '{normalized}'")

            response = self._dispatch(intent, params, normalized, command)
            self._add_to_history(command, response)
            log_message("info", f"Response: {response[:120]}")
            return response

        except Exception as exc:
            log_message("error", f"process_command() error for '{command}': {exc}")
            error_resp = "Sorry, something went wrong while processing your command."
            self._add_to_history(command, error_resp)
            return error_resp

    # =========================================================
    # App Path Resolver
    # =========================================================
    @staticmethod
    def _resolve_app(fallback: str, paths: list) -> str:
        """
        Return the first path in `paths` that exists on disk,
        otherwise return `fallback` (relies on PATH).
        """
        import os
        for p in paths:
            if os.path.isfile(p):
                return p
        return fallback
    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, strip punctuation noise, collapse whitespace."""
        text = text.lower().strip()
        # Remove trailing punctuation characters that add no meaning
        text = re.sub(r"[?!.,;]+$", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    # =========================================================
    # Intent Detection — deterministic, no AI involved
    # =========================================================
    def _detect_intent(self, cmd: str) -> tuple[str, dict]:
        """
        Detect the user's intent from the normalized command text using
        regex and keyword patterns. Returns a 2-tuple of (intent, params).

        Gemini is NOT consulted here under any circumstances.
        """

        # ── 1. Custom commands (exact match, highest priority) ──────────
        if cmd in self.custom_commands:
            return Intent.CUSTOM, {"key": cmd}

        # ── 2. Stop media (check before EXIT so "stop" stops video first) ─
        if re.search(
            r"\b(stop|pause|cancel|back|close youtube|stop music|stop video|"
            r"stop playing|pause music|pause video|enough|close it|close the video|"
            r"close the music|go back|return)\b",
            cmd,
        ):
            return Intent.STOP_MEDIA, {}

        # ── 3. Exit / goodbye ───────────────────────────────────────────
        if re.search(r"\b(bye|goodbye|exit|quit|shutdown|stop listening|see you|close)\b", cmd):
            return Intent.EXIT, {}

        # ── 3. Greeting ─────────────────────────────────────────────────
        if re.search(r"\b(hello|hi|hey|good morning|good evening|good afternoon|what'?s up|howdy)\b", cmd):
            return Intent.GREETING, {}

        # ── 4. Time ─────────────────────────────────────────────────────
        if re.search(
            r"(what('?s| is)?\s+(the\s+)?time"
            r"|current\s+time"
            r"|tell me the time"
            r"|time (is it|now|right now))",
            cmd,
        ):
            return Intent.TIME, {}

        # ── 5. Date ─────────────────────────────────────────────────────
        if re.search(
            r"(what('?s| is)?\s+(the\s+)?date"
            r"|today'?s\s+date"
            r"|current\s+date"
            r"|what day is it"
            r"|date today"
            r"|what is today'?s? date"
            r"|today date)",
            cmd,
        ):
            return Intent.DATE, {}

        # ── 6. Weather ──────────────────────────────────────────────────
        if re.search(
            r"\b(weather|temperature|forecast|humidity|rain(ing)?|snow(ing)?|wind|sunny|cloudy|hot|cold)\b",
            cmd,
        ):
            city = self._extract_city(cmd)
            return Intent.WEATHER, {"city": city}

        # ── 7. Reminder ─────────────────────────────────────────────────
        if re.search(r"\b(remind|reminder|set (a\s+)?reminder)\b", cmd):
            params = self._extract_reminder_params(cmd)
            return Intent.REMINDER, params

        # ── 8. Play media ────────────────────────────────────────────────
        # "play X", "play X on youtube", "open youtube and play X"
        m = re.search(
            r"\b(?:open\s+youtube\s+and\s+)?play\s+(.+?)(?:\s+on\s+\w+)?$", cmd
        )
        if m:
            query = m.group(1).strip()
            return Intent.PLAY_MEDIA, {"query": query, "platform": "youtube"}

        # ── 9. Open website / app ────────────────────────────────────────
        if re.search(r"\b(open|launch|go to|take me to|navigate to|visit|start|run)\b", cmd):
            # Check for "open <site> and play/search <query>" pattern first
            compound = re.search(
                r"\b(?:open|launch)\s+(\w+)\s+and\s+(?:play|search|find|watch)\s+(.+)$", cmd
            )
            if compound:
                site_word = compound.group(1).strip()
                query     = compound.group(2).strip()
                # Route to the right platform
                if site_word in ("youtube",):
                    return Intent.PLAY_MEDIA, {"query": query, "platform": "youtube"}
                if site_word in ("spotify",):
                    return Intent.PLAY_MEDIA, {"query": query, "platform": "spotify"}
                # Generic: open site then search
                return Intent.SEARCH, {"query": query, "site": site_word}

            site_info = self._extract_site(cmd)
            if site_info:
                return Intent.OPEN, site_info
            # Even if no known site/app matched, still treat as OPEN —
            # extract whatever word follows "open/launch/etc." and try it
            m = re.search(r"\b(?:open|launch|start|run)\s+(.+)$", cmd)
            if m:
                target = m.group(1).strip()
                return Intent.OPEN, {"url": "", "name": target, "app": target}

        # ── 10. Search ───────────────────────────────────────────────────
        if re.search(r"\b(search|look up|lookup|find|google|bing|search for)\b", cmd):
            query = self._extract_search_query(cmd)
            return Intent.SEARCH, {"query": query}

        # ── 11. Email ───────────────────────────────────────────────────
        if re.search(r"\b(send (an?\s+)?email|compose (an?\s+)?email|email (someone|a\s+person))\b", cmd):
            return Intent.EMAIL, {}

        # ── 12. Wikipedia ───────────────────────────────────────────────
        if re.search(
            r"^(who is|who was|what is|what was|tell me about|where is|where was|"
            r"locate|location of|explain|define|describe|history of|biography of)\b",
            cmd,
        ):
            query = self._extract_wiki_query(cmd)
            return Intent.WIKIPEDIA, {"query": query}

        # ── 13. Help ────────────────────────────────────────────────────
        if re.search(r"\b(help|what can you do|how can you help|assist me|capabilities|features)\b", cmd):
            return Intent.HELP, {}

        # ── 14. Self-query ──────────────────────────────────────────────
        if re.search(r"\b(who are you|what are you|your name|what is nova|tell me about yourself|are you (a\s+)?(robot|ai|human|bot))\b", cmd):
            return Intent.SELF_QUERY, {}

        # ── 15. Gemini fallback (knowledge / conversational) ────────────
        return Intent.AI_FALLBACK, {}

    # =========================================================
    # Command Dispatcher
    # =========================================================
    def _dispatch(self, intent: str, params: dict, normalized: str, raw: str) -> str:
        """Route the detected intent to the appropriate handler."""

        if intent == Intent.GREETING:
            return self._handle_greeting()

        if intent == Intent.TIME:
            return self._handle_time()

        if intent == Intent.DATE:
            return self._handle_date()

        if intent == Intent.WEATHER:
            return self._handle_weather(params)

        if intent == Intent.REMINDER:
            return self._handle_reminder(params)

        if intent == Intent.OPEN:
            return self._handle_open(params)

        if intent == Intent.PLAY_MEDIA:
            return self._handle_play_media(params)

        if intent == Intent.STOP_MEDIA:
            return self._handle_stop_media()

        if intent == Intent.SEARCH:
            return self._handle_search(params)

        if intent == Intent.EMAIL:
            return self._handle_email()

        if intent == Intent.WIKIPEDIA:
            return self._handle_wikipedia_query(params)

        if intent == Intent.HELP:
            return self._handle_help()

        if intent == Intent.SELF_QUERY:
            return self._handle_self_query()

        if intent == Intent.CUSTOM:
            return self._handle_custom(params["key"])

        if intent == Intent.EXIT:
            return self._handle_exit()

        # Gemini is always last
        if intent == Intent.AI_FALLBACK:
            return self._handle_ai(raw)

        # Should never reach here
        log_message("warning", f"Unhandled intent: {intent}")
        return self._handle_ai(raw)

    # =========================================================
    # Parameter Extractors
    # =========================================================
    def _extract_city(self, cmd: str) -> str:
        """Extract city name from a weather-related command."""
        # Try "weather/temperature/… in/at/for <city>"
        m = re.search(
            r"\b(weather|temperature|forecast|humidity|rain|snow|wind)\b"
            r"[\w\s]*?\b(in|at|for)\s+([a-zA-Z][\w\s]+?)(?:\s+(today|now|tonight|currently|please))?$",
            cmd,
        )
        if m:
            return m.group(3).strip()

        # Try "how is the weather in <city>"
        m = re.search(r"\bhow\s+is\s+(?:the\s+)?weather\s+(?:in|at|for)\s+([a-zA-Z][\w\s]+?)$", cmd)
        if m:
            return m.group(1).strip()

        # Generic "in <city>" anywhere
        m = re.search(r"\bin\s+([a-zA-Z][\w\s]+?)(?:\s+(today|now|tonight|currently|please))?$", cmd)
        if m:
            return m.group(1).strip()

        return ""

    def _extract_site(self, cmd: str) -> dict | None:
        """
        Extract site/app info from an 'open' command.
        Uses exact match first, then fuzzy match for typos (e.g. 'wattsapp' → 'whatsapp').
        Returns dict with 'url', 'name', and optionally 'app', or None if no match.
        """
        from difflib import get_close_matches

        # ── Exact match: websites ───────────────────────────────────────
        for name, url in self.website_map.items():
            if re.search(rf"\b{re.escape(name)}\b", cmd):
                return {"url": url, "name": name}

        # ── Exact match: local apps ─────────────────────────────────────
        for name, exe in self.app_map.items():
            if re.search(rf"\b{re.escape(name)}\b", cmd):
                return {"url": "", "name": name, "app": exe}

        # ── Fuzzy match: extract the target word(s) after open/launch ───
        m = re.search(r"\b(?:open|launch|start|visit|go to|run)\s+(.+)$", cmd)
        if m:
            target = m.group(1).strip()
            # Remove filler words that aren't part of the target
            target_clean = re.sub(r"\b(please|now|for me)\b", "", target).strip()

            all_names = list(self.website_map.keys()) + list(self.app_map.keys())
            matches = get_close_matches(target_clean, all_names, n=1, cutoff=0.6)
            if matches:
                best = matches[0]
                if best in self.website_map:
                    return {"url": self.website_map[best], "name": best}
                if best in self.app_map:
                    return {"url": "", "name": best, "app": self.app_map[best]}

        # ── Bare URL pattern ────────────────────────────────────────────
        m = re.search(r"(https?://[\w\-./?&=%]+)", cmd)
        if m:
            return {"url": m.group(1), "name": m.group(1)}

        # ── "open <word>.com" pattern ───────────────────────────────────
        m = re.search(r"\b(open|launch|visit)\s+([\w\-]+\.(?:com|org|net|io|co))\b", cmd)
        if m:
            domain = m.group(2)
            return {"url": f"https://{domain}", "name": domain}

        return None

    def _extract_search_query(self, cmd: str) -> str:
        """Strip search trigger words and return the query."""
        query = cmd
        for trigger in ["search for", "search", "look up", "lookup", "google for", "google", "find", "bing"]:
            query = re.sub(rf"\b{re.escape(trigger)}\b", "", query, flags=re.IGNORECASE)
        return query.strip()

    def _extract_wiki_query(self, cmd: str) -> str:
        """Strip Wikipedia trigger prefixes and return the topic."""
        prefixes = [
            "who is", "who was", "what is", "what was", "tell me about",
            "where is", "where was", "locate", "location of",
            "explain", "define", "describe", "history of", "biography of",
        ]
        query = cmd
        for prefix in prefixes:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        return query

    def _extract_reminder_params(self, cmd: str) -> dict:
        """Extract duration and message from a reminder command."""
        m = re.search(
            r"remind\s+(?:me\s+)?(?:in|after)\s+(\d+)\s*(second|seconds|minute|minutes|hour|hours)"
            r"\s*(?:to|that|about)?\s*(.*)$",
            cmd,
            re.IGNORECASE,
        )
        if m:
            amount = int(m.group(1))
            unit   = m.group(2).lower()
            msg    = m.group(3).strip() or "Your reminder is due."
            if "second" in unit:
                seconds = amount
            elif "minute" in unit:
                seconds = amount * 60
            else:
                seconds = amount * 3600
            return {"seconds": seconds, "message": msg, "amount": amount, "unit": unit}
        return {}

    # =========================================================
    # Local Handlers — these NEVER call Gemini
    # =========================================================

    def _handle_greeting(self) -> str:
        hour = datetime.datetime.now().hour
        if hour < 12:
            period = "morning"
        elif hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        return f"Good {period}! I am {self.assistant_name}. How can I help you today?"

    def _handle_time(self) -> str:
        """Returns the current time directly from datetime — Gemini is NOT called."""
        try:
            t = get_current_time()
            log_message("info", f"Executed: get_current_time() → {t}")
            return f"The current time is {t}."
        except Exception as e:
            log_message("error", f"_handle_time error: {e}")
            return "Unable to retrieve the current time."

    def _handle_date(self) -> str:
        """Returns today's date directly from datetime — Gemini is NOT called."""
        try:
            d = get_current_date()
            log_message("info", f"Executed: get_current_date() → {d}")
            return f"Today's date is {d}."
        except Exception as e:
            log_message("error", f"_handle_date error: {e}")
            return "Unable to retrieve today's date."

    def _handle_weather(self, params: dict) -> str:
        """
        Calls the Weather API directly. Gemini is NEVER used here.
        If no city was extracted, asks the user to specify one.
        """
        city = params.get("city", "").strip()
        if not city:
            return "Which city would you like the weather for?"

        if not getattr(config, "WEATHER_API_KEY", None):
            log_message("error", "WEATHER_API_KEY not set.")
            return "Weather service is currently unavailable. Please set your WEATHER_API_KEY in the .env file."

        log_message("info", f"Executed: get_weather('{city}')")
        result = get_weather(city)
        log_message("info", f"Weather result for '{city}': {result[:100]}")
        return result

    def _handle_search(self, params: dict) -> str:
        """Opens Google search in the browser — Gemini is NOT called."""
        query = params.get("query", "").strip()
        if not query:
            return "What would you like me to search for?"

        log_message("info", f"Executed: search_google('{query}')")
        try:
            result = search_google(query)
            return result
        except Exception as e:
            log_message("error", f"_handle_search error: {e}")
            return "Unable to open the browser for the search. Please check your browser settings."

    def _handle_open(self, params: dict) -> str:
        """
        Opens a website in the browser OR launches a local application.
        Gemini is NEVER called here.
        """
        import subprocess
        import os as _os

        url  = params.get("url", "").strip()
        name = params.get("name", "").strip()
        app  = params.get("app", "").strip()

        # ── Case 1: Known URL ───────────────────────────────────────────
        if url:
            log_message("info", f"Executed: open_website('{url}')")
            try:
                result = open_website(url)
                return result
            except Exception as e:
                log_message("error", f"_handle_open url error: {e}")
                return f"Unable to open {name}. Please check your browser settings."

        # ── Case 2: Known local app (resolved path or exe name) ─────────
        if app:
            log_message("info", f"Executed: launch app '{app}'")

            # ms-settings: URI scheme
            if app.startswith("ms-settings:"):
                try:
                    _os.startfile(app)
                    return f"Opening {name}."
                except Exception as e:
                    log_message("error", f"os.startfile '{app}' failed: {e}")
                    return f"Unable to open {name}."

            # Full path on disk — use it directly
            if _os.path.isfile(app):
                try:
                    subprocess.Popen([app],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    log_message("info", f"Launched: {app}")
                    return f"Opening {name}."
                except Exception as e:
                    log_message("error", f"Popen '{app}' failed: {e}")

            # Short name — try shell=True so Windows finds it on PATH
            try:
                subprocess.Popen(app, shell=True,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                log_message("info", f"Launched via shell: {app}")
                return f"Opening {name}."
            except Exception as e:
                log_message("error", f"shell launch '{app}' failed: {e}")

            # Last resort: os.startfile
            try:
                _os.startfile(app)
                return f"Opening {name}."
            except Exception as e:
                log_message("error", f"os.startfile '{app}' failed: {e}")
                return f"Unable to open {name}. Make sure it is installed."

        # ── Case 3: Unknown target — try as URL, then as app ────────────
        if name:
            if re.search(r"\.(com|org|net|io|co|gov|edu)$", name):
                try:
                    result = open_website(f"https://{name}")
                    return result
                except Exception as e:
                    log_message("error", f"_handle_open domain '{name}' failed: {e}")

            try:
                subprocess.Popen(name, shell=True,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                log_message("info", f"Launched unknown target: {name}")
                return f"Attempting to open {name}."
            except Exception as e:
                log_message("error", f"_handle_open unknown '{name}' failed: {e}")
                return f"I couldn't open '{name}'. Please check the name and try again."

        return "I could not identify what to open. Please be more specific."

    def _handle_play_media(self, params: dict) -> str:
        """
        Play a song or video by using Selenium to open YouTube and
        auto-click the first result. Gemini is NEVER called here.

        Falls back to a search URL if Selenium is unavailable.
        """
        import urllib.parse

        query    = params.get("query", "").strip()
        platform = params.get("platform", "youtube").lower()

        # ── Spotify ─────────────────────────────────────────────────────
        if platform == "spotify":
            url = ("https://open.spotify.com/search/" + urllib.parse.quote(query)
                   if query else "https://open.spotify.com")
            log_message("info", f"Executed: open_website('{url}') for Spotify")
            try:
                open_website(url)
                return f"Opening Spotify{' and searching for ' + query if query else ''}."
            except Exception as e:
                log_message("error", f"Spotify open failed: {e}")
                return "Unable to open Spotify."

        # ── YouTube ─────────────────────────────────────────────────────
        # Use a sensible default query if user just said "play music"
        effective_query = query if query else "top music"

        # Try Selenium auto-play first
        result = play_youtube_video(effective_query)

        # If Selenium succeeded, return immediately
        if result.startswith("Now playing"):
            return result

        # Selenium failed — fall back to opening search URL in browser
        log_message("warning", f"Selenium unavailable for '{effective_query}', falling back to search URL")
        search_url = ("https://www.youtube.com/results?search_query="
                      + urllib.parse.quote(effective_query))
        try:
            open_website(search_url)
            return f"Opened YouTube search for '{effective_query}'. Click a video to play it."
        except Exception as e:
            log_message("error", f"YouTube search fallback failed: {e}")
            return f"Unable to play '{effective_query}'. Please open YouTube manually."

    def _handle_stop_media(self) -> str:
        """Close the YouTube browser. Gemini is NOT called."""
        log_message("info", "Executed: stop_youtube_video()")
        return stop_youtube_video()

    def _handle_wikipedia_query(self, params: dict) -> str:
        """
        Looks up Wikipedia first. Falls back to Gemini ONLY if Wikipedia
        fails completely.
        """
        query = params.get("query", "").strip()
        if not query:
            return "Who or what would you like to know about?"

        log_message("info", f"Executed: search_wikipedia('{query}')")
        try:
            result = search_wikipedia(query)
            # If the wikipedia module returned an error message string, fall back to Gemini
            if result and not result.startswith("Sorry") and not result.startswith("Unable"):
                return result
            log_message("warning", f"Wikipedia returned no useful result for '{query}'; falling back to Gemini.")
        except Exception as e:
            log_message("error", f"Wikipedia lookup failed for '{query}': {e}")

        # Gemini fallback only for Wikipedia failures
        return self._handle_ai(query)

    def _handle_reminder(self, params: dict) -> str:
        """Sets a timed reminder using threading — Gemini is NOT called."""
        if not params or "seconds" not in params:
            return (
                "Please specify the reminder duration. "
                "For example: remind me in 10 minutes to check the oven."
            )

        seconds = params["seconds"]
        message = params.get("message", "Your reminder is due.")
        amount  = params.get("amount", seconds)
        unit    = params.get("unit", "seconds")

        log_message("info", f"Executed: set_reminder({seconds}, '{message}')")
        try:
            result = set_reminder(seconds, message)
            # Pluralise unit for display
            display_unit = unit if unit.endswith("s") else unit + "s"
            return f"Done! I'll remind you in {amount} {display_unit} to {message}"
        except Exception as e:
            log_message("error", f"_handle_reminder error: {e}")
            return "Unable to set the reminder. Please try again."

    def _handle_email(self) -> str:
        """Starts the email workflow — Gemini is NOT called."""
        log_message("info", "Email command dispatched.")
        return (
            "The email feature is currently disabled. "
            "You can enable it by configuring EMAIL_ADDRESS and EMAIL_PASSWORD in the .env file."
        )

    def _handle_help(self) -> str:
        return (
            f"I am {self.assistant_name}, your desktop AI assistant. Here is what I can do:\n"
            "• Tell you the current time and date\n"
            "• Get live weather for any city\n"
            "• Search Google for anything\n"
            "• Open websites like YouTube, GitHub, Google, LinkedIn, and more\n"
            "• Look up topics on Wikipedia\n"
            "• Set timed reminders\n"
            "• Answer general knowledge questions via Gemini AI\n"
            "Just say a command or ask a question!"
        )

    def _handle_self_query(self) -> str:
        return (
            f"I am {self.assistant_name}, an AI-powered desktop voice assistant. "
            "I can execute local actions like opening websites, checking the weather, and setting reminders, "
            "and I can answer general knowledge questions using Gemini AI."
        )

    def _handle_custom(self, key: str) -> str:
        """Execute a user-defined custom command."""
        val = self.custom_commands.get(key)
        if not val:
            return "I could not find that custom command."
        if isinstance(val, dict) and "open" in val:
            url = val["open"]
            log_message("info", f"Custom command: open_website('{url}')")
            open_website(url)
            return f"Opening {url}."
        return str(val)

    def _handle_exit(self) -> str:
        return f"Goodbye! {self.assistant_name} is shutting down. Have a great day!"

    # =========================================================
    # Gemini AI Fallback — called ONLY when no local handler matches
    # =========================================================
    def _handle_ai(self, command: str) -> str:
        """
        Send the command to Gemini AI. This is the LAST resort — it is
        only reached when the intent detector returns AI_FALLBACK or when
        Wikipedia fails to return a useful result.
        """
        try:
            if not getattr(config, "GEMINI_API_KEY", None):
                return "AI service is unavailable. Please set your GEMINI_API_KEY in the .env file."

            prompt = self._build_ai_prompt(command)
            log_message("info", f"Executed: ask_gemini() for: '{command[:80]}'")
            result = ask_gemini(prompt)

            if not result or not result.strip():
                return "AI service did not return a response. Please try again."

            return result

        except Exception as e:
            log_message("error", f"_handle_ai error: {e}")
            return "AI service is temporarily unavailable. Please try again later."

    def _build_ai_prompt(self, command: str, max_turns: int = 6) -> str:
        """Build a contextual prompt with recent conversation history."""
        try:
            parts = [
                f"You are {self.assistant_name}, a helpful AI assistant. "
                "Answer the user's question concisely and accurately."
            ]
            for entry in self.conversation_history[-max_turns:]:
                user = entry.get("command", "")
                resp = entry.get("response", "")
                if user:
                    parts.append(f"User: {user}")
                if resp:
                    parts.append(f"Assistant: {resp}")
            parts.append(f"User: {command}")
            parts.append("Assistant:")
            return "\n".join(parts)
        except Exception as e:
            log_message("error", f"_build_ai_prompt error: {e}")
            return command

    # =========================================================
    # Conversation History
    # =========================================================
    def _add_to_history(self, command: str, response: str) -> None:
        try:
            self.conversation_history.append({
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "command":   command,
                "response":  response,
            })
            if len(self.conversation_history) > self.max_history_length:
                self.conversation_history.pop(0)
        except Exception as e:
            log_message("error", f"_add_to_history error: {e}")

    # Keep backward-compatible public alias
    def add_to_history(self, command: str, response: str) -> None:
        self._add_to_history(command, response)

    def clear_history(self) -> None:
        try:
            self.conversation_history.clear()
            log_message("info", "Conversation history cleared.")
        except Exception as e:
            log_message("error", f"clear_history error: {e}")

    def get_history(self) -> list:
        return self.conversation_history
