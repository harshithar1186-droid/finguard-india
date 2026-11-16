"""
FinGuard India - FastAPI Application
Provides RESTful APIs for banking health scoring, SHAP explainability,
forecasting, FinBERT sentiment, personal investment risk, and historical crisis validation.
"""

import os
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.data_pipeline import FinGuardPipeline
from src.crisis_validator import HistoricalCrisisValidator
from src.news_sentiment import FinBERTNewsSentimentEngine
from src.personal_risk import evaluate_personal_fd_exposure, evaluate_personal_equity_exposure

app = FastAPI(
    title="FinGuard India API",
    description="RBI-Powered Banking Health Early Warning System & Financial Intelligence Platform",
    version="1.0.0"
)

# Enable CORS for local and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline and services
pipeline = FinGuardPipeline()
pipeline.initialize()

crisis_validator = HistoricalCrisisValidator()
sentiment_engine = FinBERTNewsSentimentEngine()


# --- Pydantic Request Models ---
class HeadlineAnalysisRequest(BaseModel):
    headline: str = Field(..., example="RBI imposes penalty on bank for non-compliance with KYC directives")


class PersonalRiskRequest(BaseModel):
    bank_id: str = Field(..., example="SBI")
    holding_type: str = Field("fd", description="'fd' for Fixed Deposit / Savings, 'equity' for Shares")
    amount_or_shares: float = Field(..., example=250000.0, description="FD amount in INR, or number of shares")
    buy_price_inr: Optional[float] = Field(0.0, description="Average purchase price per share (if holding_type is equity)")


# --- REST Endpoints ---

@app.get("/api/health", summary="System Health Check")
def get_system_health():
    return {
        "status": "online",
        "service": "FinGuard India Master API",
        "banks_indexed": len(pipeline.records_by_bank),
        "total_evaluated_snapshots": len(pipeline.all_snapshots),
        "years_covered": "2015 - 2024 (10 Years)",
        "active_evaluation_year": 2024
    }


@app.get("/api/sector/overview", summary="Macro Sector Overview")
def get_sector_overview(year: int = Query(2024, ge=2015, le=2024)):
    """Returns sector-wide banking health metrics, total credit, deposits, and risk tier distributions."""
    actual_year = int(year) if isinstance(year, (int, str)) and not hasattr(year, "default") else 2024
    return pipeline.get_sector_overview(actual_year)


@app.get("/api/banks", summary="List All Indexed Banks")
def list_banks():
    """Returns list of all indexed commercial, foreign, and small finance banks."""
    banks = []
    for b_id, meta in pipeline.bank_metadata.items():
        years = pipeline.records_by_bank.get(b_id, {})
        latest_y = max(years.keys()) if years else 2024
        latest = years.get(latest_y, {})
        banks.append({
            "bank_id": b_id,
            "bank_name": meta["bank_name"],
            "bank_type": meta["bank_type"],
            "current_score": latest.get("finguard_score", 0.0),
            "zone": latest.get("zone", "Caution"),
            "latest_year": latest_y
        })
    banks.sort(key=lambda x: x["bank_name"])
    return {"banks": banks, "count": len(banks)}


@app.get("/api/leaderboard", summary="Get Bank Leaderboard and Rankings")
def get_leaderboard(
    year: int = Query(2024, ge=2015, le=2024, description="Financial Year (2015 - 2024)"),
    bank_type: Optional[str] = Query(None, description="Filter: 'psu', 'private', 'foreign', 'sfb', 'payments', or omit for all")
):
    """Returns full ranked leaderboard of all banks for the selected year."""
    actual_year = int(year) if isinstance(year, (int, str)) and not hasattr(year, "default") else 2024
    actual_bank_type = bank_type if isinstance(bank_type, str) else None
    data = pipeline.get_leaderboard(year=actual_year, bank_type=actual_bank_type)
    return {
        "year": actual_year,
        "filter_bank_type": actual_bank_type or "all",
        "total": len(data),
        "leaderboard": data
    }


@app.get("/api/banks/{bank_id}", summary="Get Deep-Dive Bank Profile")
def get_bank_profile(bank_id: str):
    """Returns full 4-year financial ratio history, latest health metrics, and vulnerability drivers."""
    profile = pipeline.get_bank_full_profile(bank_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])
    return profile


