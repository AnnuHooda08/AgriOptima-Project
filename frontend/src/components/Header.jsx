import React from 'react';
import { Sprout, CheckCircle2, FlaskConical, BarChart3, Database } from 'lucide-react';

export default function Header({ health }) {
  const cropModel = health?.models?.crop_suitability?.selected_model || 'Support Vector Machine';
  const yieldModel = health?.models?.crop_yield?.selected_model || 'Random Forest Regressor';

  return (
    <header className="app-header">
      <div>
        <h1 className="brand-title">
          <Sprout size={32} color="#059669" />
          AgriOptima
        </h1>
        <p className="brand-subtitle">
          Connected Agricultural Machine Learning & Decision Support System
        </p>
      </div>

      <div className="header-badges">
        <span className="badge badge-success" title="Crop Suitability: SVM pipeline with StandardScaler">
          <CheckCircle2 size={13} />
          Crop: SVM (79.9% Acc)
        </span>
        <span className="badge badge-success" title="Crop Yield: Random Forest pipeline with lowest MAE">
          <BarChart3 size={13} />
          Yield: Random Forest (2.10 MAE)
        </span>
        <span className="badge badge-warning" title="Mandi Prices: Historical AGMARKNET & MSP with farmer override">
          <Database size={13} />
          Prices: Historical Mandi & MSP
        </span>
        <span className="badge badge-info" title="Mandi Forecasting: HistGradientBoosting benchmarked against baseline">
          <FlaskConical size={13} />
          HGB: Experimental Benchmark
        </span>
      </div>
    </header>
  );
}
