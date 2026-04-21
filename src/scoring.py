import re
import difflib


def score_message(message_text, questions):
    """
    Score a geocacher's free-text message against a list of expected answers.
    Returns None if no questions are defined.
    Each question can optionally have a numeric tolerance.
    """
    if not questions or not message_text:
        return None

    msg_lower = message_text.lower()
    rows = []

    for q in questions:
        expected = q.get("answer", "").strip()
        tolerance = q.get("tolerance")
        s = _score_one(msg_lower, expected.lower(), tolerance)
        rows.append({
            "question": q.get("question", ""),
            "expected": expected,
            "score": round(s, 2),
            "label": "correct" if s >= 0.75 else ("partial" if s >= 0.35 else "wrong"),
        })

    avg = sum(r["score"] for r in rows) / len(rows)
    return {
        "questions": rows,
        "total": round(avg * 10, 1),
    }


def _score_one(msg_lower, expected_lower, tolerance=None):
    if not expected_lower:
        return 0.0

    # ── Numerical answer with tolerance ──────────────────────────────
    if tolerance is not None:
        try:
            expected_num = float(re.sub(r"[^\d.]", "", expected_lower))
            for raw in re.findall(r"\d+(?:[.,]\d+)?", msg_lower):
                try:
                    if abs(float(raw.replace(",", ".")) - expected_num) <= float(tolerance):
                        return 1.0
                except ValueError:
                    pass
            return 0.0
        except ValueError:
            pass

    # ── Exact substring ───────────────────────────────────────────────
    if expected_lower in msg_lower:
        return 1.0

    # ── Keyword matching ──────────────────────────────────────────────
    keywords = [w for w in re.split(r"\W+", expected_lower) if len(w) > 2]
    if keywords:
        hits = sum(1 for k in keywords if k in msg_lower)
        keyword_ratio = hits / len(keywords)
        if keyword_ratio > 0:
            return keyword_ratio

    # ── Fuzzy fallback (dampened) ─────────────────────────────────────
    ratio = difflib.SequenceMatcher(None, expected_lower, msg_lower[:400]).ratio()
    return ratio * 0.5
