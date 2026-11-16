# FinGuard India — Banking Health Early Warning System & Intelligence Platform

> **RBI-Powered AI Financial Health Screener for Scheduled Commercial Banks**
> Based on published RBI Statistical Tables (DBIE) 2015–2024 (10 consecutive years), Basel III prudential standards, and CRISIL CRAMEL framework.

---

## 📌 Project Overview
FinGuard India solves the critical information asymmetry faced by over 80 million Indian retail investors and depositors who put money into bank fixed deposits or equity shares without transparent, plain-language visibility into a bank's true solvency and distress trajectory.

When Yes Bank collapsed in March 2020, warning signals were present in RBI data for over 18 months (NPA rising from 1.7% to 13.4%, capital buffer eroding). Institutional investors exited early; retail investors holding FDs and shares were caught uninformed.

**FinGuard solves 4 core retail problems:**
1. **Aggregation:** Aggregates and normalizes 40+ disparate RBI balance sheet tables into one structured engine across 112 commercial, scheduled, foreign, and small finance banks (932 bank-year records from 2015 to 2024).
2. **Comparison:** Generates a standardized, comparable **FinGuard Health Score (0 to 100)** across all evaluated banks.
3. **Projection:** Uses predictive time-series extrapolation to project health scores **2 financial cycles ahead** with early threshold crossing warnings.
4. **Personalization:** Directly connects bank solvency to an individual's personal holding (calculating statutory **DICGC ₹5,00,000 insurance coverage**, uninsured excess, key vulnerability ratio, and action plans).

---

## 🏛️ Monitored Banking Institutions (112 Banks, 10 Years DBIE Scope)

| Type | Banks Monitored |
| :--- | :--- |
| **Public Sector (PSU)** | State Bank of India (SBI), Bank of Baroda (BOB), Punjab National Bank (PNB), Canara Bank, Union Bank of India (UBI), Bank of India (BOI), Indian Bank, Central Bank of India (CBI), Indian Overseas Bank (IOB), UCO Bank, Bank of Maharashtra (BOM), Punjab & Sind Bank (PSB), plus historical pre-merger entities (Allahabad Bank, Andhra Bank, Corporation Bank, Oriental Bank of Commerce, Syndicate Bank, Vijaya Bank) |
| **Private Sector** | HDFC Bank, ICICI Bank, Axis Bank, Kotak Mahindra Bank, IndusInd Bank, Yes Bank, IDFC First Bank, IDBI Bank, Federal Bank, Bandhan Bank, RBL Bank, City Union Bank, Karur Vysya Bank, CSB Bank, South Indian Bank, Jammu & Kashmir Bank, Karnataka Bank, Nainital Bank, etc. |
| **Foreign Banks** | Citibank, Standard Chartered Bank, HSBC, Deutsche Bank, Barclays Bank, Bank of America, DBS Bank, J.P. Morgan, Mizuho Bank, MUFG Bank, BNP Paribas, Societe Generale, etc. |
| **Small Finance Banks (SFBs)** | AU Small Finance Bank, Equitas SFB, Ujjivan SFB, Jana SFB, Suryoday SFB, ESAF SFB, Utkarsh SFB, Fincare SFB, Capital SFB, etc. |
| **Payments Banks** | Airtel Payments Bank, India Post Payments Bank, Fino Payments Bank, Paytm Payments Bank, etc. |

---

## 📊 The 8 Solvency Ratios & Weights

FinGuard implements the exact RBI ratio attributes and weights specified in the project scope document:

| # | Ratio | Key Attributes Used | Weight | Safety Threshold | Direction |
| :- | :--- | :--- | :---: | :---: | :---: |
| 1 | **Net NPA Ratio** | Net NPA Closing ÷ Advances (net of provisions) | **25%** | `< 1.0%` (Safe), `> 5.0%` (Critical) | Lower is better |
| 2 | **Capital Adequacy (CAR)** | CRAR Total (%) | **20%** | `>= 15.0%` (Safe), `< 9.0%` (Critical) | Higher is better |
| 3 | **Return on Assets (ROA)** | Net Profit ÷ Total Assets | **15%** | `>= 1.1%` (Safe), `< 0.25%` (Critical) | Higher is better |
| 4 | **Net Interest Margin (NIM)** | Net Interest Income ÷ Total Assets | **10%** | `>= 3.0%` (Safe), `< 1.8%` (Critical) | Higher is better |
| 5 | **Liquidity Coverage (LCR)** | Basel III / Pillar 3 Disclosed HQLA survival % | **10%** | `>= 130%` (Mandated min: 100%) | Higher is better |
| 6 | **Cost-to-Income (C2I)** | Operating Expenses ÷ (NII + Other Income) | **10%** | `<= 48%` (Safe), `> 65%` (Critical) | Lower is better |
| 7 | **Debt-to-Equity (Leverage)** | Borrowings ÷ (Capital + Reserves) | **5%** | `<= 1.3x` (Safe), `> 3.5x` (Critical) | Lower is better |
| 8 | **Provision Coverage (PCR)** | (Gross NPA − Net NPA) ÷ Gross NPA | **5%** | `>= 75%` (Safe), `< 50%` (Critical) | Higher is better |

