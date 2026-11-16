"""
FinGuard India - Predictive Score Forecasting (Feature 3)
Mathematical extrapolation of fundamental health score trajectories for future periods
with threshold-crossing risk alerts.
"""

from typing import List, Dict, Any
import numpy as np


def forecast_health_scores(historical_years: List[int], historical_scores: List[float], periods_ahead: int = 2) -> Dict[str, Any]:
    """
    Extrapolates the fundamental health score trajectory for the next `periods_ahead` periods.
    Provides projected score, confidence bounds, and threshold crossing alerts.
    """
    if len(historical_scores) < 2:
        return {
            "error": "Insufficient history for projection"
        }

    x = np.arange(len(historical_scores))
    y = np.array(historical_scores)
    
    # Fit weighted linear trend with recent periods given higher weight
    weights = np.linspace(0.8, 1.2, len(historical_scores))
    poly = np.polyfit(x, y, 1, w=weights)
    slope = poly[0]
    intercept = poly[1]

    # Standard error of regression
    y_pred = slope * x + intercept
    residuals = y - y_pred
    std_err = float(np.std(residuals)) if len(residuals) > 0 else 2.5

    last_year = historical_years[-1]
    projections = []
    threshold_alerts = []

    last_score = historical_scores[-1]
    current_zone = _get_zone(last_score)

    for i in range(1, periods_ahead + 1):
        target_year = last_year + i
        step_x = len(historical_scores) - 1 + i
        projected_score = slope * step_x + intercept
        # Dampen extreme runaway forecasts and clip to 0 - 100
        projected_score = max(5.0, min(98.0, projected_score))

        # Margin of error widens over time (confidence cone)
        error_margin = std_err * (1.2 + 0.4 * i)
        lower_bound = max(0.0, projected_score - error_margin)
        upper_bound = min(100.0, projected_score + error_margin)

        projected_zone = _get_zone(projected_score)

        # Check for threshold crossing
        if projected_zone != current_zone:
            if projected_score < last_score:
                alert_msg = f"ALERT: Health trajectory crosses downward from {current_zone} into {projected_zone} by FY{str(target_year)[-2:]} (Projected Score: {projected_score:.1f})."
                threshold_alerts.append({
                    "year": target_year,
                    "direction": "deterioration",
                    "from_zone": current_zone,
                    "to_zone": projected_zone,
                    "message": alert_msg
                })
            else:
                alert_msg = f"POSITIVE: Health trajectory improves from {current_zone} into {projected_zone} by FY{str(target_year)[-2:]} (Projected Score: {projected_score:.1f})."
                threshold_alerts.append({
                    "year": target_year,
                    "direction": "improvement",
                    "from_zone": current_zone,
                    "to_zone": projected_zone,
                    "message": alert_msg
                })

        projections.append({
            "year": target_year,
            "period_label": f"FY{str(target_year)[-2:]} (Projected)",
            "projected_score": round(float(projected_score), 1),
            "lower_bound": round(float(lower_bound), 1),
            "upper_bound": round(float(upper_bound), 1),
            "zone": projected_zone,
            "color": _get_zone_color(projected_zone)
        })

    rate_text = f"+{slope:.1f}" if slope >= 0 else f"{slope:.1f}"
    summary_text = (
        f"At current operational rate of change ({rate_text} pts/year), "
        f"projected health score for FY{str(last_year + 1)[-2:]} is {projections[0]['projected_score']:.1f} ({projections[0]['zone']}). "
    )
    if threshold_alerts:
        summary_text += threshold_alerts[0]["message"]
    else:
        summary_text += f"Remains comfortably within {current_zone} boundary."

    return {
        "annual_drift_rate": round(float(slope), 2),
        "projections": projections,
        "threshold_alerts": threshold_alerts,
        "summary": summary_text,
        "disclaimer": "This projection is a mathematical extrapolation of bank fundamental health scores based on published RBI metrics. It is NOT a stock price forecast, buy/sell recommendation, or financial market prediction."
    }


def _get_zone(score: float) -> str:
    if score >= 80.0:
        return "Safe"
    elif score >= 60.0:
        return "Caution"
    elif score >= 40.0:
        return "At-Risk"
    return "Critical"


def _get_zone_color(zone: str) -> str:
    colors = {
        "Safe": "#10B981",
        "Caution": "#F59E0B",
        "At-Risk": "#F97316",
        "Critical": "#EF4444"
    }
    return colors.get(zone, "#3B82F6")

