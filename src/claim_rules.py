from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


DIAGNOSIS_PROCEDURES = {
    "respiratory": {"P100", "P101", "P102"},
    "musculoskeletal": {"P200", "P201", "P202"},
    "cardiovascular": {"P300", "P301", "P302"},
    "digestive": {"P400", "P401", "P402"},
    "endocrine": {"P500", "P501", "P502"},
}

RULE_WEIGHTS = {
    "high_claim_amount": 45,
    "possible_duplicate": 45,
    "frequent_repeat_service": 35,
    "provider_billing_outlier": 40,
    "diagnosis_procedure_mismatch": 35,
}

REQUIRED_COLUMNS = {
    "diagnosis_group",
    "procedure_code",
    "claim_amount",
    "expected_amount",
    "days_since_similar_claim",
    "provider_average_amount",
}


def _validate_columns(columns: Iterable[str]) -> None:
    missing = REQUIRED_COLUMNS.difference(columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing columns required by the rule engine: {missing_text}")


def _is_diagnosis_procedure_mismatch(
    diagnosis_group: str,
    procedure_code: str,
) -> bool:
    valid_procedures = DIAGNOSIS_PROCEDURES.get(str(diagnosis_group), set())
    return str(procedure_code) not in valid_procedures


def evaluate_claim_rules(claim: pd.Series) -> list[str]:
    triggered: list[str] = []

    amount_to_expected = float(claim["amount_to_expected_ratio"])
    amount_to_provider = float(claim["amount_to_provider_average_ratio"])
    days_since_similar = int(claim["days_since_similar_claim"])

    if amount_to_expected >= 3.0:
        triggered.append("high_claim_amount")

    if days_since_similar <= 2:
        triggered.append("possible_duplicate")
    elif days_since_similar <= 7:
        triggered.append("frequent_repeat_service")

    if amount_to_provider >= 2.2:
        triggered.append("provider_billing_outlier")

    if _is_diagnosis_procedure_mismatch(
        str(claim["diagnosis_group"]),
        str(claim["procedure_code"]),
    ):
        triggered.append("diagnosis_procedure_mismatch")

    return triggered


def apply_claim_rules(claims: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(claims.columns)

    result = claims.copy()

    if "amount_to_expected_ratio" not in result.columns:
        result["amount_to_expected_ratio"] = (
            result["claim_amount"] / result["expected_amount"]
        )

    if "amount_to_provider_average_ratio" not in result.columns:
        result["amount_to_provider_average_ratio"] = (
            result["claim_amount"] / result["provider_average_amount"]
        )

    triggered_rules = result.apply(evaluate_claim_rules, axis=1)
    result["triggered_rules"] = triggered_rules.apply("|".join)
    result["rule_count"] = triggered_rules.apply(len)
    result["rule_score"] = triggered_rules.apply(
        lambda rules: min(sum(RULE_WEIGHTS[rule] for rule in rules), 100)
    )

    return result