"""
====================================================================
Project Name : Advanced Random Password Generator
Author       : Ibrar Ahmad
Internship   : Oasis Infobyte - Python Programming Internship
Description  : A professional, secure, and feature-rich desktop
                password generator built with Tkinter/ttk. The
                application allows users to generate cryptographically
                secure random passwords with full control over length
                and character composition, view real-time password
                strength/entropy analysis, copy passwords to the
                clipboard, and review recent password history.


====================================================================
"""

import math
import string
import secrets
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

try:
    import pyperclip
except ImportError:  
    pyperclip = None


class PasswordGeneratorApp:
    """
    Main application class for the Advanced Random Password Generator.

    Encapsulates the entire GUI, application state, and business
    logic required to generate, evaluate, display, and manage
    cryptographically secure passwords.
    """

    # ======================================
    # Class-Level Constants (Colors & Fonts)
    # ======================================
    COLOR_BG = "#0f1729"            # Main window background
    COLOR_PANEL = "#16213e"         # Panel / labelframe background
    COLOR_PANEL_LIGHT = "#1e2d4d"   # Slightly lighter panel accents
    COLOR_ACCENT = "#3b82f6"        # Primary blue accent
    COLOR_ACCENT_DARK = "#2563eb"   # Darker blue for hover/active
    COLOR_TEXT = "#f1f5f9"          # Primary white/light text
    COLOR_TEXT_MUTED = "#94a3b8"    # Secondary muted text
    COLOR_GREEN = "#22c55e"         # Success / strong indicator
    COLOR_RED = "#ef4444"           # Warning / weak indicator
    COLOR_ORANGE = "#f59e0b"        # Medium strength indicator
    COLOR_YELLOW = "#eab308"        # Fair strength indicator

    FONT_FAMILY = "Segoe UI"

    # Characters considered visually ambiguous / confusing
    AMBIGUOUS_CHARS = "O0Il1"

    def __init__(self, root):
        """
        Initialize the application, its state variables, and build
        the complete user interface.

        Args:
            root (tk.Tk): The root Tkinter window instance.
        """
        self.root = root
        self.root.title("Advanced Random Password Generator | Oasis Infobyte")
        self.root.geometry("700x700")
        self.root.resizable(True, True)
        self.root.configure(bg=self.COLOR_BG)

        # Character pools used for password generation
        self.CHAR_UPPER = string.ascii_uppercase
        self.CHAR_LOWER = string.ascii_lowercase
        self.CHAR_DIGITS = string.digits
        self.CHAR_SYMBOLS = "!@#$%^&*()_-+=<>?/[]{}~"

        # In-memory password history (most recent first, max length 5)
        self.password_history = []

        self._configure_styles()
        self._create_variables()
        self._build_ui()

    # ======================================
    # Style Configuration
    # ======================================
    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # General frames
        style.configure("Dark.TFrame", background=self.COLOR_BG)
        style.configure("Panel.TFrame", background=self.COLOR_PANEL)

        # Label styles
        style.configure(
            "Title.TLabel",
            background=self.COLOR_BG,
            foreground=self.COLOR_TEXT,
            font=(self.FONT_FAMILY, 20, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.COLOR_BG,
            foreground=self.COLOR_TEXT_MUTED,
            font=(self.FONT_FAMILY, 10),
        )
        style.configure(
            "Section.TLabel",
            background=self.COLOR_PANEL,
            foreground=self.COLOR_ACCENT,
            font=(self.FONT_FAMILY, 11, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background=self.COLOR_PANEL,
            foreground=self.COLOR_TEXT,
            font=(self.FONT_FAMILY, 10),
        )
        style.configure(
            "Stat.TLabel",
            background=self.COLOR_PANEL,
            foreground=self.COLOR_TEXT,
            font=(self.FONT_FAMILY, 10, "bold"),
        )
        style.configure(
            "Strength.TLabel",
            background=self.COLOR_BG,
            foreground=self.COLOR_TEXT,
            font=(self.FONT_FAMILY, 12, "bold"),
        )

        # Labelframe (section containers)
        style.configure(
            "Panel.TLabelframe",
            background=self.COLOR_PANEL,
            bordercolor=self.COLOR_ACCENT,
            relief="groove",
        )
        style.configure(
            "Panel.TLabelframe.Label",
            background=self.COLOR_PANEL,
            foreground=self.COLOR_ACCENT,
            font=(self.FONT_FAMILY, 11, "bold"),
        )

        # Checkbuttons
        style.configure(
            "Panel.TCheckbutton",
            background=self.COLOR_PANEL,
            foreground=self.COLOR_TEXT,
            font=(self.FONT_FAMILY, 10),
        )
        style.map(
            "Panel.TCheckbutton",
            background=[("active", self.COLOR_PANEL)],
            foreground=[("active", self.COLOR_ACCENT)],
        )

        # Buttons
        style.configure(
            "Accent.TButton",
            background=self.COLOR_ACCENT,
            foreground="#ffffff",
            font=(self.FONT_FAMILY, 12, "bold"),
            padding=10,
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.COLOR_ACCENT_DARK)],
        )

        style.configure(
            "Copy.TButton",
            background=self.COLOR_GREEN,
            foreground="#ffffff",
            font=(self.FONT_FAMILY, 12, "bold"),
            padding=10,
            borderwidth=0,
        )
        style.map(
            "Copy.TButton",
            background=[("active", "#16a34a")],
        )

        # Combobox
        style.configure(
            "TCombobox",
            fieldbackground=self.COLOR_PANEL_LIGHT,
            background=self.COLOR_PANEL_LIGHT,
            foreground=self.COLOR_TEXT,
            arrowcolor=self.COLOR_TEXT,
            padding=(6, 4),
        )
        style.configure(
            "Professional.TCombobox",
            fieldbackground="#ffffff",
            background="#ffffff",
            foreground="#000000",
            arrowcolor=self.COLOR_ACCENT,
            padding=(8, 6),
        )

        # Progress bar
        style.configure(
            "Weak.Horizontal.TProgressbar",
            troughcolor=self.COLOR_PANEL_LIGHT,
            background=self.COLOR_RED,
        )
        style.configure(
            "Medium.Horizontal.TProgressbar",
            troughcolor=self.COLOR_PANEL_LIGHT,
            background=self.COLOR_ORANGE,
        )
        style.configure(
            "Strong.Horizontal.TProgressbar",
            troughcolor=self.COLOR_PANEL_LIGHT,
            background=self.COLOR_YELLOW,
        )
        style.configure(
            "VeryStrong.Horizontal.TProgressbar",
            troughcolor=self.COLOR_PANEL_LIGHT,
            background=self.COLOR_GREEN,
        )

        # Treeview (password history table)
        style.configure(
            "Dark.Treeview",
            background=self.COLOR_PANEL_LIGHT,
            fieldbackground=self.COLOR_PANEL_LIGHT,
            foreground=self.COLOR_TEXT,
            rowheight=26,
            font=(self.FONT_FAMILY, 9),
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=self.COLOR_ACCENT,
            foreground="#ffffff",
            font=(self.FONT_FAMILY, 9, "bold"),
        )
        style.map(
            "Dark.Treeview",
            background=[("selected", self.COLOR_ACCENT_DARK)],
        )

    # ======================================
    # Tkinter Variables
    # ======================================
    def _create_variables(self):
        """Create and initialize all Tkinter control variables."""
        self.length_var = tk.StringVar(value="12")

        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)

        self.password_var = tk.StringVar(value="")

        self.strength_text_var = tk.StringVar(value="Strength: -")
        self.progress_var = tk.DoubleVar(value=0)

        self.stat_length_var = tk.StringVar(value="0")
        self.stat_upper_var = tk.StringVar(value="0")
        self.stat_lower_var = tk.StringVar(value="0")
        self.stat_digits_var = tk.StringVar(value="0")
        self.stat_symbols_var = tk.StringVar(value="0")
        self.stat_entropy_var = tk.StringVar(value="0.0 bits")

    # ======================================
    # UI Construction
    # ======================================
    def _bind_mousewheel(self, widget, canvas):
        """Recursively bind mousewheel events to a widget and all its children."""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        widget.bind("<MouseWheel>", _on_mousewheel, add=True)
        for child in widget.winfo_children():
            self._bind_mousewheel(child, canvas)

    def _build_ui(self):
        """Build and lay out every visual section of the application with scrollbar support."""
        # Create a canvas with scrollbar for vertical scrolling
        canvas = tk.Canvas(self.root, bg=self.COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        
        scrollable_frame = ttk.Frame(canvas, style="Dark.TFrame")
        
        def on_frame_configure(event):
            """Update scroll region when frame is configured."""
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="scrollable")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mousewheel scrolling on canvas
        def _on_canvas_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_canvas_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_canvas_mousewheel)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Build UI inside scrollable frame
        container = ttk.Frame(scrollable_frame, style="Dark.TFrame", padding=20)
        container.pack(fill="x")

        self._build_header(container)
        self._build_options_section(container)
        self._build_action_section(container)
        self._build_password_display(container)
        self._build_strength_section(container)
        self._build_statistics_section(container)
        self._build_history_section(container)
        
        # Add bottom padding frame
        bottom_spacer = ttk.Frame(scrollable_frame, style="Dark.TFrame", height=50)
        bottom_spacer.pack(fill="x", pady=(20, 0))
        
        # Bind mousewheel to all child widgets
        def bind_all_widgets():
            self._bind_mousewheel(container, canvas)
        
        # Update scroll region after all content is added
        def update_scroll():
            self.root.update_idletasks()
            # Get the full bounding box
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
            # Set canvas width to match scrollable frame
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:
                canvas.itemconfig(canvas_window, width=canvas_width)
            # Bind mousewheel to all widgets
            bind_all_widgets()
        
        self.root.after(400, update_scroll)
    #==============================
    #          Header
    #=============================
    def _build_header(self, parent):
        """Build the title/header section of the application."""
        header = ttk.Frame(parent, style="Dark.TFrame")
        header.pack(fill="x", pady=(0, 15))

        title = ttk.Label(
            header, text=" Advanced Password Generator", style="Title.TLabel"
        )
        title.pack(anchor="center")

        subtitle = ttk.Label(
            header,
            text="Oasis Infobyte Internship Project  •  Secure Password Utility",
            style="Subtitle.TLabel",
        )
        subtitle.pack(anchor="center", pady=(2, 0))

    def _build_custom_checkbutton(self, parent, text, variable, row, col):
        """Create a custom checkbutton with a green selected state."""
        def update_checkbox_color():
            """Update checkbox background color based on state."""
            if variable.get():
                checkbutton.config(bg=self.COLOR_GREEN)
            else:
                checkbutton.config(bg="#ffffff")
        
        checkbutton = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            font=(self.FONT_FAMILY, 11),
            bg=self.COLOR_GREEN,
            fg="#000000",
            activebackground=self.COLOR_GREEN,
            activeforeground="#000000",
            selectcolor="#ffffff",
            highlightthickness=1,
            highlightbackground="#e0e0e0",
            highlightcolor=self.COLOR_ACCENT,
            bd=1,
            relief="solid",
            padx=8,
            pady=6,
            anchor="w",
            command=update_checkbox_color,
        )
        checkbutton.grid(row=row, column=col, sticky="w", padx=10, pady=6)
        # Set initial color based on variable state
        update_checkbox_color()
        return checkbutton
    #==============================
    #            Options 
    #=============================
    def _build_options_section(self, parent):
        """Build the password length, character type, and exclusion options."""
        options_frame = ttk.Frame(parent, style="Dark.TFrame")
        options_frame.pack(fill="x", pady=(0, 12))

        # Password Length 
        length_panel = ttk.Frame(options_frame, style="Panel.TFrame", padding=12)
        length_panel.pack(fill="x", pady=(0, 10))

        ttk.Label(length_panel, text="Password Length", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )

        length_container = tk.Frame(
            length_panel,
            bg="#ffffff",
            highlightthickness=0,
            bd=1,
            relief="sunken",
            padx=4,
            pady=4,
        )
        length_container.grid(row=0, column=1, sticky="w")

        length_values = [str(n) for n in range(8, 21)]
        self.length_combo = ttk.Combobox(
            length_container,
            textvariable=self.length_var,
            values=length_values,
            state="readonly",
            width=6,
            font=(self.FONT_FAMILY, 10),
            style="Professional.TCombobox",
        )
        self.length_combo.pack(fill="x")
        # Set scroll position to top by making first item current
        self.length_combo.current(0)
        #============================
        # Character Types 
        #============================
        char_panel = ttk.Labelframe(
            options_frame, text="Character Types", style="Panel.TLabelframe", padding=12
        )
        char_panel.pack(fill="x", pady=(0, 10))

        self._build_custom_checkbutton(
            char_panel,
            "Uppercase Letters (A-Z)",
            self.upper_var,
            0,
            0,
        )
        self._build_custom_checkbutton(
            char_panel,
            "Lowercase Letters (a-z)",
            self.lower_var,
            0,
            1,
        )
        self._build_custom_checkbutton(
            char_panel,
            "Numbers (0-9)",
            self.digits_var,
            1,
            0,
        )
        self._build_custom_checkbutton(
            char_panel,
            "Symbols (!@#$%...)",
            self.symbols_var,
            1,
            1,
        )
        #============================
        # Exclude Ambiguous 
        #============================
        exclude_panel = ttk.Frame(options_frame, style="Panel.TFrame", padding=12)
        exclude_panel.pack(fill="x")

        self._build_custom_checkbutton(
            exclude_panel,
            "Exclude Ambiguous Characters  (O, 0, I, l, 1)",
            self.exclude_ambiguous_var,
            0,
            0,
        )
     #============================================
    #           Action Buttons 
    #============================================
    def _build_action_section(self, parent):
        """Build the Generate/Copy button area with toggle logic."""
        self.action_frame = ttk.Frame(parent, style="Dark.TFrame")
        self.action_frame.pack(fill="x", pady=(0, 12))

        self.generate_btn = ttk.Button(
            self.action_frame,
            text="Generate Password",
            style="Accent.TButton",
            command=self.generate_password,
        )
        self.copy_btn = ttk.Button(
            self.action_frame,
            text="Copy Password",
            style="Copy.TButton",
            command=self.copy_password,
        )

        # Only the Generate button is visible at start.
        self.generate_btn.pack(fill="x", ipady=4)
    #=============================================
    #  Password Display     
    #=============================================
    def _build_password_display(self, parent):
        """Build the readonly password display field."""
        display_panel = ttk.Frame(parent, style="Panel.TFrame", padding=12)
        display_panel.pack(fill="x", pady=(0, 12))

        self.password_entry = tk.Entry(
            display_panel,
            textvariable=self.password_var,
            font=(self.FONT_FAMILY, 16, "bold"),
            justify="center",
            state="readonly",
            readonlybackground=self.COLOR_PANEL_LIGHT,
            fg=self.COLOR_GREEN,
            relief="flat",
            insertbackground=self.COLOR_TEXT,
        )
        self.password_entry.pack(fill="x", ipady=8)
     #=============================
    #   Strength 
    #=============================
    def _build_strength_section(self, parent):
        """Build the password strength meter and label."""
        strength_frame = ttk.Frame(parent, style="Dark.TFrame")
        strength_frame.pack(fill="x", pady=(0, 12))

        self.strength_label = ttk.Label(
            strength_frame, textvariable=self.strength_text_var, style="Strength.TLabel"
        )
        self.strength_label.pack(anchor="w", pady=(0, 5))

        self.strength_bar = ttk.Progressbar(
            strength_frame,
            variable=self.progress_var,
            maximum=100,
            style="Weak.Horizontal.TProgressbar",
        )
        self.strength_bar.pack(fill="x", ipady=3)

    #=============================
    #   Statistics 
    #=============================
    def _build_statistics_section(self, parent):
        """Build the password statistics panel (counts and entropy)."""
        stats_panel = ttk.Labelframe(
            parent, text="Password Statistics", style="Panel.TLabelframe", padding=12
        )
        stats_panel.pack(fill="x", pady=(0, 12))

        labels_and_vars = [
            ("Length:", self.stat_length_var),
            ("Uppercase Count:", self.stat_upper_var),
            ("Lowercase Count:", self.stat_lower_var),
            ("Numbers Count:", self.stat_digits_var),
            ("Symbols Count:", self.stat_symbols_var),
            ("Entropy:", self.stat_entropy_var),
        ]

        for index, (label_text, var) in enumerate(labels_and_vars):
            row, col = divmod(index, 2)
            cell = ttk.Frame(stats_panel, style="Panel.TFrame")
            cell.grid(row=row, column=col, sticky="w", padx=15, pady=4)
            ttk.Label(cell, text=label_text, style="Body.TLabel").pack(side="left")
            ttk.Label(cell, textvariable=var, style="Stat.TLabel").pack(
                side="left", padx=(6, 0)
            )

    #=============================
    #   History 
    #=============================
    def _build_history_section(self, parent):
        """Build the password history Treeview table (last 5 passwords)."""
        history_panel = ttk.Labelframe(
            parent, text="Password History (Last 5)", style="Panel.TLabelframe", padding=12
        )
        history_panel.pack(fill="both", expand=True)

        columns = ("time", "length", "strength", "password")
        self.history_tree = ttk.Treeview(
            history_panel,
            columns=columns,
            show="headings",
            height=5,
            style="Dark.Treeview",
        )
        self.history_tree.heading("time", text="Time")
        self.history_tree.heading("length", text="Length")
        self.history_tree.heading("strength", text="Strength")
        self.history_tree.heading("password", text="Password")

        self.history_tree.column("time", width=90, anchor="center")
        self.history_tree.column("length", width=60, anchor="center")
        self.history_tree.column("strength", width=100, anchor="center")
        self.history_tree.column("password", width=280, anchor="center")

        self.history_tree.pack(fill="both", expand=True)

    # ======================================
    # Character Pool Helpers
    # ======================================
    def _get_selected_pools(self):
        """
        Build the dictionary of character pools for every currently
        selected category, applying the ambiguous-character exclusion
        filter where requested.

        Returns:
            dict: Mapping of category name -> filtered character pool
                  string, for every category currently selected.
        """
        exclude = self.exclude_ambiguous_var.get()
        pools = {}

        def _filtered(pool):
            if exclude:
                return "".join(ch for ch in pool if ch not in self.AMBIGUOUS_CHARS)
            return pool

        if self.upper_var.get():
            pools["upper"] = _filtered(self.CHAR_UPPER)
        if self.lower_var.get():
            pools["lower"] = _filtered(self.CHAR_LOWER)
        if self.digits_var.get():
            pools["digits"] = _filtered(self.CHAR_DIGITS)
        if self.symbols_var.get():
            # Symbols are never affected by ambiguous-character exclusion.
            pools["symbols"] = self.CHAR_SYMBOLS

        return pools

    # ======================================
    # Validation
    # ======================================
    def validate_inputs(self):
        """
        Validate the current user selections before generating a
        password, showing a professional error dialog on failure.

        Returns:
            bool: True if all inputs are valid, False otherwise.
        """
        try:
            length = int(self.length_var.get())
        except (TypeError, ValueError):
            messagebox.showerror("Validation Error", "Please select a valid password length.")
            return False

        if length < 8 or length > 20:
            messagebox.showerror(
                "Validation Error", "Password length must be at least 8 and at most 20."
            )
            return False

        selected_count = sum(
            [
                self.upper_var.get(),
                self.lower_var.get(),
                self.digits_var.get(),
                self.symbols_var.get(),
            ]
        )
        if selected_count < 2:
            messagebox.showerror(
                "Validation Error", "Select at least two character types."
            )
            return False

        pools = self._get_selected_pools()
        if any(len(pool) == 0 for pool in pools.values()):
            messagebox.showerror(
                "Validation Error",
                "Cannot generate password. One or more selected character "
                "types has no available characters after exclusions.",
            )
            return False

        return True

    # ======================================
    # Password Generation
    # ======================================
    def generate_password(self):
        """
        Generate a new cryptographically secure password based on the
        current user selections, then refresh the display, strength
        meter, statistics, and history sections accordingly.
        """
        if not self.validate_inputs():
            return

        length = int(self.length_var.get())
        pools = self._get_selected_pools()
        rng = secrets.SystemRandom()

        try:
            # Guarantee at least one character from every selected category.
            guaranteed_chars = [rng.choice(pool) for pool in pools.values()]

            combined_pool = "".join(pools.values())
            remaining_length = length - len(guaranteed_chars)

            if remaining_length < 0:
                messagebox.showerror(
                    "Validation Error",
                    "Cannot generate password. Selected length is too short "
                    "for the number of required character types.",
                )
                return

            filler_chars = [rng.choice(combined_pool) for _ in range(remaining_length)]

            all_chars = guaranteed_chars + filler_chars
            rng.shuffle(all_chars)  # Secure in-place shuffle
            password = "".join(all_chars)

        except (IndexError, ValueError):
            messagebox.showerror("Generation Error", "Cannot generate password.")
            return

        self.password_var.set(password)
        self.update_strength(password)
        self.update_statistics(password)
        self.update_history(password)

        # Toggle buttons: hide Generate, show Copy.
        self.generate_btn.pack_forget()
        self.copy_btn.pack(fill="x", ipady=4)

    # ======================================
    # Strength Calculation
    # ======================================
    def calculate_strength(self, password):
        """
        Calculate a 0-100 strength score and a descriptive label for
        the given password, based on its length and character variety.

        Args:
            password (str): The password to evaluate.

        Returns:
            tuple[int, str]: A (score, label) pair, where label is one
                              of "Weak", "Medium", "Strong", or
                              "Very Strong".
        """
        length = len(password)

        variety = 0
        if any(c.isupper() for c in password):
            variety += 1
        if any(c.islower() for c in password):
            variety += 1
        if any(c.isdigit() for c in password):
            variety += 1
        if any(c in self.CHAR_SYMBOLS for c in password):
            variety += 1

        length_score = min(length, 20) / 20 * 50
        variety_score = variety / 4 * 50
        score = round(length_score + variety_score)

        if score < 40:
            label = "Weak"
        elif score < 60:
            label = "Medium"
        elif score < 80:
            label = "Strong"
        else:
            label = "Very Strong"

        return score, label

    # ======================================
    # Entropy Calculation
    # ======================================
    def calculate_entropy(self, password):
        """
        Calculate the Shannon entropy (in bits) of the given password
        based on the size of the character pool it was drawn from.

        Args:
            password (str): The password to evaluate.

        Returns:
            float: The estimated entropy in bits.
        """
        pool_size = 0
        if any(c.isupper() for c in password):
            pool_size += len(self.CHAR_UPPER)
        if any(c.islower() for c in password):
            pool_size += len(self.CHAR_LOWER)
        if any(c.isdigit() for c in password):
            pool_size += len(self.CHAR_DIGITS)
        if any(c in self.CHAR_SYMBOLS for c in password):
            pool_size += len(self.CHAR_SYMBOLS)

        if pool_size == 0:
            return 0.0

        entropy = len(password) * math.log2(pool_size)
        return round(entropy, 2)

    # ======================================
    # Clipboard Copy
    # ======================================
    def copy_password(self):
        """
        Copy the currently displayed password to the system clipboard
        using pyperclip, notify the user, and reset the action buttons
        back to their initial state.
        """
        password = self.password_var.get()
        if not password:
            messagebox.showerror("Error", "There is no password to copy.")
            return

        if pyperclip is not None:
            try:
                pyperclip.copy(password)
            except Exception:
                messagebox.showerror(
                    "Clipboard Error", "Could not access the system clipboard."
                )
                return
        else:
            messagebox.showerror(
                "Missing Dependency", "pyperclip is not installed."
            )
            return

        messagebox.showinfo("Success", "Password copied successfully.")

        # Toggle buttons: hide Copy, show Generate again.
        self.copy_btn.pack_forget()
        self.generate_btn.pack(fill="x", ipady=4)

    # ======================================
    # Strength Display Update
    # ======================================
    def update_strength(self, password):
        """
        Update the strength label and progress bar to reflect the
        strength of the given password.

        Args:
            password (str): The most recently generated password.
        """
        score, label = self.calculate_strength(password)

        self.strength_text_var.set(f"Strength: {label}")
        self.progress_var.set(score)

        style_map = {
            "Weak": "Weak.Horizontal.TProgressbar",
            "Medium": "Medium.Horizontal.TProgressbar",
            "Strong": "Strong.Horizontal.TProgressbar",
            "Very Strong": "VeryStrong.Horizontal.TProgressbar",
        }
        color_map = {
            "Weak": self.COLOR_RED,
            "Medium": self.COLOR_ORANGE,
            "Strong": self.COLOR_YELLOW,
            "Very Strong": self.COLOR_GREEN,
        }

        self.strength_bar.configure(style=style_map[label])
        self.strength_label.configure(foreground=color_map[label])

    # ======================================
    # Statistics Display Update
    # ======================================
    def update_statistics(self, password):
        """
        Update the statistics panel with counts of each character
        category and the entropy of the given password.

        Args:
            password (str): The most recently generated password.
        """
        upper_count = sum(1 for c in password if c.isupper())
        lower_count = sum(1 for c in password if c.islower())
        digit_count = sum(1 for c in password if c.isdigit())
        symbol_count = sum(1 for c in password if c in self.CHAR_SYMBOLS)
        entropy = self.calculate_entropy(password)

        self.stat_length_var.set(str(len(password)))
        self.stat_upper_var.set(str(upper_count))
        self.stat_lower_var.set(str(lower_count))
        self.stat_digits_var.set(str(digit_count))
        self.stat_symbols_var.set(str(symbol_count))
        self.stat_entropy_var.set(f"{entropy} bits")

    # ======================================
    # History Display Update
    # ======================================
    def update_history(self, password):
        """
        Insert the newly generated password into the history list
        (newest first), limit the history to the last 5 entries, and
        refresh the Treeview to reflect the updated history.

        Args:
            password (str): The most recently generated password.
        """
        _, label = self.calculate_strength(password)
        timestamp = datetime.now().strftime("%H:%M:%S")

        record = {
            "time": timestamp,
            "length": len(password),
            "strength": label,
            "password": password,
        }

        self.password_history.insert(0, record)
        self.password_history = self.password_history[:5]

        # Refresh the Treeview: clear and re-populate, newest on top.
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        for entry in self.password_history:
            self.history_tree.insert(
                "",
                "end",
                values=(entry["time"], entry["length"], entry["strength"], entry["password"]),
            )


# ======================================
# Application Entry Point
# ======================================
if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()