import React from "react";
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
  customPrice,
  setCustomPrice,
  onRecalculatePlan,
  loading,
}) {
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
            These are planning reference prices, not live mandi quotes. Enter a
            local offer below to recalculate. The separate maize research
            forecast is not used here.
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
            Planning price reference
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
            Illustrative post-harvest loss assumptions
          </h3>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.5rem 0",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <span style={{ fontSize: "0.875rem" }}>Gross Production:</span>
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
              Total Physical Loss ({lossPct}%):
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
            <span>Net Marketable Quantity:</span>
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
              Stage-wise Loss Percentages:
            </h4>
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
