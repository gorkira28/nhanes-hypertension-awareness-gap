"""Reproduce the NHANES hypertension awareness-gap portfolio analysis.

Primary estimates use the 2017-March 2020 pre-pandemic MEC weights and
Taylor-series linearization across masked variance strata and PSUs.
"""

from __future__ import annotations

from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"


def read_xpt(name: str) -> pd.DataFrame:
    return pd.read_sas(RAW / name, format="xport", encoding="utf-8")


def ratio_estimate(
    frame: pd.DataFrame,
    outcome: str,
    domain: pd.Series | None = None,
) -> dict[str, float]:
    """Weighted proportion and Taylor-linearized 95% CI for a survey domain."""
    d = frame.copy()
    if domain is None:
        domain = pd.Series(True, index=d.index)
    valid = domain.fillna(False) & d[outcome].notna() & d["WTMECPRP"].gt(0)
    denominator = float(d.loc[valid, "WTMECPRP"].sum())
    if denominator == 0:
        return {"estimate": np.nan, "se": np.nan, "lcl": np.nan, "ucl": np.nan,
                "design_df": np.nan, "n_unweighted": 0, "weighted_n": 0}
    estimate = float(
        np.average(d.loc[valid, outcome], weights=d.loc[valid, "WTMECPRP"])
    )
    d["_lin"] = 0.0
    d.loc[valid, "_lin"] = (
        d.loc[valid, "WTMECPRP"] * (d.loc[valid, outcome] - estimate) / denominator
    )
    psu = (
        d.groupby(["SDMVSTRA", "SDMVPSU"], observed=True)["_lin"]
        .sum()
        .reset_index()
    )
    variance = 0.0
    for _, group in psu.groupby("SDMVSTRA", observed=True):
        m = len(group)
        if m > 1:
            values = group["_lin"].to_numpy()
            variance += (m / (m - 1)) * float(((values - values.mean()) ** 2).sum())
    se = math.sqrt(max(variance, 0.0))
    design_df = int(psu.shape[0] - psu["SDMVSTRA"].nunique())
    critical = float(student_t.ppf(0.975, design_df)) if design_df > 0 else 1.96
    return {
        "estimate": estimate,
        "se": se,
        "lcl": max(0.0, estimate - critical * se),
        "ucl": min(1.0, estimate + critical * se),
        "design_df": design_df,
        "n_unweighted": int(valid.sum()),
        "weighted_n": denominator,
    }


def build_analysis() -> pd.DataFrame:
    demo = read_xpt("P_DEMO.xpt")
    bpq = read_xpt("P_BPQ.xpt")
    bpx = read_xpt("P_BPXO.xpt")
    d = demo.merge(bpq, on="SEQN", how="inner", validate="one_to_one")
    d = d.merge(bpx, on="SEQN", how="inner", validate="one_to_one")

    sys_cols = ["BPXOSY1", "BPXOSY2", "BPXOSY3"]
    dia_cols = ["BPXODI1", "BPXODI2", "BPXODI3"]
    d["bp_readings"] = d[sys_cols].notna().sum(axis=1)
    d["mean_sbp"] = d[sys_cols].mean(axis=1)
    d["mean_dbp"] = d[dia_cols].mean(axis=1)
    d["pregnant"] = d["RIDEXPRG"].eq(1)
    d["analytic"] = (
        d["RIDAGEYR"].ge(18)
        & ~d["pregnant"]
        & d["WTMECPRP"].gt(0)
        & d["bp_readings"].ge(2)
        & d["mean_sbp"].notna()
        & d["mean_dbp"].notna()
    )
    d = d.loc[d["analytic"]].copy()

    d["aware"] = np.select([d["BPQ020"].eq(1), d["BPQ020"].eq(2)], [1.0, 0.0], np.nan)
    d["treated"] = np.select([d["BPQ050A"].eq(1), d["BPQ050A"].eq(2)], [1.0, 0.0], 0.0)
    d["high_bp_130"] = (d["mean_sbp"].ge(130) | d["mean_dbp"].ge(80)).astype(float)
    d["high_bp_140"] = (d["mean_sbp"].ge(140) | d["mean_dbp"].ge(90)).astype(float)
    d["htn130"] = (d["high_bp_130"].eq(1) | d["treated"].eq(1)).astype(float)
    d["htn140"] = (d["high_bp_140"].eq(1) | d["treated"].eq(1)).astype(float)
    d["unaware130"] = np.where(d["htn130"].eq(1) & d["aware"].notna(), 1 - d["aware"], np.nan)
    d["unaware140"] = np.where(d["htn140"].eq(1) & d["aware"].notna(), 1 - d["aware"], np.nan)
    d["controlled130"] = np.where(
        d["treated"].eq(1),
        (d["mean_sbp"].lt(130) & d["mean_dbp"].lt(80)).astype(float),
        np.nan,
    )

    d["sex"] = d["RIAGENDR"].map({1: "Men", 2: "Women"})
    d["age_group"] = pd.cut(
        d["RIDAGEYR"], [17, 39, 59, np.inf], labels=["18-39", "40-59", "60+"]
    ).astype("object")
    d["race_ethnicity"] = d["RIDRETH3"].map(
        {
            1: "Mexican American",
            2: "Other Hispanic",
            3: "Non-Hispanic White",
            4: "Non-Hispanic Black",
            6: "Non-Hispanic Asian",
            7: "Other/multiracial",
        }
    )
    d["education"] = d["DMDEDUC2"].map(
        {1: "Less than high school", 2: "Less than high school", 3: "High school/GED",
         4: "Some college/AA", 5: "College graduate+"}
    )
    d["poverty_ratio"] = pd.cut(
        d["INDFMPIR"], [-np.inf, 1.3, 3.5, np.inf],
        labels=["<=1.30", "1.31-3.50", ">3.50"],
    ).astype("object")
    return d


