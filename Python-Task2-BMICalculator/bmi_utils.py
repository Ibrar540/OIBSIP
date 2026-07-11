"""
=========================================================
BMI Calculator - Utility Functions
=========================================================
Author      : Ibrar Ahmad
Project     : OIBSIP - Task 2 (Advanced BMI Calculator)
Description : Contains BMI calculation, validation,
              classification, health recommendations,
              and UI color mapping.
=========================================================
"""


def validate_input(name, weight, height):
    """
    Validate user input.

    Returns:
        (True, "") if valid
        (False, "Error message") if invalid
    """

    name = name.strip()

    if not name:
        return False, "Please enter your name."

    try:
        weight = float(weight)
        height = float(height)
    except ValueError:
        return False, "Weight and Height must be numeric values."

    if weight <= 0:
        return False, "Weight must be greater than 0."

    if height <= 0:
        return False, "Height must be greater than 0."

    if weight > 500:
        return False, "Weight seems unrealistic."

    if height > 3:
        return False, "Height must be entered in meters (e.g. 1.75)."

    return True, ""


def calculate_bmi(weight, height):
    """
    Calculate BMI.

    Formula:
        BMI = Weight / Height²
    """

    bmi = float(weight) / (float(height) ** 2)
    return round(bmi, 2)


def get_bmi_category(bmi):
    """
    Return BMI category.
    """

    if bmi < 18.5:
        return "Underweight"

    elif bmi < 25:
        return "Normal Weight"

    elif bmi < 30:
        return "Overweight"

    else:
        return "Obese"


def get_health_advice(category):
    """
    Return professional health recommendation.
    """

    advice = {
        "Underweight":
            "You are below the recommended weight range.\n"
            "Consider eating a balanced, nutritious diet and "
            "consult a healthcare professional if needed.",

        "Normal Weight":
            "Excellent! Your BMI is within the healthy range.\n"
            "Maintain a balanced diet and regular physical activity.",

        "Overweight":
            "Your BMI indicates you are above the healthy range.\n"
            "Regular exercise and a balanced diet may help improve your health.",

        "Obese":
            "Your BMI falls within the obesity range.\n"
            "It is recommended to consult a healthcare professional "
            "for personalized advice."
    }

    return advice.get(category, "")


def get_category_color(category):
    """
    Return UI color based on BMI category.
    """

    colors = {
        "Underweight": "#3498DB",     # Blue
        "Normal Weight": "#2ECC71",   # Green
        "Overweight": "#F39C12",      # Orange
        "Obese": "#E74C3C"            # Red
    }

    return colors.get(category, "#FFFFFF")


def bmi_result(name, weight, height):
    """
    Complete BMI calculation.

    Returns:
        dict containing all result data.
    """

    bmi = calculate_bmi(weight, height)

    category = get_bmi_category(bmi)

    advice = get_health_advice(category)

    color = get_category_color(category)

    return {
        "name": name.strip(),
        "weight": round(float(weight), 2),
        "height": round(float(height), 2),
        "bmi": bmi,
        "category": category,
        "advice": advice,
        "color": color
    }