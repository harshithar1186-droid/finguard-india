/**
 * FinGuard India - Frontend Application Script
 * Orchestrates API communication, dynamic Chart.js visualizations,
 * and user interactions.
 */

let currentYear = 2024;
let currentBankType = 'all';
let selectedBankId = 'HDFC';
let trendChartInstance = null;
let forecastChartInstance = null;
let shapChartInstance = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  await loadSectorOverview(currentYear);
  await loadLeaderboard(currentYear);
  await populateBankDropdowns();
  await selectBank('HDFC');
  await loadCrisisDetail('YES_BANK');
});

// TAB SWITCHER
function switchTab(tabId) {
  const tabs = ['leaderboard', 'deepdive', 'forecast', 'shap', 'sentiment', 'personal', 'crises', 'methodology'];
  tabs.forEach(t => {
    const section = document.getElementById(`tab-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (t === tabId) {
      section?.classList.remove('hidden');
      btn?.classList.remove('text-slate-400', 'hover:text-white', 'hover:bg-slate-800/60');
      btn?.classList.add('bg-blue-600', 'text-white');
    } else {
      section?.classList.add('hidden');
      btn?.classList.remove('bg-blue-600', 'text-white');
      btn?.classList.add('text-slate-400', 'hover:text-white', 'hover:bg-slate-800/60');
    }
  });

  // Re-render chart sizes when tab opens
  setTimeout(() => {
    if (tabId === 'deepdive' && trendChartInstance) trendChartInstance.resize();
    if (tabId === 'forecast' && forecastChartInstance) forecastChartInstance.resize();
    if (tabId === 'shap' && shapChartInstance) shapChartInstance.resize();
  }, 100);

  if (window.lucide) lucide.createIcons();
}

// 1. SECTOR OVERVIEW
async function loadSectorOverview(year = currentYear) {
  try {
    const res = await fetch(`/api/sector/overview?year=${year}`);
    const data = await res.json();
    document.getElementById('stat-avg-score').innerText = `${data.average_finguard_score} / 100`;
    document.getElementById('stat-avg-npa').innerText = `${data.average_net_npa_pct.toFixed(2)}%`;
    document.getElementById('stat-avg-car').innerText = `${data.average_crar_pct.toFixed(2)}%`;
    document.getElementById('stat-advances').innerText = `₹${(data.total_system_advances_crores / 100000).toFixed(1)}L Cr`;
    
    // Zone breakdown pills
    const zd = data.zone_distribution || {};
    const pillsContainer = document.getElementById('stat-zone-pills');
    if (pillsContainer) {
      pillsContainer.innerHTML = `
        <span class="text-xs px-2 py-0.5 rounded zone-safe font-bold">Safe: ${zd.Safe || 0}</span>
        <span class="text-xs px-2 py-0.5 rounded zone-caution font-bold">Caution: ${zd.Caution || 0}</span>
        ${(zd['At-Risk'] || 0) > 0 ? `<span class="text-xs px-2 py-0.5 rounded zone-at-risk font-bold">At-Risk: ${zd['At-Risk']}</span>` : ''}
        ${(zd.Critical || 0) > 0 ? `<span class="text-xs px-2 py-0.5 rounded zone-critical font-bold">Critical: ${zd.Critical}</span>` : ''}
      `;
    }
  } catch (err) {
    console.error('Error loading sector overview:', err);
  }
}

// 2. LEADERBOARD
async function loadLeaderboard(year) {
  currentYear = year;
  const select = document.getElementById('year-select-dropdown');
  if (select) select.value = String(year);

  // Sync Macro Sector statistics with the selected year
  loadSectorOverview(year);

  try {
    let url = `/api/leaderboard?year=${year}`;
    if (currentBankType !== 'all') {
      url += `&bank_type=${currentBankType}`;
    }
    const res = await fetch(url);
    const json = await res.json();
    renderLeaderboardTable(json.leaderboard);
  } catch (err) {
    console.error('Error loading leaderboard:', err);
  }
}

function filterBankType(type) {
  currentBankType = type;
  const categories = ['all', 'psu', 'private', 'foreign', 'sfb', 'payments'];
  categories.forEach(t => {
    const btn = document.getElementById(`filter-${t}`);
    if (t === type) {
      btn?.classList.add('bg-slate-800', 'text-white', 'font-semibold');
      btn?.classList.remove('text-slate-400');
    } else {
      btn?.classList.remove('bg-slate-800', 'text-white', 'font-semibold');
      btn?.classList.add('text-slate-400');
    }
  });
  loadLeaderboard(currentYear);
}

function renderLeaderboardTable(banks) {
  const tbody = document.getElementById('leaderboard-tbody');
  if (!tbody) return;

  if (!banks || banks.length === 0) {
    tbody.innerHTML = `<tr><td colspan="13" class="py-8 text-center text-slate-500">No banks match current filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = banks.map(b => {
    const zoneBadge = getZoneBadgeHtml(b.zone, b.finguard_score);
    const trajBadge = getTrajectoryBadgeHtml(b.trajectory);
    const sentimentBadge = getSentimentBadgeHtml(b.sentiment, b.governance_flag);
    const crisisAlert = b.crisis_label === 1 
      ? `<span class="ml-2 px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 text-[10px] font-bold border border-rose-500/40 inline-flex items-center"><i data-lucide="alert-triangle" class="w-2.5 h-2.5 mr-0.5"></i>Crisis Tag</span>` 
      : '';

    return `
      <tr class="glass-card-hover cursor-pointer transition-colors" onclick="openBankDeepDive('${b.bank_id}')">
        <td class="py-3 px-4 text-center font-mono font-bold text-slate-400">${b.rank}</td>
        <td class="py-3 px-4 font-semibold text-white">
          <div class="flex items-center space-x-2.5">
            <span class="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 text-blue-400 font-mono text-xs flex items-center justify-center font-bold">${b.bank_id}</span>
            <div>
              <div class="text-sm font-bold text-slate-100 flex items-center flex-wrap gap-1">
                <span>${b.bank_name}</span>
                ${crisisAlert}
              </div>
              <div class="text-[11px] text-slate-500 font-sans">${b.bank_type}</div>
            </div>
          </div>
        </td>
        <td class="py-3 px-4 text-center font-mono font-extrabold text-base text-white">${b.finguard_score.toFixed(1)}</td>
        <td class="py-3 px-4 text-center">${zoneBadge}</td>
        <td class="py-3 px-4 text-center">${trajBadge}</td>
        <td class="py-3 px-4 text-right font-mono ${b.net_npa_pct <= 1.0 ? 'text-emerald-400' : 'text-amber-400'}">${b.net_npa_pct.toFixed(2)}%</td>
        <td class="py-3 px-4 text-right font-mono text-slate-200">${b.crar_total_pct.toFixed(2)}%</td>
        <td class="py-3 px-4 text-right font-mono text-slate-200">${b.roa_pct.toFixed(2)}%</td>
        <td class="py-3 px-4 text-right font-mono text-slate-200">${b.nim_pct.toFixed(2)}%</td>
        <td class="py-3 px-4 text-right font-mono text-slate-200">${b.lcr_pct.toFixed(0)}%</td>
        <td class="py-3 px-4 text-right font-mono text-slate-200">${b.c2i_pct.toFixed(1)}%</td>
        <td class="py-3 px-4 text-center">${sentimentBadge}</td>
        <td class="py-3 px-4 text-center">
          <button class="px-2.5 py-1 text-xs rounded bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 border border-blue-500/30 transition-colors">
            Inspect
          </button>
        </td>
      </tr>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

function getZoneBadgeHtml(zone, score) {
  if (zone === 'Safe') return `<span class="px-2.5 py-0.5 rounded-full text-xs font-bold zone-safe">Safe</span>`;
  if (zone === 'Caution') return `<span class="px-2.5 py-0.5 rounded-full text-xs font-bold zone-caution">Caution</span>`;
  if (zone === 'At-Risk') return `<span class="px-2.5 py-0.5 rounded-full text-xs font-bold zone-at-risk">At-Risk</span>`;
  return `<span class="px-2.5 py-0.5 rounded-full text-xs font-bold zone-critical">Critical</span>`;
}

function getTrajectoryBadgeHtml(traj) {
  if (traj === 'Improving') {
    return `<span class="inline-flex items-center text-xs text-emerald-400 font-semibold"><i data-lucide="trending-up" class="w-3.5 h-3.5 mr-1"></i>Improving</span>`;
  } else if (traj === 'Deteriorating') {
    return `<span class="inline-flex items-center text-xs text-rose-400 font-semibold"><i data-lucide="trending-down" class="w-3.5 h-3.5 mr-1"></i>Deteriorating</span>`;
  }
  return `<span class="inline-flex items-center text-xs text-sky-400 font-semibold"><i data-lucide="minus" class="w-3.5 h-3.5 mr-1"></i>Stable</span>`;
}

function getSentimentBadgeHtml(sentiment, govFlag) {
  if (govFlag) {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">Gov Warning</span>`;
  }
  if (sentiment === 'Positive') {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400">Positive</span>`;
  }
  if (sentiment === 'Negative') {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400">Negative</span>`;
  }
  return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-400">Neutral</span>`;
}

// 3. BANK SELECTION & PROFILE DETAILS
async function populateBankDropdowns() {
  try {
    const res = await fetch('/api/banks');
    const json = await res.json();
    const banks = json.banks || [];

    const options = banks.map(b => `<option value="${b.bank_id}">${b.bank_name} (${b.bank_id})</option>`).join('');
    
    const selector1 = document.getElementById('bank-selector');
    const selector2 = document.getElementById('personal-bank-select');
    if (selector1) selector1.innerHTML = options;
    if (selector2) selector2.innerHTML = options;
  } catch (err) {
    console.error('Error populating dropdowns:', err);
  }
}

function openBankDeepDive(bankId) {
  selectBank(bankId);
  switchTab('deepdive');
}

async function selectBank(bankId) {
  selectedBankId = bankId;
  const s1 = document.getElementById('bank-selector');
  const s2 = document.getElementById('personal-bank-select');
  if (s1) s1.value = bankId;
  if (s2) s2.value = bankId;

  try {
    const res = await fetch(`/api/banks/${bankId}`);
    const profile = await res.json();

    renderDeepDiveProfile(profile);
    renderForecastView(profile);
    renderShapView(profile);
    renderSentimentView(profile);

    // Also run personal risk evaluation
    calculatePersonalRisk();
  } catch (err) {
    console.error('Error fetching bank profile:', err);
  }
}

function renderDeepDiveProfile(profile) {
  document.getElementById('detail-bank-avatar').innerText = profile.bank_id;
  document.getElementById('detail-bank-name').innerText = profile.bank_name;
  document.getElementById('detail-bank-type').innerText = profile.bank_type;
  document.getElementById('detail-score').innerText = profile.current_score.toFixed(1);

  const badge = document.getElementById('detail-zone-badge');
  badge.className = `text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider zone-${profile.current_zone.toLowerCase()}`;
  badge.innerText = profile.current_zone;

  document.getElementById('detail-score-explanation').innerText = profile.summary;
  document.getElementById('detail-trajectory-label').innerText = profile.trajectory.trajectory;
  document.getElementById('detail-trajectory-label').style.color = profile.trajectory.color;
  document.getElementById('detail-trajectory-desc').innerText = profile.trajectory.description;

  // Render 4-Year Trend Chart
  renderTrendChart(profile.history);

  // Render 8 Ratios
  renderRatiosGrid(profile.latest_ratios);
}

function renderTrendChart(history) {
  const ctx = document.getElementById('trendChart')?.getContext('2d');
  if (!ctx) return;

  const labels = history.map(h => `FY${String(h.year).slice(-2)}`);
  const scores = history.map(h => h.finguard_score);

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  trendChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'FinGuard Health Score',
          data: scores,
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.12)',
          borderWidth: 3,
          pointBackgroundColor: '#60A5FA',
          pointBorderColor: '#1E3A8A',
          pointBorderWidth: 2,
          pointRadius: 6,
          fill: true,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 20,
          max: 100,
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#94A3B8' }
        },
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#94A3B8' }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0F172A',
          titleColor: '#F8FAFC',
          bodyColor: '#93C5FD',
          borderColor: '#334155',
          borderWidth: 1
        }
      }
    }
  });
}

