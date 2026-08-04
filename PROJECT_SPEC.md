# Project Specification

## Project

**ClaimGuard: Explainable Pattern Recognition for Healthcare Claims Review**

## Assessment Topic

This project addresses Topic 2: Clinical Decision Making and Pattern Recognition in Health Care.

The report and presentation will cover examples across Treatment, Payment, and Operations. The proof of concept will focus on Payment, specifically claims-review prioritization.

## Problem

Claims-review teams may need to examine a large number of claims with limited time. Treating every claim as equally important can make review slower and less efficient.

ClaimGuard will test whether a combination of simple rules and anomaly detection can help rank synthetic claims for review. For each claim, the system will show the review priority and the main reasons behind it.

The system will support a reviewer. It will not make a final payment decision.

## Intended User

A payment-integrity or claims-review analyst.

## Research Scope

### Treatment

The report may discuss:

- Patient-risk classification
- Care prioritization
- Clinical decision support
- Readmission or deterioration prediction
- Human oversight in treatment-related AI

### Payment

The report and prototype will focus on:

- Claims pattern recognition
- Payment-integrity review
- Billing and coding checks
- Anomaly detection
- Review-priority scoring

### Operations

The report may discuss:

- Workload forecasting
- Claims-processing delays
- Queue monitoring
- Capacity planning
- Time-series anomaly detection

## Proof of Concept

The prototype will:

1. Generate or load synthetic claims data.
2. Validate the required fields.
3. Apply a small set of explainable rules.
4. Run an anomaly-detection model.
5. Combine the rule and model results into a review score.
6. Classify each claim by review priority.
7. Show the reasons behind the score.
8. Recommend a next review step.
9. Display the results in a Streamlit dashboard.

## Initial Data Fields

The generated dataset is expected to include:

- claim_id
- patient_id
- provider_id
- service_date
- diagnosis_group
- procedure_code
- claim_amount
- expected_amount
- days_since_similar_claim
- provider_average_amount

Additional derived fields may be added during implementation.

## Review Categories

- Routine
- Review Recommended
- High-Priority Review

These labels describe review priority only. They do not indicate fraud, invalid billing, or claim denial.

## Detection Approach

### Rules

The first version may check for:

- Claim amounts well above expected values
- Similar claims submitted within a short time
- Repeated procedures within an unusual time window
- Provider billing above comparable patterns
- Simplified diagnosis-procedure mismatches

### Anomaly Detection

Isolation Forest will be used as the initial model because it is lightweight and works well for a small demonstration without labeled training data.

### Final Score

The rule score and anomaly score will be combined into a documented review-priority score. The calculation must remain simple enough to explain during the presentation.

## Synthetic Data

The dataset will be generated with Python using a fixed random seed.

It will contain:

- Routine synthetic claims
- Injected anomalous patterns
- Ground-truth fields used only for evaluation

Ground-truth fields will not be included in the model inputs.

## Success Criteria

The proof of concept is complete when it can:

- Generate or load the dataset
- Validate the expected columns
- Apply all configured rules
- Run anomaly detection without errors
- Score every claim
- Produce readable explanations
- Filter and inspect claims in the dashboard
- Show stable examples of routine, review-recommended, and high-priority claims
- Produce repeatable results for the recorded demo

## Deliverables

The final repository will include:

- Two-page Microsoft Word report
- Bibliography on a third page
- Working proof of concept
- Microsoft PowerPoint presentation
- Recorded presentation and demo
- Source code and synthetic dataset
- Setup and run instructions

## Out of Scope

The first version will not include:

- Separate Treatment and Operations applications
- Real patient or claims data
- Automatic claim approval or denial
- Fraud determination
- Medical recommendations
- React or FastAPI
- User authentication
- Production databases
- Cloud deployment
- RAG or a multi-agent system
- Production compliance claims

## Scope Rules

- Treatment and Operations stay in the research and strategy discussion.
- Payment remains the only prototype use case.
- All data stays synthetic.
- Every feature must support the report, prototype, presentation, or demo.
- A stable and explainable feature is preferred over a more complex unfinished one.