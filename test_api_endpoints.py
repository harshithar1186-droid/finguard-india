"""
Full API Functional Verification for FinGuard India
Directly invokes all API handlers to verify routes, responses, calculations, and schemas.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from api.app import (
    get_system_health,
    get_sector_overview,
    list_banks,
    get_leaderboard,
    get_bank_profile,
    get_bank_shap,
    get_bank_forecast,
    get_bank_sentiment,
    analyze_custom_headline,
    calculate_personal_risk,
    get_historical_crises,
    get_crisis_detail,
    HeadlineAnalysisRequest,
    PersonalRiskRequest
)

def run_tests():
    print("[1] Testing get_system_health() ...")
    health = get_system_health()
    assert health["status"] == "online"
    assert health["banks_indexed"] >= 100
    print(f"    -> OK: {health['banks_indexed']} banks indexed across {health['total_evaluated_snapshots']} snapshots.")

    print("[2] Testing get_sector_overview(year=2024) ...")
    sector = get_sector_overview(2024)
    assert sector["total_banks"] >= 80
    assert sector["average_finguard_score"] > 60.0
    print(f"    -> OK: Sector Avg Score: {sector['average_finguard_score']}, Avg Net NPA: {sector['average_net_npa_pct']}%, Avg CAR: {sector['average_crar_pct']}%")

    print("[3] Testing list_banks() ...")
    banks_res = list_banks()
    assert banks_res["count"] >= 100
    print(f"    -> OK: {banks_res['count']} banks listed in response.")

    print("[4] Testing get_leaderboard(year=2024) ...")
    lb_res = get_leaderboard(year=2024)
    lb = lb_res["leaderboard"]
    assert len(lb) >= 80
    top = lb[0]
    print(f"    -> OK: Rank 1 is {top['bank_name']} ({top['bank_id']}) with FinGuard Score: {top['finguard_score']} ({top['zone']})")

    print("[5] Testing get_bank_profile('HDFC') ...")
    hdfc = get_bank_profile("HDFC")
    assert hdfc["bank_id"] == "HDFC"
    assert len(hdfc["history"]) >= 4
    print(f"    -> OK: HDFC Bank score: {hdfc['current_score']} ({hdfc['current_zone']}), Trajectory: {hdfc['trajectory']['trajectory']}")

    print("[6] Testing get_bank_shap('HDFC') ...")
    shap = get_bank_shap("HDFC")["shap_explainability"]
    assert len(shap["attributions"]) == 8
    print(f"    -> OK: SHAP Summary: {shap['plain_language_summary']}")

    print("[7] Testing get_bank_forecast('HDFC', periods=2) ...")
    fore = get_bank_forecast("HDFC", 2)["forecast"]
    assert len(fore["projections"]) == 2
    p1 = fore["projections"][0]
    print(f"    -> OK: Projected FY25: {p1['projected_score']} ({p1['zone']}). {fore['summary']}")

    print("[8] Testing get_bank_sentiment('HDFC') ...")
    sent = get_bank_sentiment("HDFC")
    print(f"    -> OK: Dual Matrix: '{sent['dual_signal_matrix']['quadrant']}' - {sent['dual_signal_matrix']['guidance'][:90]}...")

    print("[9] Testing analyze_custom_headline(...) FinBERT tester ...")
    res_neg = analyze_custom_headline(HeadlineAnalysisRequest(headline="Chairman resigned citing board governance and ethical concerns"))
    assert res_neg["finbert_sentiment"] == "Negative"
    assert res_neg["governance_flag"] == True
    print(f"    -> OK: Negative governance trigger detected: {res_neg['finbert_sentiment']} (Score: {res_neg['sentiment_score']})")

    res_pos = analyze_custom_headline(HeadlineAnalysisRequest(headline="Bank posts record quarterly net profit as asset quality surges"))
    assert res_pos["finbert_sentiment"] == "Positive"
    print(f"    -> OK: Positive earnings milestone detected: {res_pos['finbert_sentiment']} (Score: {res_pos['sentiment_score']})")

    print("[10] Testing calculate_personal_risk (FD Rs. 3.5 Lakh - 100% Insured) ...")
    req_safe = PersonalRiskRequest(bank_id="SBI", holding_type="fd", amount_or_shares=350000.0)
    fd_safe = calculate_personal_risk(req_safe)
    assert fd_safe["is_fully_covered"] == True
    assert fd_safe["dicgc_covered_inr"] == 350000.0
    print(f"    -> OK: {fd_safe['insurance_badge']}: {fd_safe['output_1_insurance'][:85]}...")

    print("[11] Testing calculate_personal_risk (FD Rs. 12.5 Lakh - Rs. 7.5L Uninsured Excess) ...")
    req_high = PersonalRiskRequest(bank_id="SBI", holding_type="fd", amount_or_shares=1250000.0)
    fd_high = calculate_personal_risk(req_high)
    assert fd_high["is_fully_covered"] == False
    assert fd_high["uninsured_excess_inr"] == 750000.0
    print(f"    -> OK: Uninsured excess correctly identified: Rs. {fd_high['uninsured_excess_inr']:,.0f}")

    print("[12] Testing get_historical_crises() ...")
    crises_res = get_historical_crises()
    assert len(crises_res["crises"]) == 4
    print(f"    -> OK: All 4 historical crises available for retrospective proof.")

    print("[13] Testing get_crisis_detail('YES_BANK') ...")
    yes = get_crisis_detail("YES_BANK")
    assert yes["lead_time_months"] == 18
    assert yes["timeline"][-1]["zone"] == "Critical"
    print(f"    -> OK: Yes Bank 18-month lead time confirmed. Conclusion: {yes['validation_conclusion']}")

    print("\n" + "=" * 70)
    print("SUCCESS: ALL 13 ENDPOINTS AND CORE ENGINES VERIFIED AND PASSING!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
