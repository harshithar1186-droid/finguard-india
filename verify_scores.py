from src.data_pipeline import FinGuardPipeline

p = FinGuardPipeline()
p.initialize()
lb = p.get_leaderboard(2025)

print(f"{'Rank':<5} {'Bank ID':<8} {'Bank Name':<26} {'Score':<7} {'Zone':<10} {'Net NPA%':<10} {'CAR%':<8} {'ROA%':<8} {'Trajectory'}")
print("-" * 95)
for b in lb:
    print(f"{b['rank']:<5} {b['bank_id']:<8} {b['bank_name'][:25]:<26} {b['finguard_score']:<7.1f} {b['zone']:<10} {b['net_npa_pct']:<10.2f} {b['crar_total_pct']:<8.2f} {b['roa_pct']:<8.2f} {b['trajectory']}")

