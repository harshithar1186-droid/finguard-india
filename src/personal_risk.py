"""
FinGuard India - Personal Investment Risk Connector (Feature 6)
Connects bank fundamental health and trajectory to individual retail exposure
(Fixed Deposits, Savings, or Equity holdings).
"""

from typing import Dict, Any, Optional

DICGC_COVERAGE_LIMIT_INR = 500000.0  # ₹5,00,000 per depositor per scheduled bank


def evaluate_personal_fd_exposure(
    bank_id: str,
    bank_name: str,
    fd_amount_inr: float,
    current_finguard_score: float,
    current_zone: str,
    biggest_risk_factor: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates personal fixed deposit or savings risk against statutory DICGC protection
    and generates the 3 core outputs defined in Feature 6 of FinGuard.
    """
    amount = float(fd_amount_inr)
    covered_amount = min(amount, DICGC_COVERAGE_LIMIT_INR)
    uncovered_amount = max(0.0, amount - DICGC_COVERAGE_LIMIT_INR)
    is_fully_covered = uncovered_amount == 0.0
    coverage_pct = (covered_amount / amount * 100.0) if amount > 0 else 100.0

    # Output 1: DICGC Insurance Coverage
    if is_fully_covered:
        insurance_badge = "100% Fully Insured"
        insurance_color = "#10B981"
        output_1_text = (
            f"Your ₹{amount:,.0f} deposit in {bank_name} is fully covered by DICGC (Deposit Insurance and Credit Guarantee "
            f"Corporation, an RBI subsidiary) up to ₹5,00,000. Your capital and accrued interest are protected by law "
            f"regardless of the bank's current health score."
        )
    else:
        insurance_badge = f"{coverage_pct:.1f}% Covered (₹{uncovered_amount:,.0f} Uninsured)"
        insurance_color = "#F59E0B" if current_zone in ["Safe", "Caution"] else "#EF4444"
        output_1_text = (
            f"₹5,00,000 of your deposit is legally guaranteed by DICGC. However, you have an uninsured excess exposure "
            f"of ₹{uncovered_amount:,.0f}. In an extreme insolvency or moratorium event, recovery of amounts exceeding "
            f"₹5 Lakhs is subject to resolution proceedings. Consider diversifying excess funds across another scheduled bank."
        )

    # Output 2: The One Number to Watch
    risk_name = biggest_risk_factor.get("name", "Asset Quality")
    risk_val = biggest_risk_factor.get("current_value", 0.0)
    risk_unit = biggest_risk_factor.get("unit", "%")
    risk_key = biggest_risk_factor.get("key", "")

    # Calculate threshold based on specific metric
    if risk_key == "net_npa":
        threshold_val = min(6.0, max(2.5, risk_val * 1.35))
        metric_warning = (
            f"{bank_name}'s primary risk factor is its Net NPA ratio currently at {risk_val:.2f}%. "
            f"If this rises above {threshold_val:.2f}% in the next RBI statistical release, "
            f"that historically precedes credit rating reviews and supervisory scrutiny. Watch this number closely."
        )
    elif risk_key == "crar":
        threshold_val = max(11.5, risk_val * 0.88)
        metric_warning = (
            f"{bank_name}'s critical buffer is Capital Adequacy (CAR) at {risk_val:.2f}%. "
            f"If CAR drops below {threshold_val:.2f}%, the bank's capital buffer approaches the regulatory warning line."
        )
    elif risk_key == "cost_to_income":
        threshold_val = min(65.0, risk_val * 1.15)
        metric_warning = (
            f"{bank_name}'s key operational vulnerability is Cost-to-Income at {risk_val:.2f}%. "
            f"Rising above {threshold_val:.2f}% indicates severe operating margin squeeze."
        )
    else:
        metric_warning = (
            f"{bank_name}'s key watch metric is {risk_name} at {risk_val}{risk_unit}. "
            f"Regulatory baseline threshold is {biggest_risk_factor.get('regulatory_benchmark', 'standard limits')}."
        )

    output_2_text = metric_warning

    # Output 3: What a score drop means for you
    if current_finguard_score >= 80.0:
        output_3_text = (
            f"Bank health is currently in the Safe zone ({current_finguard_score:.1f}/100). "
            f"If the FinGuard score drops below 60 in subsequent quarters, review uninsured balances exceeding ₹5 Lakhs."
        )
    elif current_finguard_score >= 60.0:
        output_3_text = (
            f"Bank health is in the Caution zone ({current_finguard_score:.1f}/100). "
            f"If the score slips below 45 (At-Risk) next quarter — based on historical patterns in Indian banking crises — "
            f"formal prompt corrective measures or credit rating downgrades become likely. Consider spreading amounts above ₹5 Lakhs across sovereign or prime institutions."
        )
    elif current_finguard_score >= 40.0:
        output_3_text = (
            f"URGENT: Bank is in the At-Risk zone ({current_finguard_score:.1f}/100). "
            f"Historical validation shows entities in this zone experience elevated volatility. Ensure total deposits per PAN per bank stay strictly under ₹5,00,000 for 100% DICGC backing."
        )
    else:
        output_3_text = (
            f"CRITICAL WARNING: Bank is in the Critical zone ({current_finguard_score:.1f}/100). "
            f"Historical crisis models indicate that entities reaching this tier faced restructuring or liquidity curbs (as seen in Yes Bank and PMC Bank). Maintain only DICGC-insured funds."
        )

    return {
        "bank_id": bank_id,
        "bank_name": bank_name,
        "fd_amount_inr": amount,
        "dicgc_covered_inr": covered_amount,
        "uninsured_excess_inr": uncovered_amount,
        "is_fully_covered": is_fully_covered,
        "coverage_percentage": round(coverage_pct, 1),
        "insurance_badge": insurance_badge,
        "insurance_color": insurance_color,
        "output_1_insurance": output_1_text,
        "output_2_watch_number": output_2_text,
        "output_3_score_drop_impact": output_3_text,
        "disclaimer": "FinGuard connects public RBI regulatory metrics to statutory deposit insurance guidelines. It does not constitute investment advice or solicitation."
    }


def evaluate_personal_equity_exposure(
    bank_id: str,
    bank_name: str,
    shares_count: int,
    buy_price_inr: float,
    current_finguard_score: float,
    current_zone: str,
    biggest_risk_factor: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates retail equity shareholding risk based on fundamental health tier.
    """
    shares = int(shares_count)
    invested_val = shares * float(buy_price_inr)

    if current_zone == "Safe":
        equity_risk_category = "Low Fundamental Risk"
        equity_color = "#10B981"
        action_note = "Strong balance sheet fundamentals support long-term compounding. Low credit delinquency hazard."
    elif current_zone == "Caution":
        equity_risk_category = "Moderate Risk / Efficiency Drag"
        equity_color = "#F59E0B"
        action_note = "Core balance sheet is intact, but margin compression or cost efficiency may cap equity upside."
    elif current_zone == "At-Risk":
        equity_risk_category = "Elevated Equity Risk / Capital Dilution Hazard"
        equity_color = "#F97316"
        action_note = "High risk of earnings dilution or emergency capital raising if bad loans continue to escalate."
    else:
        equity_risk_category = "Severe Capital Impairment Hazard"
        equity_color = "#EF4444"
        action_note = "Substantial equity loss hazard. In banking crises (Yes Bank, PMC), equity holders absorbed heavy write-downs."

    return {
        "bank_id": bank_id,
        "bank_name": bank_name,
        "shares_count": shares,
        "invested_value_inr": round(invested_val, 2),
        "finguard_score": current_finguard_score,
        "zone": current_zone,
        "equity_risk_category": equity_risk_category,
        "equity_color": equity_color,
        "action_note": action_note,
        "key_risk_driver": f"{biggest_risk_factor.get('name')}: {biggest_risk_factor.get('current_value')}{biggest_risk_factor.get('unit')}"
    }

