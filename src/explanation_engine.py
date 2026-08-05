from __future__ import annotations

import pandas as pd


RULE_EXPLANATIONS = {
    "high_claim_amount": (
        "The claim amount is at least three times the expected amount."
    ),
    "possible_duplicate": (
        "A similar service appears within two days, which may warrant a duplicate check."
    ),
    "frequent_repeat_service": (
        "A similar service appears within seven days, indicating an unusually short repeat interval."
    ),
    "provider_billing_outlier": (
        "The claim amount is substantially above the provider's expected billing pattern."
    ),
    "diagnosis_procedure_mismatch": (
        "The diagnosis and procedure combination does not match the simplified prototype mapping."
    ),
}


def _split_rules(value: object) -> list[str]:
    if not value or pd.isna(value):
        return []
    return [rule for rule in str(value).split("|") if rule]


def build_explanation(claim: pd.Series) -> str:
    rules = _split_rules(claim["triggered_rules"])
    parts = [RULE_EXPLANATIONS[rule] for rule in rules]

    if bool(claim["model_flag"]):
        parts.append(
            "The anomaly model also identified an unusual combination of claim features."
        )

    if not parts:
        return (
            "No configured rule was triggered, and the anomaly model did not "
            "identify the claim as an outlier."
        )

    return " ".join(parts)


def recommend_action(claim: pd.Series) -> str:
    priority = str(claim["review_priority"])
    rules = set(_split_rules(claim["triggered_rules"]))

    if priority == "Routine":
        return "Continue routine processing under normal review procedures."

    if "possible_duplicate" in rules:
        return "Compare the claim with recent submissions and verify supporting documentation."

    if "diagnosis_procedure_mismatch" in rules:
        return "Review the coding relationship and verify the submitted documentation."

    if priority == "High-Priority Review":
        return "Prioritize manual review and verify the claim details before payment."

    return "Review the claim details and supporting documentation before payment."


def add_explanations(claims: pd.DataFrame) -> pd.DataFrame:
    required = {
        "triggered_rules",
        "model_flag",
        "review_priority",
    }
    missing = required.difference(claims.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(
            f"Missing fields required by the explanation engine: {missing_text}"
        )

    result = claims.copy()
    result["explanation"] = result.apply(build_explanation, axis=1)
    result["recommended_action"] = result.apply(recommend_action, axis=1)

    return result