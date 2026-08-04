# ClaimGuard

ClaimGuard is a proof of concept for healthcare claims review. It uses synthetic claims data, transparent rules, and anomaly detection to help prioritize claims for manual review.

This project is being developed for Cotiviti's internship assessment under Topic 2: Clinical Decision Making and Pattern Recognition in Health Care.

## Project Scope

The research portion of the project will cover applications across:

- Treatment
- Payment
- Operations

The working prototype will focus on payment integrity and claims-review prioritization.

The system will identify unusual patterns in synthetic claims, explain why a claim was flagged, and recommend a review priority. It will not make final payment decisions.

## Planned Features

- Generate a reproducible synthetic claims dataset
- Validate and preprocess claim records
- Apply explainable claim-review rules
- Detect unusual patterns using Isolation Forest
- Assign a review-priority score
- Explain the main reasons behind each result
- Display claims and insights in a Streamlit dashboard
- Evaluate results against injected synthetic anomalies

## Planned Technology Stack

- Python
- Pandas
- NumPy
- scikit-learn
- Streamlit
- Plotly
- Pytest

## Repository Structure

```text
claimguard-ai/
├── README.md
├── app.py
├── requirements.txt
├── data/
├── src/
├── tests/
├── report/
├── presentation/
├── screenshots/
└── video/