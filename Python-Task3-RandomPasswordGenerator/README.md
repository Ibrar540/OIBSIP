# 🔐 Advanced Random Password Generator

A professional desktop application built with **Python** and **Tkinter** that securely generates strong, customizable passwords using Python's cryptographically secure `secrets` module. The application features a modern graphical user interface, password strength analysis, clipboard support, password history, and detailed password statistics.

> **Oasis Infobyte – Python Programming Internship**  
> **Task 3: Advanced Random Password Generator**

---

##  Overview

Weak passwords are one of the leading causes of compromised online accounts. This project provides an easy-to-use desktop application that generates highly secure passwords based on user-selected criteria while offering real-time feedback on password strength and quality.

Unlike basic password generators, this application guarantees that every generated password satisfies the selected security requirements and includes useful metrics such as entropy and strength analysis.

---

#  Features

###  Secure Password Generation
- Generates cryptographically secure passwords using Python's `secrets` module
- Password length selectable from **8–20 characters**
- Guarantees at least one character from every selected category
- Prevents insecure password combinations

---

###  Customizable Password Options

Choose any combination of:

- ✅ Uppercase Letters
- ✅ Lowercase Letters
- ✅ Numbers
- ✅ Symbols

Additional security option:

- ✅ Exclude ambiguous characters (O, 0, I, l, 1)

---

###  Password Strength Analysis

The application evaluates every generated password and displays:

- Weak
- Medium
- Strong
- Very Strong

using a visual strength indicator.

---

###  Password Statistics

Displays useful information including:

- Password Length
- Uppercase Count
- Lowercase Count
- Number Count
- Symbol Count
- Password Entropy (bits)

---

###  Clipboard Support

Generated passwords can be copied instantly with a single click.

---

###  Password History

Maintains the most recent generated passwords during the current session, including:

- Time Generated
- Password Length
- Password Strength
- Generated Password

---

###  Modern Desktop Interface

- Professional dark theme
- Responsive layout
- Modern buttons
- Clean typography
- User-friendly interface

---

# Technologies Used

- Python 3
- Tkinter
- ttk
- secrets
- string
- math
- datetime
- pyperclip

---

#  Project Structure

```
Python-Task3-RandomPasswordGenerator/
│
├── password_generator.py
├── README.md
├── requirements.txt
```

---

#  Installation

## 1. Clone the repository

```bash
git clone https://github.com/yourusername/OIBSIP.git
```

---

## 2. Navigate to the project folder

```bash
cd OIBSIP/Python-Task3-RandomPasswordGenerator
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Run the application

```bash
python password_generator.py
```

---

#  Application Preview

Add screenshots here.

Example:

```
screenshots/

Home Screen

Generated Password

Password History

Strength Indicator
```

---

# Security Highlights

This application follows several password security best practices:

- Uses Python's **secrets** module instead of the insecure `random` module.
- Guarantees at least one character from every selected character group.
- Supports strong symbol combinations.
- Prevents insecure password configurations.
- Optionally removes visually confusing characters.
- Calculates password entropy for additional security analysis.

---

#  Learning Outcomes

During this project, I learned:

- Secure password generation techniques
- Cryptographically secure random number generation
- Python GUI development using Tkinter
- Event-driven programming
- Object-Oriented Programming (OOP)
- Password strength evaluation
- Clipboard integration
- Desktop application design
- Input validation
- Python project organization

---

#  Future Improvements

Potential enhancements include:

- Password save/export feature
- QR code generation
- Dark/Light theme switching
- Password breach checking using HaveIBeenPwned API
- Password expiration reminder
- Multiple language support
- Password generation presets
- Automatic password generation shortcuts

---

#  Author

**Ibrar Ahmad**

AI & Machine Learning Intern

Computer & Information Systems Engineering Student

GitHub: https://github.com/Ibrar540

LinkedIn: https://www.linkedin.com/in/ibrar-ahmad-3366bb364/

---

#  License

This project was developed for educational purposes as part of the **Oasis Infobyte Python Programming Internship**.