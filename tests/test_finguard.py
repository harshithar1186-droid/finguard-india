"""
Unit tests and pipeline verification for FinGuard India.
"""

import unittest
from src.data_pipeline import FinGuardPipeline
from src.personal_risk import evaluate_personal_fd_exposure, evaluate_personal_equity_exposure
from src.crisis_validator import HistoricalCrisisValidator
from src.news_sentiment import FinBERTNewsSentimentEngine


class TestFinGuardPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = FinGuardPipeline()
        cls.pipeline.initialize()
        cls.validator = HistoricalCrisisValidator()
        cls.sentiment = FinBERTNewsSentimentEngine()

    def test_all_master_banks_loaded(self):
        self.assertGreaterEqual(len(self.pipeline.records_by_bank), 100)
        self.assertGreaterEqual(len(self.pipeline.all_snapshots), 900)

    def test_leaderboard_fy24(self):
        leaderboard = self.pipeline.get_leaderboard(2024)
        self.assertGreaterEqual(len(leaderboard), 80)
        self.assertEqual(leaderboard[0]["rank"], 1)
        # Scores must be between 0 and 100
        for b in leaderboard:
            self.assertGreaterEqual(b["finguard_score"], 0.0)
            self.assertLessEqual(b["finguard_score"], 100.0)
            self.assertIn(b["zone"], ["Safe", "Caution", "At-Risk", "Critical"])

    def test_bank_profile_and_shap(self):
        profile = self.pipeline.get_bank_full_profile("SBI")
        self.assertEqual(profile["bank_id"], "SBI")
        self.assertIn("shap_explainability", profile)
        shap = profile["shap_explainability"]
        self.assertIn("attributions", shap)
        self.assertEqual(len(shap["attributions"]), 8)
        self.assertIn("forecast", profile)
        self.assertEqual(len(profile["forecast"]["projections"]), 2)

    def test_personal_fd_connector(self):
        profile = self.pipeline.get_bank_full_profile("HDFC")
        fd_eval = evaluate_personal_fd_exposure(
            bank_id="HDFC",
            bank_name=profile["bank_name"],
            fd_amount_inr=100000.0,
            current_finguard_score=profile["current_score"],
            current_zone=profile["current_zone"],
            biggest_risk_factor=profile["biggest_risk_factor"]
        )
        self.assertTrue(fd_eval["is_fully_covered"])
        self.assertEqual(fd_eval["dicgc_covered_inr"], 100000.0)

        # High value FD with uninsured excess
        fd_high = evaluate_personal_fd_exposure(
            bank_id="HDFC",
            bank_name=profile["bank_name"],
            fd_amount_inr=1200000.0,
            current_finguard_score=profile["current_score"],
            current_zone=profile["current_zone"],
            biggest_risk_factor=profile["biggest_risk_factor"]
        )
        self.assertFalse(fd_high["is_fully_covered"])
        self.assertEqual(fd_high["uninsured_excess_inr"], 700000.0)

    def test_historical_crisis_validation(self):
        summaries = self.validator.get_all_crisis_summaries()
        self.assertEqual(len(summaries), 4)
        entity_ids = [s["entity_id"] for s in summaries]
        self.assertIn("YES_BANK", entity_ids)
        self.assertIn("PMC_BANK", entity_ids)
        self.assertIn("ILFS", entity_ids)
        self.assertIn("DHFL", entity_ids)

        # Check Yes Bank details
        yes_detail = self.validator.get_crisis_detail("YES_BANK")
        self.assertEqual(yes_detail["lead_time_months"], 18)
        self.assertEqual(yes_detail["timeline"][-1]["zone"], "Critical")

    def test_finbert_sentiment(self):
        result = self.sentiment.analyze_headline("Chairman resigned citing board governance and ethical concerns")
        self.assertEqual(result["finbert_sentiment"], "Negative")
        self.assertTrue(result["governance_flag"])


if __name__ == "__main__":
    unittest.main()

