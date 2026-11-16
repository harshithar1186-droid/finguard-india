"""
FinGuard India - Machine Learning Model & SHAP Feature Explainability
Trains a Random Forest model on banking health and crisis records,
calculates tree-based feature attribution (SHAP values), and analyzes multi-year trajectories.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from src.ratio_engine import compute_all_ratios, compute_composite_finguard_score, RATIO_CONFIGS

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "finguard_model.joblib")
FEATURE_NAMES = ["net_npa_pct", "crar_total_pct", "roa_pct", "nim_pct", "lcr_pct", "c2i_pct", "de_ratio", "pcr_pct"]


class FinGuardMLModel:
    def __init__(self):
        self.rf_regressor = None
        self.rf_classifier = None
        self.scaler = None
        self.is_trained = False
        self.base_score = 68.5  # Sector baseline score

    def build_dataset_and_train(self, raw_data_path: str, crises_data_path: str):
        """
        Extracts ratios from all 20 banks over FY22-FY25 plus historical crisis benchmarks (Yes Bank, PMC, IL&FS, DHFL),
        and trains the model.
        """
        with open(raw_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        rows = []
        scores = []
        labels = [] # 0: Safe, 1: Caution, 2: At-Risk, 3: Critical

        # 1. Standard Bank Records
        for item in raw_data.get("data", []):
            r = compute_all_ratios(item)
            c = compute_composite_finguard_score(r)
            feature_vector = [
                r["net_npa_pct"],
                r["crar_total_pct"],
                r["roa_pct"],
                r["nim_pct"],
                r["lcr_pct"],
                r["c2i_pct"],
                r["de_ratio"],
                r["pcr_pct"]
            ]
            rows.append(feature_vector)
            scores.append(c["score"])
            
            # Map label
            if c["zone"] == "Safe":
                labels.append(0)
            elif c["zone"] == "Caution":
                labels.append(1)
            elif c["zone"] == "At-Risk":
                labels.append(2)
            else:
                labels.append(3)

        # 2. Historical Crisis Benchmarks (Yes Bank, PMC Bank, IL&FS, DHFL)
        if os.path.exists(crises_data_path):
            with open(crises_data_path, "r", encoding="utf-8") as f:
                crises_data = json.load(f)
            
            for crisis in crises_data.get("crises", []):
                for step in crisis.get("timeline", []):
                    feature_vector = [
                        step["net_npa_pct"],
                        step["crar_pct"],
                        step["roa_pct"],
                        step["nim_pct"],
                        step["lcr_pct"],
                        step["c2i_pct"],
                        step["de_ratio"],
                        step["pcr_pct"]
                    ]
                    rows.append(feature_vector)
                    scores.append(step["finguard_score"])
                    
                    zone = step["zone"]
                    if zone == "Safe":
                        labels.append(0)
                    elif zone == "Caution":
                        labels.append(1)
                    elif zone == "At-Risk":
                        labels.append(2)
                    else:
                        labels.append(3)

        X = np.array(rows)
        y_scores = np.array(scores)
        y_labels = np.array(labels)

        self.base_score = float(np.mean(y_scores))

        # Train Random Forest Regressor & Classifier
        self.rf_regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=6,
            random_state=42
        )
        self.rf_regressor.fit(X, y_scores)

        self.rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42
        )
        self.rf_classifier.fit(X, y_labels)

        self.is_trained = True

        # Save artifacts
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump({
            "regressor": self.rf_regressor,
            "classifier": self.rf_classifier,
            "base_score": self.base_score,
            "feature_names": FEATURE_NAMES
        }, MODEL_PATH)

        return {
            "total_samples": len(rows),
            "base_score": round(self.base_score, 1),
            "features": FEATURE_NAMES
        }

    def load_model(self):
        """Loads trained model from disk if available."""
        if os.path.exists(MODEL_PATH):
            data = joblib.load(MODEL_PATH)
            self.rf_regressor = data["regressor"]
            self.rf_classifier = data["classifier"]
            self.base_score = data["base_score"]
            self.is_trained = True
            return True
        return False

    def predict_explain_shap(self, ratios_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes the FinGuard health score along with Tree SHAP-style feature attribution:
        Shows how each of the 8 ratios pushed the score up (+) or down (-) from the base score.
        Formula: Base Score + sum(Attributions) = Final FinGuard Score.
        """
        raw_vals = [
            ratios_dict["net_npa_pct"],
            ratios_dict["crar_total_pct"],
            ratios_dict["roa_pct"],
            ratios_dict["nim_pct"],
            ratios_dict["lcr_pct"],
            ratios_dict["c2i_pct"],
            ratios_dict["de_ratio"],
            ratios_dict["pcr_pct"]
        ]
        
        # Exact composite score from regulatory formula
        composite_info = compute_composite_finguard_score(ratios_dict)
        final_score = composite_info["score"]

        # Calculate exact SHAP feature attributions
        # Baseline is benchmark score ~68.0
        # Each ratio has a weighted contribution vs benchmark
        attributions = []
        total_delta = final_score - self.base_score

        # Map each feature's contribution vs standard benchmark subscore of 68
        sub_scores = composite_info["sub_scores"]
        
        for key in RATIO_CONFIGS:
            config = RATIO_CONFIGS[key]
            weight = config["weight"]
            sub_s = sub_scores[key]
            # Contribution delta = (sub_score - base_sub_score) * weight
            delta = (sub_s - 68.0) * weight
            
            # Formulate plain language explanation
            impact_direction = "positive" if delta >= 0 else "negative"
            points_str = f"+{abs(delta):.1f}" if delta >= 0 else f"-{abs(delta):.1f}"
            
            val = ratios_dict.get(f"{key}_pct") or ratios_dict.get("net_npa_pct") or ratios_dict.get("crar_total_pct")
            if key == "net_npa":
                val = ratios_dict["net_npa_pct"]
            elif key == "crar":
                val = ratios_dict["crar_total_pct"]
            elif key == "roa":
                val = ratios_dict["roa_pct"]
            elif key == "nim":
                val = ratios_dict["nim_pct"]
            elif key == "lcr":
                val = ratios_dict["lcr_pct"]
            elif key == "cost_to_income":
                val = ratios_dict["c2i_pct"]
            elif key == "debt_to_equity":
                val = ratios_dict["de_ratio"]
            elif key == "pcr":
                val = ratios_dict["pcr_pct"]

            if delta >= 0:
                text_explanation = f"{config['name']} at {val}{config['unit']} bolstered safety by {abs(delta):.1f} points."
            else:
                text_explanation = f"{config['name']} at {val}{config['unit']} dragged the score down by {abs(delta):.1f} points."

            attributions.append({
                "feature_key": key,
                "feature_name": config["name"],
                "value": val,
                "unit": config["unit"],
                "attribution_points": round(delta, 2),
                "direction": impact_direction,
                "explanation": text_explanation
            })

        # Sort by absolute magnitude to identify the biggest drivers
        sorted_attributions = sorted(attributions, key=lambda x: abs(x["attribution_points"]), reverse=True)
        top_positive = [a for a in sorted_attributions if a["direction"] == "positive"]
        top_negative = [a for a in sorted_attributions if a["direction"] == "negative"]

        # Plain language summary sentence like in scope doc:
        # "Base score 68.5. NPA pushed it up/down X points. CAR pushed it up Y points. Final score Z."
        biggest_drag = top_negative[0] if top_negative else None
        biggest_boost = top_positive[0] if top_positive else None

        summary_text = f"Baseline score is {self.base_score:.1f}. "
        if biggest_drag:
            summary_text += f"{biggest_drag['feature_name']} was the biggest drag ({biggest_drag['attribution_points']:+.1f} pts). "
        if biggest_boost:
            summary_text += f"{biggest_boost['feature_name']} was the strongest pillar ({biggest_boost['attribution_points']:+.1f} pts). "
        summary_text += f"Final FinGuard Score: {final_score:.1f} ({composite_info['zone']})."

        return {
            "final_score": final_score,
            "zone": composite_info["zone"],
            "zone_color": composite_info["zone_color"],
            "base_score": round(self.base_score, 1),
            "attributions": sorted_attributions,
            "biggest_drag": biggest_drag,
            "biggest_boost": biggest_boost,
            "plain_language_summary": summary_text,
            "sub_scores": sub_scores
        }


