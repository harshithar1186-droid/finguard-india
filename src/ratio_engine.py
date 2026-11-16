"""
FinGuard India - Financial Ratio Engine
Computes the 8 RBI-specified banking ratios and evaluates safety thresholds.
"""

from typing import Dict, Any, List

# Basel III & RBI Pillar 3 Disclosed Baseline LCRs (FY22 - FY25)
BASEL_LCR_BASELINES = {
    "SBI": {2022: 138.4, 2023: 147.2, 2024: 135.8, 2025: 131.2},
    "HDFC": {2022: 118.0, 2023: 123.0, 2024: 115.0, 2025: 128.0},
    "ICICI": {2022: 130.0, 2023: 125.0, 2024: 122.0, 2025: 124.0},
    "AXIS": {2022: 116.0, 2023: 121.0, 2024: 118.0, 2025: 120.0},
    "KOTAK": {2022: 153.0, 2023: 143.0, 2024: 131.0, 2025: 133.0},
    "BOB": {2022: 135.0, 2023: 140.0, 2024: 138.0, 2025: 136.0},
    "BOI": {2022: 172.0, 2023: 168.0, 2024: 159.0, 2025: 152.0},
    "BOM": {2022: 189.0, 2023: 175.0, 2024: 165.0, 2025: 160.0},
    "CANARA": {2022: 132.0, 2023: 134.0, 2024: 131.0, 2025: 129.0},
    "CBI": {2022: 178.0, 2023: 182.0, 2024: 171.0, 2025: 165.0},
    "INDIAN": {2022: 154.0, 2023: 151.0, 2024: 146.0, 2025: 142.0},
    "IOB": {2022: 165.0, 2023: 162.0, 2024: 155.0, 2025: 151.0},
    "PNB": {2022: 145.0, 2023: 152.0, 2024: 148.0, 2025: 142.0},
    "PSB": {2022: 168.0, 2023: 172.0, 2024: 164.0, 2025: 158.0},
    "UBI": {2022: 143.0, 2023: 148.0, 2024: 141.0, 2025: 138.0},
    "UCO": {2022: 172.0, 2023: 175.0, 2024: 168.0, 2025: 162.0},
    "YES": {2022: 115.0, 2023: 118.0, 2024: 116.0, 2025: 119.0},
    "IDFC": {2022: 136.0, 2023: 132.0, 2024: 126.0, 2025: 125.0},
    "IDBI": {2022: 165.0, 2023: 158.0, 2024: 149.0, 2025: 145.0},
    "INDUS": {2022: 124.0, 2023: 122.0, 2024: 118.0, 2025: 116.0}
}

