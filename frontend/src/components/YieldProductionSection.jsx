import React from 'react';
import { TrendingUp, Calculator, Info, CheckCircle2 } from 'lucide-react';

export default function YieldProductionSection({ selectedPlan, profile }) {
  if (!selectedPlan) {
    return (
      <div className="card">
        <h2 className="card-title">
          <TrendingUp size={22} color="#059669" />
          Section 3: Yield & Production Estimates
        </h2>
        <p style={{ color: 'var(--text-muted)' }}>Generate a plan from Section 1 to view yield forecasts.</p>
      </div>
    );
  }

  const yieldVal = selectedPlan.predicted_yield_tonnes_per_ha;
  const area = selectedPlan.cultivated_area_ha;
  const tonnes = selectedPlan.gross_production_tonnes;
  const quintals = selectedPlan.gross_production_quintals;

  return (
    <div className="card">
      <h2 className="card-title">
        <TrendingUp size={22} color="#059669" />
        Section 3: Crop Yield & Production (Random Forest)
      </h2>

      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        <div className="metric-box">
          <div className="metric-label">Predicted Yield</div>
          <div className="metric-value">{yieldVal} <span style={{ fontSize: '0.875rem' }}>t/ha</span></div>
          <div className="metric-sub">Tonnes per hectare (Random Forest Regressor)</div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Cultivated Land</div>
          <div className="metric-value">{area} <span style={{ fontSize: '0.875rem' }}>ha</span></div>
          <div className="metric-sub">Cultivated field size in hectares</div>
        </div>

        <div className="metric-box" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
          <div className="metric-label" style={{ color: '#166534' }}>Gross Production</div>
          <div className="metric-value" style={{ color: '#15803d' }}>
            {tonnes} <span style={{ fontSize: '0.875rem' }}>Tonnes</span>
          </div>
          <div className="metric-sub" style={{ color: '#166534', fontWeight: 600 }}>
            = {quintals} Quintals (1 tonne = 10 quintals)
          </div>
        </div>
      </div>

      <div className="alert alert-info">
        <Calculator size={18} />
        <div>
          <strong>Exact Production Mathematical Formula:</strong>
          <br />
          <code>Estimated Production (tonnes) = Yield (tonnes/ha) × Area (ha) = {yieldVal} × {area} = {tonnes} tonnes</code>
          <br />
          <code>Production (quintals) = {tonnes} tonnes × 10 = {quintals} quintals</code>
        </div>
      </div>

      <div style={{ marginTop: '1rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
        <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Info size={16} />
          Model Selection Rationale (Random Forest vs Linear Regression):
        </h4>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
          Random Forest was selected because it achieved the <strong>lowest recorded Mean Absolute Error (MAE) of 2.10 tonnes/hectare</strong> in the evaluation reports. While Linear Regression showed higher R² on global variance, Random Forest minimizes the average absolute error magnitude for individual smallholder farm plots.
        </p>
      </div>
    </div>
  );
}