---

## 🚀 Key Features

### 1. Composite FinGuard Health Score (0–100)
- **80 to 100:** **Safe** (Green) — High capital buffer, sub-1% Net NPA, robust 30-day liquidity.
- **60 to 79:** **Caution** (Yellow) — Sound balance sheet; mild efficiency or margin drag.
- **40 to 59:** **At-Risk** (Orange) — Stress emerging; capital buffer thinning.
- **0 to 39:** **Critical** (Red) — Severe insolvency hazard; precedes RBI moratorium or PCA framework.

### 2. Multi-Year Trajectory Analysis
Classifies 4-year trend (FY22–FY25) as **Improving**, **Stable**, or **Deteriorating** based on annual health score and bad loan trajectories.

### 3. Predictive Health Score Forecasting
Mathematical extrapolation of health score trajectory forward for **FY26 and FY27** with 95% confidence intervals and early threshold-crossing risk alerts.

### 4. Tree SHAP Feature Attribution (Explainable AI)
Deconstructs why a bank scored what it scored:
- Base sector score: `68.5`
- Points added by strong ratios (e.g. `CAR at 22.2% added +3.1 pts`)
- Points subtracted by weak ratios (e.g. `Cost-to-Income dragged down -1.4 pts`)
- Automatically highlights **"The One Number to Watch"** (the bank's primary vulnerability).

### 5. FinBERT News Sentiment & Dual-Signal Matrix
- FinBERT NLP analyzes news headlines to detect leadership departures, regulatory penalties, and ethical probes that financial ratios miss.
- **Dual-Signal Risk Matrix:** Combines fundamental health score with news sentiment to catch governance divergence (e.g., strong fundamentals with adverse leadership turnover).

### 6. Personal Investment Risk Connector
Retail depositors enter their FD or equity holdings:
- **Statutory DICGC Guarantee Check:** Calculates exact coverage under the ₹5,00,000 statutory limit per depositor per bank.
- Identifies **uninsured excess exposure** and provides actionable diversification recommendations.
- Explains what a health score drop would mean for their specific investment.

### 7. Historical Crisis Validation Layer (Empirical Proof of Concept)
Retrospectively validates FinGuard on 4 major Indian financial collapses:
- **Yes Bank (2017–2020):** 18-month early warning (score plunged to At-Risk in FY19 and Critical in FY20).
- **PMC Bank (2018–2019):** 15-month early warning on single-borrower concentration.
- **IL&FS (2016–2018):** 16-month early warning on extreme wholesale leverage (D/E > 10x).
- **DHFL (2017–2019):** 14-month early warning on commercial paper rollover distress.

---

## 🛠️ Tech Stack & Directory Structure

- **Backend:** FastAPI, Uvicorn, Pydantic, Python 3.13
- **Machine Learning & Analytics:** Scikit-Learn (Random Forest), NumPy, Pandas, Tree SHAP Attribution
- **Frontend Dashboard:** Modern Responsive HTML5, Tailwind CSS, Chart.js, Lucide Icons
- **Data Source:** RBI Statistical Tables Relating to Banks in India (DBIE)

```
finguard-india/
├── api/
│   └── app.py                     # FastAPI REST API (12 endpoints + UI serving)
├── data/
│   ├── banks_master_dataset.csv   # Master dataset: 932 rows, 26 columns, 112 banks (2015-2024)
│   ├── historical_crises.json     # Yes Bank, PMC Bank, IL&FS, DHFL timelines
│   └── bank_news.json             # Audited news & FinBERT sentiment data
├── frontend/
│   ├── index.html                 # Modern responsive single-page web dashboard
│   └── app.js                     # Interactive client logic & Chart.js rendering
├── models/
│   └── finguard_model.joblib      # Trained Random Forest model artifacts
├── src/
│   ├── ratio_engine.py            # Exact 8 RBI ratio calculations & benchmarking
│   ├── ml_scoring.py              # ML scoring, SHAP explainability, trajectory
│   ├── forecaster.py              # Predictive score forecasting & threshold alerts
│   ├── news_sentiment.py          # FinBERT sentiment & Dual-Signal Matrix
│   ├── personal_risk.py           # DICGC statutory protection & retail connector
│   ├── crisis_validator.py        # Historical crisis retrospective proof
│   └── data_pipeline.py           # Master pipeline indexing all 20 banks
├── tests/
│   └── test_finguard.py           # Unit tests
├── requirements.txt
├── run.py                         # One-click application launcher
└── README.md
```

---

## 💻 Running the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Server
```bash
python run.py
```
Open your browser at:
- **Interactive Web Dashboard:** `http://127.0.0.1:8000/`
- **Interactive Swagger API Documentation:** `http://127.0.0.1:8000/docs`

### 3. Run Automated Tests
```bash
python -m unittest discover tests
```

