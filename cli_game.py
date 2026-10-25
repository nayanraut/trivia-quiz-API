"""
Command Line Interface (CLI) for Open Trivia Database Quiz Game.
Offers rich ANSI-colored menus, category selection, progress bars, streaks, lifelines, and reviews.
Supports:
  - Science: Mathematics (Category ID: 19)
  - Science: Gadgets (Category ID: 30)
  - Science: Computers (Category ID: 18)
"""

import os
import sys
import textwrap
import time
from typing import Optional, Union

from game_engine import GameEngine, HighScoreManager, PreparedQuestion
from trivia_api import (
    CATEGORIES,
    DEFAULT_CATEGORY,
    fetch_questions,
    resolve_category_id,
)

# Reconfigure stdout to UTF-8 on Windows
if sys.platform == "win32":
    os.system("")
    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

# ANSI Color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Foreground colors
FG_BLACK = "\033[30m"
FG_RED = "\033[91m"
FG_GREEN = "\033[92m"
FG_YELLOW = "\033[93m"
FG_BLUE = "\033[94m"
FG_MAGENTA = "\033[95m"
FG_CYAN = "\033[96m"
FG_WHITE = "\033[97m"


def clear_screen() -> None:
    os.system("cls" if sys.platform == "win32" else "clear")


def print_banner(category_name: str = "Science: Mathematics") -> None:
    banner = rf"""{FG_CYAN}{BOLD}
========================================================================
  _______ _____  _______      _______             __  __           _            
 |__   __|  __ \|_   _\ \    / /_   _|   /\      |  \/  |         | |           
    | |  | |__) | | |  \ \  / /  | |    /  \     | \  / | __ _ ___| |_ ___ _ __ 
    | |  |  _  /  | |   \ \/ /   | |   / /\ \    | |\/| |/ _` / __| __/ _ \ '__|
    | |  | | \ \ _| |_   \  /   _| |_ / ____ \   | |  | | (_| \__ \ ||  __/ |   
    |_|  |_|  \_\_____|   \/   |_____/_/    \_\  |_|  |_|\__,_|___/\__\___|_|   
                                                                                
      Powered by Open Trivia Database (https://opentdb.com)
      Category: {category_name}
========================================================================{RESET}"""
    print(banner)


def choose_category_interactive() -> int:
    clear_screen()
    print_banner("Category Selection")
    print(f"\n{BOLD}{FG_YELLOW}SELECT A QUIZ CATEGORY:{RESET}\n")

    cat_list = list(CATEGORIES.values())
    for idx, info in enumerate(cat_list, start=1):
        print(
            f"  {FG_CYAN}[{idx}]{RESET} {BOLD}{info['icon']} {info['display_name']}{RESET}"
        )
        print(f"      {DIM}{info['description']} (Up to {info['max_questions']} MCQs){RESET}\n")

    while True:
        try:
            choice = input(f"{BOLD}Enter choice [1-{len(cat_list)}] (default 1): {RESET}").strip()
            if not choice:
                return cat_list[0]["id"]
            if choice.isdigit() and 1 <= int(choice) <= len(cat_list):
                return cat_list[int(choice) - 1]["id"]
            print(f"{FG_RED}Invalid choice. Enter a number between 1 and {len(cat_list)}.{RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\nDefaulting to Science: Mathematics...")
            return DEFAULT_CATEGORY


def format_difficulty(diff: str) -> str:
    diff_lower = diff.lower()
    if diff_lower == "easy":
        return f"{FG_GREEN}{BOLD}[ EASY +100 ]{RESET}"
    if diff_lower == "medium":
        return f"{FG_YELLOW}{BOLD}[ MEDIUM +200 ]{RESET}"
    return f"{FG_RED}{BOLD}[ HARD +300 ]{RESET}"


def display_status_bar(engine: GameEngine, cat_info: dict) -> None:
    curr_q = engine.current_index + 1
    total_q = engine.total_questions

    bar_width = 20
    progress = int((curr_q - 1) / total_q * bar_width) if total_q > 0 else 0
    bar = f"{FG_GREEN}{'=' * progress}{FG_BLACK}{'-' * (bar_width - progress)}{RESET}"

    streak_badge = ""
    if engine.streak >= 3:
        mult = engine.get_streak_multiplier()
        streak_badge = f" | {FG_RED}{BOLD}🔥 Streak: {engine.streak} ({mult}x){RESET}"
    elif engine.streak > 0:
        streak_badge = f" | Streak: {engine.streak}"

    lives_badge = ""
    if engine.mode == "survival" and engine.lives is not None:
        hearts = "❤️ " * engine.lives
        lives_badge = f" | Lives: {hearts}"

    cat_label = f"{cat_info['icon']} {cat_info['display_name'].replace('Science: ', '')}"

    print(
        f"{FG_BLUE}[{cat_label} | Q {curr_q}/{total_q}]{RESET} [{bar}] {BOLD}Score: {engine.score}{RESET}{streak_badge}{lives_badge}"
    )
    print(f"{DIM}{'-' * 74}{RESET}")


