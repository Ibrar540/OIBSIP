"""NLU utilities with optional spaCy enrichment.

Behavior:
- If `spacy` and the English model (`en_core_web_sm`) are available,
  the parser will use spaCy to extract named entities (GPE/PERSON/ORG)
  and improve city/query detection.
- If spaCy is not available, it falls back to a lightweight rule-based
  parser (previous behavior).

The `parse_intent()` function returns a dict with at least an `intent`
key and optional entity keys like `city`, `query`, `url`, `amount`,
`unit`, and `message`.
"""
from typing import Dict, Any
import re

# Try to load spaCy and an English model; if not available, fall back
nlp = None
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        # If the packaged model is not available, a user can run:
        # python -m spacy download en_core_web_sm
        try:
            # attempt to import fallback package name
            import importlib
            pkg = importlib.import_module("en_core_web_sm")
            nlp = pkg.load()
        except Exception:
            nlp = None
except Exception:
    nlp = None


def _rule_parse(cmd: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"intent": "unknown"}

    if re.search(r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b", cmd):
        out["intent"] = "greeting"
        return out

    if any(k in cmd for k in ["bye", "exit", "shutdown", "goodbye", "quit", "stop listening"]):
        out["intent"] = "exit"
        return out

    if "time" in cmd and "what" in cmd:
        out["intent"] = "time"
        return out
    if any(k in cmd for k in ["today", "date", "what is today's date", "current date"]) and "what" in cmd:
        out["intent"] = "date"
        return out

    if any(k in cmd for k in ["weather", "rain", "raining", "forecast", "temperature", "humidity", "wind", "chance of rain"]):
        out["intent"] = "weather"
        m = re.search(r"(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\s+today|\s+now|\s+currently|$)", cmd)
        if m:
            out["city"] = m.group(1).strip()
        else:
            m2 = re.search(r"weather\s+([a-zA-Z\s]+)$", cmd)
            if m2:
                out["city"] = m2.group(1).strip()
        return out

    if any(cmd.startswith(p) for p in ["who is", "what is", "tell me about", "where is", "where are", "locate", "location of"]):
        out["intent"] = "wikipedia"
        q = cmd
        for prefix in ["who is", "what is", "tell me about", "where is", "where are", "locate", "location of"]:
            if q.startswith(prefix):
                q = q[len(prefix):]
                break
        out["query"] = q.strip()
        return out

    if any(k in cmd for k in ["search", "google", "lookup"]):
        out["intent"] = "search"
        q = cmd
        for kw in ["search for", "search", "google", "lookup"]:
            q = q.replace(kw, "")
        out["query"] = q.strip()
        return out

    if "open" in cmd:
        out["intent"] = "open"
        m = re.search(r"(https?://[\w\-./?&=%]+)", cmd)
        if m:
            out["url"] = m.group(1)
            return out
        sites = ["youtube", "github", "google", "linkedin", "gmail", "chatgpt", "stackoverflow"]
        for s in sites:
            if s in cmd:
                out["site"] = s
                return out
        return out

    m = re.search(r"remind me (?:in|after)\s+(\d+)\s*(second|seconds|minute|minutes|hour|hours)\s*(?:to|that|about)?\s*(.*)$", cmd)
    if m:
        out["intent"] = "reminder"
        out["amount"] = int(m.group(1))
        out["unit"] = m.group(2)
        out["message"] = m.group(3).strip() or "Your reminder is due."
        return out

    if "send email" in cmd or cmd.startswith("email"):
        out["intent"] = "email"
        return out

    return out


def parse_intent(command: str) -> Dict[str, Any]:
    cmd = command.lower().strip()
    # If spaCy available, use it to improve entity extraction
    if nlp is not None:
        try:
            doc = nlp(command)
            # Basic intent heuristics using tokens and lemmas
            lemmas = " ".join([t.lemma_.lower() for t in doc])
            # greetings
            if any(w in lemmas for w in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
                return {"intent": "greeting"}
            if any(w in lemmas for w in ["bye", "exit", "shutdown", "goodbye", "quit"]):
                return {"intent": "exit"}

            # time/date
            if "time" in lemmas and "what" in lemmas:
                return {"intent": "time"}
            if any(k in lemmas for k in ["today", "date"]) and "what" in lemmas:
                return {"intent": "date"}

            # entities
            ents = {ent.label_: ent.text for ent in doc.ents}

            # weather: look for GPE
            if any(tok.lower_ in ["weather", "rain", "raining", "forecast", "temperature", "humidity", "wind"] for tok in doc):
                out = {"intent": "weather"}
                if "GPE" in ents:
                    out["city"] = ents.get("GPE")
                else:
                    # try prepositions
                    m = re.search(r"(?:in|at|for)\s+([A-Za-z\s]+)", command)
                    if m:
                        out["city"] = m.group(1).strip()
                return out

            # wikipedia-like questions
            if any(command.lower().startswith(p) for p in ["who is", "what is", "tell me about", "where is", "where are", "locate", "location of"]):
                out = {"intent": "wikipedia"}
                # prefer PERSON/ORG/GPE as query
                for label in ("PERSON", "ORG", "GPE", "LOC"):
                    if label in ents:
                        out["query"] = ents[label]
                        return out
                # fallback: strip prefix
                q = command
                for prefix in ["who is", "what is", "tell me about", "where is", "where are", "locate", "location of"]:
                    if q.lower().startswith(prefix):
                        q = q[len(prefix):]
                        break
                out["query"] = q.strip()
                return out

            # search
            if any(tok.lower_ in ["search", "google", "lookup"] for tok in doc):
                q = command
                for kw in ["search for", "search", "google", "lookup"]:
                    q = re.sub(kw, "", q, flags=re.IGNORECASE)
                return {"intent": "search", "query": q.strip()}

            # open website
            if any(tok.lower_ == "open" for tok in doc):
                out = {"intent": "open"}
                # url entity
                m = re.search(r"(https?://[\w\-./?&=%]+)", command)
                if m:
                    out["url"] = m.group(1)
                    return out
                # site name heuristic
                for s in ["youtube", "github", "google", "linkedin", "gmail", "chatgpt", "stackoverflow"]:
                    if s in command.lower():
                        out["site"] = s
                        return out
                return out

            # reminder
            m = re.search(r"remind me (?:in|after)\s+(\d+)\s*(second|seconds|minute|minutes|hour|hours)\s*(?:to|that|about)?\s*(.*)$", command, flags=re.IGNORECASE)
            if m:
                return {"intent": "reminder", "amount": int(m.group(1)), "unit": m.group(2), "message": m.group(3).strip() or "Your reminder is due."}

            # email
            if "send email" in command.lower() or command.lower().startswith("email"):
                return {"intent": "email"}

            # fallback to rules
            return _rule_parse(cmd)

        except Exception:
            return _rule_parse(cmd)

    # spaCy not available: fallback
    return _rule_parse(cmd)