def estimate_row(frame: pd.DataFrame, label: str, outcome: str, domain=None) -> dict:
    result = ratio_estimate(frame, outcome, domain)
    return {"measure": label, **result}


def make_outputs(d: pd.DataFrame) -> None:
    for folder in [PROCESSED, TABLES, FIGURES]:
        folder.mkdir(parents=True, exist_ok=True)

    keep = [
        "SEQN", "WTMECPRP", "SDMVSTRA", "SDMVPSU", "RIDAGEYR", "sex",
        "age_group", "race_ethnicity", "education", "poverty_ratio", "mean_sbp",
        "mean_dbp", "bp_readings", "aware", "treated", "htn130", "htn140",
        "unaware130", "unaware140", "controlled130",
    ]
    d[keep].to_csv(PROCESSED / "analytic_file.csv", index=False)

    overall = pd.DataFrame([
        estimate_row(d, "Hypertension proxy (>=130/80 or medication)", "htn130"),
        estimate_row(d, "Unaware among adults meeting hypertension proxy", "unaware130", d["htn130"].eq(1)),
        estimate_row(d, "Treated among adults meeting hypertension proxy", "treated", d["htn130"].eq(1)),
        estimate_row(d, "Controlled below 130/80 among treated adults", "controlled130", d["treated"].eq(1)),
    ])
    overall.to_csv(TABLES / "overall_estimates.csv", index=False)

    rows = []
    for variable in ["sex", "age_group", "race_ethnicity", "education", "poverty_ratio"]:
        for level in d[variable].dropna().unique():
            domain = d["htn130"].eq(1) & d[variable].eq(level)
            estimate = ratio_estimate(d, "unaware130", domain)
            rows.append({"dimension": variable, "group": str(level), **estimate})
    subgroup = pd.DataFrame(rows).sort_values(["dimension", "estimate"], ascending=[True, False])
    subgroup.to_csv(TABLES / "awareness_gap_by_subgroup.csv", index=False)

    sensitivity = pd.DataFrame([
        estimate_row(d, ">=130/80 definition: hypertension proxy", "htn130"),
        estimate_row(d, ">=130/80 definition: unawareness", "unaware130", d["htn130"].eq(1)),
        estimate_row(d, ">=140/90 definition: hypertension proxy", "htn140"),
        estimate_row(d, ">=140/90 definition: unawareness", "unaware140", d["htn140"].eq(1)),
    ])
    sensitivity.to_csv(TABLES / "threshold_sensitivity.csv", index=False)

    quality = pd.DataFrame(
        {
            "check": [
                "Merged participants before eligibility filters",
                "Final analytic adults",
                "Analytic adults with 3 BP readings",
                "Analytic adults with valid awareness response",
                "Masked strata represented",
                "Masked PSUs represented",
                "Duplicate respondent IDs",
            ],
            "value": [
                len(read_xpt("P_DEMO.xpt").merge(read_xpt("P_BPQ.xpt"), on="SEQN").merge(read_xpt("P_BPXO.xpt"), on="SEQN")),
                len(d),
                int(d["bp_readings"].eq(3).sum()),
                int(d["aware"].notna().sum()),
                int(d["SDMVSTRA"].nunique()),
                int(d[["SDMVSTRA", "SDMVPSU"]].drop_duplicates().shape[0]),
                int(d["SEQN"].duplicated().sum()),
            ],
        }
    )
    quality.to_csv(TABLES / "data_quality_checks.csv", index=False)

    make_figure(overall, subgroup)


