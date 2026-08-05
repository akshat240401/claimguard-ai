from __future__ import annotations

import numpy as np
import pandas as pd


RULE_WEIGHT = 0.65
MODEL_WEIGHT = 0.35


def _review_category(score: int) -> str:
    if score >= 70:
        return "High-Priority Review"
    if score >= 40:
        return "Review Recommended"
    return "Routine"


def calculate_review_priority(claims: pd.DataFrame) -> pd.DataFrame:
    required = {
        "rule_score",
        "rule_count",
        "model_anomaly_score",
        "model_flag",
    }
    missing = required.difference(claims.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing fields required by the risk engine: {missing_text}")

    result = claims.copy()

    weighted_score = (
        result["rule_score"] * RULE_WEIGHT
        + result["model_anomaly_score"] * MODEL_WEIGHT
    )

    score = np.rint(weighted_score).astype(int)

    any_rule = result["rule_count"] > 0
    high_rule_signal = result["rule_score"] >= 60
    model_only_signal = result["model_flag"] & (
        result["model_anomaly_score"] >= 90
    )
    combined_high_signal = result["model_flag"] & (result["rule_score"] >= 35)

    score = np.where(any_rule | model_only_signal, np.maximum(score, 40), score)
    score = np.where(
        high_rule_signal | combined_high_signal,
        np.maximum(score, 70),
        score,
    )

    result["review_priority_score"] = np.clip(score, 0, 100).astype(int)
    result["review_priority"] = result["review_priority_score"].apply(
        _review_category
    )

    return result