"""
=========================================================
BMI Calculator - Database Module
=========================================================
Author      : Ibrar Ahmad
Project     : OIBSIP - Task 2 (Advanced BMI Calculator)
Description : Handles all SQLite database operations.
=========================================================
"""

import sqlite3
from datetime import datetime
import os

DATABASE_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bmi_records.db")


def get_connection():
    """
    Create and return a database connection.
    """
    return sqlite3.connect(DATABASE_NAME)


def create_database():
    """
    Create database and table if they don't already exist.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bmi_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            bmi REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_record(name, weight, height, bmi, category):
    """
    Save a BMI record.
    """

    conn = get_connection()
    cursor = conn.cursor()

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO bmi_records
        (name, weight, height, bmi, category, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        weight,
        height,
        bmi,
        category,
        current_date
    ))

    conn.commit()
    conn.close()


def get_all_records():
    """
    Return all records ordered by newest first.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM bmi_records
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    conn.close()

    return records


def get_user_records(name):
    """
    Return BMI history for a specific user.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM bmi_records
        WHERE LOWER(name)=LOWER(?)
        ORDER BY id ASC
    """, (name,))

    records = cursor.fetchall()

    conn.close()

    return records


def delete_record(record_id):
    """
    Delete one BMI record.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM bmi_records
        WHERE id=?
    """, (record_id,))

    conn.commit()
    conn.close()


def delete_all_records():
    """
    Delete every record from the database.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM bmi_records
    """)

    conn.commit()
    conn.close()


def search_users(keyword):
    """
    Search users by name.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM bmi_records
        WHERE name LIKE ?
        ORDER BY id DESC
    """, (f"%{keyword}%",))

    records = cursor.fetchall()

    conn.close()

    return records


def record_count():
    """
    Return total number of saved records.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM bmi_records
    """)

    total = cursor.fetchone()[0]

    conn.close()

    return total


# Automatically create database
create_database()