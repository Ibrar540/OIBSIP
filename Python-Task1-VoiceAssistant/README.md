# 🎙️ Advanced AI Voice Assistant

A modern, AI-powered desktop voice assistant developed using **Python** that performs voice recognition, natural language interaction, web search, weather updates, reminders, email automation, and AI-powered conversations using **Google Gemini 2.5 Flash**.

This project was developed as part of the **Oasis Infobyte Python Programming Internship – Task 1** and demonstrates the integration of speech recognition, desktop GUI development, external APIs, and artificial intelligence into a single desktop application.

---

## 📌 Project Overview

The **Advanced AI Voice Assistant** is a desktop application that enables users to interact with their computer using natural voice commands. It combines speech recognition, text-to-speech, internet services, and generative AI to create an interactive personal assistant.

The application features a clean and modern graphical interface, supports voice and text input, and responds with spoken feedback while performing various productivity tasks.

---

# ✨ Features

## 🎤 Voice Recognition

- Recognizes user speech through the microphone
- Converts speech into text
- Supports natural language commands
- Gracefully handles unrecognized speech

---

## 🗣 Text-to-Speech

- Converts responses into natural speech
- Adjustable voice speed
- Adjustable volume
- Human-like interaction

---

## 🤖 AI-Powered Conversations

Powered by **Google Gemini 2.5 Flash**

The assistant can answer:

- General knowledge questions
- Programming questions
- Technology topics
- Educational queries
- Explanations
- AI-generated responses

---

## 🌍 Google Search

Search the web using voice commands.

Examples:

- Search Python tutorials
- Search machine learning
- Search weather today

---

## 📖 Wikipedia Search

Retrieve concise information directly from Wikipedia.

Examples:

- Who is Alan Turing?
- Tell me about Artificial Intelligence
- What is Machine Learning?

---

## 🌦 Live Weather Updates

Fetch real-time weather information using the OpenWeatherMap API.

Displays:

- Current temperature
- Feels like temperature
- Weather condition
- Humidity
- Wind speed

---

## 📧 Email Automation

Send emails using voice commands.

Supports:

- Receiver
- Subject
- Message body

Uses Gmail SMTP with App Password authentication.

---

## ⏰ Reminder System

Create reminders using natural language.

Examples:

- Remind me in 10 minutes
- Remind me after 30 seconds
- Remind me in 2 hours

---

## 🌐 Website Launcher

Quickly open popular websites.

Supported examples:

- YouTube
- Google
- GitHub
- LinkedIn
- Gmail
- ChatGPT
- Stack Overflow

---

## 💬 Conversation History

The assistant maintains a conversation log including:

- User command
- Assistant response
- Timestamp

---

## 📝 Logging

Every interaction is recorded inside:

```
assistant.log
```

This helps debugging and monitoring application activity.

---

## 🎨 Modern Desktop Interface

The application features:

- Professional Dark Theme
- Responsive Layout
- Modern Typography
- Status Indicators
- Scrollable Conversation Area
- User-Friendly Controls

---

# 🛠 Technologies Used

- Python 3.12+
- Tkinter
- ttk
- SpeechRecognition
- PyAudio
- pyttsx3
- Google Gemini 2.5 Flash API
- OpenWeatherMap API
- Wikipedia API
- Requests
- pywhatkit
- python-dotenv
- Pillow
- SMTP
- Threading

---

# 📂 Project Structure

```
Python-Task1-VoiceAssistant/
│
├── assets/
│   └── icon.ico
│
├── screenshots/
│
├── voice_assistant.py
├── commands.py
├── config.py
├── utils.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
└── assistant.log
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Ibrar540/OIBSIP.git
```

---

## 2. Navigate to the Project

```bash
cd OIBSIP/Python-Task1-VoiceAssistant
```

---

## 3. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

### Activate

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

---

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 5. Configure Environment Variables

Create a `.env` file using `.env.example`.

