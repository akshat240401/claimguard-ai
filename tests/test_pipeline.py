from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandas.testing as pdt
import pytest

from src.anomaly_detector import EVALUATION_ONLY_COLUMNS, MODEL_FEATURES
from src.claim_rules import apply_claim_rules
from src.pipeline import add_derived_features, run_pipeline, validate_input


DATA_PATH = Path("data/synthetic_claims.csv")


@pytest.fixture(scope="module")
def claims() -> pd.DataFrame:
    if not DATA_PATH.exists():
        pytest.fail(
            "data/synthetic_claims.csv is missing. Run "
            "`python src/data_generator.py` first."
        )
    return pd.read_csv(DATA_PATH)


@pytest.fixture(scope="module")
def scored_claims(claims: pd.DataFrame) -> pd.DataFrame:
    return run_pipeline(claims, contamination=0.10, random_state=42)


def test_dataset_contains_realistic_evaluation_cases(
    claims: pd.DataFrame,
) -> None:
    assert len(claims) == 1000
    assert int(claims["injected_anomaly"].sum()) == 100
    assert (claims["anomaly_difficulty"] == "clear").sum() == 50
    assert (claims["anomaly_difficulty"] == "subtle").sum() == 50
    assert claims["case_profile"].str.startswith("routine_").sum() == 900
    assert (claims["case_profile"] != "routine_standard").sum() == 130


def test_pipeline_scores_every_claim(
    claims: pd.DataFrame,
    scored_claims: pd.DataFrame,
) -> None:
    expected_columns = {
        "rule_score",
        "triggered_rules",
        "model_anomaly_score",
        "model_flag",
        "review_priority_score",
        "review_priority",
        "explanation",
        "recommended_action",
    }

    assert len(scored_claims) == len(claims)
    assert expected_columns.issubset(scored_claims.columns)
    assert scored_claims[list(expected_columns)].isna().sum().sum() == 0


def test_scores_and_categories_are_valid(
    scored_claims: pd.DataFrame,
) -> None:
    assert scored_claims["rule_score"].between(0, 100).all()
    assert scored_claims["model_anomaly_score"].between(0, 100).all()
    assert scored_claims["review_priority_score"].between(0, 100).all()

    routine = scored_claims["review_priority_score"] < 40
    review = scored_claims["review_priority_score"].between(40, 69)
    high = scored_claims["review_priority_score"] >= 70

    assert (scored_claims.loc[routine, "review_priority"] == "Routine").all()
    assert (
        scored_claims.loc[review, "review_priority"]
        == "Review Recommended"
    ).all()
    assert (
        scored_claims.loc[high, "review_priority"]
        == "High-Priority Review"
    ).all()


def test_evaluation_labels_are_not_model_features() -> None:
    assert not EVALUATION_ONLY_COLUMNS.intersection(MODEL_FEATURES)


def test_pipeline_is_repeatable(claims: pd.DataFrame) -> None:
    first = run_pipeline(claims, contamination=0.10, random_state=42)
    second = run_pipeline(claims, contamination=0.10, random_state=42)

    columns = [
        "rule_score",
        "triggered_rules",
        "model_anomaly_score",
        "model_flag",
        "review_priority_score",
        "review_priority",
    ]

    pdt.assert_frame_equal(first[columns], second[columns])


def test_model_can_surface_claims_without_rule_matches(
    scored_claims: pd.DataFrame,
) -> None:
    model_only = (
        (scored_claims["rule_count"] == 0)
        & scored_claims["model_flag"]
        & (scored_claims["review_priority"] != "Routine")
    )
    assert model_only.any()


def test_evaluation_includes_tradeoffs(
    scored_claims: pd.DataFrame,
) -> None:
    injected = scored_claims["injected_anomaly"].astype(bool)
    surfaced = scored_claims["review_priority"] != "Routine"

    detected = int((injected & surfaced).sum())
    routine_surfaced = int((~injected & surfaced).sum())

    assert 0 < detected < int(injected.sum())
    assert routine_surfaced > 0

    clear = scored_claims["anomaly_difficulty"] == "clear"
    subtle = scored_claims["anomaly_difficulty"] == "subtle"

    assert (surfaced & clear).sum() == clear.sum()
    assert 0 < (surfaced & subtle).sum() < subtle.sum()


def test_high_amount_rule_triggers(claims: pd.DataFrame) -> None:
    derived = add_derived_features(claims)
    ruled = apply_claim_rules(derived)

    expected = ruled["amount_to_expected_ratio"] >= 3.0
    triggered = ruled["triggered_rules"].str.contains(
        "high_claim_amount",
        regex=False,
    )

    assert (triggered == expected).all()


def test_diagnosis_mismatch_rule_triggers(claims: pd.DataFrame) -> None:
    derived = add_derived_features(claims)
    ruled = apply_claim_rules(derived)

    mismatches = ruled["anomaly_type"] == "diagnosis_procedure_mismatch"
    assert mismatches.any()
    assert ruled.loc[mismatches, "triggered_rules"].str.contains(
        "diagnosis_procedure_mismatch",
        regex=False,
    ).all()


def test_missing_required_column_raises(claims: pd.DataFrame) -> None:
    incomplete = claims.drop(columns=["claim_amount"])

    with pytest.raises(ValueError, match="claim_amount"):
        validate_input(incomplete)