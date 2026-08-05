from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC_FEATURES = [
    "claim_amount",
    "expected_amount",
    "amount_to_expected_ratio",
    "days_since_similar_claim",
    "provider_average_amount",
    "amount_to_provider_average_ratio",
]

CATEGORICAL_FEATURES = [
    "diagnosis_group",
    "procedure_code",
]

MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

EVALUATION_ONLY_COLUMNS = {
    "injected_anomaly",
    "anomaly_type",
    "anomaly_difficulty",
    "case_profile",
}


def validate_model_features(claims: pd.DataFrame) -> None:
    missing = set(MODEL_FEATURES).difference(claims.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing model features: {missing_text}")

    leaked = EVALUATION_ONLY_COLUMNS.intersection(MODEL_FEATURES)
    if leaked:
        leaked_text = ", ".join(sorted(leaked))
        raise RuntimeError(f"Evaluation labels cannot be model features: {leaked_text}")


def build_anomaly_pipeline(
    contamination: float = 0.10,
    random_state: int = 42,
) -> Pipeline:
    if not 0.0 < contamination <= 0.30:
        raise ValueError("contamination must be greater than 0 and at most 0.30")

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def score_anomalies(
    claims: pd.DataFrame,
    contamination: float = 0.10,
    random_state: int = 42,
) -> pd.DataFrame:
    validate_model_features(claims)

    result = claims.copy()
    model_input = result[MODEL_FEATURES].copy()

    pipeline = build_anomaly_pipeline(
        contamination=contamination,
        random_state=random_state,
    )
    pipeline.fit(model_input)

    predictions = pipeline.predict(model_input)
    raw_scores = -pipeline.score_samples(model_input)

    percentile_scores = (
        pd.Series(raw_scores, index=result.index)
        .rank(method="average", pct=True)
        .mul(100)
    )

    result["model_anomaly_score"] = percentile_scores.round(2)
    result["model_flag"] = predictions == -1

    return result