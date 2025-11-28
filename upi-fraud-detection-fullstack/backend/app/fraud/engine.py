from typing import Dict

RULES = [
    (lambda tx: tx.get("amount", 0) > 50000, 0.9, "High amount > 50k"),
    (lambda tx: tx.get("channel") == "QR" and tx.get("amount", 0) > 10000, 0.7, "QR high amount"),
    (lambda tx: tx.get("merchant_category") == "UNKNOWN", 0.6, "Unknown merchant category"),
    (lambda tx: tx.get("user_tx_last_hour", 0) > 20, 0.8, "Burst transactions"),
]

FEATURES = [
    "amount",
    "hour",
    "day_of_week",
    "merchant_category",
    "channel",
    "user_tx_last_hour",
    "merchant_tx_last_hour",
]


def rule_score(tx: Dict) -> float:
    score = 0.0
    for pred, weight, _ in RULES:
        if pred(tx):
            score += weight
    return min(score, 1.0)


def level_from_score(s: float) -> str:
    if s >= 0.75:
        return "HIGH"
    if s >= 0.4:
        return "MEDIUM"
    return "LOW"