function renderRatiosGrid(r) {
  const container = document.getElementById('ratios-grid');
  if (!container) return;

  const ratiosData = [
    { title: '1. Net NPA Ratio', value: `${r.net_npa_pct.toFixed(2)}%`, benchmark: 'Safe: < 1.0% (RBI Limit: 6%)', status: r.net_npa_pct <= 1.0 ? 'Safe' : 'Caution', weight: '25% Weight', subscore: r.sub_scores?.net_npa },
    { title: '2. CAR (CRAR Total)', value: `${r.crar_total_pct.toFixed(2)}%`, benchmark: 'Safe: >= 15% (Min: 11.5%)', status: r.crar_total_pct >= 15.0 ? 'Safe' : 'Caution', weight: '20% Weight', subscore: r.sub_scores?.crar },
    { title: '3. Return on Assets (ROA)', value: `${r.roa_pct.toFixed(2)}%`, benchmark: 'Safe: >= 1.1% (Min: 0.25%)', status: r.roa_pct >= 1.1 ? 'Safe' : 'Caution', weight: '15% Weight', subscore: r.sub_scores?.roa },
    { title: '4. Net Interest Margin (NIM)', value: `${r.nim_pct.toFixed(2)}%`, benchmark: 'Safe: >= 3.0% (Benchmark > 2.5%)', status: r.nim_pct >= 3.0 ? 'Safe' : 'Caution', weight: '10% Weight', subscore: r.sub_scores?.nim },
    { title: '5. Liquidity Coverage (LCR)', value: `${r.lcr_pct.toFixed(0)}%`, benchmark: 'Mandated Min: 100% (Safe: > 130%)', status: r.lcr_pct >= 130 ? 'Safe' : 'Caution', weight: '10% Weight', subscore: r.sub_scores?.lcr },
    { title: '6. Cost-to-Income (C2I)', value: `${r.c2i_pct.toFixed(1)}%`, benchmark: 'Safe: <= 48% (Lower is better)', status: r.c2i_pct <= 48.0 ? 'Safe' : 'Caution', weight: '10% Weight', subscore: r.sub_scores?.cost_to_income },
    { title: '7. Debt-to-Equity (Leverage)', value: `${r.de_ratio.toFixed(2)}x`, benchmark: 'Safe: <= 1.3x (Borrowings / NW)', status: r.de_ratio <= 1.3 ? 'Safe' : 'Caution', weight: '5% Weight', subscore: r.sub_scores?.debt_to_equity },
    { title: '8. Provision Coverage (PCR)', value: `${r.pcr_pct.toFixed(1)}%`, benchmark: 'Safe: >= 75% (Min Cushion: 70%)', status: r.pcr_pct >= 75.0 ? 'Safe' : 'Caution', weight: '5% Weight', subscore: r.sub_scores?.pcr }
  ];

  container.innerHTML = ratiosData.map(item => `
    <div class="glass-card p-4 rounded-xl border border-slate-800 space-y-2">
      <div class="flex items-center justify-between text-xs text-slate-400">
        <span class="font-semibold text-slate-300">${item.title}</span>
        <span class="font-mono text-[10px] text-blue-400 font-bold bg-blue-500/10 px-1.5 py-0.5 rounded">${item.weight}</span>
      </div>
      <div class="flex items-baseline justify-between">
        <div class="text-xl font-bold font-mono text-white">${item.value}</div>
        <span class="text-xs px-2 py-0.5 rounded font-bold zone-${item.status.toLowerCase()}">${item.status}</span>
      </div>
      <div class="text-[11px] text-slate-400 border-t border-slate-800/80 pt-1.5 flex justify-between">
        <span>${item.benchmark}</span>
        <span class="font-mono text-slate-300">Pts: ${item.subscore?.toFixed(0)}</span>
      </div>
    </div>
  `).join('');
}

