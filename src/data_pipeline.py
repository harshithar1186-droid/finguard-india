"""
FinGuard India - Master Data Pipeline (120 Banks, 2015-2024 Master Dataset)
Loads 932 historical bank-year records, classifies ownership, computes PCR and advances,
and indexes for the REST API and web dashboard.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.ratio_engine import compute_composite_finguard_score, RATIO_CONFIGS
from src.ml_scoring import FinGuardMLModel, classify_trajectory
from src.forecaster import forecast_health_scores
from src.news_sentiment import FinBERTNewsSentimentEngine

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "banks_master_dataset.csv")
CRISES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "historical_crises.json")

# Classification Keywords
PSU_KEYWORDS = [
    "state bank", "bank of baroda", "punjab national bank", "canara bank", "union bank",
    "bank of india", "indian bank", "central bank of india", "indian overseas bank", "uco bank",
    "bank of maharashtra", "punjab and sind bank", "punjab & sind bank", "allahabad bank",
    "andhra bank", "corporation bank", "dena bank", "oriental bank", "syndicate bank",
    "united bank of india", "vijaya bank", "sbbj", "sbh", "sbm", "sbp", "sbt", "bharatiya mahila"
]

SFB_KEYWORDS = ["small finance", "sfb"]
PAYMENT_KEYWORDS = ["payments bank", "payment bank"]

FOREIGN_KEYWORDS = [
    "abu dhabi", "american express", "australia and new zealand", "anz", "bank of america",
    "bank of bahrain", "bank of ceylon", "bank of china", "bank of nova scotia", "barclays",
    "bnp paribas", "citibank", "commonwealth bank", "cooperatieve rabobank", "rabobank",
    "credit agricole", "credit suisse", "ctbc bank", "dbs bank", "deutsche bank", "doha bank",
    "emirates nbd", "first abu dhabi", "firstrand", "hongkong and shanghai", "hsbc",
    "industrial and commercial bank of china", "icbc", "industrial bank of korea", "jpmorgan",
    "jsc vtb", "kbc bank", "keb hana", "kookmin", "krung thai", "mashreq", "mizuho", "mufg",
    "national australia bank", "natwest", "nonghyup", "qatar national bank", "sberbank",
    "sbm bank", "shinhan", "societe generale", "sonali bank", "standard chartered",
    "sumitomo mitsui", "royal bank of scotland", "ubs", "united overseas bank", "westpac", "woori"
]


def classify_bank_type(name: str) -> str:
    n = name.lower()
    if any(k in n for k in PAYMENT_KEYWORDS):
        return "Payments Bank"
    if any(k in n for k in SFB_KEYWORDS):
        return "Small Finance Bank (SFB)"
    if any(k in n for k in PSU_KEYWORDS):
        return "Public Sector Bank (PSU)"
    if any(k in n for k in FOREIGN_KEYWORDS):
        return "Foreign Bank"
    return "Private Sector Bank"


def generate_bank_id(name: str) -> str:
    # Common mappings
    mapping = {
        "State Bank Of India": "SBI",
        "Hdfc Bank Ltd.": "HDFC",
        "Icici Bank Limited": "ICICI",
        "Axis Bank Limited": "AXIS",
        "Kotak Mahindra Bank Ltd.": "KOTAK",
        "Bank Of Baroda": "BOB",
        "Punjab National Bank": "PNB",
        "Canara Bank": "CANARA",
        "Union Bank Of India": "UBI",
        "Bank Of India": "BOI",
        "Indian Bank": "INDIAN",
        "Central Bank Of India": "CBI",
        "Indian Overseas Bank": "IOB",
        "Uco Bank": "UCO",
        "Bank Of Maharashtra": "BOM",
        "Punjab And Sind Bank": "PSB",
        "Yes Bank Ltd.": "YES",
        "Idfc First Bank Limited": "IDFC",
        "Idfc Bank Limited": "IDFC",
        "Idbi Bank Limited": "IDBI",
        "Indusind Bank Ltd": "INDUS",
        "Federal Bank Ltd": "FEDERAL",
        "Bandhan Bank Limited": "BANDHAN",
        "Rbl Bank Ltd": "RBL",
        "Au Small Finance Bank Limited": "AU-SFB",
        "Equitas Small Finance Bank Limited": "EQUITAS",
        "Ujjivan Small Finance Bank Limited": "UJJIVAN",
        "Standard Chartered Bank": "STANCHAR",
        "Citibank N.A": "CITI",
        "Deutsche Bank Ag": "DEUTSCHE",
        "Hongkong And Shanghai Banking Corpn.Ltd.": "HSBC",
        "Barclays Bank Plc": "BARCLAYS"
    }
    if name in mapping:
        return mapping[name]
    
    clean = re.sub(r'[^A-Za-z0-9 ]+', '', name).strip()
    words = clean.split()
    if len(words) == 1:
        return words[0][:6].upper()
    return "".join(w[0] for w in words[:4]).upper()


class FinGuardPipeline:
    def __init__(self):
        self.df = None
        self.records_by_bank = {}  # {bank_id: {year: snapshot}}
        self.bank_metadata = {}   # {bank_id: {name, type}}
        self.all_snapshots = []
        self.ml_model = FinGuardMLModel()
        self.sentiment_engine = FinBERTNewsSentimentEngine()
        self.is_initialized = False

    def initialize(self):
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"Master dataset not found at {CSV_PATH}")

        self.df = pd.read_csv(CSV_PATH)
        
        # Clean numeric fields
        numeric_cols = [
            'net_npa_ratio', 'car_crar_total', 'roa_pct', 'nim_pct', 'cost_to_income_ratio',
            'equity_cr', 'deposits_cr', 'debt_to_equity_calc', 'basel3_tier1_crar',
            'basel3_tier2_crar', 'basel3_total_crar', 'gross_npa_open_cr',
            'gross_npa_additions_cr', 'gross_npa_writeoff_cr', 'gross_npa_closing_cr',
            'net_npa_closing_cr', 'sensitive_capital_market_cr', 'sensitive_real_estate_cr',
            'sensitive_total_exposure_cr', 'short_term_deposits_under_90d_cr',
            'crisis_label', 'finbert_sentiment_score', 'lcr_pct', 'finguard_composite_score'
        ]
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0.0)

        self.records_by_bank = {}
        self.bank_metadata = {}
        self.all_snapshots = []

        for _, row in self.df.iterrows():
            name = str(row['bank_name']).strip()
            year = int(row['year'])
            b_id = generate_bank_id(name)
            b_type = classify_bank_type(name)

            net_npa_pct = float(row.get('net_npa_ratio', 0.0))
            car_total = float(row.get('car_crar_total', 0.0))
            roa_pct = float(row.get('roa_pct', 0.0))
            nim_pct = float(row.get('nim_pct', 0.0))
            c2i_pct = float(row.get('cost_to_income_ratio', 0.0))
            de_ratio = float(row.get('debt_to_equity_calc', 0.0))
            lcr_pct = float(row.get('lcr_pct', 120.0))
            
            gnpa_close = float(row.get('gross_npa_closing_cr', 0.0))
            nnpa_close = float(row.get('net_npa_closing_cr', 0.0))
            pcr_pct = ((gnpa_close - nnpa_close) / gnpa_close * 100.0) if gnpa_close > 0 else 85.0
            pcr_pct = max(0.0, min(100.0, pcr_pct))

            advances_cr = (nnpa_close / (net_npa_pct / 100.0)) if net_npa_pct > 0 else (gnpa_close * 15.0)

            composite_score = float(row.get('finguard_composite_score', 0.0))
            if composite_score <= 0:
                calc_info = compute_composite_finguard_score({
                    "net_npa_pct": net_npa_pct,
                    "crar_total_pct": car_total,
                    "roa_pct": roa_pct,
                    "nim_pct": nim_pct,
                    "lcr_pct": lcr_pct,
                    "c2i_pct": c2i_pct,
                    "de_ratio": de_ratio,
                    "pcr_pct": pcr_pct
                })
                composite_score = calc_info["score"]
                zone = calc_info["zone"]
                zone_color = calc_info["zone_color"]
                sub_scores = calc_info["sub_scores"]
                biggest_risk = calc_info["biggest_risk_factor"]
            else:
                if composite_score >= 80.0:
                    zone = "Safe"
                    zone_color = "#10B981"
                elif composite_score >= 60.0:
                    zone = "Caution"
                    zone_color = "#F59E0B"
                elif composite_score >= 40.0:
                    zone = "At-Risk"
                    zone_color = "#F97316"
                else:
                    zone = "Critical"
                    zone_color = "#EF4444"

                # Subscore approximations
                sub_scores = {
                    "net_npa": max(10, min(100, 100 - net_npa_pct * 15)),
                    "crar": max(10, min(100, car_total * 5)),
                    "roa": max(10, min(100, 60 + roa_pct * 20)),
                    "nim": max(10, min(100, nim_pct * 25)),
                    "lcr": max(10, min(100, lcr_pct * 0.7)),
                    "cost_to_income": max(10, min(100, 110 - c2i_pct)),
                    "debt_to_equity": max(10, min(100, 100 - de_ratio * 4)),
                    "pcr": pcr_pct
                }
                worst_k = min(sub_scores, key=sub_scores.get)
                worst_cfg = RATIO_CONFIGS.get(worst_k, RATIO_CONFIGS["net_npa"])
                biggest_risk = {
                    "key": worst_k,
                    "name": worst_cfg["name"],
                    "current_value": net_npa_pct if worst_k == "net_npa" else car_total if worst_k == "crar" else roa_pct,
                    "unit": worst_cfg["unit"],
                    "sub_score": sub_scores[worst_k],
                    "regulatory_benchmark": worst_cfg["regulatory_min_or_max"]
                }

            snapshot = {
                "bank_id": b_id,
                "bank_name": name,
                "bank_type": b_type,
                "year": year,
                "finguard_score": round(composite_score, 1),
                "zone": zone,
                "zone_color": zone_color,
                "net_npa_pct": round(net_npa_pct, 2),
                "crar_total_pct": round(car_total, 2),
                "roa_pct": round(roa_pct, 2),
                "nim_pct": round(nim_pct, 2),
                "c2i_pct": round(c2i_pct, 1),
                "de_ratio": round(de_ratio, 2),
                "lcr_pct": round(lcr_pct, 1),
                "pcr_pct": round(pcr_pct, 1),
                "equity_crores": round(float(row.get('equity_cr', 0.0)), 2),
                "deposits_crores": round(float(row.get('deposits_cr', 0.0)), 2),
                "advances_crores": round(advances_cr, 2),
                "gross_npa_crores": round(gnpa_close, 2),
                "net_npa_crores": round(nnpa_close, 2),
                "sensitive_total_exposure_crores": round(float(row.get('sensitive_total_exposure_cr', 0.0)), 2),
                "short_term_deposits_under_90d_crores": round(float(row.get('short_term_deposits_under_90d_cr', 0.0)), 2),
                "crisis_label": int(row.get('crisis_label', 0)),
                "finbert_sentiment_score": round(float(row.get('finbert_sentiment_score', 0.2)), 2),
                "sub_scores": sub_scores,
                "biggest_risk_factor": biggest_risk,
                "summary": f"{name} exhibits a {zone} health score of {composite_score:.1f} with Net NPA at {net_npa_pct:.2f}% and CAR buffer of {car_total:.2f}%."
            }

            if b_id not in self.records_by_bank:
                self.records_by_bank[b_id] = {}
                self.bank_metadata[b_id] = {"bank_id": b_id, "bank_name": name, "bank_type": b_type}
            self.records_by_bank[b_id][year] = snapshot
            self.all_snapshots.append(snapshot)

        self.is_initialized = True
        return len(self.all_snapshots)

    def get_leaderboard(self, year: int = 2024, bank_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_initialized:
            self.initialize()

        actual_year = int(year)
        results = []

        for b_id, years_data in self.records_by_bank.items():
            if actual_year in years_data:
                rec = years_data[actual_year]
                if bank_type and bank_type.lower() != 'all' and bank_type.lower() not in rec['bank_type'].lower():
                    continue

                # Multi-year trajectory across all years for this bank up to actual_year
                avail_years = sorted([y for y in years_data.keys() if y <= actual_year])
                scores = [years_data[y]["finguard_score"] for y in avail_years]
                npas = [years_data[y]["net_npa_pct"] for y in avail_years]
                traj = classify_trajectory(scores, npas)

                # Sentiment
                sent_score = rec["finbert_sentiment_score"]
                sentiment_text = "Positive" if sent_score >= 0.25 else "Negative" if sent_score <= -0.1 else "Neutral"

                results.append({
                    "rank": 0,
                    "bank_id": b_id,
                    "bank_name": rec["bank_name"],
                    "bank_type": rec["bank_type"],
                    "finguard_score": rec["finguard_score"],
                    "zone": rec["zone"],
                    "zone_color": rec["zone_color"],
                    "trajectory": traj["trajectory"],
                    "trajectory_color": traj["color"],
                    "net_npa_pct": rec["net_npa_pct"],
                    "crar_total_pct": rec["crar_total_pct"],
                    "roa_pct": rec["roa_pct"],
                    "nim_pct": rec["nim_pct"],
                    "lcr_pct": rec["lcr_pct"],
                    "c2i_pct": rec["c2i_pct"],
                    "de_ratio": rec["de_ratio"],
                    "pcr_pct": rec["pcr_pct"],
                    "advances_crores": rec["advances_crores"],
                    "deposits_crores": rec["deposits_crores"],
                    "crisis_label": rec["crisis_label"],
                    "sentiment": sentiment_text,
                    "governance_flag": rec["crisis_label"] == 1 or sent_score < -0.5
                })

        results.sort(key=lambda x: x["finguard_score"], reverse=True)
        for i, r in enumerate(results, 1):
            r["rank"] = i

        return results

    def get_bank_full_profile(self, bank_id: str) -> Dict[str, Any]:
        if not self.is_initialized:
            self.initialize()

        b_upper = bank_id.upper()
        if b_upper not in self.records_by_bank:
            # Try searching by name match
            for k, meta in self.bank_metadata.items():
                if bank_id.lower() in meta["bank_name"].lower() or bank_id.lower() == k.lower():
                    b_upper = k
                    break

        if b_upper not in self.records_by_bank:
            return {"error": f"Bank {bank_id} not found in master dataset."}

        years_data = self.records_by_bank[b_upper]
        sorted_years = sorted(years_data.keys())
        latest_year = sorted_years[-1]
        latest_rec = years_data[latest_year]

        history = [years_data[y] for y in sorted_years]
        scores = [years_data[y]["finguard_score"] for y in sorted_years]
        npas = [years_data[y]["net_npa_pct"] for y in sorted_years]
        traj_info = classify_trajectory(scores, npas)

        # Forecasting for next 2 years (e.g. 2025 & 2026)
        forecast_info = forecast_health_scores(sorted_years, scores, periods_ahead=2)

        # SHAP attribution
        shap_info = self.ml_model.predict_explain_shap(latest_rec)

        # Sentiment info
        sent_info = self.sentiment_engine.get_bank_sentiment(b_upper)
        dual_matrix = self.sentiment_engine.get_dual_signal_matrix(
            latest_rec["finguard_score"],
            latest_rec["finbert_sentiment_score"],
            b_upper
        )

        return {
            "bank_id": b_upper,
            "bank_name": latest_rec["bank_name"],
            "bank_type": latest_rec["bank_type"],
            "latest_year": latest_year,
            "current_score": latest_rec["finguard_score"],
            "current_zone": latest_rec["zone"],
            "current_zone_color": latest_rec["zone_color"],
            "summary": latest_rec["summary"],
            "trajectory": traj_info,
            "latest_ratios": latest_rec,
            "history": history,
            "shap_explainability": shap_info,
            "forecast": forecast_info,
            "sentiment": sent_info,
            "dual_signal_matrix": dual_matrix,
            "biggest_risk_factor": latest_rec["biggest_risk_factor"]
        }

    def get_sector_overview(self, year: int = 2024) -> Dict[str, Any]:
        if not self.is_initialized:
            self.initialize()

        leaderboard = self.get_leaderboard(year=year)
        total = len(leaderboard)
        if total == 0:
            return {"error": "No banks for year"}

        safe_c = sum(1 for b in leaderboard if b["zone"] == "Safe")
        caution_c = sum(1 for b in leaderboard if b["zone"] == "Caution")
        at_risk_c = sum(1 for b in leaderboard if b["zone"] == "At-Risk")
        critical_c = sum(1 for b in leaderboard if b["zone"] == "Critical")

        avg_score = sum(b["finguard_score"] for b in leaderboard) / total
        avg_npa = sum(b["net_npa_pct"] for b in leaderboard) / total
        avg_car = sum(b["crar_total_pct"] for b in leaderboard) / total
        total_advances = sum(b["advances_crores"] for b in leaderboard)
        total_deposits = sum(b["deposits_crores"] for b in leaderboard)

        return {
            "total_banks": total,
            "evaluation_year": year,
            "available_years": sorted(list(set(self.df["year"].dropna().astype(int)))),
            "average_finguard_score": round(avg_score, 1),
            "average_net_npa_pct": round(avg_npa, 2),
            "average_crar_pct": round(avg_car, 2),
            "total_system_advances_crores": round(total_advances, 2),
            "total_system_deposits_crores": round(total_deposits, 2),
            "zone_distribution": {
                "Safe": safe_c,
                "Caution": caution_c,
                "At-Risk": at_risk_c,
                "Critical": critical_c
            }
        }
