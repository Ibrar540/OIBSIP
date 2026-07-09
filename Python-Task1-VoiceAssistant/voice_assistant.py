import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import datetime
import json
import os
import traceback
import uuid

import config
from commands import CommandProcessor
from utils import speak, listen, initialize_engine, log_message

# ─────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────
C = {
    "sidebar":       "#171717",   # left panel bg
    "sidebar_hover": "#2a2a2a",   # session row hover
    "sidebar_sel":   "#343541",   # selected session
    "main_bg":       "#212121",   # chat area bg
    "input_bg":      "#2f2f2f",   # input bar bg
    "input_border":  "#404040",   # input border (idle)
    "input_focus":   "#6b6b6b",   # input border (focused)
    "user_bubble":   "#2f2f2f",   # user message card
    "nova_bubble":   "#171717",   # assistant message card
    "accent":        "#19c37d",   # green accent (mic active, send btn)
    "accent_hover":  "#1aab6d",
    "btn_hover":     "#404040",
    "text":          "#ececec",
    "text_dim":      "#8e8ea0",
    "text_muted":    "#6e6e80",
    "error":         "#ff4d4d",
    "border":        "#2e2e2e",
    "new_chat_bg":   "#2f2f2f",
    "dot_menu":      "#8e8ea0",
    "white":         "#ffffff",
}

SESSIONS_FILE = "sessions.json"


# ─────────────────────────────────────────────
# Session persistence helpers
# ─────────────────────────────────────────────
def _load_sessions() -> list:
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []


def _save_sessions(sessions: list) -> None:
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_message("error", f"Failed to save sessions: {e}")