// 4. PREDICTIVE FORECASTING
function renderForecastView(profile) {
  const f = profile.forecast;
  if (!f) return;

  const alertBox = document.getElementById('forecast-alert-box');
  if (alertBox) {
    if (f.threshold_alerts && f.threshold_alerts.length > 0) {
      alertBox.className = 'mt-4 p-4 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-200 text-xs leading-relaxed flex items-center space-x-3';
      alertBox.innerHTML = `<i data-lucide="alert-triangle" class="w-5 h-5 text-amber-400 flex-shrink-0"></i><div><strong>Forward Warning:</strong> ${f.threshold_alerts[0].message}</div>`;
    } else {
      alertBox.className = 'mt-4 p-4 rounded-xl border border-emerald-500/40 bg-emerald-500/10 text-emerald-200 text-xs leading-relaxed flex items-center space-x-3';
      alertBox.innerHTML = `<i data-lucide="check-circle" class="w-5 h-5 text-emerald-400 flex-shrink-0"></i><div>${f.summary}</div>`;
    }
  }

  // List schedule
  const list = document.getElementById('forecast-timeline-list');
  if (list) {
    list.innerHTML = f.projections.map(p => `
      <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
        <div>
          <div class="font-bold text-white">${p.period_label}</div>
          <div class="text-[11px] text-slate-400">95% Range: ${p.lower_bound} – ${p.upper_bound}</div>
        </div>
        <div class="text-right">
          <div class="text-base font-bold font-mono text-white">${p.projected_score}</div>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold zone-${p.zone.toLowerCase()}">${p.zone}</span>
        </div>
      </div>
    `).join('');
  }

  // Forecast Chart
  const ctx = document.getElementById('forecastChart')?.getContext('2d');
  if (!ctx) return;

  const historyYears = profile.history.map(h => `FY${String(h.year).slice(-2)}`);
  const historyScores = profile.history.map(h => h.finguard_score);

  const forecastYears = f.projections.map(p => `FY${String(p.year).slice(-2)} (F)`);
  const forecastScores = f.projections.map(p => p.projected_score);

  const allLabels = [...historyYears, ...forecastYears];
  const histDataset = [...historyScores, ...Array(forecastScores.length).fill(null)];
  const foreDataset = [...Array(Math.max(0, historyScores.length - 1)).fill(null), historyScores[historyScores.length - 1], ...forecastScores];

  if (forecastChartInstance) forecastChartInstance.destroy();

  forecastChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Historical Health Score',
          data: histDataset,
          borderColor: '#3B82F6',
          borderWidth: 3,
          pointRadius: 5,
          tension: 0.2
        },
        {
          label: 'Extrapolated Health Score',
          data: foreDataset,
          borderColor: '#A855F7',
          borderDash: [6, 6],
          borderWidth: 3,
          pointRadius: 6,
          pointBackgroundColor: '#C084FC',
          tension: 0.2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 20, max: 100, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94A3B8' } },
        x: { grid: { color: 'rgba(255, 255, 255, 0.04)' }, ticks: { color: '#94A3B8' } }
      }
    }
  });

  if (window.lucide) lucide.createIcons();
}

