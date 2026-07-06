import re
import unicodedata
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz, process
except Exception:
    fuzz = None
    process = None


def clean_text(text: str) -> str:
    text = str(text or "").lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )
    text = text.replace("-", " ")
    text = text.replace("_", " ")
    text = text.replace("'", " ")
    text = re.sub(r"[^a-z0-9+ ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compact_text(text: str) -> str:
    return clean_text(text).replace(" ", "")


def fallback_score(query: str, choice: str) -> int:
    query_clean = clean_text(query)
    choice_clean = clean_text(choice)

    if not query_clean or not choice_clean:
        return 0

    ratio = SequenceMatcher(None, query_clean, choice_clean).ratio() * 100
    partial = 0

    if query_clean in choice_clean or choice_clean in query_clean:
        partial = 90

    query_compact = query_clean.replace(" ", "")
    choice_compact = choice_clean.replace(" ", "")

    compact_ratio = SequenceMatcher(None, query_compact, choice_compact).ratio() * 100

    return int(max(ratio, partial, compact_ratio))


def score(query: str, choice: str) -> int:
    query_clean = clean_text(query)
    choice_clean = clean_text(choice)

    if not query_clean or not choice_clean:
        return 0

    if fuzz:
        return int(max(
            fuzz.ratio(query_clean, choice_clean),
            fuzz.partial_ratio(query_clean, choice_clean),
            fuzz.token_sort_ratio(query_clean, choice_clean),
            fuzz.WRatio(query_clean, choice_clean),
        ))

    return fallback_score(query_clean, choice_clean)


def best_match(query: str, candidates, threshold: int = 78):
    query_clean = clean_text(query)

    if not query_clean:
        return None

    best_item = None
    best_score = 0

    for candidate in candidates:
        if isinstance(candidate, dict):
            value = candidate.get("alias_clean") or candidate.get("alias") or candidate.get("name") or candidate.get("label")
        else:
            value = str(candidate)

        candidate_score = score(query_clean, value)

        if candidate_score > best_score:
            best_score = candidate_score
            best_item = candidate

    if best_item is None:
        return None

    if best_score < threshold:
        return None

    return {
        "item": best_item,
        "score": best_score,
        "query": query_clean,
    }
