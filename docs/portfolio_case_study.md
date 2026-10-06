# Portfolio case study: Hidden Hypertension

## The question

Among U.S. adults who meet a measured-blood-pressure or medication-based
hypertension proxy, how many report that they have never been told they have
hypertension—and which population groups show the largest awareness gaps?

## The approach

I linked three public-use CDC NHANES components covering demographics,
oscillometric blood-pressure measurements, and hypertension awareness and
treatment. I restricted the sample to 7,938 nonpregnant adults with at least two
valid readings and applied the special 2017-March 2020 examination weight,
strata, and PSUs.

The analysis has two reproducible implementations. SAS handles XPORT ingestion,
complex-survey estimates, domain analysis, and an adjusted descriptive model.
Python independently rebuilds the cohort, calculates Taylor-linearized estimates,
runs automated QA, and produces the visual dashboard.

## What I found

Using a >=130/80 mmHg or current-medication definition, 48.1% of adults met the
hypertension proxy. Among that group, 39.8% reported no prior diagnosis. The gap
was largest among adults aged 18-39 (64.3%) and fell with age. Only 44.2% of
treated adults had mean measured BP below 130/80 during the examination.

Changing the measured threshold to 140/90 reduced the apparent unawareness gap
to 21.0%, demonstrating how operational definitions change the public-health
story and the target population.

## Why it matters

The project separates prevalence, awareness, treatment, and control—four
different program decisions that are often collapsed into one statistic. It also
shows how to communicate subgroup patterns without converting descriptive
differences into causal claims.

## Tools

SAS 9.4-compatible code, Python, pandas, NumPy, Matplotlib, complex-survey
methods, QA/QC, reproducible documentation, and public CDC data.
