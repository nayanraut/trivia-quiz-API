"""
Main entry point for Trivia Master (Open Trivia Database API: https://opentdb.com).
Supports both Modern Desktop GUI and Terminal CLI modes with category selection:
  - Science: Mathematics (Category ID: 19)
  - Science: Gadgets (Category ID: 30)
  - Science: Computers (Category ID: 18)

Usage:
    py main.py                             # Launch desktop GUI
    py main.py --category gadgets          # Launch GUI with Science: Gadgets
    py main.py --cli                       # Launch CLI mode with interactive category picker
    py main.py --cli --category gadgets    # Launch CLI directly in Science: Gadgets
    py main.py --refresh                   # Refresh cached questions from OpenTDB
"""

import argparse
import sys
import tkinter as tk

from cli_game import run_cli_game
from trivia_api import (
    CATEGORIES,
    DEFAULT_CATEGORY,
    fetch_questions,
    resolve_category_id,
)


def check_gui_available() -> bool:
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Trivia Master Quiz Game (Open Trivia Database: https://opentdb.com)"
    )
    parser.add_argument(
        "--category",
        choices=["math", "gadgets", "computers", "19", "30", "18"],
        default=None,
        help="Category: 'math' (Science: Mathematics), 'gadgets' (Science: Gadgets), 'computers' (Science: Computers)",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run game in Terminal CLI mode instead of Desktop GUI",
    )
    parser.add_argument(
        "--mode",
        choices=["marathon", "sprint", "blitz", "survival"],
        default="marathon",
        help="Game mode (marathon=all questions, sprint=25, blitz=10, survival=3 lives)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-fetching questions from Open Trivia DB",
    )

    args = parser.parse_args()

    resolved_cat = resolve_category_id(args.category) if args.category else DEFAULT_CATEGORY

    # Pre-fetch or refresh if requested
    if args.refresh:
        cat_info = CATEGORIES.get(resolved_cat, CATEGORIES[DEFAULT_CATEGORY])
        print(f"Connecting to Open Trivia Database (https://opentdb.com) for {cat_info['display_name']}...")
        try:
            questions = fetch_questions(amount=50, category=resolved_cat, force_refresh=True)
            print(f"Successfully fetched and cached {len(questions)} questions for {cat_info['display_name']}!")
        except Exception as e:
            print(f"Error fetching questions: {e}")
            sys.exit(1)

    # CLI Mode execution
    if args.cli:
        run_cli_game(category=args.category, mode=args.mode, force_refresh=args.refresh)
        return

    # Try GUI mode, fallback to CLI if display/GUI is unavailable
    if check_gui_available():
        from gui_game import start_gui

        start_gui(category=resolved_cat)
    else:
        print("[Notice] Graphical display not available. Falling back to CLI mode...")
        run_cli_game(category=args.category, mode=args.mode, force_refresh=args.refresh)


if __name__ == "__main__":
    main()
