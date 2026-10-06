from pathlib import Path
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class OutputChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overall = pd.read_csv(ROOT / "outputs/tables/overall_estimates.csv")
        cls.sensitivity = pd.read_csv(ROOT / "outputs/tables/threshold_sensitivity.csv")
        cls.quality = pd.read_csv(ROOT / "outputs/tables/data_quality_checks.csv")

    def test_four_headline_measures(self):
        self.assertEqual(len(self.overall), 4)
        self.assertTrue(self.overall["estimate"].between(0, 1).all())
        self.assertTrue((self.overall["lcl"] <= self.overall["estimate"]).all())
        self.assertTrue((self.overall["estimate"] <= self.overall["ucl"]).all())

    def test_expected_analytic_n(self):
        row = self.quality.loc[self.quality["check"].eq("Final analytic adults"), "value"]
        self.assertEqual(int(row.iloc[0]), 7938)

    def test_no_duplicate_respondents(self):
        row = self.quality.loc[self.quality["check"].eq("Duplicate respondent IDs"), "value"]
        self.assertEqual(int(row.iloc[0]), 0)

    def test_threshold_sensitivity_direction(self):
        estimates = self.sensitivity.set_index("measure")["estimate"]
        self.assertGreater(estimates.iloc[0], estimates.iloc[2])
        self.assertGreater(estimates.iloc[1], estimates.iloc[3])

    def test_dashboard_exists(self):
        figure = ROOT / "outputs/figures/hypertension_awareness_dashboard.png"
        self.assertTrue(figure.exists())
        self.assertGreater(figure.stat().st_size, 100_000)


if __name__ == "__main__":
    unittest.main()
