"""
Modern Graphical User Interface (GUI) for the Open Trivia Database Quiz Game.
Supports category selection:
  - Science: Mathematics (Category ID: 19)
  - Science: Gadgets (Category ID: 30)
  - Science: Computers (Category ID: 18)
Built with Python's built-in Tkinter framework (zero external dependencies).
"""

import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

from game_engine import AnswerRecord, GameEngine, HighScoreManager, PreparedQuestion
from trivia_api import CATEGORIES, DEFAULT_CATEGORY, fetch_questions, resolve_category_id

# Visual Theme Palette (Modern Dark / Slate)
BG_MAIN = "#0f172a"        # Deep slate
BG_CARD = "#1e293b"        # Card background
BG_CARD_HOVER = "#334155"  # Card hover
BG_ACCENT = "#6366f1"      # Indigo
BG_ACCENT_HOVER = "#4f46e5"
COLOR_SUCCESS = "#10b981"  # Emerald
COLOR_ERROR = "#ef4444"    # Crimson
COLOR_WARN = "#f59e0b"     # Amber
COLOR_CYAN = "#06b6d4"     # Cyan
TEXT_PRIMARY = "#f8fafc"   # White
TEXT_MUTED = "#94a3b8"     # Light slate
BORDER_COLOR = "#334155"

FONT_HEADING = ("Segoe UI", 18, "bold")
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)


