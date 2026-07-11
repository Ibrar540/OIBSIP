"""
bmi_calculator.py  —  Advanced BMI Calculator
OIBSIP Task 2

Layout
──────
┌─────────────┬──────────────────────────────────┐
│  Left panel │  Right: centred form + result     │
│  History    │                                   │
│  by user    │  Name / Weight / Height inputs     │
│             │  [Calculate BMI]                  │
│             │  ┌────────────────────────────┐   │
│             │  │ BMI · Category · Advice    │   │
│             │  └────────────────────────────┘   │
│  ─────────  │                                   │
│  👤  Exit   │                                   │
└─────────────┴──────────────────────────────────┘
"""

import os
import sqlite3

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from bmi_utils import calculate_bmi, get_bmi_category, get_health_advice, get_category_color
from database import (
    save_record, get_all_records, get_user_records,
    delete_record, delete_all_records, search_users,
)


class BMICalculatorApp:
    # ── Palette ────────────────────────────────────────────────────────
    BG          = "#1E1E2F"
    SIDEBAR     = "#16162A"
    CARD        = "#2A2A40"
    ACCENT      = "#4A90E2"
    SUCCESS     = "#2ECC71"
    WARNING     = "#F39C12"
    DANGER      = "#E74C3C"
    TEXT        = "#FFFFFF"
    MUTED       = "#B0B0C3"
    ENTRY_BG    = "#3A3A55"
    BORDER      = "#44445A"
    ROW_HOVER   = "#32324E"
    ROW_SEL     = "#4A90E2"

    # ── Fonts ──────────────────────────────────────────────────────────
    F_TITLE   = ("Segoe UI", 18, "bold")
    F_HEAD    = ("Segoe UI", 12, "bold")
    F_LABEL   = ("Segoe UI", 11)
    F_ENTRY   = ("Segoe UI", 11)
    F_BTN     = ("Segoe UI", 11, "bold")
    F_BIG     = ("Segoe UI", 36, "bold")
    F_CAT     = ("Segoe UI", 15, "bold")
    F_ADV     = ("Segoe UI", 11)
    F_SIDE    = ("Segoe UI", 10)
    F_SIDE_H  = ("Segoe UI", 10, "bold")

    # ── Sidebar width ──────────────────────────────────────────────────
    SIDE_W = 220

    def __init__(self, root: tk.Tk):
        self.root = root
        self.current_bmi      = None
        self.current_category = None
        self._history_rows: list[tk.Frame] = []

        self._configure_window()
        self._configure_styles()
        self._build_root_grid()
        self._build_sidebar()
        self._build_main()
        self._refresh_sidebar()
        self.name_entry.focus_set()

    # ──────────────────────────────────────────────────────────────────
    # Window / style setup
    # ──────────────────────────────────────────────────────────────────
    def _configure_window(self):
        self.root.title("Advanced BMI Calculator")
        self.root.geometry("1020x680")
        self.root.minsize(860, 580)
        self.root.configure(bg=self.BG)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)
        icon_path = os.path.join("assets", "app_icon.ico")
        try:
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except tk.TclError:
            pass

    def _configure_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview",
                    background=self.CARD, foreground=self.TEXT,
                    fieldbackground=self.CARD, rowheight=26,
                    font=self.F_SIDE, borderwidth=0)
        s.configure("Treeview.Heading",
                    background=self.ACCENT, foreground=self.TEXT,
                    font=self.F_SIDE_H, relief="flat")
        s.map("Treeview",
              background=[("selected", self.ROW_SEL)],
              foreground=[("selected", self.TEXT)])
        s.configure("Vertical.TScrollbar",
                    background=self.CARD, troughcolor=self.SIDEBAR,
                    arrowcolor=self.TEXT)

    # ──────────────────────────────────────────────────────────────────
    # Root grid: sidebar (col 0) | divider (col 1) | main (col 2)
    # ──────────────────────────────────────────────────────────────────
    def _build_root_grid(self):
        self.root.columnconfigure(0, minsize=self.SIDE_W, weight=0)
        self.root.columnconfigure(1, minsize=1, weight=0)
        self.root.columnconfigure(2, weight=1)
        self.root.rowconfigure(0, weight=1)

    # ──────────────────────────────────────────────────────────────────
    # LEFT SIDEBAR  — history list + profile/exit footer
    # ──────────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        # Outer sidebar frame
        self._sidebar = tk.Frame(self.root, bg=self.SIDEBAR, width=self.SIDE_W)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)
        self._sidebar.rowconfigure(2, weight=1)   # history list expands
        self._sidebar.columnconfigure(0, weight=1)

        # Title strip
        tk.Label(self._sidebar, text="BMI History",
                 font=self.F_HEAD, bg=self.SIDEBAR, fg=self.TEXT,
                 pady=14).grid(row=0, column=0, sticky="ew", padx=14)

        # Thin separator
        tk.Frame(self._sidebar, bg=self.BORDER, height=1).grid(
            row=1, column=0, sticky="ew")

        # Scrollable history list
        hist_canvas = tk.Canvas(self._sidebar, bg=self.SIDEBAR,
                                highlightthickness=0, bd=0)
        hist_scroll = ttk.Scrollbar(self._sidebar, orient="vertical",
                                    command=hist_canvas.yview)
        hist_canvas.configure(yscrollcommand=hist_scroll.set)
        hist_canvas.grid(row=2, column=0, sticky="nsew")
        hist_scroll.grid(row=2, column=1, sticky="ns")

        self._hist_inner = tk.Frame(hist_canvas, bg=self.SIDEBAR)
        self._hist_win   = hist_canvas.create_window(
            (0, 0), window=self._hist_inner, anchor="nw")

        def _cc(e):
            hist_canvas.configure(scrollregion=hist_canvas.bbox("all"))
        def _cw(e):
            hist_canvas.itemconfig(self._hist_win, width=e.width)

        self._hist_inner.bind("<Configure>", _cc)
        hist_canvas.bind("<Configure>", _cw)
        hist_canvas.bind_all("<MouseWheel>",
            lambda e: hist_canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        self._hist_canvas = hist_canvas

        # Bottom separator
        tk.Frame(self._sidebar, bg=self.BORDER, height=1).grid(
            row=3, column=0, columnspan=2, sticky="ew")

        # Profile / Exit footer
        footer = tk.Frame(self._sidebar, bg=self.SIDEBAR)
        footer.grid(row=4, column=0, columnspan=2, sticky="ew", padx=14, pady=12)
        footer.columnconfigure(1, weight=1)

        tk.Label(footer, text="👤", font=("Segoe UI", 18),
                 bg=self.SIDEBAR, fg=self.MUTED).grid(row=0, column=0, padx=(0, 8))

        tk.Label(footer, text="Profile", font=self.F_SIDE_H,
                 bg=self.SIDEBAR, fg=self.TEXT).grid(row=0, column=1, sticky="w")

        exit_btn = tk.Button(footer, text="Exit", font=self.F_SIDE,
                             bg=self.DANGER, fg=self.TEXT,
                             relief="flat", bd=0, cursor="hand2",
                             padx=10, pady=3, command=self._on_exit)
        exit_btn.grid(row=0, column=2)
        self._hover(exit_btn, self.DANGER)

    # ──────────────────────────────────────────────────────────────────
    # Sidebar: populate history rows
    # ──────────────────────────────────────────────────────────────────
    def _refresh_sidebar(self):
        """Rebuild the history list from the database."""
        for w in self._hist_inner.winfo_children():
            w.destroy()

        try:
            records = get_all_records()
        except Exception:
            records = []

        if not records:
            tk.Label(self._hist_inner,
                     text="No records yet.",
                     font=self.F_SIDE, bg=self.SIDEBAR, fg=self.MUTED,
                     pady=12).pack(padx=10)
            return

        # Group by user name (preserving insertion order)
        seen: dict[str, list] = {}
        for rec in records:
            nm = rec[1]
            seen.setdefault(nm, []).append(rec)

        for name, recs in seen.items():
            # Name header row
            hdr = tk.Frame(self._hist_inner, bg=self.SIDEBAR)
            hdr.pack(fill="x", padx=6, pady=(8, 2))
            tk.Label(hdr, text=f"👤  {name}",
                     font=self.F_SIDE_H, bg=self.SIDEBAR,
                     fg=self.ACCENT).pack(anchor="w", padx=4)

            # Individual records
            for rec in recs:
                # rec: (id, name, weight, height, bmi, category, date)
                bmi_val  = rec[4]
                cat      = rec[5]
                date_str = rec[6][:10]   # yyyy-mm-dd
                color    = get_category_color(cat)

                row = tk.Frame(self._hist_inner, bg=self.SIDEBAR, cursor="hand2")
                row.pack(fill="x", padx=6, pady=1)

                left = tk.Frame(row, bg=self.SIDEBAR)
                left.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=4)

                tk.Label(left, text=f"BMI {bmi_val}",
                         font=self.F_SIDE_H, bg=self.SIDEBAR,
                         fg=color).pack(anchor="w")
                tk.Label(left, text=f"{cat}  ·  {date_str}",
                         font=self.F_SIDE, bg=self.SIDEBAR,
                         fg=self.MUTED).pack(anchor="w")

                # Delete ✕ button
                rec_id = rec[0]
                del_btn = tk.Button(
                    row, text="✕", font=("Segoe UI", 8),
                    bg=self.SIDEBAR, fg=self.MUTED,
                    relief="flat", bd=0, cursor="hand2",
                    command=lambda rid=rec_id: self._delete_history_row(rid))
                del_btn.pack(side="right", padx=6)

                # Hover highlight
                def _enter(e, r=row, d=del_btn, *ws):
                    r.config(bg=self.ROW_HOVER)
                    d.config(bg=self.ROW_HOVER)
                    for w in r.winfo_children():
                        try:
                            w.config(bg=self.ROW_HOVER)
                            for ww in w.winfo_children():
                                ww.config(bg=self.ROW_HOVER)
                        except Exception:
                            pass

                def _leave(e, r=row, d=del_btn):
                    r.config(bg=self.SIDEBAR)
                    d.config(bg=self.SIDEBAR)
                    for w in r.winfo_children():
                        try:
                            w.config(bg=self.SIDEBAR)
                            for ww in w.winfo_children():
                                ww.config(bg=self.SIDEBAR)
                        except Exception:
                            pass

                row.bind("<Enter>", _enter)
                row.bind("<Leave>", _leave)

                # Click row → load that user's trend
                row.bind("<Button-1>",
                    lambda e, n=name: self._sidebar_row_click(n))

    def _delete_history_row(self, record_id):
        if not messagebox.askyesno("Delete", f"Delete record #{record_id}?",
                                   parent=self.root):
            return
        try:
            delete_record(record_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._refresh_sidebar()

    def _sidebar_row_click(self, name: str):
        """Fill the name field and show the BMI trend for that user."""
        self.name_var.set(name)
        self._show_trend_for(name)

    # ──────────────────────────────────────────────────────────────────
    # VERTICAL DIVIDER
    # ──────────────────────────────────────────────────────────────────
    # (the root grid column 1 is 1 px wide with BORDER color)
    # We just place a 1-px frame there.
    # ──────────────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────────────
    # MAIN RIGHT AREA
    # ──────────────────────────────────────────────────────────────────
    def _build_main(self):
        # Thin divider line
        tk.Frame(self.root, bg=self.BORDER, width=1).grid(
            row=0, column=1, sticky="ns")

        main = tk.Frame(self.root, bg=self.BG)
        main.grid(row=0, column=2, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        # Scrollable canvas so content never gets clipped vertically
        canvas = tk.Canvas(main, bg=self.BG, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(main, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        inner = tk.Frame(canvas, bg=self.BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(e):
            # Keep inner frame at least as wide as the canvas
            canvas.itemconfig(win_id, width=e.width)

        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))

        # Centre the form + result card horizontally inside inner
        inner.columnconfigure(0, weight=1)

        content = tk.Frame(inner, bg=self.BG)
        content.grid(row=0, column=0)   # no sticky → centred

        self._build_form(content)
        self._build_result_card(content)

    # ──────────────────────────────────────────────────────────────────
    # FORM  (Name / Weight / Height / Calculate button)
    # ──────────────────────────────────────────────────────────────────
    def _build_form(self, parent):
        form = tk.Frame(parent, bg=self.BG)
        form.pack(pady=(30, 18))

        # App title
        tk.Label(form, text="Advanced BMI Calculator",
                 font=self.F_TITLE, bg=self.BG, fg=self.TEXT
                 ).pack(pady=(0, 4))
        tk.Label(form,
                 text="Track, analyze and visualize your Body Mass Index over time",
                 font=self.F_LABEL, bg=self.BG, fg=self.MUTED
                 ).pack(pady=(0, 24))

        # Input block — fixed width, centred
        fields_frame = tk.Frame(form, bg=self.BG)
        fields_frame.pack()

        FIELD_W = 340   # px

        def _field(label_text, var):
            grp = tk.Frame(fields_frame, bg=self.BG)
            grp.pack(fill="x", pady=7)
            tk.Label(grp, text=label_text, font=self.F_LABEL,
                     bg=self.BG, fg=self.MUTED, anchor="w"
                     ).pack(fill="x")
            entry = tk.Entry(grp, textvariable=var,
                             font=self.F_ENTRY, width=38,
                             bg=self.ENTRY_BG, fg=self.TEXT,
                             insertbackground=self.TEXT,
                             relief="flat", highlightthickness=1,
                             highlightbackground=self.BORDER,
                             highlightcolor=self.ACCENT)
            entry.pack(fill="x", ipady=8)
            return entry

        self.name_var   = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()

        self.name_entry   = _field("Enter Name",              self.name_var)
        self.weight_entry = _field("Enter Weight (kg)",       self.weight_var)
        self.height_entry = _field("Enter Height (metres)",   self.height_var)

        # Calculate button
        calc_btn = tk.Button(
            fields_frame, text="Calculate BMI",
            font=self.F_BTN, bg=self.ACCENT, fg=self.TEXT,
            relief="flat", bd=0, cursor="hand2",
            padx=24, pady=10,
            command=self._calculate)
        calc_btn.pack(fill="x", pady=(16, 0))
        self._hover(calc_btn, self.ACCENT)

    # ──────────────────────────────────────────────────────────────────
    # RESULT CARD
    # ──────────────────────────────────────────────────────────────────
    def _build_result_card(self, parent):
        self._result_card = tk.Frame(parent, bg=self.CARD,
                                     padx=32, pady=24)
        self._result_card.pack(fill="x", padx=0, pady=(0, 30))
        self._result_card.columnconfigure(0, weight=1)

        # BMI number
        tk.Label(self._result_card, text="BMI", font=self.F_LABEL,
                 bg=self.CARD, fg=self.MUTED).grid(row=0, column=0, sticky="w")

        self.bmi_val_lbl = tk.Label(self._result_card, text="--",
                                    font=self.F_BIG, bg=self.CARD, fg=self.TEXT)
        self.bmi_val_lbl.grid(row=1, column=0, sticky="w", pady=(0, 10))

        # Thin separator
        tk.Frame(self._result_card, bg=self.BORDER, height=1).grid(
            row=2, column=0, sticky="ew", pady=(0, 10))

        # Category
        tk.Label(self._result_card, text="Category", font=self.F_LABEL,
                 bg=self.CARD, fg=self.MUTED).grid(row=3, column=0, sticky="w")

        self.cat_lbl = tk.Label(self._result_card, text="--",
                                font=self.F_CAT, bg=self.CARD, fg=self.TEXT)
        self.cat_lbl.grid(row=4, column=0, sticky="w", pady=(2, 10))

        # Thin separator
        tk.Frame(self._result_card, bg=self.BORDER, height=1).grid(
            row=5, column=0, sticky="ew", pady=(0, 10))

        # Advice
        tk.Label(self._result_card, text="Health Advice", font=self.F_LABEL,
                 bg=self.CARD, fg=self.MUTED).grid(row=6, column=0, sticky="w")

        self.advice_lbl = tk.Label(
            self._result_card,
            text="Enter your details above and click Calculate BMI.",
            font=self.F_ADV, bg=self.CARD, fg=self.TEXT,
            wraplength=360, justify="left")
        self.advice_lbl.grid(row=7, column=0, sticky="w", pady=(2, 14))

        # Action row: Save + Trend
        action_row = tk.Frame(self._result_card, bg=self.CARD)
        action_row.grid(row=8, column=0, sticky="w", pady=(4, 0))

        self._save_btn = tk.Button(
            action_row, text="💾  Save Record",
            font=self.F_BTN, bg=self.SUCCESS, fg=self.TEXT,
            relief="flat", bd=0, cursor="hand2",
            padx=16, pady=7, command=self._save)
        self._save_btn.pack(side="left", padx=(0, 10))
        self._hover(self._save_btn, self.SUCCESS)

        self._trend_btn = tk.Button(
            action_row, text="📈  BMI Trend",
            font=self.F_BTN, bg=self.ACCENT, fg=self.TEXT,
            relief="flat", bd=0, cursor="hand2",
            padx=16, pady=7,
            command=lambda: self._show_trend_for(self.name_var.get().strip()))
        self._trend_btn.pack(side="left")
        self._hover(self._trend_btn, self.ACCENT)

        self._clear_btn = tk.Button(
            action_row, text="✕  Clear",
            font=self.F_BTN, bg=self.BORDER, fg=self.TEXT,
            relief="flat", bd=0, cursor="hand2",
            padx=16, pady=7, command=self._clear)
        self._clear_btn.pack(side="left", padx=(10, 0))
        self._hover(self._clear_btn, self.BORDER)

    # ──────────────────────────────────────────────────────────────────
    # ACTIONS
    # ──────────────────────────────────────────────────────────────────
    def _validate(self):
        name       = self.name_var.get().strip()
        weight_str = self.weight_var.get().strip()
        height_str = self.height_var.get().strip()

        if not name:
            messagebox.showwarning("Missing", "Please enter a name.", parent=self.root)
            return None
        if not weight_str or not height_str:
            messagebox.showwarning("Missing",
                "Please enter both weight and height.", parent=self.root)
            return None
        try:
            weight = float(weight_str)
            height = float(height_str)
        except ValueError:
            messagebox.showerror("Invalid",
                "Weight and height must be numeric values.", parent=self.root)
            return None
        if weight <= 0 or height <= 0:
            messagebox.showerror("Invalid",
                "Weight and height must be greater than zero.", parent=self.root)
            return None
        if weight > 500 or height > 3:
            messagebox.showerror("Invalid",
                "Enter realistic values (weight ≤ 500 kg, height ≤ 3 m).",
                parent=self.root)
            return None
        return name, weight, height

    def _calculate(self):
        validated = self._validate()
        if validated is None:
            return
        _, weight, height = validated
        try:
            bmi      = calculate_bmi(weight, height)
            category = get_bmi_category(bmi)
            advice   = get_health_advice(category)
            color    = get_category_color(category)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.root)
            return

        self.current_bmi      = round(bmi, 2)
        self.current_category = category

        self.bmi_val_lbl.configure(text=str(self.current_bmi), fg=color)
        self.cat_lbl.configure(text=category, fg=color)
        self.advice_lbl.configure(text=advice)

    def _save(self):
        if self.current_bmi is None:
            messagebox.showwarning("No Result",
                "Please calculate your BMI first.", parent=self.root)
            return
        validated = self._validate()
        if validated is None:
            return
        name, weight, height = validated
        try:
            save_record(name, weight, height, self.current_bmi, self.current_category)
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self.root)
            return
        messagebox.showinfo("Saved", "Record saved successfully!", parent=self.root)
        self._refresh_sidebar()

    def _clear(self):
        self.name_var.set("")
        self.weight_var.set("")
        self.height_var.set("")
        self.current_bmi      = None
        self.current_category = None
        self.bmi_val_lbl.configure(text="--",  fg=self.TEXT)
        self.cat_lbl.configure(text="--",      fg=self.TEXT)
        self.advice_lbl.configure(
            text="Enter your details above and click Calculate BMI.")
        self.name_entry.focus_set()

    def _on_exit(self):
        if messagebox.askyesno("Exit", "Exit the application?", parent=self.root):
            self.root.destroy()

    # ──────────────────────────────────────────────────────────────────
    # BMI TREND CHART
    # ──────────────────────────────────────────────────────────────────
    def _show_trend_for(self, name: str):
        if not name:
            messagebox.showwarning("Missing",
                "Please enter or select a name.", parent=self.root)
            return
        try:
            records = get_user_records(name)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.root)
            return
        if not records:
            messagebox.showinfo("No Data",
                f"No BMI history found for '{name}'.", parent=self.root)
            return

        dates  = [r[6][:10] for r in records]
        values = [r[4]      for r in records]

        win = tk.Toplevel(self.root)
        win.title(f"BMI Trend — {name}")
        win.geometry("760x480")
        win.configure(bg=self.BG)
        win.transient(self.root)
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)

        fig = Figure(figsize=(7, 4.2), dpi=100)
        fig.patch.set_facecolor(self.BG)
        ax  = fig.add_subplot(111)
        ax.set_facecolor(self.CARD)

        ax.plot(dates, values, marker="o", linestyle="-",
                color=self.ACCENT, linewidth=2, markersize=7,
                markerfacecolor=self.SUCCESS, markeredgecolor=self.TEXT)

        ax.set_title(f"BMI Trend for {name}",
                     color=self.TEXT, fontsize=13, pad=12)
        ax.set_xlabel("Date", color=self.TEXT, fontsize=10)
        ax.set_ylabel("BMI",  color=self.TEXT, fontsize=10)
        ax.tick_params(axis="x", colors=self.TEXT, rotation=40)
        ax.tick_params(axis="y", colors=self.TEXT)
        for spine in ax.spines.values():
            spine.set_color(self.BORDER)
        ax.grid(True, color=self.BORDER, linestyle="--", linewidth=0.5)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew",
                                    padx=16, pady=16)

        tk.Button(win, text="Close", font=self.F_BTN,
                  bg=self.DANGER, fg=self.TEXT,
                  relief="flat", bd=0, cursor="hand2",
                  padx=20, pady=7,
                  command=win.destroy
                  ).grid(row=1, column=0, pady=(0, 14))

    # ──────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────
    def _hover(self, btn: tk.Button, base_color: str, factor: float = 0.15):
        """Attach a simple lighten-on-hover effect to a button."""
        def _lighten(c, f):
            c = c.lstrip("#")
            r, g, b = (int(c[i:i+2], 16) for i in (0, 2, 4))
            r = min(255, int(r + (255 - r) * f))
            g = min(255, int(g + (255 - g) * f))
            b = min(255, int(b + (255 - b) * f))
            return f"#{r:02x}{g:02x}{b:02x}"

        light = _lighten(base_color, factor)
        btn.bind("<Enter>", lambda e: btn.configure(bg=light))
        btn.bind("<Leave>", lambda e: btn.configure(bg=base_color))


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    BMICalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
