# ClaimGuard Research Notes

## Assessment-Aligned Scope

This research supports Topic 2: **Clinical Decision Making and Pattern Recognition in Health Care**.

The final report will:

- define the topic;
- analyze relevant trends;
- describe opportunities and threats; and
- propose strategic options for Cotiviti.

The research discussion will cover **Treatment, Payment, and Operations (TPO)**. The proof of concept will focus on **Payment**, using synthetic claims data to demonstrate review prioritization through transparent rules and anomaly detection.

## Working Thesis

Healthcare decision-support systems are moving from isolated rules or single predictive models toward hybrid systems that combine pattern recognition, machine learning, structured reasoning, and human review. Across Treatment, Payment, and Operations, the main opportunity is better prioritization and more consistent decisions. The main risk is allowing unreliable, biased, or poorly explained outputs to influence high-impact decisions without sufficient oversight.

For Cotiviti, the strongest near-term opportunity is an explainable claims-review assistant that combines deterministic rules, anomaly detection, and human review. This is closely aligned with Cotiviti's existing payment-integrity work and is narrow enough to demonstrate clearly in a hackathon proof of concept.

---

## 1. Topic Definition

Clinical decision making is the process of using available evidence, patient or claims information, policies, and professional judgment to choose an action. Pattern recognition supports that process by identifying recurring relationships, groups, trends, and unusual observations within healthcare data.

Topic 2 includes several related technical approaches:

- **Classification:** assigning an observation to a defined category.
- **Prediction:** estimating a future outcome or value.
- **Inference:** drawing a conclusion from available evidence.
- **Clustering:** grouping similar observations without predefined labels.
- **Time-series anomaly detection:** identifying unusual behavior across time.
- **Reasoning and agentic AI:** coordinating multi-step tasks, tools, or actions toward a defined goal.

These approaches can support decisions across Treatment, Payment, and Operations, but the level of acceptable automation depends on the impact of the decision and the quality of the evidence behind it.

---

## 2. Treatment

### Relevant Application

In Treatment, AI-based clinical decision-support systems can help clinicians identify risk, interpret patient-specific information, and consider evidence-based recommendations. A 2024 review of 26 studies found recurring applications in early detection and diagnosis, decision support, medication-error reduction, and clinician-facing workflows.

### Opportunity

The main opportunity is improved prioritization: helping clinicians identify patients who may need attention sooner, while reducing repetitive information review.

### Threat

Treatment decisions directly affect patients. Incorrect predictions, biased models, poor explanations, or automation bias can create clinical harm. Treatment-related AI therefore requires strong validation and meaningful clinician oversight.

### Role in This Project

Treatment will be covered in the report and presentation to show the broader TPO landscape. It will not be implemented in the proof of concept.

**Primary source:** Ouanes and Farhah (2024).

---

## 3. Payment

### Relevant Application

Payment-integrity teams review claims for coding errors, inappropriate billing, unusual utilization, and patterns that may require investigation. Cotiviti states that its Payment Accuracy capabilities use large sets of payment rules and policies, prepay and postpay review, artificial intelligence, deterministic rules, and pattern analysis.

This makes Payment the most direct Cotiviti-aligned use case for the prototype.

### Research Trend

Healthcare claims research uses supervised, unsupervised, and hybrid machine-learning methods. A 2025 systematic review of 137 experimental studies found substantial use of both supervised and unsupervised approaches. The review also identified recurring problems: inconsistent data, limited standardization, privacy restrictions, and a shortage of labeled cases.

### Opportunity

A hybrid review system can:

- prioritize claims for manual review;
- detect combinations that fixed rules may miss;
- explain transparent rule violations;
- improve reviewer consistency; and
- help analysts focus limited time on higher-priority cases.

### Threat

An anomaly is not proof of fraud, waste, abuse, incorrect coding, or an improper payment. False positives can waste reviewer time or create unnecessary payment friction. Model outputs should therefore be treated as review signals rather than final decisions.

### Role in This Project

Payment is the only proof-of-concept implementation area.

**Primary sources:** Cotiviti Payment Accuracy; Cotiviti Claim Pattern Review; du Preez et al. (2025).

---

## 4. Operations

### Relevant Application

Healthcare Operations includes demand forecasting, staffing, queue management, capacity planning, and process monitoring. A 2025 review of 156 studies on unscheduled-care forecasting found that forecasting is used to support operational, tactical, and strategic decisions across emergency, inpatient, ambulatory, surgical, home, and telecare settings.