class TriviaGUIApp(tk.Tk):
    def __init__(self, initial_category: int = DEFAULT_CATEGORY):
        super().__init__()
        self.title("Trivia Master - Open Trivia DB (Science: Math & Gadgets)")
        self.geometry("940x720")
        self.minsize(840, 640)
        self.configure(bg=BG_MAIN)

        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.current_category_id: int = resolve_category_id(initial_category)
        self.category_cache_pool: Dict[int, List[Dict[str, Any]]] = {}
        self.engine: Optional[GameEngine] = None
        self.timer_seconds_left: float = 25.0
        self.timer_active: bool = False
        self.timer_job = None
        self.enable_timer: bool = True

        self.container = tk.Frame(self, bg=BG_MAIN)
        self.container.pack(fill="both", expand=True)

        # Preload current category in background
        self.after(100, self.preload_current_category)
        self.show_welcome_screen()

    def preload_current_category(self) -> None:
        try:
            qs = fetch_questions(amount=50, category=self.current_category_id, force_refresh=False)
            self.category_cache_pool[self.current_category_id] = qs
        except Exception as e:
            print(f"[Warning] Failed to preload category {self.current_category_id}: {e}")

    def clear_container(self) -> None:
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_active = False

        for widget in self.container.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------
    # WELCOME / CATEGORY & MODE SELECTION SCREEN
    # -------------------------------------------------------------
    def show_welcome_screen(self) -> None:
        self.clear_container()

        wrapper = tk.Frame(self.container, bg=BG_MAIN)
        wrapper.pack(expand=True, fill="both", padx=35, pady=20)

        # Title Card
        title_frame = tk.Frame(
            wrapper,
            bg=BG_CARD,
            bd=1,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        title_frame.pack(fill="x", pady=(0, 15), ipady=12, padx=10)

        tk.Label(
            title_frame,
            text="⚡ TRIVIA MASTER: SCIENCE & TECH ⚡",
            font=("Segoe UI", 20, "bold"),
            fg=COLOR_CYAN,
            bg=BG_CARD,
        ).pack(pady=(5, 3))

        cat_info = CATEGORIES.get(self.current_category_id, CATEGORIES[DEFAULT_CATEGORY])
        self.subtitle_label = tk.Label(
            title_frame,
            text=f"Selected Category: {cat_info['icon']} {cat_info['display_name']} • Powered by Open Trivia Database (https://opentdb.com)",
            font=FONT_BODY,
            fg=TEXT_MUTED,
            bg=BG_CARD,
        )
        self.subtitle_label.pack(pady=(0, 5))

        # Two-column layout for Category Selection and Mode Selection
        cards_row = tk.Frame(wrapper, bg=BG_MAIN)
        cards_row.pack(fill="both", expand=True, padx=10, pady=5)
        cards_row.columnconfigure(0, weight=1)
        cards_row.columnconfigure(1, weight=1)

        # Left Column: Category Selection
        cat_frame = tk.LabelFrame(
            cards_row,
            text=" 1. Select Quiz Category ",
            font=FONT_TITLE,
            fg=COLOR_CYAN,
            bg=BG_CARD,
            bd=1,
            relief="solid",
            highlightbackground=BORDER_COLOR,
        )
        cat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5, ipady=10)

        self.category_var = tk.IntVar(value=self.current_category_id)

        for cat_id, info in CATEGORIES.items():
            row = tk.Frame(cat_frame, bg=BG_CARD)
            row.pack(fill="x", padx=15, pady=6)

            rb = tk.Radiobutton(
                row,
                text=f"{info['icon']}  {info['display_name']}",
                variable=self.category_var,
                value=cat_id,
                font=FONT_BOLD,
                fg=TEXT_PRIMARY,
                bg=BG_CARD,
                activebackground=BG_CARD,
                activeforeground=COLOR_CYAN,
                selectcolor=BG_MAIN,
                indicatoron=True,
                command=self.on_category_changed,
            )
            rb.pack(anchor="w")

            tk.Label(
                row,
                text=f"    {info['description']} (Up to {info['max_questions']} Qs)",
                font=FONT_SMALL,
                fg=TEXT_MUTED,
                bg=BG_CARD,
                wraplength=360,
                justify="left",
            ).pack(anchor="w")

        # Right Column: Game Mode Selection
        mode_frame = tk.LabelFrame(
            cards_row,
            text=" 2. Select Game Mode ",
            font=FONT_TITLE,
            fg=COLOR_WARN,
            bg=BG_CARD,
            bd=1,
            relief="solid",
            highlightbackground=BORDER_COLOR,
        )
        mode_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5, ipady=10)

        self.selected_mode = tk.StringVar(value="marathon")
        modes = [
            ("marathon", "🏃 Full Marathon", "Play through all available questions in this category."),
            ("sprint", "⚡ Sprint Mode (25 Questions)", "Fast-paced half marathon challenge."),
            ("blitz", "🎯 Quick Blitz (10 Questions)", "Quick 10-question warm-up session."),
            ("survival", "💀 Sudden Death (3 Lives)", "Make 3 mistakes and game is over!"),
        ]

        for val, title, desc in modes:
            row = tk.Frame(mode_frame, bg=BG_CARD)
            row.pack(fill="x", padx=15, pady=6)

            rb = tk.Radiobutton(
                row,
                text=title,
                variable=self.selected_mode,
                value=val,
                font=FONT_BOLD,
                fg=TEXT_PRIMARY,
                bg=BG_CARD,
                activebackground=BG_CARD,
                activeforeground=COLOR_WARN,
                selectcolor=BG_MAIN,
                indicatoron=True,
            )
            rb.pack(anchor="w")

            tk.Label(
                row,
                text=f"    {desc}",
                font=FONT_SMALL,
                fg=TEXT_MUTED,
                bg=BG_CARD,
            ).pack(anchor="w")

        # Settings: Timer toggle
        settings_frame = tk.Frame(wrapper, bg=BG_MAIN)
        settings_frame.pack(fill="x", padx=10, pady=10)

        self.timer_var = tk.BooleanVar(value=True)
        cb_timer = tk.Checkbutton(
            settings_frame,
            text="Enable 25-Second Per-Question Countdown Timer (Bonus points for speed!)",
            variable=self.timer_var,
            font=FONT_BODY,
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
            selectcolor=BG_CARD,
            activebackground=BG_MAIN,
            activeforeground=TEXT_PRIMARY,
        )
        cb_timer.pack(anchor="w")

        # Action Buttons
        btn_frame = tk.Frame(wrapper, bg=BG_MAIN)
        btn_frame.pack(fill="x", padx=10, pady=(10, 5))

        start_btn = tk.Button(
            btn_frame,
            text="START QUIZ 🚀",
            font=("Segoe UI", 13, "bold"),
            bg=BG_ACCENT,
            fg=TEXT_PRIMARY,
            activebackground=BG_ACCENT_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=25,
            pady=10,
            command=self.start_game,
        )
        start_btn.pack(side="left", padx=(0, 15))

        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh Questions from OpenTDB",
            font=FONT_BODY,
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            activebackground=BG_CARD_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=10,
            command=self.force_refresh_current_category,
        )
        refresh_btn.pack(side="left", padx=5)

        high_scores_btn = tk.Button(
            btn_frame,
            text="🏆 Hall of Fame",
            font=FONT_BODY,
            bg=BG_CARD,
            fg=COLOR_WARN,
            activebackground=BG_CARD_HOVER,
            activeforeground=COLOR_WARN,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=10,
            command=self.show_high_scores_screen,
        )
        high_scores_btn.pack(side="right")

    def on_category_changed(self) -> None:
        new_cat = self.category_var.get()
        self.current_category_id = new_cat
        cat_info = CATEGORIES.get(new_cat, CATEGORIES[DEFAULT_CATEGORY])
        self.subtitle_label.config(
            text=f"Selected Category: {cat_info['icon']} {cat_info['display_name']} • Powered by Open Trivia Database (https://opentdb.com)"
        )
        # Preload in background if not already cached in memory
        if new_cat not in self.category_cache_pool:
            try:
                qs = fetch_questions(amount=50, category=new_cat, force_refresh=False)
                self.category_cache_pool[new_cat] = qs
            except Exception as e:
                print(f"[Notice] Will fetch upon start: {e}")

    def force_refresh_current_category(self) -> None:
        cat_id = self.category_var.get()
        cat_info = CATEGORIES.get(cat_id, CATEGORIES[DEFAULT_CATEGORY])
        try:
            self.config(cursor="wait")
            self.update()
            qs = fetch_questions(amount=50, category=cat_id, force_refresh=True)
            self.category_cache_pool[cat_id] = qs
            messagebox.showinfo(
                "Questions Refreshed",
                f"Successfully fetched {len(qs)} fresh questions for {cat_info['display_name']} from OpenTDB!",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch questions from OpenTDB:\n{e}")
        finally:
            self.config(cursor="")

    def start_game(self) -> None:
        cat_id = self.category_var.get()
        self.current_category_id = cat_id
        cat_info = CATEGORIES.get(cat_id, CATEGORIES[DEFAULT_CATEGORY])
        mode = self.selected_mode.get()
        self.enable_timer = self.timer_var.get()

        pool = self.category_cache_pool.get(cat_id)
        if not pool:
            try:
                self.config(cursor="wait")
                self.update()
                pool = fetch_questions(amount=50, category=cat_id, force_refresh=False)
                self.category_cache_pool[cat_id] = pool
            except Exception as e:
                messagebox.showerror(
                    "Network Error",
                    f"Failed to load questions for {cat_info['display_name']} from OpenTDB:\n{e}",
                )
                return
            finally:
                self.config(cursor="")

        self.engine = GameEngine(
            pool,
            category_name=cat_info["display_name"],
            mode=mode,
            time_limit=25 if self.enable_timer else 0,
        )
        self.show_question_screen()

    # -------------------------------------------------------------
    # ACTIVE QUESTION SCREEN
    # -------------------------------------------------------------
    def show_question_screen(self) -> None:
        self.clear_container()

        curr_q = self.engine.get_current_question()
        if not curr_q or self.engine.game_over:
            self.show_game_over_screen()
            return

        self.engine.start_question_timer()
        self.timer_seconds_left = 25.0

        cat_info = CATEGORIES.get(self.current_category_id, CATEGORIES[DEFAULT_CATEGORY])

        # Top Status Bar
        status_bar = tk.Frame(self.container, bg=BG_CARD, height=65)
        status_bar.pack(fill="x", side="top", ipady=8, padx=20, pady=(15, 10))

        # Category Badge
        tk.Label(
            status_bar,
            text=f"{cat_info['icon']} {cat_info['display_name']}",
            font=FONT_BOLD,
            fg=COLOR_CYAN,
            bg=BG_CARD,
        ).pack(side="left", padx=15)

        # Question counter
        counter_txt = f"Q {curr_q.index}/{self.engine.total_questions}"
        tk.Label(status_bar, text=counter_txt, font=FONT_BOLD, fg=TEXT_PRIMARY, bg=BG_CARD).pack(
            side="left", padx=5
        )

        # Difficulty Badge
        diff_color = (
            COLOR_SUCCESS
            if curr_q.difficulty == "easy"
            else (COLOR_WARN if curr_q.difficulty == "medium" else COLOR_ERROR)
        )
        diff_lbl = tk.Label(
            status_bar,
            text=f" {curr_q.difficulty.upper()} ",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_PRIMARY,
            bg=diff_color,
            padx=8,
            pady=2,
        )
        diff_lbl.pack(side="left", padx=10)

        # Score & Streak Display
        self.score_label = tk.Label(
            status_bar,
            text=f"Score: {self.engine.score}",
            font=("Segoe UI", 13, "bold"),
            fg=COLOR_SUCCESS,
            bg=BG_CARD,
        )
        self.score_label.pack(side="right", padx=15)

        streak_text = f"🔥 {self.engine.streak}x" if self.engine.streak >= 2 else ""
        self.streak_label = tk.Label(
            status_bar,
            text=streak_text,
            font=("Segoe UI", 12, "bold"),
            fg=COLOR_WARN,
            bg=BG_CARD,
        )
        self.streak_label.pack(side="right", padx=10)

        if self.engine.mode == "survival" and self.engine.lives is not None:
            hearts = "❤️ " * self.engine.lives
            tk.Label(
                status_bar,
                text=f"Lives: {hearts}",
                font=FONT_BOLD,
                fg=COLOR_ERROR,
                bg=BG_CARD,
            ).pack(side="right", padx=15)

        # Progress indicator bar
        progress_pct = (curr_q.index - 1) / self.engine.total_questions
        progress_frame = tk.Frame(self.container, bg=BORDER_COLOR, height=4)
        progress_frame.pack(fill="x", padx=20, pady=(0, 10))

        fill_frame = tk.Frame(progress_frame, bg=BG_ACCENT, height=4)
        fill_frame.place(relx=0, rely=0, relwidth=progress_pct, relheight=1.0)

        # Timer Bar (if enabled)
        if self.enable_timer:
            self.timer_canvas = tk.Canvas(
                self.container, height=8, bg=BORDER_COLOR, highlightthickness=0
            )
            self.timer_canvas.pack(fill="x", padx=20, pady=(0, 10))
            self.timer_bar = self.timer_canvas.create_rectangle(
                0, 0, 940, 8, fill=COLOR_CYAN, width=0
            )

        # Main Question Card Frame
        card = tk.Frame(
            self.container,
            bg=BG_CARD,
            bd=1,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=20, pady=10)

        # Question Text Label
        q_label = tk.Label(
            card,
            text=curr_q.question,
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
            wraplength=800,
            justify="center",
        )
        q_label.pack(expand=True, fill="both", padx=30, pady=(30, 20))

        # Option Buttons (2x2 Grid)
        options_container = tk.Frame(card, bg=BG_CARD)
        options_container.pack(fill="both", expand=True, padx=30, pady=(0, 25))

        self.option_buttons: Dict[str, tk.Button] = {}
        letters = ["A", "B", "C", "D"]

        options_container.columnconfigure(0, weight=1)
        options_container.columnconfigure(1, weight=1)
        options_container.rowconfigure(0, weight=1)
        options_container.rowconfigure(1, weight=1)

        for i, ltr in enumerate(letters):
            row = i // 2
            col = i % 2
            opt_text = curr_q.options.get(ltr, "")

            is_disabled = ltr in curr_q.disabled_options
            btn_state = "disabled" if is_disabled else "normal"
            btn_bg = BG_MAIN if not is_disabled else "#161d2d"
            btn_fg = TEXT_PRIMARY if not is_disabled else TEXT_MUTED

            btn = tk.Button(
                options_container,
                text=f"[{ltr}]  {opt_text}",
                font=FONT_BOLD,
                bg=btn_bg,
                fg=btn_fg,
                activebackground=BG_CARD_HOVER,
                activeforeground=TEXT_PRIMARY,
                bd=1,
                relief="flat",
                highlightbackground=BORDER_COLOR,
                highlightthickness=1,
                wraplength=360,
                cursor="hand2" if not is_disabled else "arrow",
                state=btn_state,
                command=lambda letter=ltr: self.handle_answer_click(letter),
            )
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.option_buttons[ltr] = btn

        # Bottom Controls: Lifelines & Quit
        bottom_bar = tk.Frame(self.container, bg=BG_MAIN, height=50)
        bottom_bar.pack(fill="x", side="bottom", padx=20, pady=(5, 15))

        # 50:50 Lifeline
        btn_5050_state = (
            "normal"
            if self.engine.lifelines.get("50_50", False) and not curr_q.disabled_options
            else "disabled"
        )
        self.btn_5050 = tk.Button(
            bottom_bar,
            text="⚡ 50 / 50 Lifeline",
            font=FONT_SMALL,
            bg=COLOR_CYAN if btn_5050_state == "normal" else BG_CARD,
            fg=BG_MAIN if btn_5050_state == "normal" else TEXT_MUTED,
            activebackground="#0891b2",
            activeforeground=BG_MAIN,
            relief="flat",
            state=btn_5050_state,
            cursor="hand2" if btn_5050_state == "normal" else "arrow",
            padx=12,
            pady=6,
            command=self.activate_fifty_fifty,
        )
        self.btn_5050.pack(side="left", padx=(0, 10))

        # Skip Lifeline
        btn_skip_state = "normal" if self.engine.lifelines.get("skip", False) else "disabled"
        self.btn_skip = tk.Button(
            bottom_bar,
            text="⏩ Skip Question",
            font=FONT_SMALL,
            bg=COLOR_WARN if btn_skip_state == "normal" else BG_CARD,
            fg=BG_MAIN if btn_skip_state == "normal" else TEXT_MUTED,
            activebackground="#d97706",
            activeforeground=BG_MAIN,
            relief="flat",
            state=btn_skip_state,
            cursor="hand2" if btn_skip_state == "normal" else "arrow",
            padx=12,
            pady=6,
            command=self.activate_skip,
        )
        self.btn_skip.pack(side="left")

        # Quit / Surrender Button
        quit_btn = tk.Button(
            bottom_bar,
            text="Quit Game",
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT_MUTED,
            activebackground=BG_CARD_HOVER,
            activeforeground=COLOR_ERROR,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=self.confirm_quit,
        )
        quit_btn.pack(side="right")

        # Start countdown tick
        if self.enable_timer:
            self.timer_active = True
            self.tick_timer()

    def tick_timer(self) -> None:
        if not self.timer_active:
            return

        self.timer_seconds_left -= 0.1
        if self.timer_seconds_left <= 0:
            self.timer_active = False
            self.handle_timeout()
            return

        # Update visual timer canvas width
        try:
            width = self.timer_canvas.winfo_width()
            fraction = max(0.0, self.timer_seconds_left / 25.0)
            self.timer_canvas.coords(self.timer_bar, 0, 0, width * fraction, 8)
            # Turn red when < 5 seconds
            fill_color = COLOR_ERROR if self.timer_seconds_left < 5 else COLOR_CYAN
            self.timer_canvas.itemconfig(self.timer_bar, fill=fill_color)
        except Exception:
            pass

        self.timer_job = self.after(100, self.tick_timer)

    def handle_timeout(self) -> None:
        curr_q = self.engine.get_current_question()
        if not curr_q:
            return

        for btn in self.option_buttons.values():
            btn.config(state="disabled")

        if curr_q.correct_letter in self.option_buttons:
            self.option_buttons[curr_q.correct_letter].config(bg=COLOR_SUCCESS, fg=TEXT_PRIMARY)

        self.engine.submit_answer(None)  # Timeout recorded
        self.after(1200, self.show_question_screen)

    def handle_answer_click(self, selected_letter: str) -> None:
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_active = False

        curr_q = self.engine.get_current_question()
        if not curr_q:
            return

        for btn in self.option_buttons.values():
            btn.config(state="disabled")

        record = self.engine.submit_answer(selected_letter)

        if record.is_correct:
            self.option_buttons[selected_letter].config(bg=COLOR_SUCCESS, fg=TEXT_PRIMARY)
        else:
            self.option_buttons[selected_letter].config(bg=COLOR_ERROR, fg=TEXT_PRIMARY)
            if curr_q.correct_letter in self.option_buttons:
                self.option_buttons[curr_q.correct_letter].config(bg=COLOR_SUCCESS, fg=TEXT_PRIMARY)

        self.after(850, self.show_question_screen)

    def activate_fifty_fifty(self) -> None:
        if self.engine and self.engine.use_fifty_fifty():
            curr_q = self.engine.get_current_question()
            if curr_q:
                for ltr in curr_q.disabled_options:
                    if ltr in self.option_buttons:
                        btn = self.option_buttons[ltr]
                        btn.config(
                            text=f"[{ltr}]  ~~~ Eliminated ~~~",
                            state="disabled",
                            bg="#161d2d",
                            fg=TEXT_MUTED,
                        )
                self.btn_5050.config(state="disabled", bg=BG_CARD, fg=TEXT_MUTED)

    def activate_skip(self) -> None:
        if self.engine and self.engine.use_skip():
            self.show_question_screen()

    def confirm_quit(self) -> None:
        if messagebox.askyesno("Quit Game", "Are you sure you want to end your current session?"):
            self.engine.game_over = True
            self.show_game_over_screen()

    # -------------------------------------------------------------
    # GAME OVER / SCORECARD SCREEN
    # -------------------------------------------------------------
    def show_game_over_screen(self) -> None:
        self.clear_container()

        summary = self.engine.get_summary()

        wrapper = tk.Frame(self.container, bg=BG_MAIN)
        wrapper.pack(expand=True, fill="both", padx=40, pady=20)

        # Top Header Card
        header = tk.Frame(
            wrapper,
            bg=BG_CARD,
            bd=1,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        header.pack(fill="x", pady=(0, 15), ipady=15)

        tk.Label(
            header,
            text="🎉 QUIZ COMPLETED! 🎉",
            font=("Segoe UI", 20, "bold"),
            fg=COLOR_SUCCESS,
            bg=BG_CARD,
        ).pack(pady=(0, 5))

        tk.Label(
            header,
            text=f"Category: {summary['category']} • Rank: {summary['rank']}",
            font=("Segoe UI", 13, "bold"),
            fg=COLOR_WARN,
            bg=BG_CARD,
        ).pack()

        # Metrics Grid
        stats_frame = tk.Frame(wrapper, bg=BG_MAIN)
        stats_frame.pack(fill="x", pady=10)
        stats_frame.columnconfigure((0, 1, 2), weight=1)

        def make_stat_box(col: int, title: str, value: str, subtext: str, val_color: str):
            box = tk.Frame(
                stats_frame,
                bg=BG_CARD,
                bd=1,
                relief="flat",
                highlightbackground=BORDER_COLOR,
                highlightthickness=1,
            )
            box.grid(row=0, column=col, padx=8, pady=5, sticky="nsew", ipady=12)
            tk.Label(box, text=title, font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack()
            tk.Label(box, text=value, font=("Segoe UI", 20, "bold"), fg=val_color, bg=BG_CARD).pack(pady=2)
            tk.Label(box, text=subtext, font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack()

        make_stat_box(0, "FINAL SCORE", f"{summary['score']}", "Points Earned", COLOR_SUCCESS)
        make_stat_box(
            1,
            "ACCURACY",
            f"{summary['accuracy_percent']}%",
            f"{summary['correct_count']} of {summary['answered_count']} correct",
            COLOR_CYAN,
        )
        make_stat_box(
            2,
            "LONGEST STREAK",
            f"{summary['max_streak']} 🔥",
            f"Avg {summary['avg_time_per_question']}s / Q",
            COLOR_WARN,
        )

        # High score save box
        save_box = tk.Frame(
            wrapper,
            bg=BG_CARD,
            bd=1,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        save_box.pack(fill="x", pady=15, padx=8, ipady=10)

        tk.Label(
            save_box,
            text="Save Score to Hall of Fame:",
            font=FONT_BOLD,
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
        ).pack(side="left", padx=20)

        self.player_name_entry = tk.Entry(
            save_box,
            font=FONT_BODY,
            bg=BG_MAIN,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            width=20,
        )
        self.player_name_entry.insert(0, "Trivia Master")
        self.player_name_entry.pack(side="left", padx=10)

        save_btn = tk.Button(
            save_box,
            text="Save Record 💾",
            font=FONT_BOLD,
            bg=BG_ACCENT,
            fg=TEXT_PRIMARY,
            activebackground=BG_ACCENT_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=lambda: self.save_score_action(summary),
        )
        save_btn.pack(side="left", padx=10)
        self.save_status_lbl = tk.Label(save_box, text="", font=FONT_SMALL, fg=COLOR_SUCCESS, bg=BG_CARD)
        self.save_status_lbl.pack(side="left", padx=10)

        # Action Buttons
        btn_row = tk.Frame(wrapper, bg=BG_MAIN)
        btn_row.pack(fill="x", pady=15)

        review_btn = tk.Button(
            btn_row,
            text="📜 Review All Answers",
            font=FONT_BOLD,
            bg=BG_CARD,
            fg=COLOR_CYAN,
            activebackground=BG_CARD_HOVER,
            activeforeground=COLOR_CYAN,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=10,
            command=self.show_review_screen,
        )
        review_btn.pack(side="left", padx=8)

        leaderboard_btn = tk.Button(
            btn_row,
            text="🏆 Hall of Fame",
            font=FONT_BOLD,
            bg=BG_CARD,
            fg=COLOR_WARN,
            activebackground=BG_CARD_HOVER,
            activeforeground=COLOR_WARN,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=10,
            command=self.show_high_scores_screen,
        )
        leaderboard_btn.pack(side="left", padx=8)

        replay_btn = tk.Button(
            btn_row,
            text="🔄 Play Again / Change Category",
            font=FONT_BOLD,
            bg=BG_ACCENT,
            fg=TEXT_PRIMARY,
            activebackground=BG_ACCENT_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=self.show_welcome_screen,
        )
        replay_btn.pack(side="right", padx=8)

    def save_score_action(self, summary: dict) -> None:
        name = self.player_name_entry.get().strip() or "Anonymous Player"
        HighScoreManager.save_score(name, summary)
        self.save_status_lbl.config(text=f"✓ Saved for {name}!")

    # -------------------------------------------------------------
    # QUESTION REVIEW SCREEN (SCROLLABLE)
    # -------------------------------------------------------------
    def show_review_screen(self) -> None:
        self.clear_container()

        summary = self.engine.get_summary()

        top_bar = tk.Frame(self.container, bg=BG_CARD)
        top_bar.pack(fill="x", ipady=10, padx=20, pady=10)

        tk.Label(
            top_bar,
            text=f"Answer Review: {summary['category']} ({summary['correct_count']}/{summary['answered_count']} Correct)",
            font=FONT_HEADING,
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
        ).pack(side="left", padx=15)

        back_btn = tk.Button(
            top_bar,
            text="← Back to Scorecard",
            font=FONT_BOLD,
            bg=BG_ACCENT,
            fg=TEXT_PRIMARY,
            activebackground=BG_ACCENT_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
            command=self.show_game_over_screen,
        )
        back_btn.pack(side="right", padx=15)

        canvas = tk.Canvas(self.container, bg=BG_MAIN, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG_MAIN)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=10)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        for idx, rec in enumerate(summary["history"], 1):
            q = rec.question
            card_border = COLOR_SUCCESS if rec.is_correct else COLOR_ERROR
            if rec.selected_letter == "SKIPPED":
                card_border = COLOR_WARN

            item = tk.Frame(
                scrollable_frame,
                bg=BG_CARD,
                bd=1,
                relief="flat",
                highlightbackground=card_border,
                highlightthickness=1,
                width=860,
            )
            item.pack(fill="x", padx=10, pady=6, ipady=8)

            header_row = tk.Frame(item, bg=BG_CARD)
            header_row.pack(fill="x", padx=15, pady=(5, 3))

            status_txt = (
                "✓ CORRECT"
                if rec.is_correct
                else ("⏩ SKIPPED" if rec.selected_letter == "SKIPPED" else "✗ INCORRECT")
            )
            status_fg = (
                COLOR_SUCCESS
                if rec.is_correct
                else (COLOR_WARN if rec.selected_letter == "SKIPPED" else COLOR_ERROR)
            )

            tk.Label(
                header_row,
                text=f"Q{idx}. [{q.difficulty.upper()}]",
                font=FONT_BOLD,
                fg=COLOR_CYAN,
                bg=BG_CARD,
            ).pack(side="left")

            tk.Label(
                header_row,
                text=f"{status_txt} (+{rec.points_earned} pts, {rec.time_taken:.1f}s)",
                font=FONT_BOLD,
                fg=status_fg,
                bg=BG_CARD,
            ).pack(side="right")

            tk.Label(
                item,
                text=q.question,
                font=FONT_BODY,
                fg=TEXT_PRIMARY,
                bg=BG_CARD,
                wraplength=800,
                justify="left",
            ).pack(anchor="w", padx=15, pady=4)

            ans_row = tk.Frame(item, bg=BG_CARD)
            ans_row.pack(fill="x", padx=15, pady=4)

            user_fg = COLOR_SUCCESS if rec.is_correct else COLOR_ERROR
            tk.Label(
                ans_row,
                text=f"Your Answer: [{rec.selected_letter}] {rec.selected_text}",
                font=FONT_SMALL,
                fg=user_fg,
                bg=BG_CARD,
            ).pack(anchor="w")

            if not rec.is_correct:
                tk.Label(
                    ans_row,
                    text=f"Correct Answer: [{q.correct_letter}] {q.correct_answer}",
                    font=FONT_SMALL,
                    fg=COLOR_SUCCESS,
                    bg=BG_CARD,
                ).pack(anchor="w")

    # -------------------------------------------------------------
    # HIGH SCORES / HALL OF FAME SCREEN
    # -------------------------------------------------------------
    def show_high_scores_screen(self) -> None:
        self.clear_container()

        top_bar = tk.Frame(self.container, bg=BG_CARD)
        top_bar.pack(fill="x", ipady=10, padx=20, pady=10)

        tk.Label(
            top_bar,
            text="🏆 HALL OF FAME - TOP TRIVIA MASTERS",
            font=FONT_HEADING,
            fg=COLOR_WARN,
            bg=BG_CARD,
        ).pack(side="left", padx=15)

        back_btn = tk.Button(
            top_bar,
            text="← Main Menu",
            font=FONT_BOLD,
            bg=BG_ACCENT,
            fg=TEXT_PRIMARY,
            activebackground=BG_ACCENT_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
            command=self.show_welcome_screen,
        )
        back_btn.pack(side="right", padx=15)

        content = tk.Frame(self.container, bg=BG_MAIN)
        content.pack(fill="both", expand=True, padx=20, pady=10)

        scores = HighScoreManager.load_scores()
        if not scores:
            tk.Label(
                content,
                text="No records yet! Play a game and register your high score.",
                font=FONT_TITLE,
                fg=TEXT_MUTED,
                bg=BG_MAIN,
            ).pack(pady=50)
            return

        table_card = tk.Frame(
            content,
            bg=BG_CARD,
            bd=1,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        table_card.pack(fill="both", expand=True, padx=10, pady=10)

        headers = ["Rank", "Player", "Category", "Score", "Accuracy", "Correct", "Date"]
        header_frame = tk.Frame(table_card, bg="#182234")
        header_frame.pack(fill="x", ipady=6)

        col_weights = [1, 3, 3, 2, 2, 2, 2]
        for col, h in enumerate(headers):
            header_frame.columnconfigure(col, weight=col_weights[col])
            tk.Label(
                header_frame,
                text=h,
                font=FONT_BOLD,
                fg=COLOR_CYAN,
                bg="#182234",
            ).grid(row=0, column=col, sticky="w", padx=8)

        for i, s in enumerate(scores[:12], 1):
            row_bg = BG_CARD if i % 2 == 0 else "#162030"
            row_frame = tk.Frame(table_card, bg=row_bg)
            row_frame.pack(fill="x", ipady=6)

            for col in range(len(headers)):
                row_frame.columnconfigure(col, weight=col_weights[col])

            medal = "🥇 " if i == 1 else ("🥈 " if i == 2 else ("🥉 " if i == 3 else f"{i}. "))
            name = s.get("name", "Unknown")
            cat_name = s.get("category", "Mathematics").replace("Science: ", "")
            score = f"{s.get('score', 0):,}"
            accuracy = f"{s.get('accuracy', 0)}%"
            correct = f"{s.get('correct', 0)}/{s.get('total', 50)}"
            date = s.get("date", "")

            tk.Label(row_frame, text=medal, font=FONT_BOLD, fg=COLOR_WARN, bg=row_bg).grid(
                row=0, column=0, sticky="w", padx=8
            )
            tk.Label(row_frame, text=name, font=FONT_BOLD, fg=TEXT_PRIMARY, bg=row_bg).grid(
                row=0, column=1, sticky="w", padx=8
            )
            tk.Label(row_frame, text=cat_name, font=FONT_BODY, fg=COLOR_CYAN, bg=row_bg).grid(
                row=0, column=2, sticky="w", padx=8
            )
            tk.Label(row_frame, text=score, font=FONT_BOLD, fg=COLOR_SUCCESS, bg=row_bg).grid(
                row=0, column=3, sticky="w", padx=8
            )
            tk.Label(row_frame, text=accuracy, font=FONT_BODY, fg=COLOR_WARN, bg=row_bg).grid(
                row=0, column=4, sticky="w", padx=8
            )
            tk.Label(row_frame, text=correct, font=FONT_BODY, fg=TEXT_MUTED, bg=row_bg).grid(
                row=0, column=5, sticky="w", padx=8
            )
            tk.Label(row_frame, text=date, font=FONT_SMALL, fg=TEXT_MUTED, bg=row_bg).grid(
                row=0, column=6, sticky="w", padx=8
            )


def start_gui(category: int = DEFAULT_CATEGORY) -> None:
    app = TriviaGUIApp(initial_category=category)
    app.mainloop()


if __name__ == "__main__":
    cat_arg = DEFAULT_CATEGORY
    if len(sys.argv) > 1:
        cat_arg = resolve_category_id(sys.argv[1])
    start_gui(category=cat_arg)
