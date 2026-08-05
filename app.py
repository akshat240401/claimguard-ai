from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.pipeline import run_pipeline


DATA_PATH = Path("data/synthetic_claims.csv")

PRIORITY_ORDER = [
    "Routine",
    "Review Recommended",
    "High-Priority Review",
]

PRIORITY_COLORS = {
    "Routine": "#2E8B57",
    "Review Recommended": "#E09F3E",
    "High-Priority Review": "#C53D43",
}

RULE_LABELS = {
    "high_claim_amount": "High claim amount",
    "possible_duplicate": "Possible duplicate",
    "frequent_repeat_service": "Frequent repeat service",
    "provider_billing_outlier": "Provider billing outlier",
    "diagnosis_procedure_mismatch": "Diagnosis-procedure mismatch",
}


st.set_page_config(
    page_title="ClaimGuard",
    layout="wide",
)

st.markdown(
    """
    <style>
        #MainMenu,
        footer,
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDeployButton"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        [data-testid="stStatusWidget"],
        [data-testid="stHeaderActionElements"] {
            display: none !important;
        }

        section[data-testid="stSidebar"] {
            width: 300px !important;
            min-width: 300px !important;
        }

        section[data-testid="stSidebar"] > div {
            width: 300px !important;
        }

        [data-testid="stSidebarUserContent"] {
            padding-top: 0.75rem !important;
            padding-right: 1rem !important;
            padding-bottom: 0.75rem !important;
            padding-left: 1rem !important;
            overflow-y: auto !important;
            scrollbar-width: none;
        }

        [data-testid="stSidebarUserContent"]::-webkit-scrollbar {
            display: none;
        }

        [data-testid="stSidebarUserContent"] h1 {
            margin: 0 0 0.2rem 0 !important;
            padding: 0 !important;
            font-size: 1.9rem !important;
        }

        [data-testid="stSidebarUserContent"] h3 {
            margin-top: 0.35rem !important;
            margin-bottom: 0.15rem !important;
        }

        [data-testid="stSidebarUserContent"] p {
            margin-top: 0.2rem !important;
            margin-bottom: 0.45rem !important;
            line-height: 1.45 !important;
        }

        [data-testid="stMainBlockContainer"],
        .block-container {
            max-width: 100% !important;
            padding-top: 0.65rem !important;
            padding-right: 2.5rem !important;
            padding-bottom: 1rem !important;
            padding-left: 2.5rem !important;
        }

        [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }

        [data-testid="stMetric"] {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        [data-testid="stMetricLabel"] {
            margin-bottom: 0 !important;
        }

        [data-testid="stMetricValue"] {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
            font-size: 2rem !important;
            line-height: 1.15 !important;
        }

        [data-testid="stCaptionContainer"] {
            margin-top: 0 !important;
            margin-bottom: 0.15rem !important;
        }

        button[data-baseweb="tab"] {
            padding-top: 0.35rem !important;
            padding-bottom: 0.35rem !important;
        }

        hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Scoring claims...")
def load_scored_claims(
    path: str,
    modified_time: float,
) -> pd.DataFrame:
    del modified_time

    claims = pd.read_csv(path)
    return run_pipeline(claims)


def boolean_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    return series.astype(str).str.lower().eq("true")


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def format_rule_name(rule: str) -> str:
    return RULE_LABELS.get(
        rule,
        rule.replace("_", " ").title(),
    )


def split_rules(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []

    value_text = str(value).strip()

    if not value_text:
        return []

    return [
        rule
        for rule in value_text.split("|")
        if rule
    ]


def evaluation_summary(
    scored: pd.DataFrame,
) -> dict[str, float | int]:
    if "injected_anomaly" not in scored.columns:
        return {}

    injected = boolean_series(
        scored["injected_anomaly"]
    )

    surfaced = (
        scored["review_priority"] != "Routine"
    )

    detected = int(
        (injected & surfaced).sum()
    )

    total_injected = int(
        injected.sum()
    )

    routine_surfaced = int(
        (~injected & surfaced).sum()
    )

    total_routine = int(
        (~injected).sum()
    )

    total_surfaced = int(
        surfaced.sum()
    )

    return {
        "detected": detected,
        "total_injected": total_injected,
        "detection_rate": (
            detected / total_injected
            if total_injected
            else 0.0
        ),
        "routine_surfaced": routine_surfaced,
        "total_routine": total_routine,
        "routine_surfacing_rate": (
            routine_surfaced / total_routine
            if total_routine
            else 0.0
        ),
        "surfaced_precision": (
            detected / total_surfaced
            if total_surfaced
            else 0.0
        ),
    }


def filtered_claims(
    scored: pd.DataFrame,
) -> pd.DataFrame:
    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_priorities = st.multiselect(
            "Review priority",
            options=PRIORITY_ORDER,
            default=PRIORITY_ORDER,
        )

    with col2:
        providers = sorted(
            scored["provider_id"]
            .astype(str)
            .unique()
        )

        selected_providers = st.multiselect(
            "Provider",
            options=providers,
        )

    with col3:
        diagnosis_groups = sorted(
            scored["diagnosis_group"]
            .astype(str)
            .unique()
        )

        selected_diagnoses = st.multiselect(
            "Diagnosis group",
            options=diagnosis_groups,
        )

    only_surfaced = st.checkbox(
        "Show only claims surfaced for review",
        value=False,
    )

    mask = scored["review_priority"].isin(
        selected_priorities
    )

    if selected_providers:
        mask &= scored["provider_id"].isin(
            selected_providers
        )

    if selected_diagnoses:
        mask &= scored["diagnosis_group"].isin(
            selected_diagnoses
        )

    if only_surfaced:
        mask &= (
            scored["review_priority"] != "Routine"
        )

    return scored.loc[mask].copy()


def render_overview(
    scored: pd.DataFrame,
) -> None:
    surfaced = (
        scored["review_priority"] != "Routine"
    )

    high_priority = (
        scored["review_priority"]
        == "High-Priority Review"
    )

    summary = evaluation_summary(scored)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Claims analyzed",
        f"{len(scored):,}",
    )

    col2.metric(
        "Surfaced for review",
        f"{int(surfaced.sum()):,}",
    )

    col3.metric(
        "High-priority claims",
        f"{int(high_priority.sum()):,}",
    )

    surfaced_amount = scored.loc[
        surfaced,
        "claim_amount",
    ].sum()

    col4.metric(
        "Surfaced claim amount",
        format_currency(
            float(surfaced_amount)
        ),
    )

    if summary:
        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Injected anomalies surfaced",
            f"{summary['detection_rate']:.1%}",
        )

        col1.caption(
            f"{summary['detected']} of "
            f"{summary['total_injected']} "
            "injected anomalies"
        )

        col2.metric(
            "Routine claims surfaced",
            f"{summary['routine_surfacing_rate']:.1%}",
        )

        col2.caption(
            f"{summary['routine_surfaced']} of "
            f"{summary['total_routine']} "
            "routine claims"
        )

        col3.metric(
            "Synthetic review precision",
            f"{summary['surfaced_precision']:.1%}",
        )

        col3.caption(
            "Share of surfaced claims that were "
            "injected anomalies"
        )

    chart_col1, chart_col2 = st.columns(2)

    priority_counts = (
        scored["review_priority"]
        .value_counts()
        .reindex(
            PRIORITY_ORDER,
            fill_value=0,
        )
        .rename_axis("review_priority")
        .reset_index(name="claims")
    )

    priority_chart = px.bar(
        priority_counts,
        x="review_priority",
        y="claims",
        color="review_priority",
        color_discrete_map=PRIORITY_COLORS,
        category_orders={
            "review_priority": PRIORITY_ORDER
        },
        labels={
            "review_priority": "Review priority",
            "claims": "Claims",
        },
        title="Review-priority distribution",
    )

    priority_chart.update_layout(
        showlegend=False,
        height=285,
        margin={
            "l": 15,
            "r": 15,
            "t": 45,
            "b": 10,
        },
    )

    with chart_col1:
        st.plotly_chart(
            priority_chart,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

    scatter = px.scatter(
        scored,
        x="expected_amount",
        y="claim_amount",
        color="review_priority",
        color_discrete_map=PRIORITY_COLORS,
        category_orders={
            "review_priority": PRIORITY_ORDER
        },
        hover_data=[
            "claim_id",
            "provider_id",
            "procedure_code",
            "review_priority_score",
        ],
        labels={
            "expected_amount": "Expected amount ($)",
            "claim_amount": "Claim amount ($)",
            "review_priority": "Review priority",
        },
        title=(
            "Claim amount compared with "
            "expected amount"
        ),
    )

    scatter.update_layout(
        height=285,
        margin={
            "l": 15,
            "r": 15,
            "t": 45,
            "b": 10,
        },
    )

    max_amount = max(
        float(
            scored["expected_amount"].max()
        ),
        float(
            scored["claim_amount"].max()
        ),
    )

    scatter.add_shape(
        type="line",
        x0=0,
        y0=0,
        x1=max_amount,
        y1=max_amount,
        line={
            "color": "#777777",
            "dash": "dash",
        },
    )

    with chart_col2:
        st.plotly_chart(
            scatter,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

    st.caption(
        "The dashed line represents a claim amount "
        "equal to the expected amount."
    )


def render_claims_review(
    scored: pd.DataFrame,
) -> None:
    filtered = filtered_claims(scored)

    st.write(
        f"Showing **{len(filtered):,}** of "
        f"**{len(scored):,}** claims."
    )

    table = filtered[
        [
            "claim_id",
            "provider_id",
            "diagnosis_group",
            "procedure_code",
            "claim_amount",
            "expected_amount",
            "review_priority_score",
            "review_priority",
            "triggered_rules",
        ]
    ].copy()

    table["triggered_rules"] = (
        table["triggered_rules"].apply(
            lambda value: ", ".join(
                format_rule_name(rule)
                for rule in split_rules(value)
            )
            or "None"
        )
    )

    table = table.rename(
        columns={
            "claim_id": "Claim ID",
            "provider_id": "Provider",
            "diagnosis_group": "Diagnosis",
            "procedure_code": "Procedure",
            "claim_amount": "Claim Amount",
            "expected_amount": "Expected Amount",
            "review_priority_score": "Review Score",
            "review_priority": "Review Priority",
            "triggered_rules": "Triggered Rules",
        }
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Claim Amount": (
                st.column_config.NumberColumn(
                    format="$%.2f",
                )
            ),
            "Expected Amount": (
                st.column_config.NumberColumn(
                    format="$%.2f",
                )
            ),
            "Review Score": (
                st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%d",
                )
            ),
        },
    )

    st.download_button(
        "Download filtered results",
        data=table.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=(
            "claimguard_filtered_results.csv"
        ),
        mime="text/csv",
    )


def render_claim_details(
    scored: pd.DataFrame,
) -> None:
    priority_rank = {
        "High-Priority Review": 0,
        "Review Recommended": 1,
        "Routine": 2,
    }

    sorted_claims = (
        scored.assign(
            priority_rank=(
                scored["review_priority"].map(
                    priority_rank
                )
            )
        )
        .sort_values(
            [
                "priority_rank",
                "review_priority_score",
            ],
            ascending=[True, False],
        )
    )

    claim_ids = (
        sorted_claims["claim_id"].tolist()
    )

    selected_claim_id = st.selectbox(
        "Select a claim",
        claim_ids,
    )

    claim = scored.loc[
        scored["claim_id"]
        == selected_claim_id
    ].iloc[0]

    rules = split_rules(
        claim["triggered_rules"]
    )

    col1, col2, col3, col4 = st.columns(
        [1.4, 1, 1, 1]
    )

    col1.metric(
        "Review priority",
        str(claim["review_priority"]),
    )

    col2.metric(
        "Review score",
        f"{int(claim['review_priority_score'])}/100",
    )

    col3.metric(
        "Rule score",
        f"{int(claim['rule_score'])}/100",
    )

    col4.metric(
        "Model anomaly score",
        f"{float(claim['model_anomaly_score']):.1f}/100",
    )

    detail_col1, detail_col2 = st.columns(2)

    claim_information = pd.DataFrame(
        {
            "Field": [
                "Claim ID",
                "Patient ID",
                "Provider ID",
                "Service date",
                "Diagnosis group",
                "Procedure code",
                "Days since similar claim",
            ],
            "Value": [
                claim["claim_id"],
                claim["patient_id"],
                claim["provider_id"],
                claim["service_date"],
                claim["diagnosis_group"],
                claim["procedure_code"],
                int(
                    claim[
                        "days_since_similar_claim"
                    ]
                ),
            ],
        }
    )

    amount_information = pd.DataFrame(
        {
            "Field": [
                "Claim amount",
                "Expected amount",
                "Provider average",
                "Amount / expected",
                "Amount / provider average",
            ],
            "Value": [
                (
                    f"${float(claim['claim_amount']):,.2f}"
                ),
                (
                    f"${float(claim['expected_amount']):,.2f}"
                ),
                (
                    f"${float(claim['provider_average_amount']):,.2f}"
                ),
                (
                    f"{float(claim['amount_to_expected_ratio']):.2f}×"
                ),
                (
                    f"{float(claim['amount_to_provider_average_ratio']):.2f}×"
                ),
            ],
        }
    )

    with detail_col1:
        st.subheader("Claim information")

        st.dataframe(
            claim_information,
            use_container_width=True,
            hide_index=True,
        )

    with detail_col2:
        st.subheader("Amount comparison")

        st.dataframe(
            amount_information,
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Triggered checks")

    if rules:
        st.write(
            " | ".join(
                format_rule_name(rule)
                for rule in rules
            )
        )
    else:
        st.write(
            "No configured rule was triggered."
        )

    st.subheader("Explanation")
    st.write(
        str(claim["explanation"])
    )

    st.subheader("Recommended action")
    st.write(
        str(claim["recommended_action"])
    )

    with st.expander(
        "Synthetic evaluation details"
    ):
        if "injected_anomaly" in scored.columns:
            injected_value = boolean_series(
                pd.Series(
                    [
                        claim[
                            "injected_anomaly"
                        ]
                    ]
                )
            ).iloc[0]

            evaluation_details = pd.DataFrame(
                {
                    "Field": [
                        "Injected anomaly",
                        "Anomaly type",
                        "Difficulty",
                        "Case profile",
                    ],
                    "Value": [
                        bool(injected_value),
                        claim.get(
                            "anomaly_type",
                            "not available",
                        ),
                        claim.get(
                            "anomaly_difficulty",
                            "not available",
                        ),
                        claim.get(
                            "case_profile",
                            "not available",
                        ),
                    ],
                }
            )

            st.dataframe(
                evaluation_details,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write(
                "Evaluation labels are not "
                "available for this dataset."
            )


def render_evaluation(
    scored: pd.DataFrame,
) -> None:
    summary = evaluation_summary(scored)

    if not summary:
        st.write(
            "Synthetic evaluation labels are not "
            "available in the loaded dataset."
        )
        return

    st.markdown(
        "**Evaluation note:** These results apply "
        "only to the controlled synthetic dataset "
        "and do not represent real-world "
        "payment-integrity performance."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Detection rate",
        f"{summary['detection_rate']:.1%}",
    )

    col1.caption(
        f"{summary['detected']} of "
        f"{summary['total_injected']} "
        "anomalies surfaced"
    )

    col2.metric(
        "Routine surfacing rate",
        f"{summary['routine_surfacing_rate']:.1%}",
    )

    col2.caption(
        f"{summary['routine_surfaced']} of "
        f"{summary['total_routine']} "
        "routine claims surfaced"
    )

    col3.metric(
        "Synthetic review precision",
        f"{summary['surfaced_precision']:.1%}",
    )

    col3.caption(
        "Injected anomalies among all "
        "surfaced claims"
    )

    injected = boolean_series(
        scored["injected_anomaly"]
    )

    surfaced = (
        scored["review_priority"] != "Routine"
    )

    if "anomaly_difficulty" in scored.columns:
        anomaly_rows = scored.loc[
            injected
        ].copy()

        anomaly_rows["surfaced"] = (
            surfaced.loc[injected].to_numpy()
        )

        by_difficulty = (
            anomaly_rows
            .groupby(
                "anomaly_difficulty",
                as_index=False,
            )
            .agg(
                surfaced=("surfaced", "sum"),
                total=("surfaced", "count"),
            )
        )

        by_difficulty["detection_rate"] = (
            by_difficulty["surfaced"]
            / by_difficulty["total"]
        )

        difficulty_chart = px.bar(
            by_difficulty,
            x="anomaly_difficulty",
            y="detection_rate",
            text=(
                by_difficulty[
                    "detection_rate"
                ].map(
                    lambda value: f"{value:.0%}"
                )
            ),
            labels={
                "anomaly_difficulty": (
                    "Anomaly difficulty"
                ),
                "detection_rate": (
                    "Detection rate"
                ),
            },
            title=(
                "Detection by anomaly difficulty"
            ),
        )

        difficulty_chart.update_yaxes(
            range=[0, 1],
            tickformat=".0%",
        )

        difficulty_chart.update_traces(
            textposition="outside",
        )

        difficulty_chart.update_layout(
            height=300,
            margin={
                "l": 15,
                "r": 15,
                "t": 45,
                "b": 10,
            },
        )

        st.plotly_chart(
            difficulty_chart,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

    evaluation_table = pd.DataFrame(
        {
            "Outcome": [
                "Injected anomaly surfaced",
                "Injected anomaly missed",
                "Routine claim surfaced",
                "Routine claim not surfaced",
            ],
            "Claims": [
                int(
                    (injected & surfaced).sum()
                ),
                int(
                    (injected & ~surfaced).sum()
                ),
                int(
                    (~injected & surfaced).sum()
                ),
                int(
                    (~injected & ~surfaced).sum()
                ),
            ],
        }
    )

    st.subheader(
        "Synthetic evaluation breakdown"
    )

    st.dataframe(
        evaluation_table,
        use_container_width=True,
        hide_index=True,
    )

    if "case_profile" in scored.columns:
        profile_summary = (
            scored.assign(
                surfaced=surfaced
            )
            .groupby(
                "case_profile",
                as_index=False,
            )
            .agg(
                claims=("claim_id", "count"),
                surfaced=("surfaced", "sum"),
            )
        )

        profile_summary[
            "surfacing_rate"
        ] = (
            profile_summary["surfaced"]
            / profile_summary["claims"]
            * 100
        )

        st.subheader(
            "Results by synthetic case profile"
        )

        st.dataframe(
            profile_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "case_profile": (
                    st.column_config.TextColumn(
                        "Case Profile"
                    )
                ),
                "claims": (
                    st.column_config.NumberColumn(
                        "Claims",
                        format="%d",
                    )
                ),
                "surfaced": (
                    st.column_config.NumberColumn(
                        "Surfaced",
                        format="%d",
                    )
                ),
                "surfacing_rate": (
                    st.column_config.NumberColumn(
                        "Surfacing Rate",
                        format="%.1f%%",
                    )
                ),
            },
        )


def main() -> None:
    if not DATA_PATH.exists():
        st.error(
            "The dataset was not found. Run "
            "`python src/data_generator.py` from "
            "the project root and reload the page."
        )
        st.stop()

    try:
        scored = load_scored_claims(
            str(DATA_PATH),
            DATA_PATH.stat().st_mtime,
        )
    except Exception as exc:
        st.error(
            "Unable to score the claims dataset: "
            f"{exc}"
        )
        st.stop()

    with st.sidebar:
        st.title("ClaimGuard")

        st.caption(
            "Claims review prioritization using "
            "rules and anomaly detection"
        )

        st.write(
            "Prioritizes synthetic claims for "
            "manual review. It does not identify "
            "fraud or make payment decisions."
        )

        st.divider()

        st.subheader("Model")

        st.write(
            "Five transparent claim-review rules "
            "combined with Isolation Forest anomaly "
            "detection."
        )

        st.write(
            "**Final score:** 65% rules, "
            "35% anomaly score"
        )

        st.caption(
            "Evaluation labels are excluded from "
            "model features."
        )

    (
        overview_tab,
        review_tab,
        detail_tab,
        evaluation_tab,
    ) = st.tabs(
        [
            "Overview",
            "Claims Review",
            "Claim Details",
            "Synthetic Evaluation",
        ]
    )

    with overview_tab:
        render_overview(scored)

    with review_tab:
        render_claims_review(scored)

    with detail_tab:
        render_claim_details(scored)

    with evaluation_tab:
        render_evaluation(scored)


if __name__ == "__main__":
    main()