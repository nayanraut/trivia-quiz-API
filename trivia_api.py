"""
Open Trivia Database API Client
Fetches multiple choice questions across categories from opentdb.com
Supports:
  - Science: Mathematics (Category ID: 19)
  - Science: Gadgets (Category ID: 30)
  - Science: Computers (Category ID: 18)
Handles rate-limiting, category-specific caching, and HTML entity unescaping.
"""

import html
import json
import os
import random
import time
from typing import Any, Dict, List, Optional, Union
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://opentdb.com/api.php"

# OpenTDB Response Codes
RC_SUCCESS = 0
RC_NO_RESULTS = 1
RC_INVALID_PARAMETER = 2
RC_TOKEN_NOT_FOUND = 3
RC_TOKEN_EMPTY = 4
RC_RATE_LIMIT = 5

CATEGORIES: Dict[int, Dict[str, Any]] = {
    19: {
        "id": 19,
        "name": "Science: Mathematics",
        "slug": "math",
        "display_name": "Science: Mathematics",
        "icon": "📐",
        "max_questions": 50,
        "description": "Calculus, geometry, algebra, and number theory.",
    },
    30: {
        "id": 30,
        "name": "Science: Gadgets",
        "slug": "gadgets",
        "display_name": "Science: Gadgets",
        "icon": "📱",
        "max_questions": 34,
        "description": "Smartphones, hardware, consumer electronics, and modern tech gadgets.",
    },
    18: {
        "id": 18,
        "name": "Science: Computers",
        "slug": "computers",
        "display_name": "Science: Computers",
        "icon": "💻",
        "max_questions": 50,
        "description": "Programming, operating systems, hardware, networks, and algorithms.",
    },
}

DEFAULT_CATEGORY = 19


def resolve_category_id(identifier: Union[int, str, None]) -> int:
    """Resolves an integer ID or slug/string into a valid category ID."""
    if identifier is None:
        return DEFAULT_CATEGORY
    if isinstance(identifier, int) and identifier in CATEGORIES:
        return identifier

    str_val = str(identifier).strip().lower()
    if str_val.isdigit() and int(str_val) in CATEGORIES:
        return int(str_val)

    for cat_id, info in CATEGORIES.items():
        if str_val in (info["slug"], info["name"].lower(), info["display_name"].lower()):
            return cat_id
        if "gadget" in str_val and cat_id == 30:
            return 30
        if "math" in str_val and cat_id == 19:
            return 19
        if "computer" in str_val and cat_id == 18:
            return 18

    return DEFAULT_CATEGORY


def get_cache_path(category_id: int) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    primary = os.path.join(base_dir, f"questions_cache_{category_id}.json")
    if not os.path.exists(primary) and category_id == 19:
        legacy = os.path.join(base_dir, "questions_cache.json")
        if os.path.exists(legacy):
            return legacy
    return primary