@app.get("/api/banks/{bank_id}/shap", summary="SHAP Feature Attribution Explainability")
def get_bank_shap(bank_id: str):
    """Calculates tree SHAP-style points added/subtracted by each of the 8 ratios from baseline."""
    profile = pipeline.get_bank_full_profile(bank_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])
    return {
        "bank_id": bank_id.upper(),
        "bank_name": profile["bank_name"],
        "shap_explainability": profile["shap_explainability"]
    }


@app.get("/api/banks/{bank_id}/forecast", summary="Predictive Score Forecasting (2 Periods Ahead)")
def get_bank_forecast(bank_id: str, periods: int = Query(2, ge=1, le=4)):
    """Forward mathematical projection of health score trajectory with threshold crossing alerts."""
    actual_periods = int(periods) if isinstance(periods, (int, str)) and not hasattr(periods, "default") else 2
    profile = pipeline.get_bank_full_profile(bank_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])
    return {
        "bank_id": bank_id.upper(),
        "bank_name": profile["bank_name"],
        "current_score": profile["current_score"],
        "current_zone": profile["current_zone"],
        "forecast": profile["forecast"]
    }


@app.get("/api/banks/{bank_id}/sentiment", summary="FinBERT News Sentiment & Governance Matrix")
def get_bank_sentiment(bank_id: str):
    """Retrieves news headlines, FinBERT sentiment polarity, governance flags, and dual-signal matrix."""
    profile = pipeline.get_bank_full_profile(bank_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])
    return {
        "bank_id": bank_id.upper(),
        "bank_name": profile["bank_name"],
        "sentiment": profile["sentiment"],
        "dual_signal_matrix": profile["dual_signal_matrix"]
    }


@app.post("/api/sentiment/analyze", summary="Analyze Custom News Headline with FinBERT")
def analyze_custom_headline(req: HeadlineAnalysisRequest):
    """Runs FinBERT sentiment classification and governance flag detection on any custom financial headline."""
    return sentiment_engine.analyze_headline(req.headline)


@app.post("/api/personal-risk", summary="Personal Investment Risk Connector")
def calculate_personal_risk(req: PersonalRiskRequest):
    """Connects user personal FD or stock exposure to bank health score, DICGC statutory insurance, and watch triggers."""
    profile = pipeline.get_bank_full_profile(req.bank_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])

    if req.holding_type.lower() == "equity":
        return evaluate_personal_equity_exposure(
            bank_id=req.bank_id.upper(),
            bank_name=profile["bank_name"],
            shares_count=int(req.amount_or_shares),
            buy_price_inr=req.buy_price_inr or 0.0,
            current_finguard_score=profile["current_score"],
            current_zone=profile["current_zone"],
            biggest_risk_factor=profile["biggest_risk_factor"]
        )
    else:
        return evaluate_personal_fd_exposure(
            bank_id=req.bank_id.upper(),
            bank_name=profile["bank_name"],
            fd_amount_inr=req.amount_or_shares,
            current_finguard_score=profile["current_score"],
            current_zone=profile["current_zone"],
            biggest_risk_factor=profile["biggest_risk_factor"]
        )


@app.get("/api/historical-crises", summary="Historical Crisis Validation Summaries")
def get_historical_crises():
    """Empirical proof of concept: summarizes retrospective early warnings for Yes Bank, PMC Bank, IL&FS, DHFL."""
    return {
        "crises": crisis_validator.get_all_crisis_summaries(),
        "methodology": "Trained model evaluated on historical quarters leading up to moratoriums/defaults. Verified 12-18 month early warning lead time."
    }


@app.get("/api/historical-crises/{entity_id}", summary="Historical Crisis Entity Detail")
def get_crisis_detail(entity_id: str):
    """Detailed quarter-by-quarter timeline and score deterioration for a specific crisis entity."""
    detail = crisis_validator.get_crisis_detail(entity_id)
    if "error" in detail:
        raise HTTPException(status_code=404, detail=detail["error"])
    return detail


# --- Serve Modern Interactive UI Frontend ---
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", summary="FinGuard India Web Dashboard")
def serve_dashboard():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "FinGuard India API is operational. Visit /docs for Swagger UI documentation."}
