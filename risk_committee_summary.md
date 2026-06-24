\# Credit Risk Scorecard — Risk Committee Summary



\## Objective

Build a Probability of Default (PD) model to classify loan applicants 

as Good or Bad borrowers using LendingClub data (176,075 loans).



\## Methodology

\- Target Variable: Binary (1 = Default, 0 = Fully Paid)

\- Feature Selection: Information Value (IV) — 12 variables selected

\- Transformation: Weight of Evidence (WoE) encoding

\- Model: Logistic Regression with scorecard scaling (300–850)



\## Key Risk Drivers

| Feature | IV | Risk Direction |

|---|---|---|

| Sub Grade | 0.65 | Higher grade = lower risk |

| Interest Rate | 0.64 | Higher rate = higher risk |

| Term | 0.32 | 60 months riskier than 36 |

| DTI | 0.09 | Higher DTI = higher risk |



\## Model Performance

| Metric | Score | Benchmark | Status |

|---|---|---|---|

| Gini | 0.47 | 0.45–0.75 | Pass |

| KS | 0.34 | > 0.30 | Pass |

| AUC | 0.74 | > 0.70 | Pass |



\## Score Distribution

\- Good borrowers: concentrated above 535

\- Bad borrowers: concentrated below 525

\- Recommended cutoff: 530



\## Business Recommendation

Reject all applications scoring below 530. This captures the majority 

of bad borrowers while approving most good borrowers. At current default 

rate of 19.93%, this threshold reduces expected credit losses significantly.



\## Limitations

\- Model trained on US data — recalibration needed for GCC deployment

\- Economic cycle not accounted for — stress testing recommended

\- Requires annual redevelopment as borrower behavior shifts



