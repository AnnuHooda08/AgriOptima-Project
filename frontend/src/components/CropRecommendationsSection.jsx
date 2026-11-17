import React from "react";
import { Leaf, AlertCircle, Award, CheckCircle } from "lucide-react";

export default function CropRecommendationsSection({
  cropResult,
  selectedPlan,
  season,
  state,
}) {
  if (!cropResult && !selectedPlan) {
    return (
      <div className="card">
        <h2 className="card-title">
          <Leaf size={22} color="#059669" />
          Crop Suitability Recommendations
        </h2>
        <div className="alert alert-info">
          <AlertCircle size={18} />
          <span>
            Add your measurements in My field and choose{" "}
            <strong>Generate farm plan</strong>.
          </span>
        </div>
      </div>
    );
  }

  const primaryCrop = selectedPlan?.crop || cropResult?.recommended_crop;
  const candidates = (cropResult?.candidate_ranking || []).filter(
    (candidate) =>
      !cropResult?.seasonal_candidates ||
      cropResult.seasonal_candidates.includes(candidate.crop),
  );

  return (
    <div className="card">
      <h2 className="card-title">
        <Leaf size={22} color="#059669" />
        Crop suggestions for your field
      </h2>

      <div className="alert alert-info">
        <Leaf size={18} />
        <div>
          <strong>
            Crops to consider for your field.
          </strong>
          <p>
            These suggestions use the soil and weather details you entered. The crop
            shown first also has growing-season records for {state} ({season}).
            Before sowing, check water availability, seed variety and local advice.
            Update your field details if your growing conditions change.
          </p>
        </div>
      </div>
      <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
        <div
          className="metric-box"
          style={{ background: "#ecfdf5", borderColor: "#a7f3d0" }}
        >
          <div className="metric-label" style={{ color: "#065f46" }}>
            Season-checked planning crop
          </div>
          <div
            className="metric-value"
            style={{
              color: "#047857",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Award size={28} />
            {primaryCrop}
          </div>
          <div className="metric-sub" style={{ color: "#065f46" }}>
            Highest-ranked candidate with recorded state/season yield data
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">
            Unfiltered soil/climate model label
          </div>
          <div className="metric-value">
            {cropResult?.recommended_crop ?? "Not available"}
          </div>
          <div className="metric-sub">
            This raw label ignores season. It is not the season-checked
            recommendation.
          </div>
        </div>
      </div>

      {candidates.length > 0 && (
        <div>
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 700,
              marginBottom: "0.75rem",
            }}
          >
            Season-screened candidates (soil/climate ranking)
          </h3>
          <div className="table-responsive">
            <table className="styled-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Crop</th>
                  <th>Decision Margin Score</th>
                  <th>Classification Status</th>
                </tr>
              </thead>
              <tbody>
                {candidates.slice(0, 8).map((cand, idx) => (
                  <tr
                    key={cand.crop}
                    style={
                      idx === 0
                        ? { background: "#f0fdf4", fontWeight: 600 }
                        : {}
                    }
                  >
                    <td>#{idx + 1}</td>
                    <td style={{ textTransform: "capitalize" }}>{cand.crop}</td>
                    <td>
                      <code>{cand.decision_score}</code>
                    </td>
                    <td>
                      {idx === 0 ? (
                        <span className="badge badge-success">
                          <CheckCircle size={12} />
                          Seasonal planning choice
                        </span>
                      ) : (
                        <span className="badge">Alternative label</span>
                      )}
                    </td>
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
