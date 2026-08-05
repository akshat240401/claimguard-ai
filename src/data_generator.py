from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DIAGNOSIS_PROCEDURES = {
    "respiratory": ["P100", "P101", "P102"],
    "musculoskeletal": ["P200", "P201", "P202"],
    "cardiovascular": ["P300", "P301", "P302"],
    "digestive": ["P400", "P401", "P402"],
    "endocrine": ["P500", "P501", "P502"],
}

PROCEDURE_BASE_AMOUNTS = {
    "P100": 125.0,
    "P101": 240.0,
    "P102": 310.0,
    "P200": 140.0,
    "P201": 275.0,
    "P202": 180.0,
    "P300": 165.0,
    "P301": 390.0,
    "P302": 620.0,
    "P400": 135.0,
    "P401": 350.0,
    "P402": 780.0,
    "P500": 150.0,
    "P501": 95.0,
    "P502": 210.0,
}

ANOMALY_TYPES = [
    "high_claim_amount",
    "possible_duplicate",
    "frequent_repeat_service",
    "provider_billing_outlier",
    "diagnosis_procedure_mismatch",
]


def generate_base_claims(
    num_claims: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    patient_ids = [f"PAT-{number:04d}" for number in range(1, 251)]
    provider_ids = [f"PRV-{number:03d}" for number in range(1, 41)]

    provider_factors = {
        provider_id: float(rng.uniform(0.88, 1.12))
        for provider_id in provider_ids
    }

    diagnosis_groups = list(DIAGNOSIS_PROCEDURES)
    start_date = pd.Timestamp("2025-01-01")
    claims: list[dict[str, object]] = []

    for index in range(num_claims):
        diagnosis_group = str(rng.choice(diagnosis_groups))
        procedure_code = str(
            rng.choice(DIAGNOSIS_PROCEDURES[diagnosis_group])
        )
        provider_id = str(rng.choice(provider_ids))

        expected_amount = PROCEDURE_BASE_AMOUNTS[procedure_code]
        provider_average = expected_amount * provider_factors[provider_id]

        claim_amount = provider_average * rng.normal(1.0, 0.09)
        claim_amount = max(claim_amount, expected_amount * 0.55)

        service_date = start_date + pd.Timedelta(
            days=int(rng.integers(0, 365))
        )

        claims.append(
            {
                "claim_id": f"CLM-{index + 1:05d}",
                "patient_id": str(rng.choice(patient_ids)),
                "provider_id": provider_id,
                "service_date": service_date,
                "diagnosis_group": diagnosis_group,
                "procedure_code": procedure_code,
                "claim_amount": round(float(claim_amount), 2),
                "expected_amount": round(float(expected_amount), 2),
                "days_since_similar_claim": int(rng.integers(14, 181)),
                "provider_average_amount": round(
                    float(provider_average),
                    2,
                ),
                "injected_anomaly": False,
                "anomaly_type": "none",
            }
        )

    return pd.DataFrame(claims)


def inject_high_amount_anomalies(
    claims: pd.DataFrame,
    indices: np.ndarray,
    rng: np.random.Generator,
) -> None:
    for index in indices:
        multiplier = float(rng.uniform(3.5, 6.0))
        claims.at[index, "claim_amount"] = round(
            float(claims.at[index, "expected_amount"]) * multiplier,
            2,
        )
        mark_anomaly(claims, index, "high_claim_amount")


def inject_duplicate_anomalies(
    claims: pd.DataFrame,
    indices: np.ndarray,
    source_pool: np.ndarray,
    rng: np.random.Generator,
) -> None:
    for index in indices:
        source_index = int(rng.choice(source_pool))
        source = claims.loc[source_index]

        claims.at[index, "patient_id"] = source["patient_id"]
        claims.at[index, "provider_id"] = source["provider_id"]
        claims.at[index, "diagnosis_group"] = source["diagnosis_group"]
        claims.at[index, "procedure_code"] = source["procedure_code"]
        claims.at[index, "claim_amount"] = source["claim_amount"]
        claims.at[index, "expected_amount"] = source["expected_amount"]
        claims.at[index, "provider_average_amount"] = source[
            "provider_average_amount"
        ]
        claims.at[index, "service_date"] = (
            pd.Timestamp(source["service_date"])
            + pd.Timedelta(days=int(rng.integers(1, 3)))
        )
        claims.at[index, "days_since_similar_claim"] = int(
            rng.integers(1, 3)
        )

        mark_anomaly(claims, index, "possible_duplicate")


def inject_repeat_service_anomalies(
    claims: pd.DataFrame,
    indices: np.ndarray,
    source_pool: np.ndarray,
    rng: np.random.Generator,
) -> None:
    for index in indices:
        source_index = int(rng.choice(source_pool))
        source = claims.loc[source_index]

        claims.at[index, "patient_id"] = source["patient_id"]
        claims.at[index, "diagnosis_group"] = source["diagnosis_group"]
        claims.at[index, "procedure_code"] = source["procedure_code"]
        claims.at[index, "expected_amount"] = source["expected_amount"]
        claims.at[index, "service_date"] = (
            pd.Timestamp(source["service_date"])
            + pd.Timedelta(days=int(rng.integers(3, 8)))
        )
        claims.at[index, "days_since_similar_claim"] = int(
            rng.integers(3, 8)
        )

        amount = float(source["claim_amount"]) * float(
            rng.uniform(0.88, 1.12)
        )
        claims.at[index, "claim_amount"] = round(amount, 2)

        mark_anomaly(claims, index, "frequent_repeat_service")


def inject_provider_outliers(
    claims: pd.DataFrame,
    indices: np.ndarray,
    rng: np.random.Generator,
) -> None:
    outlier_providers = ["PRV-039", "PRV-040"]

    for index in indices:
        provider_id = str(rng.choice(outlier_providers))
        expected_amount = float(claims.at[index, "expected_amount"])

        claims.at[index, "provider_id"] = provider_id
        claims.at[index, "provider_average_amount"] = round(
            expected_amount * float(rng.uniform(0.95, 1.10)),
            2,
        )
        claims.at[index, "claim_amount"] = round(
            expected_amount * float(rng.uniform(2.4, 3.4)),
            2,
        )

        mark_anomaly(claims, index, "provider_billing_outlier")


def inject_mismatch_anomalies(
    claims: pd.DataFrame,
    indices: np.ndarray,
    rng: np.random.Generator,
) -> None:
    diagnosis_groups = list(DIAGNOSIS_PROCEDURES)

    for index in indices:
        diagnosis_group = str(claims.at[index, "diagnosis_group"])

        other_groups = [
            group
            for group in diagnosis_groups
            if group != diagnosis_group
        ]

        mismatched_group = str(rng.choice(other_groups))
        procedure_code = str(
            rng.choice(DIAGNOSIS_PROCEDURES[mismatched_group])
        )
        expected_amount = PROCEDURE_BASE_AMOUNTS[procedure_code]

        claims.at[index, "procedure_code"] = procedure_code
        claims.at[index, "expected_amount"] = round(
            expected_amount,
            2,
        )
        claims.at[index, "provider_average_amount"] = round(
            expected_amount * float(rng.uniform(0.90, 1.10)),
            2,
        )
        claims.at[index, "claim_amount"] = round(
            expected_amount * float(rng.uniform(0.90, 1.15)),
            2,
        )

        mark_anomaly(
            claims,
            index,
            "diagnosis_procedure_mismatch",
        )


def mark_anomaly(
    claims: pd.DataFrame,
    index: int,
    anomaly_type: str,
) -> None:
    claims.at[index, "injected_anomaly"] = True
    claims.at[index, "anomaly_type"] = anomaly_type


def inject_anomalies(
    claims: pd.DataFrame,
    anomaly_rate: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    anomaly_count = max(
        len(ANOMALY_TYPES),
        int(round(len(claims) * anomaly_rate)),
    )

    anomaly_count = min(anomaly_count, len(claims) // 2)

    selected_indices = rng.choice(
        claims.index.to_numpy(),
        size=anomaly_count,
        replace=False,
    )

    anomaly_groups = np.array_split(
        selected_indices,
        len(ANOMALY_TYPES),
    )

    selected_set = set(int(index) for index in selected_indices)
    source_pool = np.array(
        [
            index
            for index in claims.index
            if int(index) not in selected_set
        ]
    )

    inject_high_amount_anomalies(
        claims,
        anomaly_groups[0],
        rng,
    )
    inject_duplicate_anomalies(
        claims,
        anomaly_groups[1],
        source_pool,
        rng,
    )
    inject_repeat_service_anomalies(
        claims,
        anomaly_groups[2],
        source_pool,
        rng,
    )
    inject_provider_outliers(
        claims,
        anomaly_groups[3],
        rng,
    )
    inject_mismatch_anomalies(
        claims,
        anomaly_groups[4],
        rng,
    )

    return claims


def validate_dataset(claims: pd.DataFrame) -> None:
    required_columns = {
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
        "injected_anomaly",
        "anomaly_type",
    }

    missing_columns = required_columns.difference(claims.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing columns: {missing}")

    if claims["claim_id"].duplicated().any():
        raise ValueError("Claim IDs must be unique.")

    if claims.isna().any().any():
        raise ValueError("Generated dataset contains missing values.")

    if (claims["claim_amount"] <= 0).any():
        raise ValueError("Claim amounts must be positive.")

    if (claims["expected_amount"] <= 0).any():
        raise ValueError("Expected amounts must be positive.")


def generate_dataset(
    num_claims: int = 1000,
    anomaly_rate: float = 0.10,
    seed: int = 42,
) -> pd.DataFrame:
    if num_claims < 100:
        raise ValueError("num_claims must be at least 100.")

    if not 0.0 < anomaly_rate <= 0.30:
        raise ValueError(
            "anomaly_rate must be greater than 0 and at most 0.30."
        )

    rng = np.random.default_rng(seed)

    claims = generate_base_claims(
        num_claims=num_claims,
        rng=rng,
    )

    claims = inject_anomalies(
        claims=claims,
        anomaly_rate=anomaly_rate,
        rng=rng,
    )

    claims["service_date"] = pd.to_datetime(
        claims["service_date"]
    ).dt.strftime("%Y-%m-%d")

    validate_dataset(claims)

    return claims


def save_dataset(
    claims: pd.DataFrame,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    claims.to_csv(output_path, index=False)


def print_summary(
    claims: pd.DataFrame,
    output_path: Path,
) -> None:
    anomaly_summary = (
        claims.loc[claims["injected_anomaly"], "anomaly_type"]
        .value_counts()
        .sort_index()
    )

    print(f"Generated {len(claims):,} synthetic claims")
    print(
        "Injected anomalies: "
        f"{int(claims['injected_anomaly'].sum()):,}"
    )

    for anomaly_type, count in anomaly_summary.items():
        print(f"  {anomaly_type}: {count}")

    print(f"Saved dataset to: {output_path}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic healthcare claims data."
    )

    parser.add_argument(
        "--claims",
        type=int,
        default=1000,
        help="Number of claims to generate.",
    )
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.10,
        help="Fraction of claims containing injected anomalies.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for reproducible output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/synthetic_claims.csv"),
        help="CSV output path.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    claims = generate_dataset(
        num_claims=args.claims,
        anomaly_rate=args.anomaly_rate,
        seed=args.seed,
    )

    save_dataset(
        claims=claims,
        output_path=args.output,
    )

    print_summary(
        claims=claims,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()