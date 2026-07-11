# Advanced BMI Calculator

A professional desktop **Body Mass Index (BMI) Calculator** developed in **Python** using **Tkinter** and **SQLite** as part of the **Oasis Infobyte Internship (OIBSIP) – Task 2**.

The application allows users to calculate their BMI, classify their health status, save records locally, view historical data, and visualize BMI trends through interactive charts.

---

## Features

* Modern and user-friendly graphical interface
* BMI calculation using the standard WHO formula
* Automatic BMI category classification
* Color-coded health status
* Personalized health recommendations
* Multi-user support
* Save BMI records to SQLite database
* View complete BMI history
* Search records by user name
* Delete saved records
* Interactive BMI trend graph using Matplotlib
* Input validation with professional error handling
* Custom application icon
* Responsive and clean interface

---

## BMI Formula

BMI is calculated using:

```
BMI = Weight (kg) / Height² (m²)
```

---

## BMI Categories

|      BMI Range | Category      |
| -------------: | ------------- |
|     Below 18.5 | Underweight   |
|    18.5 – 24.9 | Normal Weight |
|    25.0 – 29.9 | Overweight    |
| 30.0 and Above | Obese         |

---

## Technologies Used

* Python 3
* Tkinter
* SQLite3
* Matplotlib
* Pillow

---

## Project Structure

```
Python-Task2-BMICalculator/
│
├── assets/
│   └── app_icon.ico
│
├── screenshots/
│
├── bmi_calculator.py
├── bmi_utils.py
├── database.py
│
├── README.md
├── requirements.txt
├── .gitignore
├── pyproject.toml
└── setup.cfg
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Ibrar540/OIBSIP.git
```

Navigate to the project folder:

```bash
cd Python-Task2-BMICalculator
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python bmi_calculator.py
```

---

## Screenshots

Add screenshots of the application inside the **screenshots/** folder.

Recommended screenshots:

* Main Window
* BMI Calculation Result
* History Window
* BMI Trend Graph

---

## Learning Outcomes

Through this project, I practiced:

* GUI development using Tkinter
* Modular Python programming
* Object-Oriented Programming (OOP)
* SQLite database integration
* Data visualization with Matplotlib
* Input validation and exception handling
* Desktop application design

---

## Future Improvements

* Export records to PDF
* Dark and Light mode
* User authentication
* BMI statistics dashboard
* Cloud database synchronization
* Nutrition and fitness recommendations

---

## Author

**Ibrar Ahmad**

AI & Machine Learning Intern
Oasis Infobyte

GitHub: https://github.com/Ibrar540

LinkedIn: https://www.linkedin.com/in/ibrar-ahmad-3366bb364/

---

## License

This project is developed for educational and internship purposes as part of the Oasis Infobyte Internship Program.
