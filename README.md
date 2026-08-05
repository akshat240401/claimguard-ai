# ClaimGuard

ClaimGuard is a proof of concept for healthcare claims review. It combines transparent rules with unsupervised anomaly detection to prioritize synthetic claims for manual review.

The project was developed for Cotiviti's internship assessment under Topic 2: Clinical Decision Making and Pattern Recognition in Health Care.

## Scope

The research portion covers applications across Treatment, Payment, and Operations. The working prototype focuses on Payment, specifically claims-review prioritization.

ClaimGuard does not identify fraud or make final claim decisions. It surfaces unusual patterns, explains the main reasons behind each result, and recommends a review action.

## How It Works

1. Generate a reproducible synthetic claims dataset.
2. Calculate amount and provider comparison features.
3. Apply five transparent review rules.
4. Score broader patterns with Isolation Forest.
5. Combine the rule and model signals into a review score.
6. Generate an explanation and recommended next step.
7. Display the results in a Streamlit dashboard.

## Review Signals

The rule engine checks for:

- High claim amounts
- Possible duplicate submissions
- Frequent repeat services
- Provider billing outliers
- Simplified diagnosis-procedure mismatches

The final review score uses:

```text
65% rule score + 35% anomaly score
```

Claims are grouped as:

- Routine
- Review Recommended
- High-Priority Review

## Synthetic Evaluation

The current dataset contains 1,000 synthetic claims:

- 100 injected anomalies
- 30 legitimate edge cases
- 870 standard routine claims

On the fixed synthetic dataset, ClaimGuard surfaced:

- 83 of 100 injected anomalies
- 63 of 900 routine claims
- 50 of 50 clear anomalies
- 33 of 50 subtle anomalies

These results demonstrate the workflow and the trade-off between anomaly coverage and reviewer workload. They do not represent production payment-integrity accuracy.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Generate the dataset:

```powershell
python src/data_generator.py
```

Run the tests:

```powershell
python -m pytest -q
```

Start the dashboard:

```powershell
python -m streamlit run app.py
```

Streamlit will normally open the application at `http://localhost:8501`.

## Repository Structure

```text
claimguard-ai/
├── app.py
├── requirements.txt
├── data/
│   └── synthetic_claims.csv
├── research/
│   └── notes.md
├── src/
│   ├── anomaly_detector.py
│   ├── claim_rules.py
│   ├── data_generator.py
│   ├── explanation_engine.py
│   ├── pipeline.py
│   └── risk_engine.py
├── tests/
│   └── test_pipeline.py
├── report/
├── presentation/
├── screenshots/
└── video/
```