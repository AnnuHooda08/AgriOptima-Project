// API client for AgriOptima Backend

const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchWeather(lat, lon, district) {
  const params = new URLSearchParams({ latitude: lat, longitude: lon });
  if (district) params.append('district', district);
  const res = await fetch(`${API_BASE}/weather?${params.toString()}`);
  if (!res.ok) throw new Error(`Weather fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchCropRecommendation(features) {
  const res = await fetch(`${API_BASE}/crop-recommendation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(features),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Crop recommendation failed');
  }
  return res.json();
}

export async function fetchYieldPrediction(payload) {
  const res = await fetch(`${API_BASE}/yield-prediction`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Yield prediction failed');
  }
  return res.json();
}

export async function fetchMandiAnalysis(crop, state = 'All', userPriceOverride = null) {
  const payload = { crop, state };
  if (userPriceOverride) payload.user_price_override = parseFloat(userPriceOverride);
  const res = await fetch(`${API_BASE}/mandi-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Mandi analysis failed');
  }
  return res.json();
}

export async function generatePlan(profile) {
  const res = await fetch(`${API_BASE}/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Plan generation failed');
  }
  return res.json();
}

export async function simulateWhatIf(basePlan, priceChangePct, yieldShockPct, storageMonths, areaOverride = null) {
  const payload = {
    base_plan: basePlan,
    price_change_pct: parseFloat(priceChangePct) || 0,
    yield_shock_pct: parseFloat(yieldShockPct) || 0,
    storage_months: parseInt(storageMonths, 10) || 0,
  };
  if (areaOverride) payload.area_override = parseFloat(areaOverride);

  const res = await fetch(`${API_BASE}/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'What-If simulation failed');
  }
  return res.json();
}
