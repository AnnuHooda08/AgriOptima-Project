import React from 'react';
import { FileCheck2, IndianRupee, Layers, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';

export default function FinalPlanSection({ selectedPlan, alternativePlans = [] }) {
  if (!selectedPlan) {
    return (
      <div className="card">
        <h2 className="card-title">
          <FileCheck2 size={22} color="#059669" />
          Section 5: Final Connected Farm Plan
        </h2>
        <p style={{ color: 'var(--text-muted)' }}>Generate a plan from Section 1 to view the complete financial statement.</p>
      </div>
    );
  }

  const p = selectedPlan;
  const isProfitable = p.net_return_rs > 0;

  return (
    <div className="card">
      <h2 className="card-title">
        <FileCheck2 size={22} color="#059669" />
        Section 5: Final Connected Farm Plan & Financial Statement
      </h2>

      {/* Top Level Summary Cards */}
      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        <div className="metric-box">
          <div className="metric-label">Gross Revenue</div>
          <div className="metric-value" style={{ color: '#0369a1' }}>
            ₹{p.gross_revenue_rs.toLocaleString()}
          </div>
          <div className="metric-sub">{p.marketable_production_quintals} qtl × ₹{p.applicable_price_per_quintal}/qtl</div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Total Included Costs</div>
          <div className="metric-value" style={{ color: '#b91c1c' }}>
            ₹{p.total_costs_rs.toLocaleString()}
          </div>
          <div className="metric-sub">Cultivation + Logistics + Storage</div>
        </div>

        <div className="metric-box" style={{ background: isProfitable ? '#f0fdf4' : '#fef2f2', borderColor: isProfitable ? '#86efac' : '#fca5a5' }}>
          <div className="metric-label" style={{ color: isProfitable ? '#166534' : '#991b1b' }}>
            Estimated Net Return
          </div>
          <div className="metric-value" style={{ color: isProfitable ? '#15803d' : '#dc2626' }}>
            ₹{p.net_return_rs.toLocaleString()}
          </div>
          <div className="metric-sub" style={{ fontWeight: 700, color: isProfitable ? '#15803d' : '#dc2626' }}>
            ROI: {p.roi_percentage}% (₹{p.net_return_per_ha_rs.toLocaleString()}/ha)
          </div>
        </div>
      </div>

      {/* Itemized P&L Statement Table */}
      <div className="card" style={{ background: '#f8fafc', marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Layers size={18} color="#059669" />
          Itemized Financial Breakdown & Profit-and-Loss Statement
        </h3>

        <div className="table-responsive">
          <table className="styled-table">
            <thead>
              <tr>
                <th>Financial Item</th>
                <th>Quantity / Metric</th>
                <th>Unit Rate</th>
                <th>Amount (Rs.)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Gross Marketable Revenue</strong></td>
                <td>{p.marketable_production_quintals} Quintals sold</td>
                <td>₹{p.applicable_price_per_quintal} / quintal</td>
                <td style={{ color: '#0369a1', fontWeight: 700 }}>+₹{p.gross_revenue_rs.toLocaleString()}</td>
              </tr>
              <tr>
                <td>Cultivation Operational Cost (Seeds, Fertilizer, Labor)</td>
                <td>{p.cultivated_area_ha} Hectares</td>
                <td>₹{(p.cultivation_cost_rs / p.cultivated_area_ha).toLocaleString()} / ha</td>
                <td style={{ color: '#b91c1c' }}>-₹{p.cultivation_cost_rs.toLocaleString()}</td>
              </tr>
              <tr>
                <td>Transportation & Cartage</td>
                <td>{p.marketable_production_quintals} Quintals</td>
                <td>₹35 / quintal</td>
                <td style={{ color: '#b91c1c' }}>-₹{p.transport_cost_rs.toLocaleString()}</td>
              </tr>
              {p.storage_cost_rs > 0 && (
                <tr>
                  <td>Storage / Warehousing</td>
                  <td>{p.marketable_production_quintals} Quintals</td>
                  <td>₹45 / quintal / month</td>
                  <td style={{ color: '#b91c1c' }}>-₹{p.storage_cost_rs.toLocaleString()}</td>
                </tr>
              )}
              <tr>
                <td>Packaging & Handling</td>
                <td>{p.marketable_production_quintals} Quintals</td>
                <td>₹20 / quintal</td>
                <td style={{ color: '#b91c1c' }}>-₹{p.packaging_cost_rs.toLocaleString()}</td>
              </tr>
              <tr style={{ background: '#f1f5f9', fontWeight: 700 }}>
                <td>Total Expenditures</td>
                <td>-</td>
                <td>-</td>
                <td style={{ color: '#b91c1c' }}>-₹{p.total_costs_rs.toLocaleString()}</td>
              </tr>
              <tr style={{ background: isProfitable ? '#dcfce7' : '#fee2e2', fontWeight: 800, fontSize: '0.95rem' }}>
                <td>Net Profit / Return</td>
                <td>{p.cultivated_area_ha} ha field</td>
                <td>₹{p.net_return_per_ha_rs.toLocaleString()} / ha</td>
                <td style={{ color: isProfitable ? '#15803d' : '#b91c1c' }}>₹{p.net_return_rs.toLocaleString()}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Feasibility and Advisory Notes */}
      {p.feasibility_notes && p.feasibility_notes.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            Agronomic & Operational Feasibility Notes:
          </h4>
          <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {p.feasibility_notes.map((note, idx) => (
              <li key={idx} style={{ marginBottom: '0.25rem' }}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Alternative Plans Comparison */}
      {alternativePlans.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
            Comparison with Alternative Candidate Crops
          </h3>
          <div className="table-responsive">
            <table className="styled-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Crop</th>
                  <th>Yield (t/ha)</th>
                  <th>Production (qtl)</th>
                  <th>Price (₹/qtl)</th>
                  <th>Total Costs</th>
                  <th>Net Return</th>
                  <th>ROI (%)</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ background: '#f0fdf4', fontWeight: 700 }}>
                  <td>#1 (Selected)</td>
                  <td>{p.crop}</td>
                  <td>{p.predicted_yield_tonnes_per_ha}</td>
                  <td>{p.marketable_production_quintals}</td>
                  <td>₹{p.applicable_price_per_quintal}</td>
                  <td>₹{p.total_costs_rs.toLocaleString()}</td>
                  <td style={{ color: '#15803d' }}>₹{p.net_return_rs.toLocaleString()}</td>
                  <td>{p.roi_percentage}%</td>
                </tr>
                {alternativePlans.map((alt, idx) => (
                  <tr key={alt.crop}>
                    <td>#{idx + 2}</td>
                    <td>{alt.crop}</td>
                    <td>{alt.predicted_yield_tonnes_per_ha}</td>
                    <td>{alt.marketable_production_quintals}</td>
                    <td>₹{alt.applicable_price_per_quintal}</td>
                    <td>₹{alt.total_costs_rs.toLocaleString()}</td>
                    <td style={{ color: alt.net_return_rs > 0 ? '#15803d' : '#b91c1c' }}>
                      ₹{alt.net_return_rs.toLocaleString()}
                    </td>
                    <td>{alt.roi_percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