# ─────────────────────────────────────────────
# Rounded-rectangle canvas helper
# ─────────────────────────────────────────────
def _round_rect(canvas, x1, y1, x2, y2, r=12, **kw):
    pts = [
        x1+r, y1,  x2-r, y1,
        x2,   y1,  x2,   y1+r,
        x2,   y2-r,x2,   y2,
        x2-r, y2,  x1+r, y2,
        x1,   y2,  x1,   y2-r,
        x1,   y1+r,x1,   y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


class NovaGUI:
    # ──────────────────────────────────────────
    # Init
    # ──────────────────────────────────────────
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Nova AI")
        self.root.geometry("1200x760")
        self.root.minsize(900, 600)
        self.root.configure(bg=C["main_bg"])

        self.is_listening     = False
        self.is_recording_once = False   # single-shot mic press
        self.listening_thread = None

        self.command_processor = CommandProcessor(
            assistant_name=getattr(config, "ASSISTANT_NAME", "Nova")
        )

        try:
            initialize_engine()
        except Exception as e:
            log_message("error", f"TTS engine init failed: {e}")

        # Sessions: list of dicts {id, title, messages:[{role,text,ts}]}
        self._sessions: list  = _load_sessions()
        self._active_sid: str = ""   # id of currently open session

        self._build_ui()
        self._refresh_session_list()

        # Open most-recent session or create a new one
        if self._sessions:
            self._open_session(self._sessions[0]["id"])
        else:
            self._new_session()

    # ──────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────
    def _build_ui(self):
        # ── Root grid: sidebar | divider | main ──
        self.root.grid_columnconfigure(0, minsize=240, weight=0)
        self.root.grid_columnconfigure(1, minsize=1,   weight=0)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_divider()
        self._build_main()

    # ──────────────────────────────────────────
    # Sidebar
    # ──────────────────────────────────────────
    def _build_sidebar(self):
        sb = tk.Frame(self.root, bg=C["sidebar"], width=240)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(1, weight=1)
        sb.grid_columnconfigure(0, weight=1)

        # ── Top: logo + new-chat btn ──────────
        top = tk.Frame(sb, bg=C["sidebar"])
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(14, 6))

        logo = tk.Label(top, text="✦  Nova AI", fg=C["white"],
                        bg=C["sidebar"], font=("Segoe UI", 13, "bold"))
        logo.pack(side="left")

        new_btn = tk.Button(
            top, text="＋", bg=C["new_chat_bg"], fg=C["text"],
            font=("Segoe UI", 13), bd=0, relief="flat", cursor="hand2",
            padx=8, pady=2,
            command=self._new_session
        )
        new_btn.pack(side="right")
        self._hover(new_btn, C["new_chat_bg"], C["btn_hover"])

        # ── Session list (scrollable) ─────────
        list_container = tk.Frame(sb, bg=C["sidebar"])
        list_container.grid(row=1, column=0, sticky="nsew")

        canvas = tk.Canvas(list_container, bg=C["sidebar"],
                           highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._session_inner = tk.Frame(canvas, bg=C["sidebar"])
        self._session_win   = canvas.create_window(
            (0, 0), window=self._session_inner, anchor="nw"
        )

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(self._session_win, width=e.width)

        self._session_inner.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            -1 if e.delta > 0 else 1, "units"))

        self._session_canvas = canvas

        # ── Bottom: separator + settings row ─
        sep = tk.Frame(sb, bg=C["border"], height=1)
        sep.grid(row=2, column=0, sticky="ew", pady=(4, 0))

        bottom = tk.Frame(sb, bg=C["sidebar"])
        bottom.grid(row=3, column=0, sticky="ew", padx=12, pady=10)

        tk.Label(bottom, text="Nova AI  v1.0", fg=C["text_muted"],
                 bg=C["sidebar"], font=("Segoe UI", 9)).pack(side="left")

    def _build_divider(self):
        div = tk.Frame(self.root, bg=C["border"], width=1)
        div.grid(row=0, column=1, sticky="ns")

    # ──────────────────────────────────────────
    # Main area (chat + input)
    # ──────────────────────────────────────────
    def _build_main(self):
        main = tk.Frame(self.root, bg=C["main_bg"])
        main.grid(row=0, column=2, sticky="nsew")
        main.grid_rowconfigure(0, weight=0)   # header
        main.grid_rowconfigure(1, weight=1)   # chat
        main.grid_rowconfigure(2, weight=0)   # input
        main.grid_columnconfigure(0, weight=1)

        # ── Header bar ────────────────────────
        hdr = tk.Frame(main, bg=C["main_bg"], height=48)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        self._chat_title_var = tk.StringVar(value="Nova AI")
        self._chat_title_lbl = tk.Label(
            hdr, textvariable=self._chat_title_var,
            fg=C["text"], bg=C["main_bg"],
            font=("Segoe UI", 13, "bold")
        )
        self._chat_title_lbl.pack(side="left", padx=20, pady=12)

        # Status pill (top-right)
        self._status_var = tk.StringVar(value="● Ready")
        self._status_lbl = tk.Label(
            hdr, textvariable=self._status_var,
            fg=C["accent"], bg=C["main_bg"],
            font=("Segoe UI", 10)
        )
        self._status_lbl.pack(side="right", padx=20)

        # ── Chat scroll area ──────────────────
        chat_frame = tk.Frame(main, bg=C["main_bg"])
        chat_frame.grid(row=1, column=0, sticky="nsew")
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self._chat_canvas = tk.Canvas(
            chat_frame, bg=C["main_bg"],
            highlightthickness=0, bd=0
        )
        chat_vsb = tk.Scrollbar(
            chat_frame, orient="vertical",
            command=self._chat_canvas.yview
        )
        self._chat_canvas.configure(yscrollcommand=chat_vsb.set)
        self._chat_canvas.grid(row=0, column=0, sticky="nsew")
        chat_vsb.grid(row=0, column=1, sticky="ns")

        self._chat_inner = tk.Frame(self._chat_canvas, bg=C["main_bg"])
        self._chat_win   = self._chat_canvas.create_window(
            (0, 0), window=self._chat_inner, anchor="nw"
        )

        def _cc(e): self._chat_canvas.configure(
            scrollregion=self._chat_canvas.bbox("all"))
        def _cw(e): self._chat_canvas.itemconfig(
            self._chat_win, width=e.width)
        self._chat_inner.bind("<Configure>", _cc)
        self._chat_canvas.bind("<Configure>", _cw)
        self._chat_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._chat_canvas.yview_scroll(
                -1 if e.delta > 0 else 1, "units")
        )

        self._build_input_bar(main)
        self._build_statusbar(main)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ──────────────────────────────────────────
    # Input bar  (matches screenshot exactly)
    # Layout:  [ text field .............. 🎙  ↑ ]
    #  • White/light pill, full width
    #  • 🎙 mic symbol  – right side, plain icon
    #  • ↑  send        – dark circle, rightmost
    # ──────────────────────────────────────────
    def _build_input_bar(self, parent):
        # Outer wrapper row
        wrapper = tk.Frame(parent, bg=C["main_bg"])
        wrapper.grid(row=2, column=0, sticky="ew", padx=32, pady=(6, 14))
        wrapper.grid_columnconfigure(0, weight=1)

        # ── Pill container ─────────────────────
        # Light background pill (like ChatGPT's white bar on dark bg)
        PILL_BG    = "#f4f4f4"   # near-white
        PILL_FG    = "#0d0d0d"   # dark text inside
        PILL_PH    = "#9a9a9a"   # placeholder colour
        PILL_H     = 52          # height of pill

        pill = tk.Frame(
            wrapper,
            bg=PILL_BG,
            highlightthickness=1,
            highlightbackground="#d9d9d9",
        )
        pill.grid(row=0, column=0, sticky="ew")
        pill.grid_columnconfigure(0, weight=1)
        pill.grid_rowconfigure(0, weight=1)

        # ── Text entry (fills all space) ───────
        self._input_entry = tk.Text(
            pill,
            font=("Segoe UI", 12),
            bg=PILL_BG, fg=PILL_FG,
            insertbackground=PILL_FG,
            bd=0, relief="flat",
            wrap="word", height=1,
            padx=14, pady=14,
        )
        self._input_entry.grid(row=0, column=0, sticky="nsew", pady=0)
        self._input_entry.bind("<Return>",   self._on_enter_pressed)
        self._input_entry.bind("<FocusIn>",  self._clear_placeholder)
        self._input_entry.bind("<FocusOut>", self._restore_placeholder)
        self._input_entry.bind("<Key>",      self._on_key_typed)
        self._placeholder_active = True
        self._PILL_PH = PILL_PH
        self._PILL_FG = PILL_FG
        self._PILL_BG = PILL_BG
        self._set_placeholder()

        # ── Right button cluster ───────────────
        btn_frame = tk.Frame(pill, bg=PILL_BG)
        btn_frame.grid(row=0, column=1, padx=(0, 8), pady=6)

        # 🎙 mic icon  (plain symbol, no circle)
        self._mic_btn = tk.Label(
            btn_frame,
            text="🎙",
            bg=PILL_BG, fg="#555555",
            font=("Segoe UI", 17),
            cursor="hand2",
        )
        self._mic_btn.pack(side="left", padx=(0, 8))
        self._mic_btn.bind("<Button-1>", lambda e: self._mic_press())
        self._mic_btn.bind("<Enter>", lambda e: self._mic_btn.config(fg="#111111"))
        self._mic_btn.bind("<Leave>", lambda e: self._mic_btn.config(
            fg=C["accent"] if self.is_recording_once or self.is_listening
            else "#555555"))

        # ↑ send  (dark filled circle)
        self._send_btn = tk.Canvas(
            btn_frame,
            width=34, height=34,
            bg=PILL_BG, highlightthickness=0,
            cursor="hand2",
        )
        self._send_btn.pack(side="left")
        self._send_btn.create_oval(0, 0, 34, 34, fill="#0d0d0d", outline="")
        self._send_btn.create_text(
            17, 17, text="↑",
            fill="white", font=("Segoe UI", 14, "bold")
        )
        self._send_btn.bind("<Button-1>", lambda e: self._on_send())
        self._send_btn.bind("<Enter>",  lambda e: self._send_btn.itemconfig(1, fill="#333333"))
        self._send_btn.bind("<Leave>",  lambda e: self._send_btn.itemconfig(1, fill="#0d0d0d"))

        # Hint below bar
        tk.Label(
            wrapper,
            text="Enter  send  •  Shift+Enter  newline  •  � for voice  •  Ctrl+L  continuous listen",
            fg=C["text_muted"], bg=C["main_bg"],
            font=("Segoe UI", 8),
        ).grid(row=1, column=0, pady=(3, 0))

        # Keyboard shortcuts
        self.root.bind("<Control-l>", lambda e: self._mic_press())
        self._input_entry.focus_set()

    def _build_statusbar(self, parent):
        sb = tk.Frame(parent, bg=C["sidebar"], height=22)
        sb.grid(row=3, column=0, sticky="ew")
        sb.grid_propagate(False)
        self._statusbar_var = tk.StringVar(value="Ready")
        tk.Label(sb, textvariable=self._statusbar_var,
                 fg=C["text_muted"], bg=C["sidebar"],
                 font=("Segoe UI", 8)).pack(side="left", padx=10)

    # ──────────────────────────────────────────
    # Placeholder helpers
    # ──────────────────────────────────────────
    def _set_placeholder(self):
        self._input_entry.delete("1.0", tk.END)
        self._input_entry.insert("1.0", "Message Nova…")
        self._input_entry.config(fg=getattr(self, "_PILL_PH", C["text_muted"]))
        self._placeholder_active = True

    def _clear_placeholder(self, event=None):
        if self._placeholder_active:
            self._input_entry.delete("1.0", tk.END)
            self._input_entry.config(fg=getattr(self, "_PILL_FG", C["text"]))
            self._placeholder_active = False

    def _on_key_typed(self, event=None):
        """Clear placeholder state and text as soon as the user starts typing."""
        if self._placeholder_active:
            # Clear placeholder text first, then let the keystroke insert normally
            self._input_entry.delete("1.0", tk.END)
            self._input_entry.config(fg=getattr(self, "_PILL_FG", C["text"]))
            self._placeholder_active = False

    def _restore_placeholder(self, event=None):
        """Re-show placeholder if the field is empty (bound to FocusOut)."""
        if not self._input_entry.get("1.0", tk.END).strip():
            self._set_placeholder()

    def _get_input_text(self) -> str:
        raw = self._input_entry.get("1.0", tk.END).strip()
        # Treat placeholder text or empty field as no input
        if not raw or raw == "Message Nova…":
            return ""
        return raw

    def _clear_input(self):
        self._input_entry.delete("1.0", tk.END)
        self._placeholder_active = False

    # ──────────────────────────────────────────
    # Hover helper
    # ──────────────────────────────────────────
    @staticmethod
    def _hover(w, normal, hovered):
        w.bind("<Enter>", lambda e: w.config(bg=hovered))
        w.bind("<Leave>", lambda e: w.config(bg=normal))

    # ──────────────────────────────────────────
    # Status helpers
    # ──────────────────────────────────────────
    def _set_status(self, text: str, color: str = None):
        color = color or C["text_dim"]
        colors = {
            "Ready":        C["accent"],
            "Listening...": "#ffc107",
            "Recording...": "#ffc107",
            "Processing...": C["accent"],
            "Stopped":      C["error"],
        }
        dot_color = colors.get(text, color)
        self._status_var.set(f"● {text}")
        self._status_lbl.config(fg=dot_color)
        self._statusbar_var.set(text)

    # ──────────────────────────────────────────
    # Session management
    # ──────────────────────────────────────────
    def _new_session(self):
        sid   = str(uuid.uuid4())
        title = datetime.datetime.now().strftime("Chat %b %d, %H:%M")
        sess  = {"id": sid, "title": title, "messages": []}
        self._sessions.insert(0, sess)
        _save_sessions(self._sessions)
        self._refresh_session_list()
        self._open_session(sid)

    def _open_session(self, sid: str):
        self._active_sid = sid
        sess = self._get_session(sid)
        if sess is None:
            return

        self._chat_title_var.set(sess["title"])
        self._refresh_session_list()  # re-render to show selection

        # Rebuild chat display
        for w in self._chat_inner.winfo_children():
            w.destroy()

        if not sess["messages"]:
            self._render_welcome()
        else:
            for msg in sess["messages"]:
                self._render_bubble(msg["role"], msg["text"], msg.get("ts", ""))

        self._scroll_to_bottom()

    def _get_session(self, sid: str):
        for s in self._sessions:
            if s["id"] == sid:
                return s
        return None

    def _rename_session(self, sid: str):
        sess = self._get_session(sid)
        if not sess:
            return
        new_name = simpledialog.askstring(
            "Rename Session", "Enter new name:",
            initialvalue=sess["title"], parent=self.root
        )
        if new_name and new_name.strip():
            sess["title"] = new_name.strip()
            _save_sessions(self._sessions)
            self._refresh_session_list()
            if sid == self._active_sid:
                self._chat_title_var.set(sess["title"])

    def _delete_session(self, sid: str):
        if not messagebox.askyesno(
            "Delete Session", "Delete this session?", parent=self.root
        ):
            return
        self._sessions = [s for s in self._sessions if s["id"] != sid]
        _save_sessions(self._sessions)
        self._refresh_session_list()

        if sid == self._active_sid:
            if self._sessions:
                self._open_session(self._sessions[0]["id"])
            else:
                self._new_session()

    def _add_message(self, role: str, text: str):
        sess = self._get_session(self._active_sid)
        if sess is None:
            return
        ts = datetime.datetime.now().strftime("%I:%M %p")
        sess["messages"].append({"role": role, "text": text, "ts": ts})
        # Auto-rename session from first user message
        if role == "user" and len(sess["messages"]) == 1:
            title = text[:40] + ("…" if len(text) > 40 else "")
            sess["title"] = title
            self._chat_title_var.set(title)
            self._refresh_session_list()
        _save_sessions(self._sessions)
        self._render_bubble(role, text, ts)
        self._scroll_to_bottom()

    # ──────────────────────────────────────────
    # Sidebar session list renderer
    # ──────────────────────────────────────────
    def _refresh_session_list(self):
        for w in self._session_inner.winfo_children():
            w.destroy()

        # Section label
        tk.Label(
            self._session_inner, text="Recent",
            fg=C["text_muted"], bg=C["sidebar"],
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=14, pady=(6, 2))

        for sess in self._sessions:
            self._build_session_row(sess)

    def _build_session_row(self, sess: dict):
        sid      = sess["id"]
        is_sel   = (sid == self._active_sid)
        row_bg   = C["sidebar_sel"] if is_sel else C["sidebar"]

        row = tk.Frame(
            self._session_inner, bg=row_bg,
            cursor="hand2"
        )
        row.pack(fill="x", padx=6, pady=1)
        row.grid_columnconfigure(0, weight=1)

        # Chat icon + title
        inner = tk.Frame(row, bg=row_bg)
        inner.grid(row=0, column=0, sticky="ew", padx=6, pady=6)

        tk.Label(
            inner, text="💬",
            bg=row_bg, fg=C["text_dim"],
            font=("Segoe UI", 10)
        ).pack(side="left")

        title_lbl = tk.Label(
            inner, text=sess["title"],
            bg=row_bg, fg=C["text"],
            font=("Segoe UI", 10),
            anchor="w", width=18,
            cursor="hand2"
        )
        title_lbl.pack(side="left", padx=(6, 0))

        # Three-dot menu button (hidden until hover)
        dot_btn = tk.Button(
            row, text="⋯", bg=row_bg, fg=C["dot_menu"],
            font=("Segoe UI", 12), bd=0, relief="flat",
            cursor="hand2",
            command=lambda s=sid, b=None: self._show_session_menu(s)
        )
        dot_btn.grid(row=0, column=1, padx=(0, 6))

        # Click row → open session
        for w in (row, inner, title_lbl):
            w.bind("<Button-1>", lambda e, s=sid: self._open_session(s))

        # Hover: highlight row
        def _enter(e, r=row, b=dot_btn, bg=row_bg):
            r.config(bg=C["sidebar_hover"])
            b.config(bg=C["sidebar_hover"])
            for c in r.winfo_children():
                try:
                    c.config(bg=C["sidebar_hover"])
                    for cc in c.winfo_children():
                        cc.config(bg=C["sidebar_hover"])
                except Exception:
                    pass

        def _leave(e, r=row, b=dot_btn, bg=row_bg):
            r.config(bg=bg)
            b.config(bg=bg)
            for c in r.winfo_children():
                try:
                    c.config(bg=bg)
                    for cc in c.winfo_children():
                        cc.config(bg=bg)
                except Exception:
                    pass

        row.bind("<Enter>", _enter)
        row.bind("<Leave>", _leave)
        inner.bind("<Enter>", _enter)
        inner.bind("<Leave>", _leave)

    def _show_session_menu(self, sid: str):
        menu = tk.Menu(self.root, tearoff=0,
                       bg=C["sidebar_sel"], fg=C["text"],
                       activebackground=C["btn_hover"],
                       activeforeground=C["white"],
                       font=("Segoe UI", 10))
        menu.add_command(label="✏  Rename",
                         command=lambda: self._rename_session(sid))
        menu.add_separator()
        menu.add_command(label="🗑  Delete",
                         command=lambda: self._delete_session(sid))
        try:
            menu.tk_popup(self.root.winfo_pointerx(),
                          self.root.winfo_pointery())
        finally:
            menu.grab_release()


    # ──────────────────────────────────────────
    # Welcome screen (empty session)
    # ──────────────────────────────────────────
    def _render_welcome(self):
        frame = tk.Frame(self._chat_inner, bg=C["main_bg"])
        frame.pack(expand=True, pady=80)

        tk.Label(
            frame, text="✦", fg=C["accent"],
            bg=C["main_bg"], font=("Segoe UI", 36)
        ).pack()
        tk.Label(
            frame,
            text=f"Hello! I'm {self.command_processor.assistant_name}",
            fg=C["text"], bg=C["main_bg"],
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(8, 4))
        tk.Label(
            frame,
            text="Ask me anything — I can open apps, play music,\ncheck weather, search the web, and much more.",
            fg=C["text_dim"], bg=C["main_bg"],
            font=("Segoe UI", 11), justify="center"
        ).pack()

        # Quick-action suggestion pills
        pills_frame = tk.Frame(frame, bg=C["main_bg"])
        pills_frame.pack(pady=24)
        suggestions = [
            "What time is it?",
            "Weather in Karachi",
            "Play lofi music",
            "Open YouTube",
        ]
        for s in suggestions:
            btn = tk.Button(
                pills_frame, text=s,
                bg=C["user_bubble"], fg=C["text_dim"],
                font=("Segoe UI", 10), bd=0, relief="flat",
                padx=14, pady=8, cursor="hand2",
                command=lambda t=s: self._send_text(t)
            )
            btn.pack(side="left", padx=6)
            self._hover(btn, C["user_bubble"], C["btn_hover"])

    # ──────────────────────────────────────────
    # Chat bubble renderer
    # ──────────────────────────────────────────
    def _render_bubble(self, role: str, text: str, ts: str = ""):
        is_user = (role == "user")

        outer = tk.Frame(self._chat_inner, bg=C["main_bg"])
        outer.pack(fill="x", padx=0, pady=2)
        outer.grid_columnconfigure(0, weight=1)

        # Avatar + name row
        meta = tk.Frame(outer, bg=C["main_bg"])
        meta.pack(
            fill="x",
            padx=(60 if is_user else 20),
            pady=(6, 0),
            anchor="e" if is_user else "w"
        )

        avatar_text = "You" if is_user else self.command_processor.assistant_name
        avatar_color = "#6c63ff" if is_user else C["accent"]
        tk.Label(
            meta, text=avatar_text,
            fg=avatar_color, bg=C["main_bg"],
            font=("Segoe UI", 9, "bold")
        ).pack(side="left" if not is_user else "right")

        if ts:
            tk.Label(
                meta, text=ts,
                fg=C["text_muted"], bg=C["main_bg"],
                font=("Segoe UI", 8)
            ).pack(
                side="left" if not is_user else "right",
                padx=8
            )

        # Bubble
        bubble_bg = C["user_bubble"] if is_user else C["nova_bubble"]
        bubble = tk.Frame(
            outer, bg=bubble_bg,
            bd=0, relief="flat",
            highlightthickness=1,
            highlightbackground=C["border"] if not is_user else "#3d3d4a"
        )
        bubble.pack(
            anchor="e" if is_user else "w",
            padx=(120 if is_user else 20),
            pady=(2, 8)
        )

        tk.Label(
            bubble, text=text,
            fg=C["text"], bg=bubble_bg,
            font=("Segoe UI", 11),
            wraplength=640,
            justify="left",
            padx=16, pady=10
        ).pack()

    def _scroll_to_bottom(self):
        self.root.after(80, lambda: self._chat_canvas.yview_moveto(1.0))


    # ──────────────────────────────────────────
    # Input handlers
    # ──────────────────────────────────────────
    def _on_enter_pressed(self, event=None):
        # Shift+Enter → newline; plain Enter → send
        if event and event.state & 0x1:   # Shift held
            return None                    # allow default newline
        self._on_send()
        return "break"

    def _on_send(self, event=None):
        text = self._get_input_text()
        if not text:
            return
        self._clear_input()
        self._set_placeholder()
        self._send_text(text)

    def _send_text(self, text: str):
        """Add user message and dispatch to backend."""
        self._add_message("user", text)
        self._process_command_async(text)

    # ──────────────────────────────────────────
    # Command processing (background thread)
    # ──────────────────────────────────────────
    def _process_command_async(self, text: str):
        def worker():
            try:
                self._set_status("Processing...")
                response = self.command_processor.process_command(text)
                if response and response.strip():
                    self.root.after(0, lambda r=response: self._add_message("nova", r))
                    # Speak directly from the worker thread — speak() is thread-safe
                    # (it only puts text onto the TTS queue). Using root.after caused
                    # later responses to be skipped because the callback could be
                    # delayed or dropped when the TTS engine was still busy.
                    speak(response)
                else:
                    self.root.after(0, lambda: self._add_message(
                        "nova", "Sorry, I didn't get a response. Please try again."))
            except Exception as e:
                log_message("error", f"process_command_async error: {e}")
                self.root.after(0, lambda: self._add_message(
                    "nova", "Sorry, something went wrong processing your request."))
            finally:
                self.root.after(0, lambda: self._set_status(
                    "Listening..." if self.is_listening else "Ready"))

        threading.Thread(target=worker, daemon=True).start()

    # ──────────────────────────────────────────
    # Microphone — single-shot press
    # ──────────────────────────────────────────
    def _mic_press(self):
        """
        One-shot voice input: click 🎙 to record one phrase.
        Recognised text fills the input and sends automatically.
        If continuous listening is active, stops it instead.
        """
        if self.is_listening:
            self._stop_continuous_listen()
            return

        if self.is_recording_once:
            return  # already recording

        self.is_recording_once = True
        self._mic_btn.config(fg=C["accent"], text="⏹")
        self._set_status("Recording…")

        def _record():
            try:
                recognized = listen()
                if recognized and recognized.strip():
                    self.root.after(0, lambda r=recognized: self._on_voice_result(r))
                else:
                    self.root.after(0, lambda: self._set_status("Ready"))
                    self.root.after(0, lambda: self._add_message(
                        "nova", "I didn't catch that — please try again."))
            except Exception as e:
                log_message("error", f"mic record error: {e}")
                self.root.after(0, lambda: self._set_status("Ready"))
                self.root.after(0, lambda: self._add_message(
                    "nova", "Microphone error. Make sure your mic is connected."))
            finally:
                self.is_recording_once = False
                self.root.after(0, lambda: self._mic_btn.config(
                    fg="#555555", text="🎙"))

        threading.Thread(target=_record, daemon=True).start()

    def _on_voice_result(self, text: str):
        self._set_status("Ready")
        # Show recognised text in input box briefly, then auto-send
        self._clear_input()
        self._input_entry.config(fg=getattr(self, "_PILL_FG", C["text"]))
        self._input_entry.insert("1.0", text)
        self._placeholder_active = False
        # Small delay so user can see the text before it sends
        self.root.after(250, self._on_send)


    # ──────────────────────────────────────────
    # Continuous voice listening (Ctrl+L)
    # ──────────────────────────────────────────
    def _start_continuous_listen(self):
        if self.is_listening:
            return
        self.is_listening = True
        self._set_status("Listening...")
        self._mic_btn.config(fg="#ffc107", text="⏹")

        def _loop():
            try:
                while self.is_listening:
                    recognized = listen()
                    if not self.is_listening:
                        break
                    if recognized and recognized.strip():
                        self.root.after(
                            0, lambda r=recognized: self._on_voice_result(r))
            except Exception as e:
                log_message("error", f"continuous listen error: {e}")
            finally:
                self.is_listening = False
                self.root.after(0, lambda: self._set_status("Ready"))
                self.root.after(0, lambda: self._mic_btn.config(
                    fg="#555555", text="🎙"))

        self.listening_thread = threading.Thread(target=_loop, daemon=True)
        self.listening_thread.start()

    def _stop_continuous_listen(self):
        self.is_listening = False
        self._set_status("Ready")
        self._mic_btn.config(fg="#555555", text="🎙")

    # ──────────────────────────────────────────
    # Close
    # ──────────────────────────────────────────
    def _on_close(self):
        try:
            if messagebox.askyesno("Exit", "Exit Nova AI?", parent=self.root):
                self.is_listening = False
                _save_sessions(self._sessions)
                self.root.destroy()
        except Exception:
            self.root.destroy()


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def main():
    root = tk.Tk()

    # High-DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = NovaGUI(root)

    # Speak initial greeting for the active session
    def _greet():
        sess = app._get_session(app._active_sid)
        if sess and not sess["messages"]:
            greeting = (
                f"Hello! I'm {app.command_processor.assistant_name}. "
                "How can I assist you today?"
            )
            speak(greeting)

    root.after(400, _greet)
    root.mainloop()


if __name__ == "__main__":
    main()
