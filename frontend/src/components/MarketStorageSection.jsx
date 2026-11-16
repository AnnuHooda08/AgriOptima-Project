import React, { useEffect, useState } from "react";
import {
  Store,
  ShieldAlert,
  PackageCheck,
  AlertCircle,
  Edit3,
  FlaskConical,
} from "lucide-react";

export default function MarketStorageSection({
  selectedPlan,
  profile,
  customPrice,
  setCustomPrice,
  onRecalculatePlan,
  loading,
}) {
  const [loss, setLoss] = useState(null);
  const [market, setMarket] = useState(null);
  useEffect(() => {
    let active = true;
    setMarket(null);
    if (selectedPlan) fetch("/api/mandi-analysis", {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({crop: selectedPlan.crop, state: profile?.state, district: profile?.district})})
      .then(r => r.ok ? r.json() : null).then(data => {if(active) setMarket(data);}).catch(() => {});
    return () => {active = false;};
  }, [selectedPlan?.crop, profile?.state, profile?.district]);
  useEffect(() => {
    let active = true;
    setLoss(null);
    if (selectedPlan) fetch("/api/loss-analysis", {method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({crop: selectedPlan.crop,state: profile?.state})})
      .then(r => r.ok ? r.json() : null).then(data => {if(active) setLoss(data);}).catch(() => {});
    return () => {active = false;};
  }, [selectedPlan?.crop,profile?.state]);
  if (!selectedPlan) {
    return (
      <div className="card">
        <h2 className="card-title">
          <Store size={22} color="#059669" />
          Market Prices, Post-Harvest Loss & Storage
        </h2>
        <p style={{ color: "var(--text-muted)" }}>
          Generate a plan to view mandi prices and loss breakdowns.
        </p>
      </div>
    );
  }

  const stages = selectedPlan.loss_stage_breakdown || {};
  const lossPct = selectedPlan.total_loss_percentage;
  const marketableQtl = selectedPlan.marketable_production_quintals;
  const grossQtl = selectedPlan.gross_production_quintals;
  const price = selectedPlan.applicable_price_per_quintal;

  return (
    <div className="card">
      <h2 className="card-title">
        <Store size={22} color="#059669" />
        Market Prices, Post-Harvest Losses & Storage
      </h2>

      <div className="alert alert-info">
        <Store size={18} />
        <div>
          <strong>Use a price you can actually get.</strong>
          <p>
            Historical prices are read from the crop dataset for your location, with a wider-area fallback when needed. These are not live quotes. Enter a local offer to recalculate.
          </p>
        </div>
      </div>
      <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
        {/* Mandi Price Details */}
        <div className="card" style={{ background: "#f8fafc", margin: 0 }}>
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 700,
              marginBottom: "0.75rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <PackageCheck size={18} color="#059669" />
            Historical market price
          </h3>

          <div
            className="metric-box"
            style={{ background: "#ffffff", marginBottom: "1rem" }}
          >
            <div className="metric-label">Price used in this plan</div>
            <div className="metric-value" style={{ color: "#047857" }}>
              ₹{price} <span style={{ fontSize: "0.875rem" }}>/ Quintal</span>
            </div>
            <div className="metric-sub">{selectedPlan.price_source}</div>
          </div>

          {market && <p>Dataset median: ₹{market.historical_median}/quintal · {market.market_scope} · {market.sample_size} reports</p>}
          {market?.forecast_price_quintal != null && <div className="alert alert-info"><div><strong>Maize model estimate: ₹{market.forecast_price_quintal}/quintal</strong><p>{market.forecast_note}</p><p>This estimate is shown separately and does not replace your planning price.</p></div></div>}
          <div className="form-group">
            <label
              htmlFor="custom-price"
              className="form-label"
              style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
            >
              <Edit3 size={14} />
              Your offer for this crop (Rs./quintal)
            </label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                id="custom-price"
                type="number"
                step="0.01"
                min="0.01"
                className="form-control"
                placeholder={`Default: ₹${price}`}
                value={customPrice || ""}
                onChange={(e) => setCustomPrice(e.target.value)}
              />
              <button
                className="btn btn-secondary"
                onClick={onRecalculatePlan}
                disabled={loading}
              >
                Update
              </button>
            </div>
            <small style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
              Enter your local APMC mandi spot rate to instantly update all
              financial projections for the selected crop. Alternative crops
              keep their own reference prices.
            </small>
          </div>
        </div>

        {/* Post-Harvest Loss Breakdown */}
        <div className="card" style={{ background: "#f8fafc", margin: 0 }}>
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 700,
              marginBottom: "0.75rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <ShieldAlert size={18} color="#d97706" />
            Crop lost before sale
          </h3>

          <p>Some produce may be lost during handling, transport or storage. We estimate this automatically when calculating how much you can sell.</p>
          <p>This is an estimate. Actual losses on your farm may be different.</p>
          <details>
            <summary>How is this estimated?</summary>
            <p>{selectedPlan.loss_source}</p>
            {loss && <div><p>Study reference: <strong>{loss.published_loss_pct}%</strong></p><p>Model estimate: <strong>{loss.model_available ? `${loss.model_loss_pct}%` : "Not available for this crop or state"}</strong></p><small>{loss.note}</small></div>}
          </details>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.5rem 0",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <span style={{ fontSize: "0.875rem" }}>Expected harvest:</span>
            <strong>{grossQtl} Quintals</strong>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.5rem 0",
              borderBottom: "1px solid var(--border)",
              color: "#b91c1c",
            }}
          >
            <span style={{ fontSize: "0.875rem" }}>
              Estimated crop lost ({lossPct}%):
            </span>
            <strong>-{(grossQtl - marketableQtl).toFixed(2)} Quintals</strong>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.5rem 0",
              borderBottom: "2px solid var(--border)",
              color: "#047857",
              fontWeight: 700,
            }}
          >
            <span>Amount left to sell:</span>
            <span>{marketableQtl} Quintals</span>
          </div>

          <div style={{ marginTop: "0.75rem" }}>
            <h4
              style={{
                fontSize: "0.8rem",
                color: "var(--text-muted)",
                textTransform: "uppercase",
                marginBottom: "0.4rem",
              }}
            >
              {Object.keys(stages).length ? "Published stage reference percentages" : "Overall estimate only"}
            </h4>
            {!Object.keys(stages).length && <p>This estimate covers the total crop lost before sale. A separate estimate for each handling step is not available.</p>}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "0.35rem",
                fontSize: "0.8rem",
              }}
            >
              {Object.entries(stages).map(([stg, val]) => (
                <div
                  key={stg}
                  style={{
                    background: "#ffffff",
                    padding: "0.35rem 0.5rem",
                    borderRadius: "4px",
                    border: "1px solid var(--border)",
                  }}
                >
                  <span>{stg}: </span>
                  <strong style={{ color: "#b91c1c" }}>{val}%</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