// 5. SHAP EXPLAINABILITY
function renderShapView(profile) {
  const shap = profile.shap_explainability;
  if (!shap) return;

  document.getElementById('shap-summary-box').innerText = shap.plain_language_summary;

  const watchMetric = profile.biggest_risk_factor;
  if (watchMetric) {
    document.getElementById('shap-watch-metric-title').innerText = `${watchMetric.name} (${watchMetric.current_value}${watchMetric.unit})`;
    document.getElementById('shap-watch-metric-desc').innerText = `Regulatory limit: ${watchMetric.regulatory_benchmark}. This ratio had the lowest sub-score (${watchMetric.sub_score.toFixed(0)}/100) and represents ${profile.bank_name}'s foremost supervisory focus.`;
  }

  // Attribution Table
  const tbody = document.getElementById('shap-table-body');
  if (tbody) {
    tbody.innerHTML = shap.attributions.map(a => `
      <tr class="hover:bg-slate-900/60">
        <td class="py-2.5 px-3 font-semibold text-white">${a.feature_name}</td>
        <td class="py-2.5 px-3 text-right font-mono text-slate-300">${a.value}${a.unit}</td>
        <td class="py-2.5 px-3 text-right font-mono font-bold ${a.attribution_points >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
          ${a.attribution_points >= 0 ? '+' : ''}${a.attribution_points.toFixed(1)} pts
        </td>
        <td class="py-2.5 px-3 text-slate-400">${a.explanation}</td>
      </tr>
    `).join('');
  }

  // Horizontal SHAP Bar Chart
  const ctx = document.getElementById('shapChart')?.getContext('2d');
  if (!ctx) return;

  const labels = shap.attributions.map(a => a.feature_name);
  const values = shap.attributions.map(a => a.attribution_points);
  const colors = values.map(v => v >= 0 ? '#10B981' : '#EF4444');

  if (shapChartInstance) shapChartInstance.destroy();

  shapChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Points Added / Subtracted vs Base Score (68.5)',
          data: values,
          backgroundColor: colors,
          borderRadius: 4
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94A3B8' } },
        y: { ticks: { color: '#CBD5E1', font: { size: 11 } } }
      },
      plugins: { legend: { display: false } }
    }
  });

  if (window.lucide) lucide.createIcons();
}

