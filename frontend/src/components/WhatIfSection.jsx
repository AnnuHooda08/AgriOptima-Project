import React, { useState, useEffect } from 'react';
import { SlidersHorizontal, ArrowUpRight, ArrowDownRight, RefreshCcw, TrendingUp } from 'lucide-react';
import { simulateWhatIf } from '../api';

export default function WhatIfSection({ selectedPlan }) {
  const [priceChange, setPriceChange] = useState(0);
  const [yieldShock, setYieldShock] = useState(0);
  const [storageMonths, setStorageMonths] = useState(0);
  const [area, setArea] = useState(selectedPlan?.cultivated_area_ha ?? 0);
  const [simResult, setSimResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Keep the selected area in sync when the generated plan changes.
  useEffect(() => {
    if (selectedPlan) {
      setArea(selectedPlan.cultivated_area_ha);
    }
  }, [selectedPlan]);

  // Run a simulation only after a base plan exists.
  useEffect(() => {
    if (!selectedPlan) {
      setSimResult(null);
      setLoading(false);
      return undefined;
    }

    let isMounted = true;
    const runSim = async () => {
      setLoading(true);
      try {
        const res = await simulateWhatIf(
          selectedPlan,
          priceChange,
          yieldShock,
          storageMonths,
          area
        );
        if (isMounted) setSimResult(res);
      } catch (err) {
        console.error('What-If simulation failed:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    runSim();
    return () => { isMounted = false; };
  }, [selectedPlan, priceChange, yieldShock, storageMonths, area]);

  if (!selectedPlan) {
    return (
      <div className="card">
        <h2 className="card-title">
          <SlidersHorizontal size={22} color="#059669" />
          Section 6: What-If Sensitivity Analysis
        </h2>
        <p style={{ color: 'var(--text-muted)' }}>Generate a plan from Section 1 to enable interactive scenario simulations.</p>
      </div>
    );
  }

  const applyPreset = (pChange, yShock, sMonths) => {
    setPriceChange(pChange);
    setYieldShock(yShock);
    setStorageMonths(sMonths);
  };

  const resetAll = () => {
    setPriceChange(0);
    setYieldShock(0);
    setStorageMonths(0);
    setArea(selectedPlan.cultivated_area_ha);
  };

  const diff = simResult ? simResult.diff_net_return : 0;
  const isPositive = diff >= 0;

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h2 className="card-title" style={{ margin: 0 }}>
          <SlidersHorizontal size={22} color="#059669" />
          Section 6: What-If Sensitivity & Risk Analysis
        </h2>
        <button className="btn btn-secondary" onClick={resetAll} style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}>
          <RefreshCcw size={14} />
          Reset to Baseline
        </button>
      </div>

      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
        Simulate climate shocks, market price crashes or rallies, storage holding periods, and land expansions to evaluate farm financial resilience.
      </p>

      {/* Preset Scenario Quick-Buttons */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', alignSelf: 'center' }}>
          Quick Presets:
        </span>
        <button className="btn btn-secondary" onClick={() => applyPreset(-20, -25, 0)} style={{ fontSize: '0.78rem' }}>
          Drought & Crash (-25% yield, -20% price)
        </button>
        <button className="btn btn-secondary" onClick={() => applyPreset(0, -20, 0)} style={{ fontSize: '0.78rem' }}>
          Dry Spell (-20% yield)
        </button>
        <button className="btn btn-secondary" onClick={() => applyPreset(15, 0, 3)} style={{ fontSize: '0.78rem' }}>
          Delayed 3mo Off-Season (+15% price)
        </button>
        <button className="btn btn-secondary" onClick={() => applyPreset(25, 10, 0)} style={{ fontSize: '0.78rem' }}>
          Bumper Harvest (+10% yield, +25% price)
        </button>
      </div>

      <div className="grid-2">
        {/* Sliders Panel */}
        <div className="card" style={{ background: '#f8fafc', margin: 0 }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1.25rem' }}>
            Interactive Scenario Controls
          </h3>

          {/* Price Change Slider */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <label className="form-label" style={{ margin: 0 }}>Market Price Shift</label>
              <strong style={{ color: priceChange > 0 ? '#059669' : priceChange < 0 ? '#dc2626' : 'inherit' }}>
                {priceChange > 0 ? `+${priceChange}` : priceChange}%
              </strong>
            </div>
            <input 
              type="range"
              min="-50"
              max="100"
              step="5"
              className="range-slider"
              value={priceChange}
              onChange={(e) => setPriceChange(parseFloat(e.target.value))}
            />
            <div className="slider-labels">
              <span>-50% (Crash)</span>
              <span>0% (Base: ₹{selectedPlan.applicable_price_per_quintal})</span>
              <span>+100% (Surge)</span>
            </div>
          </div>

          {/* Yield Shock Slider */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <label className="form-label" style={{ margin: 0 }}>Yield Shock (Weather/Pests)</label>
              <strong style={{ color: yieldShock > 0 ? '#059669' : yieldShock < 0 ? '#dc2626' : 'inherit' }}>
                {yieldShock > 0 ? `+${yieldShock}` : yieldShock}%
              </strong>
            </div>
            <input 
              type="range"
              min="-50"
              max="50"
              step="5"
              className="range-slider"
              value={yieldShock}
              onChange={(e) => setYieldShock(parseFloat(e.target.value))}
            />
            <div className="slider-labels">
              <span>-50% (Severe Drought)</span>
              <span>0% (Base: {selectedPlan.predicted_yield_tonnes_per_ha} t/ha)</span>
              <span>+50% (Favorable)</span>
            </div>
          </div>

          {/* Storage Duration Slider */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <label className="form-label" style={{ margin: 0 }}>Storage Holding Duration</label>
              <strong>{storageMonths} Months</strong>
            </div>
            <input 
              type="range"
              min="0"
              max="12"
              step="1"
              className="range-slider"
              value={storageMonths}
              onChange={(e) => setStorageMonths(parseInt(e.target.value, 10))}
            />
            <div className="slider-labels">
              <span>0 (Immediate)</span>
              <span>6 Months</span>
              <span>12 Months</span>
            </div>
          </div>

          {/* Cultivated Area Slider */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <label className="form-label" style={{ margin: 0 }}>Cultivated Area</label>
              <strong>{area} Hectares</strong>
            </div>
            <input 
              type="range"
              min="0.5"
              max="20"
              step="0.5"
              className="range-slider"
              value={area}
              onChange={(e) => setArea(parseFloat(e.target.value))}
            />
            <div className="slider-labels">
              <span>0.5 ha</span>
              <span>10 ha</span>
              <span>20 ha</span>
            </div>
          </div>
        </div>

        {/* Live Simulation Output Panel */}
        <div className="card" style={{ background: '#f8fafc', margin: 0 }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>
            Simulated Impact vs Base Plan
          </h3>

          {simResult && (
            <div>
              <div className="metric-box" style={{ background: isPositive ? '#f0fdf4' : '#fef2f2', borderColor: isPositive ? '#86efac' : '#fca5a5', marginBottom: '1rem' }}>
                <div className="metric-label" style={{ color: isPositive ? '#166534' : '#991b1b' }}>
                  Simulated Net Return
                </div>
                <div className="metric-value" style={{ color: isPositive ? '#15803d' : '#dc2626' }}>
                  ₹{simResult.simulated_net_return.toLocaleString()}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.25rem', fontSize: '0.85rem' }}>
                  {isPositive ? <ArrowUpRight size={16} color="#059669" /> : <ArrowDownRight size={16} color="#dc2626" />}
                  <span className={isPositive ? 'diff-positive' : 'diff-negative'}>
                    {isPositive ? '+' : ''}₹{diff.toLocaleString()} vs Baseline
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border)' }}>
                  <span>Simulated Yield:</span>
                  <strong>{simResult.simulated_yield_t_ha} t/ha (from {simResult.original_yield_t_ha})</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border)' }}>
                  <span>Marketable Quantity:</span>
                  <strong>{simResult.simulated_marketable_quintals} Quintals</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border)' }}>
                  <span>Simulated Price:</span>
                  <strong>₹{simResult.simulated_price_quintal} / quintal</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border)' }}>
                  <span>Simulated Gross Revenue:</span>
                  <strong style={{ color: '#0369a1' }}>₹{simResult.simulated_gross_revenue.toLocaleString()}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border)' }}>
                  <span>Simulated Total Costs:</span>
                  <strong style={{ color: '#b91c1c' }}>₹{simResult.simulated_total_costs.toLocaleString()}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', fontWeight: 700 }}>
                  <span>Simulated ROI:</span>
                  <strong style={{ color: simResult.roi_percentage > 0 ? '#15803d' : '#dc2626' }}>
                    {simResult.roi_percentage}%
                  </strong>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
