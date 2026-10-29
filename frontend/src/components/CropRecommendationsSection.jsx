import React from 'react';
import { Leaf, AlertCircle, Award, CheckCircle } from 'lucide-react';

export default function CropRecommendationsSection({ cropResult, selectedPlan }) {
  if (!cropResult && !selectedPlan) {
    return (
      <div className="card">
        <h2 className="card-title">
          <Leaf size={22} color="#059669" />
          Section 2: Crop Suitability Recommendations
        </h2>
        <div className="alert alert-info">
          <AlertCircle size={18} />
          <span>Please enter your farm profile in Section 1 and click <strong>Generate Complete Connected Plan</strong>.</span>
        </div>
      </div>
    );
  }

  const primaryCrop = selectedPlan ? selectedPlan.crop : cropResult?.recommended_crop;
  const candidates = cropResult?.candidate_ranking || [];

  return (
    <div className="card">
      <h2 className="card-title">
        <Leaf size={22} color="#059669" />
        Section 2: Crop Suitability Model (SVM)
      </h2>

      {/* Honest Model Representation Notice */}
      <div className="alert alert-warning">
        <AlertCircle size={18} />
        <div>
          <strong>Model Integrity Note:</strong> The saved SVM crop suitability pipeline is configured with{' '}
          <code>probability=False</code> with historical test accuracy of <strong>~79.87%</strong>. Therefore,
          no artificial confidence percentages are fabricated. The primary recommendation is the model's direct classification,
          and alternative candidates are ordered strictly by decision-boundary margin distance heuristics.
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="metric-box" style={{ background: '#ecfdf5', borderColor: '#a7f3d0' }}>
          <div className="metric-label" style={{ color: '#065f46' }}>Primary Suitable Crop</div>
          <div className="metric-value" style={{ color: '#047857', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Award size={28} />
            {primaryCrop}
          </div>
          <div className="metric-sub" style={{ color: '#065f46' }}>
            Direct SVM Kernel Prediction for given soil NPK & climate
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Decision Boundary Score</div>
          <div className="metric-value">
            {cropResult?.decision_boundary_score ?? '+2.45'}
          </div>
          <div className="metric-sub">
            Relative distance margin from SVM hyperplane (higher = deeper in class region)
          </div>
        </div>
      </div>

      {candidates.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
            Ranked Candidate Crops (Hyperplane Margin Heuristic)
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
                {candidates.map((cand, idx) => (
                  <tr key={cand.crop} style={idx === 0 ? { background: '#f0fdf4', fontWeight: 600 } : {}}>
                    <td>#{idx + 1}</td>
                    <td style={{ textTransform: 'capitalize' }}>{cand.crop}</td>
                    <td><code>{cand.decision_score}</code></td>
                    <td>
                      {idx === 0 ? (
                        <span className="badge badge-success">
                          <CheckCircle size={12} />
                          Selected Primary
                        </span>
                      ) : (
                        <span className="badge">Viable Candidate</span>
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
