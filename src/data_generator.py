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

CLEAR_ANOMALY_TYPES = [
    "high_claim_amount",
    "possible_duplicate",
    "frequent_repeat_service",
    "provider_billing_outlier",
    "diagnosis_procedure_mismatch",
]

SUBTLE_ANOMALY_TYPES = [
    "moderate_high_amount",
    "borderline_repeat_service",
    "moderate_provider_deviation",
    "combined_moderate_signals",
    "rare_billing_pattern",
]

EDGE_CASE_TYPES = [
    "routine_high_cost_exception",
    "routine_authorized_followup",
    "routine_provider_baseline_exception",
    "routine_coding_exception",
    "routine_corrected_resubmission",
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
        procedure_code = str(rng.choice(DIAGNOSIS_PROCEDURES[diagnosis_group]))
        provider_id = str(rng.choice(provider_ids))

        expected_amount = PROCEDURE_BASE_AMOUNTS[procedure_code]
        provider_average = expected_amount * provider_factors[provider_id]
        claim_amount = provider_average * rng.normal(1.0, 0.09)
        claim_amount = max(claim_amount, expected_amount * 0.55)

        service_date = start_date + pd.Timedelta(days=int(rng.integers(0, 365)))

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
                "provider_average_amount": round(float(provider_average), 2),
                "injected_anomaly": False,
                "anomaly_type": "none",
                "anomaly_difficulty": "none",
                "case_profile": "routine_standard",
            }
        )

    return pd.DataFrame(claims)


def mark_anomaly(
    claims: pd.DataFrame,
    index: int,
    anomaly_type: str,
    difficulty: str,
) -> None:
    claims.at[index, "injected_anomaly"] = True
    claims.at[index, "anomaly_type"] = anomaly_type
    claims.at[index, "anomaly_difficulty"] = difficulty
    claims.at[index, "case_profile"] = f"anomaly_{difficulty}"


def mark_edge_case(
    claims: pd.DataFrame,
    index: int,
    case_profile: str,
) -> None:
    claims.at[index, "injected_anomaly"] = False
    claims.at[index, "anomaly_type"] = "none"
    claims.at[index, "anomaly_difficulty"] = "none"
    claims.at[index, "case_profile"] = case_profile


def inject_clear_anomalies(
    claims: pd.DataFrame,
    groups: list[np.ndarray],
    source_pool: np.ndarray,
    rng: np.random.Generator,
) -> None:
    for index in groups[0]:
        multiplier = float(rng.uniform(3.5, 6.0))
        claims.at[index, "claim_amount"] = round(
            float(claims.at[index, "expected_amount"]) * multiplier,
            2,
        )
        mark_anomaly(claims, int(index), "high_claim_amount", "clear")

    for index in groups[1]:
        source_index = int(rng.choice(source_pool))
        source = claims.loc[source_index]
        for column in [
            "patient_id",
            "provider_id",
            "diagnosis_group",
            "procedure_code",
            "claim_amount",
            "expected_amount",
            "provider_average_amount",
        ]:
            claims.at[index, column] = source[column]
        claims.at[index, "service_date"] = pd.Timestamp(source["service_date"]) + pd.Timedelta(
            days=int(rng.integers(1, 3))
        )
        claims.at[index, "days_since_similar_claim"] = int(rng.integers(1, 3))
        mark_anomaly(claims, int(index), "possible_duplicate", "clear")

    for index in groups[2]:
        source_index = int(rng.choice(source_pool))
        source = claims.loc[source_index]
        for column in [
            "patient_id",
            "diagnosis_group",
            "procedure_code",
            "expected_amount",
        ]:
            claims.at[index, column] = source[column]
        claims.at[index, "service_date"] = pd.Timestamp(source["service_date"]) + pd.Timedelta(
            days=int(rng.integers(3, 8))
        )
        claims.at[index, "days_since_similar_claim"] = int(rng.integers(3, 8))
        claims.at[index, "claim_amount"] = round(
            float(source["claim_amount"]) * float(rng.uniform(0.88, 1.12)),
            2,
        )
        mark_anomaly(claims, int(index), "frequent_repeat_service", "clear")

    for index in groups[3]:
        expected_amount = float(claims.at[index, "expected_amount"])
        claims.at[index, "provider_id"] = str(rng.choice(["PRV-039", "PRV-040"]))
        claims.at[index, "provider_average_amount"] = round(
            expected_amount * float(rng.uniform(0.95, 1.10)),
            2,
        )
        claims.at[index, "claim_amount"] = round(
            expected_amount * float(rng.uniform(2.4, 3.4)),
            2,
        )
        mark_anomaly(claims, int(index), "provider_billing_outlier", "clear")

    diagnosis_groups = list(DIAGNOSIS_PROCEDURES)
    for index in groups[4]:
        diagnosis_group = str(claims.at[index, "diagnosis_group"])
        other_groups = [group for group in diagnosis_groups if group != diagnosis_group]
        mismatched_group = str(rng.choice(other_groups))
        procedure_code = str(rng.choice(DIAGNOSIS_PROCEDURES[mismatched_group]))
        expected_amount = PROCEDURE_BASE_AMOUNTS[procedure_code]
        claims.at[index, "procedure_code"] = procedure_code
        claims.at[index, "expected_amount"] = round(expected_amount, 2)
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
            int(index),
            "diagnosis_procedure_mismatch",
            "clear",
        )


