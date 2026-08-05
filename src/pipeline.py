from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .anomaly_detector import score_anomalies
from .claim_rules import apply_claim_rules
from .explanation_engine import add_explanations
from .risk_engine import calculate_review_priority


REQUIRED_INPUT_COLUMNS = {
    "claim_id",
    "patient_id",
    "provider_id",
    "service_date",
    "diagnosis_group",
    "procedure_code",
    "claim_amount",
    "expected_amount",
    "days_since_similar_claim",
    "provider_average_amount",
}


def validate_input(claims: pd.DataFrame) -> None:
    missing = REQUIRED_INPUT_COLUMNS.difference(claims.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing required input columns: {missing_text}")

    if claims.empty:
        raise ValueError("The claims dataset is empty.")

    if claims["claim_id"].duplicated().any():
        raise ValueError("Claim IDs must be unique.")

    if claims[list(REQUIRED_INPUT_COLUMNS)].isna().any().any():
        raise ValueError("The claims dataset contains missing required values.")

    for column in [
        "claim_amount",
        "expected_amount",
        "provider_average_amount",
    ]:
        if (claims[column] <= 0).any():
            raise ValueError(f"{column} must contain only positive values.")


def add_derived_features(claims: pd.DataFrame) -> pd.DataFrame:
    result = claims.copy()
    result["service_date"] = pd.to_datetime(
        result["service_date"],
        errors="raise",
    )

    result["amount_to_expected_ratio"] = (
        result["claim_amount"] / result["expected_amount"]
    )
    result["amount_to_provider_average_ratio"] = (
        result["claim_amount"] / result["provider_average_amount"]
    )

    return result


def run_pipeline(
    claims: pd.DataFrame,
    contamination: float = 0.10,
    random_state: int = 42,
) -> pd.DataFrame:
    validate_input(claims)

    scored = add_derived_features(claims)
    scored = apply_claim_rules(scored)
    scored = score_anomalies(
        scored,
        contamination=contamination,
        random_state=random_state,
    )
    scored = calculate_review_priority(scored)
    scored = add_explanations(scored)

    scored["service_date"] = scored["service_date"].dt.strftime("%Y-%m-%d")

    return scored


def summarize_results(scored: pd.DataFrame) -> None:
    print(f"Scored {len(scored):,} claims")
    print("\nReview priority:")
    print(scored["review_priority"].value_counts().to_string())

    if {"injected_anomaly", "anomaly_type"}.issubset(scored.columns):
        injected = scored["injected_anomaly"].astype(bool)
        surfaced = scored["review_priority"] != "Routine"

        detected = int((injected & surfaced).sum())
        total_injected = int(injected.sum())
        routine_flagged = int((~injected & surfaced).sum())
        total_routine = int((~injected).sum())

        total_surfaced = int(surfaced.sum())
        precision = detected / total_surfaced if total_surfaced else 0.0
        detection_rate = detected / total_injected if total_injected else 0.0
        routine_flag_rate = (
            routine_flagged / total_routine if total_routine else 0.0
        )

        print("\nSynthetic evaluation:")
        print(
            f"Injected anomalies surfaced: {detected}/{total_injected} "
            f"({detection_rate:.1%})"
        )
        print(
            f"Routine claims surfaced: {routine_flagged}/{total_routine} "
            f"({routine_flag_rate:.1%})"
        )
        print(
            f"Surfaced claims that were injected anomalies: "
            f"{detected}/{total_surfaced} ({precision:.1%})"
        )

        if "anomaly_difficulty" in scored.columns:
            anomaly_rows = scored.loc[injected].copy()
            by_difficulty = (
                anomaly_rows.assign(surfaced=surfaced.loc[injected].to_numpy())
                .groupby("anomaly_difficulty")["surfaced"]
                .agg(["sum", "count"])
            )
            print("\nDetection by difficulty:")
            for difficulty, row in by_difficulty.iterrows():
                rate = row["sum"] / row["count"] if row["count"] else 0.0
                print(
                    f"  {difficulty}: {int(row['sum'])}/{int(row['count'])} "
                    f"({rate:.1%})"
                )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score synthetic healthcare claims for review priority."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/synthetic_claims.csv"),
        help="Input claims CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/scored_claims.csv"),
        help="Output CSV for scored claims.",
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.10,
        help="Expected anomaly fraction used by Isolation Forest.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used by Isolation Forest.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    claims = pd.read_csv(args.input)
    scored = run_pipeline(
        claims,
        contamination=args.contamination,
        random_state=args.seed,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(args.output, index=False)

    summarize_results(scored)
    print(f"\nSaved scored claims to: {args.output}")


if __name__ == "__main__":
    main()