"""
bmi_calculator.py

Advanced BMI Calculator - Main Application Module
OIBSIP - Task 2

This module contains the BMICalculatorApp class which implements a
modern, dark-themed Tkinter GUI for calculating, saving, viewing,
and visualizing BMI records.

Dependencies:
    - bmi_utils.py : BMI calculation, category, recommendation, color logic
    - database.py  : SQLite database operations (CRUD for BMI records)
"""

import os
import sqlite3
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Local modules (already implemented - DO NOT MODIFY)
from bmi_utils import (
    calculate_bmi,
    get_bmi_category,
    get_health_advice,
    get_category_color,
)
import database


class BMICalculatorApp:
    """
    Main application class for the Advanced BMI Calculator.

    This class builds and manages the entire Tkinter GUI, including
    input fields, result display, history viewing, BMI trend plotting,
    and database interaction.
    """

    # ------------------------------------------------------------------
    # THEME CONSTANTS
    # ------------------------------------------------------------------
    BG_COLOR = "#1E1E2F"        # Main window background
    CARD_COLOR = "#2A2A40"      # Card / panel background
    PRIMARY_BTN = "#4A90E2"     # Primary accent button (blue)
    SUCCESS_COLOR = "#2ECC71"   # Success green
    WARNING_COLOR = "#F39C12"   # Warning orange
    DANGER_COLOR = "#E74C3C"    # Danger red
    TEXT_COLOR = "#FFFFFF"      # Default text color
    MUTED_TEXT = "#B0B0C3"      # Secondary/muted text color

    FONT_TITLE = ("Segoe UI", 20, "bold")
    FONT_HEADING = ("Segoe UI", 13, "bold")
    FONT_LABEL = ("Segoe UI", 11)
    FONT_ENTRY = ("Segoe UI", 11)
    FONT_RESULT_VALUE = ("Segoe UI", 26, "bold")
    FONT_RESULT_LABEL = ("Segoe UI", 12, "bold")
    FONT_BUTTON = ("Segoe UI", 10, "bold")

    def __init__(self, root):
        """
        Initialize the BMI Calculator application.

        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        database.create_database()

        # Holds the currently calculated BMI values (used when saving)
        self.current_bmi = None
        self.current_category = None

        self._configure_window()
        self._configure_styles()
        self._build_layout()

    # ------------------------------------------------------------------
    # WINDOW CONFIGURATION
    # ------------------------------------------------------------------
    def _configure_window(self):
        """Configure the main application window (title, size, icon, bg)."""
        self.root.title("Advanced BMI Calculator")
        self.root.geometry("950x680")
        self.root.minsize(880, 620)
        self.root.configure(bg=self.BG_COLOR)

        # Attempt to set window icon; fail silently if not found/unsupported
        icon_path = os.path.join("assets", "app_icon.ico")
        try:
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except tk.TclError:
            # Icon format not supported on this platform (e.g., Linux/Mac)
            pass

        # Handle window close event gracefully
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)

        # Configure grid weights for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _configure_styles(self):
        """Configure ttk styles for a consistent professional dark theme."""
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview styling (used in History window)
        style.configure(
            "Treeview",
            background=self.CARD_COLOR,
            foreground=self.TEXT_COLOR,
            fieldbackground=self.CARD_COLOR,
            rowheight=28,
            font=self.FONT_LABEL,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=self.PRIMARY_BTN,
            foreground=self.TEXT_COLOR,
            font=self.FONT_HEADING,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", self.PRIMARY_BTN)],
            foreground=[("selected", self.TEXT_COLOR)],
        )

        # Scrollbar styling
        style.configure(
            "Vertical.TScrollbar",
            background=self.CARD_COLOR,
            troughcolor=self.BG_COLOR,
            bordercolor=self.BG_COLOR,
            arrowcolor=self.TEXT_COLOR,
        )

    # ------------------------------------------------------------------
    # MAIN LAYOUT
    # ------------------------------------------------------------------
    def _build_layout(self):
        """Build the main application layout (header, input card, results, buttons)."""
        main_container = tk.Frame(self.root, bg=self.BG_COLOR)
        main_container.grid(row=0, column=0, sticky="nsew", padx=25, pady=20)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(2, weight=1)

        self._build_header(main_container)
        self._build_input_card(main_container)
        self._build_result_card(main_container)
        self._build_action_buttons(main_container)

    def _build_header(self, parent):
        """Build the application header/title section."""
        header_frame = tk.Frame(parent, bg=self.BG_COLOR)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        title_label = tk.Label(
            header_frame,
            text="Advanced BMI Calculator",
            font=self.FONT_TITLE,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame,
            text="Track, analyze, and visualize your Body Mass Index over time",
            font=self.FONT_LABEL,
            bg=self.BG_COLOR,
            fg=self.MUTED_TEXT,
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

    def _build_input_card(self, parent):
        """Build the card containing Name, Weight, and Height input fields."""
        card = tk.Frame(parent, bg=self.CARD_COLOR, padx=20, pady=20)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        card.columnconfigure(1, weight=1)
        card.columnconfigure(3, weight=1)

        card_title = tk.Label(
            card,
            text="Personal Details",
            font=self.FONT_HEADING,
            bg=self.CARD_COLOR,
            fg=self.TEXT_COLOR,
        )
        card_title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 15))

        # Name field
        tk.Label(
            card, text="Name", font=self.FONT_LABEL,
            bg=self.CARD_COLOR, fg=self.TEXT_COLOR,
        ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=8)

        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(
            card, textvariable=self.name_var, font=self.FONT_ENTRY,
            bg="#3A3A55", fg=self.TEXT_COLOR, insertbackground=self.TEXT_COLOR,
            relief="flat", highlightthickness=1,
            highlightbackground="#44445A", highlightcolor=self.PRIMARY_BTN,
        )
        self.name_entry.grid(row=1, column=1, columnspan=3, sticky="ew", ipady=6, pady=8)

        # Weight field
        tk.Label(
            card, text="Weight (kg)", font=self.FONT_LABEL,
            bg=self.CARD_COLOR, fg=self.TEXT_COLOR,
        ).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=8)

        self.weight_var = tk.StringVar()
        self.weight_entry = tk.Entry(
            card, textvariable=self.weight_var, font=self.FONT_ENTRY,
            bg="#3A3A55", fg=self.TEXT_COLOR, insertbackground=self.TEXT_COLOR,
            relief="flat", highlightthickness=1,
            highlightbackground="#44445A", highlightcolor=self.PRIMARY_BTN,
        )
        self.weight_entry.grid(row=2, column=1, sticky="ew", ipady=6, pady=8, padx=(0, 15))

        # Height field
        tk.Label(
            card, text="Height (m)", font=self.FONT_LABEL,
            bg=self.CARD_COLOR, fg=self.TEXT_COLOR,
        ).grid(row=2, column=2, sticky="w", padx=(0, 10), pady=8)

        self.height_var = tk.StringVar()
        self.height_entry = tk.Entry(
            card, textvariable=self.height_var, font=self.FONT_ENTRY,
            bg="#3A3A55", fg=self.TEXT_COLOR, insertbackground=self.TEXT_COLOR,
            relief="flat", highlightthickness=1,
            highlightbackground="#44445A", highlightcolor=self.PRIMARY_BTN,
        )
        self.height_entry.grid(row=2, column=3, sticky="ew", ipady=6, pady=8)

    def _build_result_card(self, parent):
        """Build the card that displays BMI value, category, and recommendation."""
        card = tk.Frame(parent, bg=self.CARD_COLOR, padx=20, pady=20)
        card.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=2)

        card_title = tk.Label(
            card,
            text="Result",
            font=self.FONT_HEADING,
            bg=self.CARD_COLOR,
            fg=self.TEXT_COLOR,
        )
        card_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Left side: BMI value display
        value_frame = tk.Frame(card, bg=self.CARD_COLOR)
        value_frame.grid(row=1, column=0, sticky="nw", padx=(0, 30))

        tk.Label(
            value_frame, text="BMI Value", font=self.FONT_LABEL,
            bg=self.CARD_COLOR, fg=self.MUTED_TEXT,
        ).pack(anchor="w")

        self.bmi_value_label = tk.Label(
            value_frame, text="--", font=self.FONT_RESULT_VALUE,
            bg=self.CARD_COLOR, fg=self.TEXT_COLOR,
        )
        self.bmi_value_label.pack(anchor="w", pady=(2, 10))

        tk.Label(
            value_frame, text="Category", font=self.FONT_LABEL,
            bg=self.CARD_COLOR, fg=self.MUTED_TEXT,
        ).pack(anchor="w")

        self.bmi_category_label = tk.Label(
            value_frame, text="--", font=self.FONT_RESULT_LABEL,
            bg=self.CARD_COLOR, fg=self.TEXT_COLOR,
        )
        self.bmi_category_label.pack(anchor="w", pady=(2, 0))

        # Right side: Health recommendation
        recommendation_frame = tk.Frame(card, bg=self.CARD_COLOR)
        recommendation_frame.grid(row=1, column=1, sticky="nsew")

        tk.Label(
            recommendation_frame, text="Health Advice",
            font=self.FONT_LABEL, bg=self.CARD_COLOR, fg=self.MUTED_TEXT,
        ).pack(anchor="w")

        self.recommendation_label = tk.Label(
            recommendation_frame,
            text="Enter your details and click 'Calculate BMI' to see your results.",
            font=self.FONT_LABEL, bg=self.CARD_COLOR, fg=self.TEXT_COLOR,
            wraplength=420, justify="left",
        )
        self.recommendation_label.pack(anchor="w", pady=(2, 0))

    def _build_action_buttons(self, parent):
        """Build the row of action buttons at the bottom of the window."""
        button_frame = tk.Frame(parent, bg=self.BG_COLOR)
        button_frame.grid(row=3, column=0, sticky="ew")

        # Configure equal-width responsive columns for buttons
        for i in range(6):
            button_frame.columnconfigure(i, weight=1)

        buttons_config = [
            ("Calculate BMI", self.calculate_bmi_action, self.PRIMARY_BTN),
            ("Save Record", self.save_record_action, self.SUCCESS_COLOR),
            ("View History", self.view_history_action, self.PRIMARY_BTN),
            ("Show BMI Trend", self.show_bmi_trend_action, self.PRIMARY_BTN),
            ("Clear Fields", self.clear_fields_action, self.WARNING_COLOR),
            ("Exit", self.exit_application, self.DANGER_COLOR),
        ]

        for idx, (text, command, color) in enumerate(buttons_config):
            btn = self._create_button(button_frame, text, command, color)
            btn.grid(row=0, column=idx, sticky="ew", padx=5, ipady=8)

    def _create_button(self, parent, text, command, bg_color):
        """
        Create a styled, flat, hover-responsive button.

        Args:
            parent (tk.Widget): The parent widget.
            text (str): Button label.
            command (callable): Function to call on click.
            bg_color (str): Background color (hex string).

        Returns:
            tk.Button: The configured button widget.
        """
        btn = tk.Button(
            parent, text=text, command=command, font=self.FONT_BUTTON,
            bg=bg_color, fg=self.TEXT_COLOR, activebackground=bg_color,
            activeforeground=self.TEXT_COLOR, relief="flat", bd=0,
            cursor="hand2", padx=10,
        )

        # Simple hover effect: slightly lighten on enter, restore on leave
        def on_enter(_event):
            btn.configure(bg=self._lighten_color(bg_color))

        def on_leave(_event):
            btn.configure(bg=bg_color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    @staticmethod
    def _lighten_color(hex_color, factor=0.15):
        """
        Lighten a hex color by a given factor for hover effects.

        Args:
            hex_color (str): Color in '#RRGGBB' format.
            factor (float): Amount to lighten (0-1).

        Returns:
            str: Lightened color in '#RRGGBB' format.
        """
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ------------------------------------------------------------------
    # INPUT VALIDATION
    # ------------------------------------------------------------------
    def _validate_inputs(self):
        """
        Validate the Name, Weight, and Height input fields.

        Returns:
            tuple: (name, weight, height) if valid, otherwise None.
        """
        name = self.name_var.get().strip()
        weight_str = self.weight_var.get().strip()
        height_str = self.height_var.get().strip()

        if not name:
            messagebox.showwarning("Missing Information", "Please enter a name.")
            return None

        if not weight_str or not height_str:
            messagebox.showwarning(
                "Missing Information", "Please enter both weight and height."
            )
            return None

        try:
            weight = float(weight_str)
            height = float(height_str)
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Weight and Height must be numeric values."
            )
            return None

        if weight <= 0 or height <= 0:
            messagebox.showerror(
                "Invalid Input", "Weight and Height must be greater than zero."
            )
            return None

        if weight > 500 or height > 3:
            messagebox.showerror(
                "Invalid Input",
                "Please enter realistic values for weight (kg) and height (m).",
            )
            return None

        return name, weight, height

    # ------------------------------------------------------------------
    # CALCULATE BMI
    # ------------------------------------------------------------------
    def calculate_bmi_action(self):
        """Calculate BMI from user input and display the result."""
        validated = self._validate_inputs()
        if validated is None:
            return

        _, weight, height = validated

        try:
            bmi = calculate_bmi(weight, height)
            category = get_bmi_category(bmi)
            recommendation = get_health_advice(category)
            color = get_category_color(category)
        except Exception as error:
            messagebox.showerror(
                "Calculation Error", f"An error occurred while calculating BMI:\n{error}"
            )
            return

        # Store current results for later saving
        self.current_bmi = round(bmi, 2)
        self.current_category = category

        # Update result labels
        self.bmi_value_label.configure(text=f"{self.current_bmi}", fg=color)
        self.bmi_category_label.configure(text=category, fg=color)
        self.recommendation_label.configure(text=recommendation)

    # ------------------------------------------------------------------
    # SAVE RECORD
    # ------------------------------------------------------------------
    def save_record_action(self):
        """Save the current BMI record to the database."""
        if self.current_bmi is None or self.current_category is None:
            messagebox.showwarning(
                "No Result", "Please calculate your BMI before saving a record."
            )
            return

        validated = self._validate_inputs()
        if validated is None:
            return

        name, weight, height = validated
        current_date = datetime.now().strftime("%Y-%m-%d")

        try:
            self.db.insert_record(
                name, weight, height, self.current_bmi, self.current_category, current_date
            )
        except sqlite3.Error as db_error:
            messagebox.showerror(
                "Database Error", f"Failed to save record:\n{db_error}"
            )
            return
        except Exception as error:
            messagebox.showerror(
                "Unexpected Error", f"An unexpected error occurred:\n{error}"
            )
            return

        messagebox.showinfo("Success", "Record saved successfully!")

    # ------------------------------------------------------------------
    # VIEW HISTORY
    # ------------------------------------------------------------------
    def view_history_action(self):
        """Open a Toplevel window displaying all saved BMI records."""
        history_window = tk.Toplevel(self.root)
        history_window.title("BMI History")
        history_window.geometry("850x550")
        history_window.configure(bg=self.BG_COLOR)
        history_window.minsize(700, 450)
        history_window.transient(self.root)

        history_window.columnconfigure(0, weight=1)
        history_window.rowconfigure(2, weight=1)

        # --- Search bar ---
        search_frame = tk.Frame(history_window, bg=self.BG_COLOR)
        search_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        search_frame.columnconfigure(1, weight=1)

        tk.Label(
            search_frame, text="Search by Name:", font=self.FONT_LABEL,
            bg=self.BG_COLOR, fg=self.TEXT_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, textvariable=search_var, font=self.FONT_ENTRY,
            bg="#3A3A55", fg=self.TEXT_COLOR, insertbackground=self.TEXT_COLOR,
            relief="flat", highlightthickness=1,
            highlightbackground="#44445A", highlightcolor=self.PRIMARY_BTN,
        )
        search_entry.grid(row=0, column=1, sticky="ew", ipady=5, padx=(0, 10))

        # --- Toolbar buttons ---
        toolbar_frame = tk.Frame(history_window, bg=self.BG_COLOR)
        toolbar_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # --- Treeview for displaying records ---
        tree_frame = tk.Frame(history_window, bg=self.BG_COLOR)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("ID", "Name", "Weight", "Height", "BMI", "Category", "Date")
        tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse"
        )

        column_widths = {
            "ID": 50, "Name": 140, "Weight": 80, "Height": 80,
            "BMI": 80, "Category": 130, "Date": 110,
        }
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths.get(col, 100), anchor="center")

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=v_scrollbar.set)

        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Helper functions local to this window ---
        def load_records(records=None):
            """Load records into the Treeview, fetching from DB if not provided."""
            tree.delete(*tree.get_children())
            try:
                data = records if records is not None else self.db.fetch_all_records()
            except sqlite3.Error as db_error:
                messagebox.showerror(
                    "Database Error", f"Failed to fetch records:\n{db_error}"
                )
                return
            except Exception as error:
                messagebox.showerror(
                    "Unexpected Error", f"An unexpected error occurred:\n{error}"
                )
                return

            if not data:
                messagebox.showinfo("No Records Found", "There are no records to display.")
                return

            for row in data:
                tree.insert("", "end", values=row)

        def search_records():
            """Search and display records matching the entered name."""
            query = search_var.get().strip()
            if not query:
                load_records()
                return
            try:
                results = self.db.fetch_records_by_name(query)
            except sqlite3.Error as db_error:
                messagebox.showerror(
                    "Database Error", f"Failed to search records:\n{db_error}"
                )
                return
            except Exception as error:
                messagebox.showerror(
                    "Unexpected Error", f"An unexpected error occurred:\n{error}"
                )
                return

            if not results:
                messagebox.showinfo(
                    "No Records Found", f"No records found for '{query}'."
                )
            load_records(results)

        def delete_selected_record():
            """Delete the currently selected record from the database."""
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning(
                    "No Selection", "Please select a record to delete."
                )
                return

            record_values = tree.item(selected_item[0], "values")
            record_id = record_values[0]

            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete record ID {record_id}?",
            )
            if not confirm:
                return

            try:
                self.db.delete_record(record_id)
            except sqlite3.Error as db_error:
                messagebox.showerror(
                    "Database Error", f"Failed to delete record:\n{db_error}"
                )
                return
            except Exception as error:
                messagebox.showerror(
                    "Unexpected Error", f"An unexpected error occurred:\n{error}"
                )
                return

            messagebox.showinfo("Deleted", "Record deleted successfully.")
            load_records()

        # --- Toolbar buttons (created after helper functions are defined) ---
        search_btn = self._create_button(
            search_frame, "Search", search_records, self.PRIMARY_BTN
        )
        search_btn.grid(row=0, column=2, ipady=4, padx=(0, 0))

        delete_btn = self._create_button(
            toolbar_frame, "Delete Selected", delete_selected_record, self.DANGER_COLOR
        )
        delete_btn.grid(row=0, column=0, padx=(0, 10), ipady=6)

        refresh_btn = self._create_button(
            toolbar_frame, "Refresh", lambda: load_records(), self.PRIMARY_BTN
        )
        refresh_btn.grid(row=0, column=1, padx=(0, 10), ipady=6)

        close_btn = self._create_button(
            toolbar_frame, "Close", history_window.destroy, self.WARNING_COLOR
        )
        close_btn.grid(row=0, column=2, ipady=6)

        # Initial load of all records
        load_records()

    # ------------------------------------------------------------------
    # BMI TREND (MATPLOTLIB)
    # ------------------------------------------------------------------
    def show_bmi_trend_action(self):
        """Display a BMI trend line chart for the currently entered user name."""
        name = self.name_var.get().strip()

        if not name:
            messagebox.showwarning(
                "Missing Name", "Please enter a name to view their BMI trend."
            )
            return

        try:
            records = self.db.fetch_records_by_name(name)
        except sqlite3.Error as db_error:
            messagebox.showerror(
                "Database Error", f"Failed to fetch records:\n{db_error}"
            )
            return
        except Exception as error:
            messagebox.showerror(
                "Unexpected Error", f"An unexpected error occurred:\n{error}"
            )
            return

        if not records:
            messagebox.showinfo(
                "No Graph Data", f"No BMI history found for '{name}'."
            )
            return

        # Expected record columns: ID, Name, Weight, Height, BMI, Category, Date
        try:
            dates = [record[6] for record in records]
            bmi_values = [record[4] for record in records]
        except IndexError:
            messagebox.showerror(
                "Data Error", "Record format is invalid. Unable to plot trend."
            )
            return

        if len(dates) < 1:
            messagebox.showinfo(
                "No Graph Data", "Not enough data points to display a trend."
            )
            return

        self._open_trend_window(name, dates, bmi_values)

    def _open_trend_window(self, name, dates, bmi_values):
        """
        Open a Toplevel window and render a BMI trend chart using matplotlib.

        Args:
            name (str): The user's name (used in chart title).
            dates (list): List of date strings (X-axis).
            bmi_values (list): List of BMI float values (Y-axis).
        """
        trend_window = tk.Toplevel(self.root)
        trend_window.title(f"BMI Trend - {name}")
        trend_window.geometry("800x550")
        trend_window.configure(bg=self.BG_COLOR)
        trend_window.transient(self.root)

        trend_window.columnconfigure(0, weight=1)
        trend_window.rowconfigure(0, weight=1)

        # Create matplotlib figure styled to match the dark theme
        figure = Figure(figsize=(7.5, 5), dpi=100)
        figure.patch.set_facecolor(self.BG_COLOR)

        axes = figure.add_subplot(111)
        axes.set_facecolor(self.CARD_COLOR)

        axes.plot(
            dates, bmi_values, marker="o", linestyle="-",
            color=self.PRIMARY_BTN, linewidth=2, markersize=6,
            markerfacecolor=self.SUCCESS_COLOR, markeredgecolor=self.TEXT_COLOR,
        )

        axes.set_title(f"BMI Trend for {name}", color=self.TEXT_COLOR, fontsize=14, pad=15)
        axes.set_xlabel("Date", color=self.TEXT_COLOR, fontsize=11)
        axes.set_ylabel("BMI", color=self.TEXT_COLOR, fontsize=11)

        axes.tick_params(axis="x", colors=self.TEXT_COLOR, rotation=45)
        axes.tick_params(axis="y", colors=self.TEXT_COLOR)

        for spine in axes.spines.values():
            spine.set_color(self.MUTED_TEXT)

        axes.grid(True, color="#44445A", linestyle="--", linewidth=0.5)
        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=trend_window)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        close_btn = self._create_button(
            trend_window, "Close", trend_window.destroy, self.DANGER_COLOR
        )
        close_btn.grid(row=1, column=0, pady=(0, 15), ipady=6)

    # ------------------------------------------------------------------
    # CLEAR FIELDS
    # ------------------------------------------------------------------
    def clear_fields_action(self):
        """Reset all input fields and result labels to their default state."""
        self.name_var.set("")
        self.weight_var.set("")
        self.height_var.set("")

        self.current_bmi = None
        self.current_category = None

        self.bmi_value_label.configure(text="--", fg=self.TEXT_COLOR)
        self.bmi_category_label.configure(text="--", fg=self.TEXT_COLOR)
        self.recommendation_label.configure(
            text="Enter your details and click 'Calculate BMI' to see your results."
        )

        self.name_entry.focus_set()

    # ------------------------------------------------------------------
    # EXIT APPLICATION
    # ------------------------------------------------------------------
    def exit_application(self):
        """Prompt for confirmation and close the application gracefully."""
        confirm = messagebox.askyesno(
            "Exit Application", "Are you sure you want to exit?"
        )
        if confirm:
            self.root.destroy()


def main():
    """Application entry point."""
    root = tk.Tk()
    app = BMICalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()