### Opportunity

Forecasting and time-series analysis can help organizations anticipate demand, allocate resources, and identify unusual process behavior.

### Threat

Operational models can fail when demand patterns change, data feeds are delayed, or model performance is measured only with technical metrics instead of real workflow outcomes.

### Role in This Project

Operations will be covered in the report and presentation. It will not be implemented in the proof of concept.

**Primary source:** Shi, Rostami-Tabar, and Gartner (2025).

---

## 5. Relevant Trends

Only trends that directly support the assessment and project should appear in the final report.

### 5.1 Hybrid Decision Support

Rules are transparent and easy to audit but may miss unfamiliar patterns. Machine learning can identify broader relationships but may be harder to explain. Cotiviti's public Payment Accuracy material describes the use of both artificial intelligence and deterministic rules, supporting a hybrid design.

### 5.2 Human-in-the-Loop Decisions

Across TPO, AI is most defensible when it supports a qualified reviewer rather than making an irreversible high-impact decision on its own. This is especially important when model outputs affect treatment, payment, or access to services.

### 5.3 Unsupervised Anomaly Detection

Claims datasets may contain few confirmed labels and many unknown patterns. Unsupervised methods can rank unusual observations without requiring a large labeled training set. Isolation Forest is appropriate for this demonstration because it isolates unusual observations through recursive random partitioning and is lightweight enough for a small prototype.

### 5.4 Emerging Agentic AI

Agentic AI systems can pursue goals, invoke tools, and coordinate multi-step tasks. A 2026 healthcare review found promising demonstrations but only seven eligible studies; most were exploratory and lacked robust clinical validation. Agentic AI should therefore be presented as an emerging direction, not as a mature replacement for human decision makers.

### 5.5 Governance and Explainability

WHO guidance emphasizes that AI for health should protect autonomy, safety, transparency, accountability, privacy, and equity. These concerns apply across TPO even when the model is used for administrative rather than clinical decisions.

### 5.6 Synthetic Data for Prototyping

CMS publishes synthetic claims files specifically to help analysts and software developers become familiar with claims data, develop applications, and test data-mining ideas while protecting beneficiary privacy. CMS also warns that synthetic data has limited value for drawing conclusions about real populations.

That same boundary will apply to ClaimGuard: synthetic data is suitable for proving the workflow, but synthetic performance cannot establish real-world accuracy.

---

## 6. Opportunities

### Treatment

- Earlier identification of risk
- Better prioritization of clinical attention
- More consistent access to patient-specific evidence
- Reduced repetitive information review

### Payment

- Faster prioritization of claims for review
- Detection of patterns across multiple claim attributes
- More consistent reviewer workflows
- Clear reasons for why a claim was surfaced
- Better use of limited analyst capacity

### Operations

- Demand and workload forecasting
- Capacity and staffing support
- Identification of unusual process delays
- Better operational planning under uncertainty

### Shared Opportunity

The shared opportunity across TPO is not full automation. It is using pattern recognition to direct human attention where it is most useful.

---

## 7. Threats

The final report should focus on the following high-value risks:

- **False positives and false negatives:** unusual does not always mean incorrect, and normal-looking records may still contain issues.
- **Data quality:** incomplete, inconsistent, or outdated data can distort results.
- **Bias:** historical data can reproduce unequal patterns.
- **Privacy and security:** healthcare data is highly sensitive.
- **Poor explainability:** users may not understand why a system produced a recommendation.
- **Automation bias:** users may trust a model even when the available evidence is weak.
- **Model drift:** performance can change as coding, utilization, policies, or workflows change.
- **Generative AI error:** generated explanations may sound convincing while being unsupported.
- **Weak validation:** agentic and other emerging systems may look impressive in demonstrations without sufficient real-world evidence.
- **Unclear accountability:** organizations must retain responsibility for decisions influenced by AI.

---

## 8. Strategic Options for Cotiviti

### Option 1: Pilot an Explainable Claims-Review Assistant

Cotiviti could test a reviewer-facing system that combines:

- deterministic payment rules;
- anomaly or pattern scores;
- claim-level explanations;
- recommended review actions; and
- final human judgment.

The system should prioritize work rather than approve, deny, or label claims automatically.

### Option 2: Build a Shared AI Evaluation and Governance Layer

