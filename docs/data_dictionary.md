# Analytic data dictionary

| Variable | Definition |
|---|---|
| `SEQN` | NHANES public respondent sequence number |
| `WTMECPRP` | 2017-March 2020 pre-pandemic MEC examination weight |
| `SDMVSTRA`, `SDMVPSU` | Masked variance stratum and primary sampling unit |
| `mean_sbp`, `mean_dbp` | Mean of available oscillometric readings; at least two required |
| `aware` | Respondent reported ever being told by a health professional that they had hypertension |
| `treated` | Respondent currently taking prescribed antihypertensive medicine |
| `htn130` | Mean BP >=130/80 mmHg or current medication |
| `unaware130` | Meets `htn130` and reports never having been told of hypertension |
| `controlled130` | Current medication and mean BP below 130/80 mmHg |
| `htn140`, `unaware140` | Sensitivity definitions using the >=140/90 mmHg threshold |

The hypertension variables are analytic screening proxies, not individual
clinical diagnoses. A single NHANES examination does not replace longitudinal
clinical assessment.
