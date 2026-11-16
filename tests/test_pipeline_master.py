import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.data_pipeline import FinGuardPipeline

p = FinGuardPipeline()
count = p.initialize()
print(f"Initialized! Snapshots: {count}, Unique banks: {len(p.records_by_bank)}")

overview = p.get_sector_overview(2024)
print(f"Overview 2024: Total banks: {overview['total_banks']}, Avg Score: {overview['average_finguard_score']}")

lb = p.get_leaderboard(2024)
print("\nTop 8 Banks in 2024:")
for b in lb[:8]:
    print(f"  Rank {b['rank']:<2}: {b['bank_name'][:30]:<32} ({b['bank_id']:<6}) | Score: {b['finguard_score']:<5} ({b['zone']:<7}) | {b['bank_type']}")

print("\nSample Crisis Bank Check (Yes Bank in 2020):")
yes = p.get_bank_full_profile("YES")
for h in yes["history"]:
    print(f"  Year {h['year']}: Score {h['finguard_score']:<5} ({h['zone']:<8}) Net NPA: {h['net_npa_pct']:<5}% CAR: {h['crar_total_pct']:<5}% Crisis: {h['crisis_label']}")

print("\nForecast for Yes Bank into 2025 & 2026:")
for f in yes["forecast"]["projections"]:
    print(f"  {f['period_label']}: Projected Score {f['projected_score']} ({f['zone']})")