def inject_subtle_anomalies(
    claims: pd.DataFrame,
    groups: list[np.ndarray],
    rng: np.random.Generator,
) -> None:
    for index in groups[0]:
        expected = float(claims.at[index, "expected_amount"])
        ratio = float(rng.uniform(1.75, 2.15))
        claims.at[index, "claim_amount"] = round(expected * ratio, 2)
        claims.at[index, "provider_average_amount"] = round(
            expected * float(rng.uniform(0.95, 1.10)),
            2,
        )
        mark_anomaly(claims, int(index), "moderate_high_amount", "subtle")

    for index in groups[1]:
        claims.at[index, "days_since_similar_claim"] = int(rng.integers(8, 13))
        mark_anomaly(
            claims,
            int(index),
            "borderline_repeat_service",
            "subtle",
        )

    for index in groups[2]:
        expected = float(claims.at[index, "expected_amount"])
        claim_amount = expected * float(rng.uniform(1.45, 1.85))
        provider_average = claim_amount / float(rng.uniform(1.75, 2.15))
        claims.at[index, "claim_amount"] = round(claim_amount, 2)
        claims.at[index, "provider_average_amount"] = round(provider_average, 2)
        mark_anomaly(
            claims,
            int(index),
            "moderate_provider_deviation",
            "subtle",
        )

    for index in groups[3]:
        expected = float(claims.at[index, "expected_amount"])
        claim_amount = expected * float(rng.uniform(1.55, 1.95))
        claims.at[index, "claim_amount"] = round(claim_amount, 2)
        claims.at[index, "provider_average_amount"] = round(
            claim_amount / float(rng.uniform(1.55, 2.05)),
            2,
        )
        claims.at[index, "days_since_similar_claim"] = int(rng.integers(8, 15))
        mark_anomaly(
            claims,
            int(index),
            "combined_moderate_signals",
            "subtle",
        )

    rare_pairs = [
        ("PRV-040", "digestive", "P402"),
        ("PRV-039", "cardiovascular", "P302"),
        ("PRV-038", "respiratory", "P102"),
    ]
    for index in groups[4]:
        provider_id, diagnosis_group, procedure_code = rare_pairs[
            int(rng.integers(0, len(rare_pairs)))
        ]
        expected = PROCEDURE_BASE_AMOUNTS[procedure_code]
        claims.at[index, "provider_id"] = provider_id
        claims.at[index, "diagnosis_group"] = diagnosis_group
        claims.at[index, "procedure_code"] = procedure_code
        claims.at[index, "expected_amount"] = expected
        claims.at[index, "claim_amount"] = round(
            expected * float(rng.uniform(1.45, 1.85)),
            2,
        )
        claims.at[index, "provider_average_amount"] = round(
            expected * float(rng.uniform(0.95, 1.10)),
            2,
        )
        claims.at[index, "days_since_similar_claim"] = int(rng.integers(8, 20))
        mark_anomaly(claims, int(index), "rare_billing_pattern", "subtle")


def inject_legitimate_edge_cases(
    claims: pd.DataFrame,
    groups: list[np.ndarray],
    rng: np.random.Generator,
) -> None:
    for index in groups[0]:
        expected = float(claims.at[index, "expected_amount"])
        claim_amount = expected * float(rng.uniform(3.0, 3.35))
        claims.at[index, "claim_amount"] = round(claim_amount, 2)
        claims.at[index, "provider_average_amount"] = round(
            claim_amount * float(rng.uniform(0.94, 1.06)),
            2,
        )
        mark_edge_case(claims, int(index), "routine_high_cost_exception")

    for index in groups[1]:
        claims.at[index, "days_since_similar_claim"] = int(rng.integers(3, 8))
        mark_edge_case(claims, int(index), "routine_authorized_followup")

    for index in groups[2]:
        expected = float(claims.at[index, "expected_amount"])
        claim_amount = expected * float(rng.uniform(0.95, 1.10))
        claims.at[index, "claim_amount"] = round(claim_amount, 2)
        claims.at[index, "provider_average_amount"] = round(
            claim_amount / float(rng.uniform(2.2, 2.5)),
            2,
        )
        mark_edge_case(
            claims,
            int(index),
            "routine_provider_baseline_exception",
        )

    diagnosis_groups = list(DIAGNOSIS_PROCEDURES)
    for index in groups[3]:
        diagnosis_group = str(claims.at[index, "diagnosis_group"])
        other_groups = [group for group in diagnosis_groups if group != diagnosis_group]
        procedure_group = str(rng.choice(other_groups))
        procedure_code = str(rng.choice(DIAGNOSIS_PROCEDURES[procedure_group]))
        expected = PROCEDURE_BASE_AMOUNTS[procedure_code]
        claims.at[index, "procedure_code"] = procedure_code
        claims.at[index, "expected_amount"] = expected
        claims.at[index, "claim_amount"] = round(
            expected * float(rng.uniform(0.90, 1.10)),
            2,
        )
        claims.at[index, "provider_average_amount"] = round(
            expected * float(rng.uniform(0.90, 1.10)),
            2,
        )
        mark_edge_case(claims, int(index), "routine_coding_exception")

    for index in groups[4]:
        claims.at[index, "days_since_similar_claim"] = int(rng.integers(1, 3))
        claims.at[index, "claim_amount"] = round(
            float(claims.at[index, "expected_amount"]) * float(rng.uniform(0.55, 0.80)),
            2,
        )
        mark_edge_case(
            claims,
            int(index),
            "routine_corrected_resubmission",
        )