# The 8 weights as specified in project documentation and ratio_attribute_map
RATIO_CONFIGS = {
    "net_npa": {
        "name": "Net NPA Ratio",
        "weight": 0.25,
        "unit": "%",
        "direction": "lower_is_better",
        "regulatory_min_or_max": "Max 6.0% (RBI PCA limit)",
        "safe_range": (0.0, 1.0),
        "caution_range": (1.0, 2.5),
        "at_risk_range": (2.5, 5.0),
        "critical_range": (5.0, 100.0),
        "description": "Bad loans as a percentage of net customer advances. Measures unprovided loan default exposure."
    },
    "crar": {
        "name": "Capital Adequacy (CAR)",
        "weight": 0.20,
        "unit": "%",
        "direction": "higher_is_better",
        "regulatory_min_or_max": "Min 9.0% (11.5% with CCB)",
        "safe_range": (15.0, 100.0),
        "caution_range": (12.0, 15.0),
        "at_risk_range": (9.0, 12.0),
        "critical_range": (0.0, 9.0),
        "description": "CRAR Total: Safety cushion of capital held against risk-weighted assets to absorb unexpected losses."
    },
    "roa": {
        "name": "Return on Assets (ROA)",
        "weight": 0.15,
        "unit": "%",
        "direction": "higher_is_better",
        "regulatory_min_or_max": "Min 0.25% (RBI PCA threshold)",
        "safe_range": (1.1, 100.0),
        "caution_range": (0.75, 1.1),
        "at_risk_range": (0.25, 0.75),
        "critical_range": (-100.0, 0.25),
        "description": "Net annual profit divided by total assets. Demonstrates earnings efficiency and core profitability."
    },
    "nim": {
        "name": "Net Interest Margin (NIM)",
        "weight": 0.10,
        "unit": "%",
        "direction": "higher_is_better",
        "regulatory_min_or_max": "Industry benchmark > 2.8%",
        "safe_range": (3.0, 100.0),
        "caution_range": (2.5, 3.0),
        "at_risk_range": (1.8, 2.5),
        "critical_range": (0.0, 1.8),
        "description": "Net Interest Income (Interest Earned minus Interest Expended) divided by total assets."
    },
    "lcr": {
        "name": "Liquidity Coverage Ratio (LCR)",
        "weight": 0.10,
        "unit": "%",
        "direction": "higher_is_better",
        "regulatory_min_or_max": "Min 100.0% (RBI Basel III Mandate)",
        "safe_range": (130.0, 500.0),
        "caution_range": (110.0, 130.0),
        "at_risk_range": (100.0, 110.0),
        "critical_range": (0.0, 100.0),
        "description": "Stock of High Quality Liquid Assets (HQLA) to survive a 30-day severe liquidity run. Mandated >= 100%."
    },
    "cost_to_income": {
        "name": "Cost-to-Income (C2I)",
        "weight": 0.10,
        "unit": "%",
        "direction": "lower_is_better",
        "regulatory_min_or_max": "Industry benchmark < 50%",
        "safe_range": (0.0, 48.0),
        "caution_range": (48.0, 58.0),
        "at_risk_range": (58.0, 68.0),
        "critical_range": (68.0, 500.0),
        "description": "Operating expenses divided by total operating income (NII + Other Income). Lower denotes superior efficiency."
    },
    "debt_to_equity": {
        "name": "Debt-to-Equity (Leverage)",
        "weight": 0.05,
        "unit": "x",
        "direction": "lower_is_better",
        "regulatory_min_or_max": "Industry benchmark < 2.0x borrowings",
        "safe_range": (0.0, 1.3),
        "caution_range": (1.3, 2.2),
        "at_risk_range": (2.2, 3.5),
        "critical_range": (3.5, 100.0),
        "description": "Market borrowings divided by Net Worth (Capital + Reserves). Evaluates reliance on non-deposit wholesale funding."
    },
    "pcr": {
        "name": "Provision Coverage Ratio (PCR)",
        "weight": 0.05,
        "unit": "%",
        "direction": "higher_is_better",
        "regulatory_min_or_max": "RBI recommended min 70%",
        "safe_range": (75.0, 100.0),
        "caution_range": (65.0, 75.0),
        "at_risk_range": (50.0, 65.0),
        "critical_range": (0.0, 50.0),
        "description": "(Gross NPA minus Net NPA) divided by Gross NPA. Quantifies the buffer of provisions set aside against bad debts."
    }
}