def pct(x: float) -> float:
    return 100 * x


def make_figure(overall: pd.DataFrame, subgroup: pd.DataFrame) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(15, 9), facecolor="#F7FAFC")
    grid = fig.add_gridspec(2, 2, height_ratios=[0.8, 1.35], hspace=0.35, wspace=0.22)
    navy, teal, coral, gold = "#15324B", "#168C86", "#E76F51", "#E9B44C"

    ax0 = fig.add_subplot(grid[0, :])
    ax0.axis("off")
    vals = overall.set_index("measure")["estimate"]
    cards = [
        ("National hypertension proxy", pct(vals.iloc[0]), navy),
        ("Unaware among affected adults", pct(vals.iloc[1]), coral),
        ("Receiving medication", pct(vals.iloc[2]), teal),
        ("Controlled among treated", pct(vals.iloc[3]), gold),
    ]
    for i, (label, value, color) in enumerate(cards):
        x = 0.02 + i * 0.245
        ax0.add_patch(plt.Rectangle((x, 0.08), 0.225, 0.78, transform=ax0.transAxes,
                                    color="white", ec="#DDE6ED", lw=1.2))
        ax0.text(x + 0.02, 0.62, f"{value:.1f}%", transform=ax0.transAxes,
                 fontsize=30, weight="bold", color=color)
        ax0.text(x + 0.02, 0.28, label, transform=ax0.transAxes,
                 fontsize=11, color=navy, wrap=True)
    ax0.text(0.02, 1.02, "The hypertension awareness gap in U.S. adults",
             transform=ax0.transAxes, fontsize=22, weight="bold", color=navy)
    ax0.text(0.02, 0.91, "NHANES 2017-March 2020 pre-pandemic | survey-weighted estimates",
             transform=ax0.transAxes, fontsize=12, color="#52616B")

    ax1 = fig.add_subplot(grid[1, 0])
    age = subgroup[subgroup["dimension"].eq("age_group")].copy()
    order = ["18-39", "40-59", "60+"]
    age["group"] = pd.Categorical(age["group"], order, ordered=True)
    age = age.sort_values("group")
    x = np.arange(len(age))
    y = age["estimate"].map(pct).to_numpy()
    lower = (age["estimate"] - age["lcl"]).map(pct).to_numpy()
    upper = (age["ucl"] - age["estimate"]).map(pct).to_numpy()
    ax1.bar(x, y, color=[coral, gold, teal], width=0.62)
    ax1.errorbar(x, y, yerr=[lower, upper], fmt="none", ecolor=navy, capsize=4)
    ax1.set_xticks(x, age["group"])
    ax1.set_ylabel("Unaware among adults meeting proxy (%)")
    ax1.set_title("Awareness gap by age", loc="left", weight="bold", color=navy)
    ax1.set_ylim(0, max(60, float(np.nanmax(upper + y)) + 8))
    for i, v in enumerate(y):
        ax1.text(i, v + 2, f"{v:.1f}%", ha="center", weight="bold", color=navy)

    ax2 = fig.add_subplot(grid[1, 1])
    race = subgroup[subgroup["dimension"].eq("race_ethnicity")].sort_values("estimate")
    y_pos = np.arange(len(race))
    ax2.barh(y_pos, race["estimate"].map(pct), color=teal, alpha=0.9)
    ax2.set_yticks(y_pos, race["group"])
    ax2.set_xlabel("Unaware among adults meeting proxy (%)")
    ax2.set_title("Awareness gap by race and Hispanic origin", loc="left", weight="bold", color=navy)
    for i, v in enumerate(race["estimate"].map(pct)):
        ax2.text(v + 0.6, i, f"{v:.1f}%", va="center", fontsize=9, color=navy)

    fig.text(0.01, 0.01,
             "Hypertension proxy: mean measured BP >=130/80 mmHg or current antihypertensive medication. "
             "Descriptive screening analysis; not a clinical diagnosis or causal model.",
             fontsize=9.5, color="#52616B")
    fig.savefig(FIGURES / "hypertension_awareness_dashboard.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    data = build_analysis()
    make_outputs(data)
    print(f"Analysis complete: {len(data):,} eligible adults")


if __name__ == "__main__":
    main()
