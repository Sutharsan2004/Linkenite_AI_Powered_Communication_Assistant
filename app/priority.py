from typing import Tuple
import re

URGENT_KEYWORDS = [
    "immediately", "urgent", "asap", "cannot access", "down", "critical", "refund", "403", "error", "latency", "discrepancy"
]

def compute_priority(subject: str, body: str, sentiment_label: str) -> Tuple[str, float]:
    text = f"{subject} {body}".lower()
    score = 0.0
    for kw in URGENT_KEYWORDS:
        if kw in text:
            score += 2.0
    # Penalize positive, boost negative
    if sentiment_label.lower().startswith("neg"):
        score += 1.0
    elif sentiment_label.lower().startswith("pos"):
        score -= 0.5
    # Basic cap/floor
    score = max(score, 0.0)
    label = "Urgent" if score >= 2.0 else "Not urgent"
    return label, score