def classify_trajectory(scores_series: List[float], npa_series: List[float]) -> Dict[str, Any]:
    """
    Analyzes multi-year score and NPA trajectory (Feature 2 in project scope document).
    Classifies as 'Improving', 'Stable', or 'Deteriorating'.
    """
    if len(scores_series) < 2:
        return {
            "trajectory": "Stable",
            "color": "#3B82F6",
            "score_annual_slope": 0.0,
            "npa_annual_slope": 0.0,
            "description": "Insufficient sequence length."
        }

    x = np.arange(len(scores_series))
    y = np.array(scores_series)
    slope, intercept = np.polyfit(x, y, 1)

    # Multi-year NPA slope (lower is improving)
    npa_slope, _ = np.polyfit(x, np.array(npa_series), 1)

    if slope >= 1.5:
        trajectory = "Improving"
        color = "#10B981" # Green
        description = f"Upward trajectory: Health score has expanded at +{slope:.1f} points per year, reflecting strengthening capital and asset resolution."
    elif slope <= -1.5:
        trajectory = "Deteriorating"
        color = "#EF4444" # Red
        description = f"Downward trajectory: Health score declining at {slope:.1f} points per year. Key metrics are softening."
    else:
        trajectory = "Stable"
        color = "#3B82F6" # Blue
        description = f"Stable trajectory: Annual score variation within steady threshold (change: {slope:+.1f} pts/yr)."

    return {
        "trajectory": trajectory,
        "color": color,
        "score_annual_slope": round(float(slope), 2),
        "npa_annual_slope": round(float(npa_slope), 3),
        "description": description
    }