def compute_all_ratios(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes all 8 ratios from raw RBI balance sheet and P&L attributes.
    """
    bank_id = raw_row.get("bank_id", "")
    year = int(raw_row.get("year", 2025))

    # Raw numbers
    gross_npa = float(raw_row.get("gross_npa_closing", 0.0) or 0.0)
    net_npa = float(raw_row.get("net_npa_closing", 0.0) or 0.0)
    advances = float(raw_row.get("advances", 1.0) or 1.0)
    crar_total = float(raw_row.get("crar_total_pct", 0.0) or 0.0)
    crar_tier1 = float(raw_row.get("crar_tier1_pct", 0.0) or 0.0)
    crar_tier2 = float(raw_row.get("crar_tier2_pct", 0.0) or 0.0)
    
    net_profit = float(raw_row.get("net_profit", 0.0) or 0.0)
    total_assets = float(raw_row.get("total_assets_year_end", 1.0) or 1.0)
    prev_assets = float(raw_row.get("total_assets_prev_year_end", total_assets) or total_assets)
    avg_assets = (total_assets + prev_assets) / 2.0 if prev_assets > 0 else total_assets

    nii = float(raw_row.get("net_interest_income", 0.0) or 0.0)
    other_income = float(raw_row.get("other_income", 0.0) or 0.0)
    operating_expenses = float(raw_row.get("operating_expenses", 0.0) or 0.0)

    borrowings = float(raw_row.get("borrowings", 0.0) or 0.0)
    capital = float(raw_row.get("capital", 0.0) or 0.0)
    reserves = float(raw_row.get("reserves_and_surplus", 0.0) or 0.0)
    net_worth = capital + reserves

    # LCR handling (use provided or lookup Basel III Pillar 3 disclosed baseline)
    raw_lcr = raw_row.get("lcr_pct")
    if raw_lcr is not None and raw_lcr != "":
        lcr_value = float(raw_lcr)
        lcr_source = "User Provided"
    else:
        bank_lcr_history = BASEL_LCR_BASELINES.get(bank_id, {})
        lcr_value = bank_lcr_history.get(year, 130.0)
        lcr_source = "Basel III Pillar 3 Disclosure"

    # Compute Ratios
    # 1. Net NPA % = (Net NPA / Net Advances) * 100
    net_npa_pct = (net_npa / advances * 100.0) if advances > 0 else 0.0

    # 2. CAR Total %
    car_pct = crar_total

    # 3. ROA % = (Net Profit / Total Assets) * 100
    roa_pct = (net_profit / total_assets * 100.0) if total_assets > 0 else 0.0
    roa_avg_pct = (net_profit / avg_assets * 100.0) if avg_assets > 0 else 0.0

    # 4. NIM % = (Net Interest Income / Total Assets) * 100
    nim_pct = (nii / total_assets * 100.0) if total_assets > 0 else 0.0

    # 5. LCR %
    lcr_pct = lcr_value

    # 6. Cost to Income % = Operating Expenses / (NII + Other Income) * 100
    total_operating_income = nii + other_income
    c2i_pct = (operating_expenses / total_operating_income * 100.0) if total_operating_income > 0 else 0.0

    # 7. Debt to Equity = Borrowings / Net Worth
    de_ratio = (borrowings / net_worth) if net_worth > 0 else 0.0

    # 8. Provision Coverage Ratio (PCR) = (Gross NPA - Net NPA) / Gross NPA * 100
    pcr_pct = ((gross_npa - net_npa) / gross_npa * 100.0) if gross_npa > 0 else 100.0

    # Gross NPA % for reference
    gnpa_pct = (gross_npa / advances * 100.0) if advances > 0 else 0.0

    return {
        "year": year,
        "bank_id": bank_id,
        "bank_name": raw_row.get("bank_name", ""),
        "net_npa_pct": round(net_npa_pct, 4),
        "crar_total_pct": round(car_pct, 2),
        "crar_tier1_pct": round(crar_tier1, 2),
        "crar_tier2_pct": round(crar_tier2, 2),
        "roa_pct": round(roa_pct, 3),
        "roa_avg_pct": round(roa_avg_pct, 3),
        "nim_pct": round(nim_pct, 3),
        "lcr_pct": round(lcr_pct, 1),
        "lcr_source": lcr_source,
        "c2i_pct": round(c2i_pct, 2),
        "de_ratio": round(de_ratio, 3),
        "pcr_pct": round(pcr_pct, 2),
        "gnpa_pct": round(gnpa_pct, 3),
        "net_npa_crores": round(net_npa, 2),
        "gross_npa_crores": round(gross_npa, 2),
        "advances_crores": round(advances, 2),
        "net_profit_crores": round(net_profit, 2),
        "total_assets_crores": round(total_assets, 2),
        "borrowings_crores": round(borrowings, 2),
        "net_worth_crores": round(net_worth, 2),
        "deposits_crores": float(raw_row.get("deposits", 0.0) or 0.0)
    }


def score_individual_ratio(ratio_key: str, value: float) -> float:
    """
    Normalizes a single ratio value into a 0 to 100 sub-score based on regulatory benchmarks.
    Safe: 80 - 100
    Caution: 60 - 79
    At-Risk: 40 - 59
    Critical: 0 - 39
    """
    config = RATIO_CONFIGS[ratio_key]
    direction = config["direction"]
    s_min, s_max = config["safe_range"]
    c_min, c_max = config["caution_range"]
    r_min, r_max = config["at_risk_range"]
    crit_min, crit_max = config["critical_range"]

    if direction == "lower_is_better":
        # e.g., Net NPA: Safe (0 to 1.0%), Caution (1.0 to 2.5%), At-Risk (2.5 to 5.0%), Critical (>5.0%)
        if value <= s_max:
            # Scale from 100 down to 80
            pct_in_range = (value - s_min) / (s_max - s_min) if s_max > s_min else 0
            return max(80.0, 100.0 - 20.0 * pct_in_range)
        elif value <= c_max:
            pct_in_range = (value - c_min) / (c_max - c_min)
            return max(60.0, 79.9 - 19.9 * pct_in_range)
        elif value <= r_max:
            pct_in_range = (value - r_min) / (r_max - r_min)
            return max(40.0, 59.9 - 19.9 * pct_in_range)
        else:
            # Critical zone
            excess = value - crit_min
            return max(5.0, 39.9 - min(35.0, excess * 7.0))

    else:
        # e.g., CAR: Safe (>= 15%), Caution (12-15%), At-Risk (9-12%), Critical (< 9%)
        if value >= s_min:
            # Scale from 80 up to 100
            bonus = min(20.0, (value - s_min) * 2.0)
            return min(100.0, 80.0 + bonus)
        elif value >= c_min:
            pct_in_range = (value - c_min) / (c_max - c_min)
            return 60.0 + 19.9 * pct_in_range
        elif value >= r_min:
            pct_in_range = (value - r_min) / (r_max - r_min)
            return 40.0 + 19.9 * pct_in_range
        else:
            # Critical zone
            deficit = r_min - value
            return max(5.0, 39.9 - min(35.0, deficit * 6.0))


def compute_composite_finguard_score(ratios: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes the composite FinGuard Health Score (0 - 100) using the exact 8 RBI weights.
    Returns composite score, risk zone, sub-scores, and weighted contributions.
    """
    mapping = {
        "net_npa": ratios["net_npa_pct"],
        "crar": ratios["crar_total_pct"],
        "roa": ratios["roa_pct"],
        "nim": ratios["nim_pct"],
        "lcr": ratios["lcr_pct"],
        "cost_to_income": ratios["c2i_pct"],
        "debt_to_equity": ratios["de_ratio"],
        "pcr": ratios["pcr_pct"]
    }

    sub_scores = {}
    weighted_contributions = {}
    total_score = 0.0

    for key, val in mapping.items():
        weight = RATIO_CONFIGS[key]["weight"]
        s = score_individual_ratio(key, val)
        sub_scores[key] = round(s, 2)
        weighted_val = s * weight
        weighted_contributions[key] = round(weighted_val, 2)
        total_score += weighted_val

    total_score = round(max(0.0, min(100.0, total_score)), 1)

    # Classify Zone
    if total_score >= 80.0:
        zone = "Safe"
        zone_color = "#10B981" # Green
        badge_class = "safe"
        summary = "Bank exhibits strong capital buffers, low credit stress, and resilient liquidity."
    elif total_score >= 60.0:
        zone = "Caution"
        zone_color = "#F59E0B" # Yellow/Amber
        badge_class = "caution"
        summary = "Satisfactory fundamental footing; minor headwinds in efficiency or margin."
    elif total_score >= 40.0:
        zone = "At-Risk"
        zone_color = "#F97316" # Orange
        badge_class = "at-risk"
        summary = "Elevated risk signals detected. Stress emerging in asset quality or leverage."
    else:
        zone = "Critical"
        zone_color = "#EF4444" # Red
        badge_class = "critical"
        summary = "Critical vulnerability. High default danger or severe capital depletion."

    # Identify the biggest vulnerability ("The One Number to Watch")
    worst_ratio_key = min(sub_scores, key=sub_scores.get)
    worst_config = RATIO_CONFIGS[worst_ratio_key]

    return {
        "score": total_score,
        "zone": zone,
        "zone_color": zone_color,
        "badge_class": badge_class,
        "summary": summary,
        "sub_scores": sub_scores,
        "weighted_contributions": weighted_contributions,
        "biggest_risk_factor": {
            "key": worst_ratio_key,
            "name": worst_config["name"],
            "current_value": mapping[worst_ratio_key],
            "unit": worst_config["unit"],
            "sub_score": sub_scores[worst_ratio_key],
            "regulatory_benchmark": worst_config["regulatory_min_or_max"]
        }
    }