Cotiviti could standardize how AI-assisted TPO systems are evaluated before and after deployment. The layer could track:

- precision and false-positive burden;
- performance by claim or population segment;
- explanation quality;
- model and data drift;
- reviewer acceptance and override rates; and
- audit history.

This would provide a controlled foundation for future generative or agentic AI use.

### Recommended Position

Cotiviti should favor **bounded, explainable, human-supervised AI** over unrestricted autonomous decision making. Payment integrity is a practical starting point because it is central to Cotiviti's current work and supports measurable reviewer workflows.

---

## 9. Proof-of-Concept Research Basis

### POC Question

Can a simple hybrid system use transparent rules and unsupervised anomaly detection to prioritize synthetic healthcare claims for manual review and explain the main reasons behind each result?

### Input

A reproducible synthetic claims dataset generated with Python.

### Processing

1. Validate required data fields.
2. Calculate simple derived features.
3. Apply transparent prototype rules.
4. Run Isolation Forest on selected numerical features.
5. Combine rule and model outputs into a review-priority score.
6. Generate explanations directly from actual rule results and model output.

### Output

- Routine
- Review Recommended
- High-Priority Review

Each result will include reasons and a suggested human-review action.

### Evaluation

Injected synthetic anomalies will be used only to evaluate whether the prototype detects the patterns it was designed to demonstrate. Ground-truth fields will not be used as model inputs.

### Method Boundaries

The POC will not:

- identify fraud;
- determine claim validity;
- approve or deny claims;
- reproduce Cotiviti's proprietary rules or products;
- use real patient or claims data; or
- claim real-world performance.

The claim-review rules are simplified demonstration heuristics, not official payment policy.

---

## 10. Source-to-Requirement Map

| Assessment requirement | Evidence used |
|---|---|
| Define the topic | Topic 2 wording; Ouanes and Farhah; Shi et al.; du Preez et al. |
| Analyze trends | Cotiviti Payment Accuracy; du Preez et al.; Collaco et al.; Liu et al. |
| Describe opportunities | Treatment decision support; claims prioritization; operations forecasting |
| Describe threats | WHO guidance; claims review limitations; agentic AI evidence limits |
| Propose options for Cotiviti | Cotiviti Payment Accuracy and Claim Pattern Review; WHO governance |
| Cite POC methods | CMS synthetic claims guidance; Liu et al. Isolation Forest |
| Explain why Payment is the POC | Cotiviti's stated payment-integrity and claims-pattern capabilities |

---

## 11. APA 7 Reference List

Centers for Medicare & Medicaid Services. (2026). *Medicare claims synthetic public use files (SynPUFs)*. https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files

Collaco, B. G., Haider, S. A., Prabha, S., Gomez-Cabello, C. A., Genovese, A., Wood, N. G., Bagaria, S. P., Gopala, N., Tao, C., et al. (2026). The role of agentic artificial intelligence in healthcare: A scoping review. *npj Digital Medicine, 9*, 345. https://doi.org/10.1038/s41746-026-02517-5

Cotiviti. (2026). *About us*. https://www.cotiviti.com/about

Cotiviti. (2026). *Claim Pattern Review*. https://www.cotiviti.com/solutions/payment-accuracy/claim-pattern-review

Cotiviti. (2026). *Healthcare claim payment accuracy solutions*. https://www.cotiviti.com/solutions/payment-accuracy

du Preez, A., Bhattacharya, S., Beling, P., & Bowen, E. (2025). Fraud detection in healthcare claims using machine learning: A systematic review. *Artificial Intelligence in Medicine, 160*, 103061. https://doi.org/10.1016/j.artmed.2024.103061

Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. In *2008 Eighth IEEE International Conference on Data Mining* (pp. 413–422). IEEE. https://doi.org/10.1109/ICDM.2008.17

Ouanes, K., & Farhah, N. (2024). Effectiveness of artificial intelligence in clinical decision support systems and care delivery. *Journal of Medical Systems, 48*, 74. https://doi.org/10.1007/s10916-024-02098-4

Shi, M., Rostami-Tabar, B., & Gartner, D. (2025). Looking for the crystal ball in unscheduled care: A systematic literature review of the forecasting process. *Health Care Management Science, 28*, 548–564. https://doi.org/10.1007/s10729-025-09711-z

World Health Organization. (2021). *Ethics and governance of artificial intelligence for health*. https://www.who.int/publications/i/item/9789240029200