def display_question(q: PreparedQuestion, engine: GameEngine) -> None:
    diff_badge = format_difficulty(q.difficulty)
    print(f"\n{diff_badge} {FG_CYAN}{BOLD}Question {q.index}:{RESET}")

    wrapped_question = textwrap.fill(
        q.question, width=70, initial_indent="  ", subsequent_indent="  "
    )
    print(f"{BOLD}{wrapped_question}{RESET}\n")

    letters = ["A", "B", "C", "D"]
    for ltr in letters:
        text = q.options.get(ltr, "")
        if ltr in q.disabled_options:
            print(f"  {DIM}[{ltr}] ~~~ (Eliminated by 50/50) ~~~{RESET}")
        else:
            print(f"  {FG_YELLOW}{BOLD}[{ltr}]{RESET} {text}")
    print()

    lifelines_available = []
    if engine.lifelines.get("50_50", False):
        lifelines_available.append(f"{FG_CYAN}[5] 50/50{RESET}")
    if engine.lifelines.get("skip", False):
        lifelines_available.append(f"{FG_CYAN}[S] Skip{RESET}")

    lifeline_str = (
        " | ".join(lifelines_available) if lifelines_available else f"{DIM}None remaining{RESET}"
    )
    print(f"{DIM}Lifelines Available: {lifeline_str}{RESET}")
    print(f"{DIM}{'-' * 74}{RESET}")


def get_player_input(engine: GameEngine) -> str:
    valid_choices = {"A", "B", "C", "D", "Q"}
    if engine.lifelines.get("50_50", False):
        valid_choices.add("5")
    if engine.lifelines.get("skip", False):
        valid_choices.add("S")

    while True:
        try:
            choice = input(f"{BOLD}Your Answer (A-D) or Option: {RESET}").strip().upper()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting quiz...")
            return "Q"

        if choice in valid_choices:
            curr_q = engine.get_current_question()
            if curr_q and choice in curr_q.disabled_options:
                print(f"{FG_RED}Option [{choice}] has been eliminated! Pick an active option.{RESET}")
                continue
            return choice

        print(
            f"{FG_RED}Invalid choice. Enter A, B, C, D (or 5 for 50/50, S for Skip, Q to Quit){RESET}"
        )


def show_summary(summary: dict) -> None:
    print(f"\n{FG_CYAN}{BOLD}" + "=" * 74)
    print(f"               QUIZ COMPLETED! SCORECARD ({summary['category']})")
    print("=" * 74 + f"{RESET}\n")

    print(f"  {BOLD}Category:{RESET}          {FG_CYAN}{BOLD}{summary['category']}{RESET}")
    print(f"  {BOLD}Player Rank:{RESET}       {FG_YELLOW}{BOLD}{summary['rank']}{RESET}")
    print(f"  {BOLD}Final Score:{RESET}       {FG_GREEN}{BOLD}{summary['score']} points{RESET}")
    print(
        f"  {BOLD}Accuracy:{RESET}          {summary['accuracy_percent']}% ({summary['correct_count']}/{summary['answered_count']} correct)"
    )
    print(f"  {BOLD}Max Streak:{RESET}        {summary['max_streak']} in a row 🔥")
    print(f"  {BOLD}Total Time:{RESET}        {summary['total_time_seconds']} seconds")
    print(f"  {BOLD}Avg Time/Q:{RESET}        {summary['avg_time_per_question']} seconds")
    print()

    diff = summary["difficulty_stats"]
    print(f"  {BOLD}Difficulty Breakdown:{RESET}")
    print(f"    - Easy:   {diff['easy'][0]}/{diff['easy'][1]} correct")
    print(f"    - Medium: {diff['medium'][0]}/{diff['medium'][1]} correct")
    print(f"    - Hard:   {diff['hard'][0]}/{diff['hard'][1]} correct")
    print(f"\n{DIM}" + "-" * 74 + f"{RESET}")


def review_answers(history: list) -> None:
    print(
        f"\n{FG_CYAN}{BOLD}=================== FULL QUESTION & ANSWER REVIEW ==================={RESET}"
    )
    for idx, rec in enumerate(history, 1):
        q = rec.question
        status = (
            f"{FG_GREEN}CORRECT (+{rec.points_earned} pts){RESET}"
            if rec.is_correct
            else f"{FG_RED}WRONG{RESET}"
        )
        if rec.selected_letter == "SKIPPED":
            status = f"{FG_YELLOW}SKIPPED{RESET}"

        print(f"\n{BOLD}Q{idx} [{q.difficulty.upper()}]: {q.question}{RESET}")
        print(f"   Status: {status} | Time: {rec.time_taken:.1f}s")
        print(f"   Your Answer:    [{rec.selected_letter}] {rec.selected_text}")
        print(f"   {FG_GREEN}Correct Answer: [{q.correct_letter}] {q.correct_answer}{RESET}")
        print(f"{DIM}{'-' * 72}{RESET}")