def unescape_question_data(q_data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively or field-wise unescapes HTML entities in question payload."""
    cleaned = dict(q_data)
    cleaned["question"] = html.unescape(q_data.get("question", ""))
    cleaned["correct_answer"] = html.unescape(q_data.get("correct_answer", ""))
    cleaned["incorrect_answers"] = [
        html.unescape(ans) for ans in q_data.get("incorrect_answers", [])
    ]
    cleaned["category"] = html.unescape(q_data.get("category", "Science: Mathematics"))
    cleaned["difficulty"] = q_data.get("difficulty", "medium").lower()
    return cleaned


def save_to_cache(questions: List[Dict[str, Any]], category_id: int) -> None:
    """Saves sanitized questions to local category-specific JSON cache."""
    cache_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), f"questions_cache_{category_id}.json"
    )
    cat_info = CATEGORIES.get(category_id, {"name": f"Category {category_id}"})
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": time.time(),
                    "category_id": category_id,
                    "category_name": cat_info["name"],
                    "count": len(questions),
                    "questions": questions,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
    except Exception as e:
        print(f"[Warning] Failed to write question cache for category {category_id}: {e}")


def load_from_cache(category_id: int) -> List[Dict[str, Any]]:
    """Loads questions from local category cache if available."""
    cache_path = get_cache_path(category_id)
    if not os.path.exists(cache_path):
        return []
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            questions = data.get("questions", [])
            return [unescape_question_data(q) for q in questions]
    except Exception as e:
        print(f"[Warning] Failed to read question cache from {cache_path}: {e}")
        return []


def fetch_questions(
    amount: int = 50,
    category: Union[int, str] = DEFAULT_CATEGORY,
    difficulty: Optional[str] = None,
    force_refresh: bool = False,
    max_retries: int = 3,
) -> List[Dict[str, Any]]:
    """
    Fetches multiple-choice questions from Open Trivia DB for the given category.
    If network is unavailable or rate limited, gracefully falls back to cached questions.
    """
    cat_id = resolve_category_id(category)
    cat_info = CATEGORIES.get(cat_id, CATEGORIES[DEFAULT_CATEGORY])
    target_amount = min(amount, cat_info.get("max_questions", amount))

    # Fast cache retrieval if not forcing a network refresh
    if not force_refresh:
        cached = load_from_cache(cat_id)
        if cached:
            if len(cached) >= target_amount:
                sampled = list(cached)
                random.shuffle(sampled)
                return sampled[:target_amount]
            elif len(cached) >= 10:
                sampled = list(cached)
                random.shuffle(sampled)
                return sampled

    # Query OpenTDB over network
    headers = {"User-Agent": "Python-Trivia-Game/2.0 (opentdb.com client)"}
    candidate_amounts = [target_amount]
    if target_amount > 30:
        candidate_amounts.extend([34, 30, 25, 20, 15, 10])

    last_error: Optional[str] = None

    for amt in candidate_amounts:
        params: Dict[str, Any] = {
            "amount": amt,
            "category": cat_id,
            "type": "multiple",
        }
        if difficulty:
            params["difficulty"] = difficulty.lower()

        url = f"{API_URL}?{urllib.parse.urlencode(params)}"

        for attempt in range(1, max_retries + 1):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                code = payload.get("response_code")
                if code == RC_SUCCESS:
                    raw_results = payload.get("results", [])
                    cleaned_questions = [unescape_question_data(q) for q in raw_results]
                    save_to_cache(cleaned_questions, cat_id)
                    return cleaned_questions

                if code == RC_RATE_LIMIT:
                    last_error = "OpenTDB API rate limit exceeded (1 request per 5 seconds)."
                    time.sleep(5)
                    continue

                if code == RC_NO_RESULTS:
                    last_error = f"API does not have {amt} questions in this category."
                    break  # Try next smaller candidate amount

                last_error = f"API returned response code {code}"

            except urllib.error.URLError as e:
                last_error = f"Network error: {e}"
                time.sleep(2)
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                time.sleep(2)

        # Pause to respect OpenTDB's 5s rate limit before trying next amount
        time.sleep(5.5)

    # Fallback to cache if available
    cached = load_from_cache(cat_id)
    if cached:
        print(f"[Notice] {last_error} Falling back to {len(cached)} cached questions for {cat_info['name']}.")
        random.shuffle(cached)
        return cached[:target_amount]

    raise RuntimeError(
        f"Unable to fetch questions for {cat_info['name']} and no local cache available. Reason: {last_error}"
    )


if __name__ == "__main__":
    print("Testing Open Trivia DB API client with category selection...")
    for c_id, info in CATEGORIES.items():
        qs = fetch_questions(amount=50, category=c_id, force_refresh=False)
        print(f"Loaded {len(qs)} questions for {info['icon']} {info['name']}")
        if qs:
            print(f"  Sample: {qs[0]['question']}")
            print(f"  Answer: {qs[0]['correct_answer']}")
