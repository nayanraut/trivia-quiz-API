# ⚡ Trivia Master: Science & Gadgets

A feature-rich Quiz game in Python powered by the **[Open Trivia Database (OpenTDB)](https://opentdb.com)** API.

Now includes **Interactive Category Selection** with:
- 📱 **Science: Gadgets** (Category ID: `30` — Smartphones, tech hardware, consumer electronics)
- 📐 **Science: Mathematics** (Category ID: `19` — Calculus, algebra, geometry, number theory)
- 💻 **Science: Computers** (Category ID: `18` — Operating systems, coding, hardware, computing history)

Includes both a **Modern Desktop GUI** (Tkinter) and an **ANSI-colored Terminal CLI**.

---

## ✨ Features

- **Category Selection**: Choose between **Science: Gadgets** and **Science: Mathematics** anytime from the main menu or CLI command line.
- **Multiple Choice Format**: Every question offers 4 choices with 1 correct answer.
- **Zero External Dependencies**: Built 100% on Python's standard library (`urllib`, `json`, `html`, `tkinter`, `dataclasses`). Works out-of-the-box on Python 3.8+!
- **Dual User Interface**:
  - 🖥️ **Modern Desktop GUI**: Sleek dark-mode interface with card layouts, responsive countdown timer bar, progress indicator, and instant visual feedback.
  - 💻 **Terminal CLI**: Rich ANSI colored terminal interface with progress meters, ASCII banners, and keyboard controls.
- **HTML Entity Decoding**: Properly unescapes mathematical symbols (e.g., $\pi$, $\times$, $\sqrt{}$) and technical quotes.
- **Offline Resilient Caching**: Caches each category separately (`questions_cache_30.json`, `questions_cache_19.json`). If OpenTDB rate-limits or the network drops, gameplay continues seamlessly without interruption.
- **Power-Ups & Lifelines**:
  - ⚡ **50 / 50**: Eliminates two incorrect choices, leaving only the right answer and one distracter.
  - ⏩ **Skip**: Skips a question without breaking your active streak or deducting points.
- **Dynamic Scoring & Streaks**:
  - Point scaling by difficulty: **Easy (+100)**, **Medium (+200)**, **Hard (+300)**.
  - Consecutive streak multipliers: **1.5x** (3+ streak), **2.0x** (5+ streak), **3.0x** (8+ streak).
  - Speed bonus points for quick answers under the 25-second timer.
- **4 Game Modes**:
  1. 🏃 **Full Marathon**: Play all available questions in the category.
  2. ⚡ **Sprint Mode**: Quick 25-question session.
  3. 🎯 **Quick Blitz**: 10-question warm-up.
  4. 💀 **Sudden Death Survival**: 3 lives — game ends when you make 3 mistakes!
- **Scorecard & Hall of Fame**:
  - Performance analytics (Accuracy %, Average Time per Question, Difficulty breakdown).
  - Title & rank achievement based on performance.
  - Persistent High Score Leaderboard stored in `highscores.json`.
  - Full Question Review: Inspect your choices vs. the correct answers after each game.

---

## 🚀 Quick Start

### 1. Launch via Windows Batch File
Double click `run.bat` or run in terminal:
```cmd
.\run.bat
```

### 2. Launch Desktop GUI (Default)
```bash
py main.py
```
*(You can select **Science: Gadgets** or **Science: Mathematics** directly in the GUI!)*

Or launch directly into Science: Gadgets:
```bash
py main.py --category gadgets
```

### 3. Launch Terminal CLI
```bash
# Interactive category picker:
py main.py --cli

# Directly play Science: Gadgets:
py main.py --cli --category gadgets

# Directly play Science: Mathematics:
py main.py --cli --category math

# Sudden Death Survival in Gadgets:
py main.py --cli --category gadgets --mode survival
```

### 4. Refresh Questions from OpenTDB
```bash
py main.py --refresh --category gadgets
py main.py --refresh --category math
```

---

## 📁 Project Architecture

```
Trivia/
│
├── main.py                 # Main entry point with CLI/GUI & category routing
├── gui_game.py             # Tkinter Modern Dark Mode Desktop Application
├── cli_game.py             # ANSI-colored interactive terminal game
├── game_engine.py          # Game logic, state management, scoring, streaks, lifelines
├── trivia_api.py           # OpenTDB REST client, category routing, retry & cache management
├── questions_cache_30.json # Offline cache for Science: Gadgets
├── questions_cache_19.json # Offline cache for Science: Mathematics
├── highscores.json         # Persistent leaderboard data
├── run.bat                 # Windows double-click launcher
├── test_game.py            # Automated unit test suite (11 tests)
├── requirements.txt        # Standard library dependencies note
└── README.md               # Documentation
```