def show_high_scores() -> None:
    scores = HighScoreManager.load_scores()
    print(
        f"\n{FG_CYAN}{BOLD}========================== HALL OF FAME =========================={RESET}"
    )
    if not scores:
        print("  No scores recorded yet. Be the first to set a record!\n")
        return

    print(
        f"{'#':<3} {'Player':<16} {'Category':<18} {'Score':<8} {'Accuracy':<10} {'Date':<14}"
    )
    print("-" * 74)
    for i, s in enumerate(scores[:10], 1):
        name = s.get("name", "Unknown")[:15]
        cat = s.get("category", "Mathematics").replace("Science: ", "")[:16]
        score = f"{s.get('score', 0):,}"
        acc = f"{s.get('accuracy', 0)}%"
        date = s.get("date", "")
        print(f"{i:<3} {name:<16} {cat:<18} {score:<8} {acc:<10} {date:<14}")
    print("-" * 74 + "\n")


def run_cli_game(
    category: Optional[Union[int, str]] = None,
    mode: str = "marathon",
    force_refresh: bool = False,
    allow_review: bool = True,
) -> None:
    # If category not specified via CLI flag, let user choose interactively
    if category is None:
        cat_id = choose_category_interactive()
    else:
        cat_id = resolve_category_id(category)

    cat_info = CATEGORIES.get(cat_id, CATEGORIES[DEFAULT_CATEGORY])

    clear_screen()
    print_banner(cat_info["display_name"])

    print(f"{FG_YELLOW}Loading questions for {cat_info['display_name']} from OpenTDB...{RESET}")
    try:
        raw_questions = fetch_questions(amount=50, category=cat_id, force_refresh=force_refresh)
    except Exception as e:
        print(f"{FG_RED}Error loading questions: {e}{RESET}")
        return

    engine = GameEngine(raw_questions, category_name=cat_info["display_name"], mode=mode)
    print(
        f"{FG_GREEN}Loaded {engine.total_questions} questions for mode '{mode.upper()}'. Starting quiz!{RESET}\n"
    )
    time.sleep(1.2)

    while not engine.game_over:
        clear_screen()
        print_banner(cat_info["display_name"])
        display_status_bar(engine, cat_info)

        curr_q = engine.get_current_question()
        if not curr_q:
            break

        engine.start_question_timer()
        display_question(curr_q, engine)

        choice = get_player_input(engine)

        if choice == "Q":
            print(f"\n{FG_YELLOW}Quiz quit by player.{RESET}")
            break
        elif choice == "5":
            if engine.use_fifty_fifty():
                print(f"{FG_CYAN}⚡ 50/50 Lifeline Activated! Two incorrect options removed.{RESET}")
                time.sleep(1)
            continue
        elif choice == "S":
            if engine.use_skip():
                print(f"{FG_YELLOW}⏩ Question skipped! Moving to next question.{RESET}")
                time.sleep(1.2)
            continue
        else:
            result = engine.submit_answer(choice)
            if result.is_correct:
                mult_txt = (
                    f" (x{engine.get_streak_multiplier()} Multiplier)"
                    if engine.streak >= 3
                    else ""
                )
                print(
                    f"\n{FG_GREEN}{BOLD}✓ CORRECT! +{result.points_earned} points!{mult_txt}{RESET}"
                )
            else:
                print(
                    f"\n{FG_RED}{BOLD}✗ INCORRECT!{RESET} Correct was: {FG_GREEN}{BOLD}[{curr_q.correct_letter}] {curr_q.correct_answer}{RESET}"
                )
                if engine.mode == "survival":
                    print(f"{FG_RED}Lives remaining: {engine.lives}{RESET}")
            time.sleep(1.5)

    # Game Over Summary
    summary = engine.get_summary()
    clear_screen()
    print_banner(cat_info["display_name"])
    show_summary(summary)

    try:
        player_name = input(
            f"{BOLD}Enter your name for the Hall of Fame (or Enter to skip): {RESET}"
        ).strip()
        if player_name:
            HighScoreManager.save_score(player_name, summary)
            print(f"{FG_GREEN}Score saved!{RESET}")
    except (KeyboardInterrupt, EOFError):
        pass

    show_high_scores()

    if allow_review and summary["answered_count"] > 0:
        try:
            rev = (
                input(f"{BOLD}Would you like to review all answered questions? (y/N): {RESET}")
                .strip()
                .lower()
            )
            if rev == "y":
                review_answers(summary["history"])
        except (KeyboardInterrupt, EOFError):
            pass

    print(f"\n{FG_CYAN}Thanks for playing! Have a great day!{RESET}\n")


if __name__ == "__main__":
    cat_arg = None
    mode_arg = "marathon"
    if len(sys.argv) > 1:
        cat_arg = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2].lower() in ["marathon", "sprint", "blitz", "survival"]:
        mode_arg = sys.argv[2].lower()
    run_cli_game(category=cat_arg, mode=mode_arg)
