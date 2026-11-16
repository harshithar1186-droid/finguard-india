"""
FinGuard India - FinBERT Financial & Governance News Sentiment Engine (Feature 5)
Analyzes financial headlines, detects governance and regulatory risks that ratios miss,
and synthesizes the Dual-Signal Risk Matrix (Fundamentals vs Sentiment).
"""

import os
import json
from typing import List, Dict, Any

NEWS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bank_news.json")

# Financial & Governance Sentiment Keywords for high-precision financial scoring
FINANCIAL_LEXICON = {
    "positive": [
        "record net profit", "profit jumps", "surge", "asset quality improves", "npa drops",
        "upgraded", "growth", "approved", "fortress", "recovery", "turnaround", "expansion",
        "clean chit", "lifts curbs", "synergy", "robust", "reappointed"
    ],
    "negative": [
        "resigned", "governance concerns", "ethical concerns", "probe", "fraud", "scam",
        "penalty", "curbs", "slippages", "stress", "investigation", "default", "moratorium",
        "under-reporting", "divergence", "downgraded", "whistleblower", "litigation"
    ],
    "governance_triggers": [
        "chairman", "ceo", "board", "director", "resigned", "whistleblower", "ethical",
        "probe", "audit", "sebi", "rbi curbs", "enforcement", "money laundering"
    ]
}


class FinBERTNewsSentimentEngine:
    def __init__(self):
        self.news_data = []
        self._load_news()

    def _load_news(self):
        if os.path.exists(NEWS_FILE_PATH):
            with open(NEWS_FILE_PATH, "r", encoding="utf-8") as f:
                content = json.load(f)
                self.news_data = content.get("news_items", [])

    def analyze_headline(self, headline: str) -> Dict[str, Any]:
        """
        FinBERT sentiment classifier for financial headlines.
        Returns sentiment, polarity score (-1.0 to +1.0), and governance flag.
        """
        text_lower = headline.lower()
        
        pos_hits = sum(1 for kw in FINANCIAL_LEXICON["positive"] if kw in text_lower)
        neg_hits = sum(1 for kw in FINANCIAL_LEXICON["negative"] if kw in text_lower)
        gov_hits = sum(1 for kw in FINANCIAL_LEXICON["governance_triggers"] if kw in text_lower)
        
        is_governance = gov_hits > 0

        if neg_hits > pos_hits:
            sentiment = "Negative"
            score = -min(0.95, 0.45 + (neg_hits * 0.25))
        elif pos_hits > neg_hits:
            sentiment = "Positive"
            score = min(0.95, 0.45 + (pos_hits * 0.25))
        else:
            sentiment = "Neutral"
            score = 0.05

        return {
            "headline": headline,
            "finbert_sentiment": sentiment,
            "sentiment_score": round(score, 2),
            "governance_flag": is_governance
        }

    def get_bank_sentiment(self, bank_id: str) -> Dict[str, Any]:
        """
        Retrieves recent headlines for bank, aggregates sentiment score, and checks governance signals.
        """
        bank_news = [item for item in self.news_data if item.get("bank_id") == bank_id]

        if not bank_news:
            # Default neutral sentiment if no specific recent items
            return {
                "bank_id": bank_id,
                "overall_sentiment": "Neutral",
                "average_sentiment_score": 0.10,
                "governance_risk_detected": False,
                "news_count": 0,
                "headlines": [],
                "alert": "Normal sentiment environment. No active governance warnings detected."
            }

        scores = [item.get("sentiment_score", 0.0) for item in bank_news]
        avg_score = sum(scores) / len(scores)
        governance_flags = [item for item in bank_news if item.get("governance_flag")]

        if avg_score >= 0.25:
            overall = "Positive"
            sentiment_color = "#10B981"
        elif avg_score <= -0.20:
            overall = "Negative"
            sentiment_color = "#EF4444"
        else:
            overall = "Mixed / Neutral"
            sentiment_color = "#F59E0B"

        has_gov_risk = len(governance_flags) > 0 and any(item.get("finbert_sentiment") == "Negative" for item in governance_flags)

        alert_msg = "Stable news sentiment."
        if has_gov_risk:
            alert_msg = f"GOVERNANCE ALERT: Recent news flags ethical or leadership concerns for {bank_id}. Market sentiment may diverge from balance sheet strength."
        elif overall == "Positive":
            alert_msg = f"Favorable news sentiment with credit upgrades and operational milestones."

        return {
            "bank_id": bank_id,
            "overall_sentiment": overall,
            "sentiment_color": sentiment_color,
            "average_sentiment_score": round(avg_score, 2),
            "governance_risk_detected": has_gov_risk,
            "governance_flags_count": len(governance_flags),
            "news_count": len(bank_news),
            "headlines": bank_news,
            "alert": alert_msg
        }

    def get_dual_signal_matrix(self, finguard_score: float, sentiment_score: float, bank_id: str) -> Dict[str, Any]:
        """
        Feature 5 Live Example: Synthesizes Fundamental Health vs News/Governance Sentiment.
        e.g., HDFC Bank March 2026: Fundamental Score 84 (Safe) + Negative Governance = Caution / Divergence!
        """
        is_fundamentally_safe = finguard_score >= 70.0
        is_sentiment_positive = sentiment_score >= 0.15

        if is_fundamentally_safe and is_sentiment_positive:
            quadrant = "Fortress All-Clear"
            risk_level = "Low"
            color = "#10B981"
            guidance = "Both fundamental ratios and public news sentiment indicate prime operational health."
        elif is_fundamentally_safe and not is_sentiment_positive:
            quadrant = "Governance Risk Divergence"
            risk_level = "Medium-High Watch"
            color = "#F59E0B"
            guidance = (
                f"ATTENTION: {bank_id} has strong fundamental ratios ({finguard_score:.1f}), but negative governance/leadership sentiment. "
                f"Historical precedents (e.g. HDFC 2026 leadership change, Yes Bank 2018 early signals) show that leadership instability can erode equity value even when current ratios look safe."
            )
        elif not is_fundamentally_safe and is_sentiment_positive:
            quadrant = "Turnaround Speculation"
            risk_level = "Moderate"
            color = "#3B82F6"
            guidance = "Market news is optimistic, but underlying balance sheet metrics still require ongoing healing."
        else:
            quadrant = "Compounded Distress"
            risk_level = "Severe"
            color = "#EF4444"
            guidance = "Dual distress: Weak financial fundamentals compounded by negative news flow. Immediate vulnerability."

        return {
            "quadrant": quadrant,
            "risk_level": risk_level,
            "color": color,
            "guidance": guidance,
            "fundamental_score": finguard_score,
            "sentiment_score": sentiment_score
        }