```env
GEMINI_API_KEY=your_gemini_api_key

WEATHER_API_KEY=your_openweathermap_api_key

EMAIL_ADDRESS=your_email@gmail.com

EMAIL_PASSWORD=your_gmail_app_password
```

---

## 6. Run the Application

```bash
python voice_assistant.py
```

---

## 📦 Packaging & Install

You can install the project locally and create an executable entrypoint.

Install build tools (recommended):

```bash
python -m pip install --upgrade pip setuptools wheel
```

Install into your environment (editable mode):

```bash
pip install -e .
```

After installation you can launch the assistant with the console script:

```bash
nova-assistant
```

Or run directly:

```bash
python -m voice_assistant
```

Notes:

- Installation will install dependencies listed in `setup.cfg`.
- For development, prefer `pip install -e .` and keep `requirements.txt` up to date.

Optional (spaCy):

If you want improved NLU using spaCy, install the model after installing dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

If `en_core_web_sm` is not installed, the NLU will automatically fall back to the rule-based parser.

# 🖥 Application Screenshots

Add screenshots here.

```
screenshots/

Home Screen

Voice Listening

Gemini Response

Weather Information

Conversation History

Reminder Notification
```

---

# 🎙 Example Voice Commands

## Greetings

- Hello
- Hi
- Good Morning

---

## Time & Date

- What time is it?
- Tell me today's date.

---

## Google Search

- Search Python programming
- Search Artificial Intelligence

---

## Wikipedia

- Who is Elon Musk?
- What is Deep Learning?

---

## Weather

- Weather in Karachi
- Weather in Islamabad

---

## Websites

- Open GitHub
- Open YouTube
- Open LinkedIn

---

## Reminders

- Remind me in 15 minutes
- Remind me after 30 seconds

---

## AI Questions

- Explain Machine Learning.
- What is Quantum Computing?
- Write a Python function for sorting.

---

## Exit

- Goodbye
- Exit
- Stop Listening

---

# 🔒 Privacy & Security

This application respects user privacy.

- Voice input is processed only when listening is activated.
- Audio recordings are **not permanently stored**.
- User credentials are stored using environment variables.
- API keys are never hardcoded.
- Gemini API receives only the user's query when AI assistance is requested.
- Sensitive files are excluded using `.gitignore`.

Notes and clarifications:

- The email-sending feature is disabled by default in this distribution. Enable it only after configuring `EMAIL_ADDRESS` and `EMAIL_PASSWORD` in a secure `.env` file and understanding the privacy implications.
- Custom commands can be defined in `custom_commands.json` (project root). These are local mappings and are not sent to external services.
- Text-to-speech (TTS) is performed locally using `pyttsx3` and is not uploaded to external providers.
- Conversation history stored in memory is kept only for context during a running session and is not persisted to disk unless you enable logging; `assistant.log` records interactions for debugging only.

---

# 📚 Learning Outcomes

This project demonstrates practical experience with:

- Speech Recognition
- Text-to-Speech Systems
- Desktop GUI Development
- Object-Oriented Programming
- API Integration
- Google Gemini AI
- Weather API Integration
- Email Automation
- Threading
- Logging
- Exception Handling
- Secure Configuration Management
- Professional Python Project Structure

---

# 🚀 Future Enhancements

Possible future improvements include:

- Voice authentication
- Wake-word detection
- Smart home integration
- Calendar integration
- To-do list management
- Speech emotion recognition
- Multi-language support
- Offline AI model support
- Voice customization
- Theme switching (Dark / Light)

---

# 👨‍💻 Author

**Ibrar Ahmad**

AI & Machine Learning Intern

Bachelor of Engineering (Computer & Information Systems)

NED University of Engineering & Technology

GitHub:
https://github.com/Ibrar540

LinkedIn:
https://www.linkedin.com/in/ibrar-ahmad-3366bb364/

---

# 📄 License

This project was developed for educational and portfolio purposes as part of the **Oasis Infobyte Python Programming Internship**.

---