def inject_evaluation_cases(
    claims: pd.DataFrame,
    anomaly_rate: float,
    edge_case_rate: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    anomaly_count = int(round(len(claims) * anomaly_rate))
    edge_count = int(round(len(claims) * edge_case_rate))

    if anomaly_count < 10 or anomaly_count % 10 != 0:
        raise ValueError("The anomaly count must be at least 10 and divisible by 10.")
    if edge_count < 5 or edge_count % 5 != 0:
        raise ValueError("The edge-case count must be at least 5 and divisible by 5.")
    if anomaly_count + edge_count > len(claims) // 2:
        raise ValueError("Anomaly and edge-case rates are too high.")

    selected = rng.choice(
        claims.index.to_numpy(),
        size=anomaly_count + edge_count,
        replace=False,
    )
    anomaly_indices = selected[:anomaly_count]
    edge_indices = selected[anomaly_count:]

    half = anomaly_count // 2
    clear_groups = list(np.array_split(anomaly_indices[:half], 5))
    subtle_groups = list(np.array_split(anomaly_indices[half:], 5))
    edge_groups = list(np.array_split(edge_indices, 5))

    selected_set = {int(index) for index in selected}
    source_pool = np.array(
        [index for index in claims.index if int(index) not in selected_set]
    )

    inject_clear_anomalies(claims, clear_groups, source_pool, rng)
    inject_subtle_anomalies(claims, subtle_groups, rng)
    inject_legitimate_edge_cases(claims, edge_groups, rng)

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
        "anomaly_difficulty",
        "case_profile",
    }

    missing = required_columns.difference(claims.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    if claims["claim_id"].duplicated().any():
        raise ValueError("Claim IDs must be unique.")
    if claims.isna().any().any():
        raise ValueError("Generated dataset contains missing values.")
    if (claims[["claim_amount", "expected_amount", "provider_average_amount"]] <= 0).any().any():
        raise ValueError("Claim and benchmark amounts must be positive.")


def generate_dataset(
    num_claims: int = 1000,
    anomaly_rate: float = 0.10,
    edge_case_rate: float = 0.03,
    seed: int = 42,
) -> pd.DataFrame:
    if num_claims < 100:
        raise ValueError("num_claims must be at least 100.")
    if not 0.0 < anomaly_rate <= 0.30:
        raise ValueError("anomaly_rate must be greater than 0 and at most 0.30.")
    if not 0.0 < edge_case_rate <= 0.20:
        raise ValueError("edge_case_rate must be greater than 0 and at most 0.20.")

    rng = np.random.default_rng(seed)
    claims = generate_base_claims(num_claims, rng)
    claims = inject_evaluation_cases(
        claims,
        anomaly_rate=anomaly_rate,
        edge_case_rate=edge_case_rate,
        rng=rng,
    )
    claims["service_date"] = pd.to_datetime(claims["service_date"]).dt.strftime(
        "%Y-%m-%d"
    )
    validate_dataset(claims)
    return claims


def save_dataset(claims: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    claims.to_csv(output_path, index=False)


def print_summary(claims: pd.DataFrame, output_path: Path) -> None:
    print(f"Generated {len(claims):,} synthetic claims")
    print(f"Injected anomalies: {int(claims['injected_anomaly'].sum()):,}")
    print(
        "Legitimate edge cases: "
        f"{int(claims['case_profile'].str.startswith('routine_').sum() - (claims['case_profile'] == 'routine_standard').sum()):,}"
    )

    print("\nAnomalies by difficulty:")
    anomaly_rows = claims[claims["injected_anomaly"]]
    print(anomaly_rows["anomaly_difficulty"].value_counts().to_string())

    print("\nEvaluation case profiles:")
    print(claims["case_profile"].value_counts().sort_index().to_string())
    print(f"\nSaved dataset to: {output_path}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic healthcare claims data."
    )
    parser.add_argument("--claims", type=int, default=1000)
    parser.add_argument("--anomaly-rate", type=float, default=0.10)
    parser.add_argument("--edge-case-rate", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/synthetic_claims.csv"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    claims = generate_dataset(
        num_claims=args.claims,
        anomaly_rate=args.anomaly_rate,
        edge_case_rate=args.edge_case_rate,
        seed=args.seed,
    )
    save_dataset(claims, args.output)
    print_summary(claims, args.output)


if __name__ == "__main__":
    main()