// 6. FINBERT NEWS & GOVERNANCE
function renderSentimentView(profile) {
  const sent = profile.sentiment;
  const dual = profile.dual_signal_matrix;

  document.getElementById('news-bank-label').innerText = profile.bank_name;
  document.getElementById('news-sentiment-badge').innerText = `Overall Polarity: ${sent.overall_sentiment}`;

  const dualBox = document.getElementById('dual-matrix-box');
  const dualQuad = document.getElementById('dual-matrix-quadrant');
  const dualGuidance = document.getElementById('dual-matrix-guidance');

  if (dualQuad) {
    dualQuad.innerHTML = `<span>${dual.quadrant}</span> <span class="text-xs px-2 py-0.5 rounded font-mono" style="background:${dual.color}20; color:${dual.color}">${dual.risk_level}</span>`;
  }
  if (dualGuidance) {
    dualGuidance.innerText = dual.guidance;
  }

  // Headlines List
  const newsList = document.getElementById('bank-news-list');
  if (newsList) {
    if (sent.headlines && sent.headlines.length > 0) {
      newsList.innerHTML = sent.headlines.map(h => `
        <div class="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-mono font-semibold text-slate-400">${h.source} • ${h.date}</span>
            <div class="flex items-center space-x-1.5">
              ${h.governance_flag ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">Governance Trigger</span>` : ''}
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${h.finbert_sentiment === 'Positive' ? 'bg-emerald-500/10 text-emerald-400' : h.finbert_sentiment === 'Negative' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-300'}">${h.finbert_sentiment}</span>
            </div>
          </div>
          <div class="text-xs font-semibold text-white leading-snug">${h.headline}</div>
          <div class="text-[11px] text-slate-400">${h.summary}</div>
        </div>
      `).join('');
    } else {
      newsList.innerHTML = `<div class="p-6 text-center text-slate-500 text-xs">No active regulatory alerts or leadership departures for this institution.</div>`;
    }
  }

  if (window.lucide) lucide.createIcons();
}

async function testHeadlineSentiment() {
  const input = document.getElementById('custom-headline-input');
  const headline = input?.value.trim();
  if (!headline) return;

  const resultDiv = document.getElementById('headline-test-result');
  resultDiv.classList.remove('hidden');
  resultDiv.innerHTML = `<div class="text-slate-400">Classifying through FinBERT NLP pipeline...</div>`;

  try {
    const res = await fetch('/api/sentiment/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ headline: headline })
    });
    const data = await res.json();

    const color = data.finbert_sentiment === 'Positive' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' : data.finbert_sentiment === 'Negative' ? 'text-rose-400 border-rose-500/30 bg-rose-500/10' : 'text-slate-300 border-slate-700 bg-slate-800';

    resultDiv.className = `mt-3 p-3 rounded-lg text-xs border ${color} space-y-1`;
    resultDiv.innerHTML = `
      <div class="flex items-center justify-between font-bold">
        <span>Sentiment: ${data.finbert_sentiment} (Polarity: ${data.sentiment_score})</span>
        ${data.governance_flag ? `<span class="px-2 py-0.5 rounded text-[10px] bg-rose-500/30 text-rose-300">Governance Risk Triggered</span>` : ''}
      </div>
      <div class="text-[11px] opacity-80">"${data.headline}"</div>
    `;
  } catch (err) {
    console.error('Error analyzing headline:', err);
  }
}

// 7. PERSONAL RISK CONNECTOR
function toggleHoldingInputs(val) {
  const fdBox = document.getElementById('container-fd-input');
  const eqBox = document.getElementById('container-equity-input');
  if (val === 'equity') {
    fdBox?.classList.add('hidden');
    eqBox?.classList.remove('hidden');
  } else {
    fdBox?.classList.remove('hidden');
    eqBox?.classList.add('hidden');
  }
}

function setFdAmount(val) {
  const input = document.getElementById('personal-fd-amount');
  if (input) input.value = val;
  calculatePersonalRisk();
}

async function calculatePersonalRisk() {
  const bankId = document.getElementById('personal-bank-select')?.value || selectedBankId;
  const holdingType = document.getElementById('personal-holding-type')?.value || 'fd';

  let amountOrShares = 300000;
  let buyPrice = 0;

  if (holdingType === 'equity') {
    amountOrShares = parseFloat(document.getElementById('personal-shares-count')?.value || 500);
    buyPrice = parseFloat(document.getElementById('personal-buy-price')?.value || 150);
  } else {
    amountOrShares = parseFloat(document.getElementById('personal-fd-amount')?.value || 300000);
  }

  try {
    const res = await fetch('/api/personal-risk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bank_id: bankId,
        holding_type: holdingType,
        amount_or_shares: amountOrShares,
        buy_price_inr: buyPrice
      })
    });
    const data = await res.json();

    if (holdingType === 'equity') {
      document.getElementById('personal-output1-badge').innerText = data.equity_risk_category;
      document.getElementById('personal-output1-badge').className = `text-xs px-2.5 py-1 rounded font-bold inline-block text-white`;
      document.getElementById('personal-output1-badge').style.backgroundColor = data.equity_color;

      document.getElementById('personal-output1-text').innerText = `Portfolio value: ₹${data.invested_value_inr.toLocaleString('en-IN')}. ${data.action_note}`;
      document.getElementById('personal-output2-text').innerText = `Key Risk Driver: ${data.key_risk_driver}`;
      document.getElementById('personal-output3-text').innerText = `Equity shares absorb first loss in bank resolution (unlike insured deposits). Monitor score trends closely.`;
    } else {
      document.getElementById('personal-output1-badge').innerText = data.insurance_badge;
      document.getElementById('personal-output1-badge').className = `text-xs px-2.5 py-1 rounded font-bold inline-block text-white`;
      document.getElementById('personal-output1-badge').style.backgroundColor = data.insurance_color;

      document.getElementById('personal-output1-text').innerText = data.output_1_insurance;
      document.getElementById('personal-output2-text').innerText = data.output_2_watch_number;
      document.getElementById('personal-output3-text').innerText = data.output_3_score_drop_impact;
    }
  } catch (err) {
    console.error('Error calculating personal risk:', err);
  }

  if (window.lucide) lucide.createIcons();
}

// 8. HISTORICAL CRISIS VALIDATION
async function loadCrisisDetail(entityId) {
  // Update pills
  ['YES_BANK', 'PMC_BANK', 'ILFS', 'DHFL'].forEach(id => {
    const btn = document.getElementById(`crisis-btn-${id}`);
    if (id === entityId) {
      btn?.classList.remove('bg-slate-800', 'text-slate-400');
      btn?.classList.add('bg-rose-600', 'text-white', 'font-bold');
    } else {
      btn?.classList.remove('bg-rose-600', 'text-white', 'font-bold');
      btn?.classList.add('bg-slate-800', 'text-slate-400');
    }
  });

  try {
    const res = await fetch(`/api/historical-crises/${entityId}`);
    const data = await res.json();

    const banner = document.getElementById('crisis-summary-banner');
    if (banner) {
      banner.innerHTML = `
        <div class="flex items-start space-x-3">
          <div class="p-2 rounded-lg bg-rose-500/20 text-rose-400 flex-shrink-0">
            <i data-lucide="shield-alert" class="w-5 h-5"></i>
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <h3 class="text-sm font-bold text-white">${data.entity_name}</h3>
              <span class="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">
                ${data.lead_time_months} Months Early Warning Proof
              </span>
            </div>
            <p class="text-xs text-slate-300 mt-1 leading-relaxed">${data.summary}</p>
            <div class="text-[11px] text-emerald-400 font-semibold mt-2">${data.validation_conclusion}</div>
          </div>
        </div>
      `;
    }

    const tbody = document.getElementById('crisis-timeline-tbody');
    if (tbody && data.timeline) {
      tbody.innerHTML = data.timeline.map(step => `
        <tr class="hover:bg-slate-900/60 ${step.zone === 'Critical' ? 'bg-rose-950/20' : ''}">
          <td class="py-3 px-4 font-mono font-bold text-white">${step.period}</td>
          <td class="py-3 px-4 text-center font-mono font-bold text-white">${step.finguard_score.toFixed(1)}</td>
          <td class="py-3 px-4 text-center">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold zone-${step.zone.toLowerCase()}">${step.zone}</span>
          </td>
          <td class="py-3 px-4 text-right font-mono text-slate-300">${step.net_npa_pct.toFixed(2)}%</td>
          <td class="py-3 px-4 text-right font-mono text-slate-300">${step.gross_npa_pct.toFixed(2)}%</td>
          <td class="py-3 px-4 text-right font-mono text-slate-300">${step.crar_pct.toFixed(1)}%</td>
          <td class="py-3 px-4 text-right font-mono text-slate-300">${step.roa_pct.toFixed(2)}%</td>
          <td class="py-3 px-4 text-xs font-sans ${step.zone in ['At-Risk', 'Critical'] ? 'text-rose-300 font-medium' : 'text-slate-400'}">
            ${step.alert}
          </td>
        </tr>
      `).join('');
    }

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Error loading crisis detail:', err);
  }
}

