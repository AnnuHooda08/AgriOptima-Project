import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Navbar from './components/Navbar';
import FarmProfileSection from './components/FarmProfileSection';
import CropRecommendationsSection from './components/CropRecommendationsSection';
import YieldProductionSection from './components/YieldProductionSection';
import MarketStorageSection from './components/MarketStorageSection';
import FinalPlanSection from './components/FinalPlanSection';
import WhatIfSection from './components/WhatIfSection';
import { fetchHealth, generatePlan, fetchCropRecommendation } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Default initial farm profile (Ambala, Haryana - standard Kharif scenario)
  const [profile, setProfile] = useState({
    state: 'Haryana',
    district: 'AMBALA',
    area_ha: 2.0,
    season: 'Kharif',
    N: 90.0,
    P: 42.0,
    K: 43.0,
    temperature: 24.5,
    humidity: 78.0,
    ph: 6.5,
    rainfall: 250.0,
    storage_months: 0,
    user_price_override: null,
  });

  const [cropResult, setCropResult] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [alternativePlans, setAlternativePlans] = useState([]);
  const [customPrice, setCustomPrice] = useState('');

  // Initial load: health check and initial plan generation
  useEffect(() => {
    const initialize = async () => {
      try {
        const healthData = await fetchHealth();
        setHealth(healthData);
      } catch (err) {
        console.error('Health check failed:', err);
      }

      // Automatically generate initial baseline plan
      handleGeneratePlan();
    };

    initialize();
  }, []);

  const handleGeneratePlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const planPayload = {
        ...profile,
        user_price_override: customPrice ? parseFloat(customPrice) : null,
      };

      // 1. Generate full connected plan
      const planRes = await generatePlan(planPayload);
      setSelectedPlan(planRes.selected_plan);
      setAlternativePlans(planRes.alternative_plans);

      // 2. Fetch detailed crop suitability candidate scores
      const cropRes = await fetchCropRecommendation({
        N: profile.N,
        P: profile.P,
        K: profile.K,
        temperature: profile.temperature,
        humidity: profile.humidity,
        ph: profile.ph,
        rainfall: profile.rainfall,
      });
      setCropResult(cropRes);
    } catch (err) {
      console.error('Plan generation failed:', err);
      setError(err.message || 'Failed to generate plan. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculateWithCustomPrice = () => {
    handleGeneratePlan();
  };

  const supportedDistricts = health?.metadata?.supported_districts || [];

  return (
    <div className="app-container">
      <Header health={health} />
      
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {error && (
        <div className="alert alert-warning" style={{ background: '#fee2e2', borderColor: '#ef4444', color: '#b91c1c' }}>
          <strong>Notice:</strong> {error}
        </div>
      )}

      {/* Tab: All-in-One Dashboard */}
      {activeTab === 'dashboard' && (
        <div>
          <FarmProfileSection 
            profile={profile}
            setProfile={setProfile}
            onGeneratePlan={handleGeneratePlan}
            loading={loading}
            supportedDistricts={supportedDistricts}
          />
          <CropRecommendationsSection 
            cropResult={cropResult}
            selectedPlan={selectedPlan}
          />
          <YieldProductionSection 
            selectedPlan={selectedPlan}
            profile={profile}
          />
          <MarketStorageSection 
            selectedPlan={selectedPlan}
            customPrice={customPrice}
            setCustomPrice={setCustomPrice}
            onRecalculatePlan={handleRecalculateWithCustomPrice}
          />
          <FinalPlanSection 
            selectedPlan={selectedPlan}
            alternativePlans={alternativePlans}
          />
          <WhatIfSection 
            selectedPlan={selectedPlan}
          />
        </div>
      )}

      {/* Tab 1: Farm Profile */}
      {activeTab === 'profile' && (
        <FarmProfileSection 
          profile={profile}
          setProfile={setProfile}
          onGeneratePlan={handleGeneratePlan}
          loading={loading}
          supportedDistricts={supportedDistricts}
        />
      )}

      {/* Tab 2: Crop Recommendations */}
      {activeTab === 'crop' && (
        <CropRecommendationsSection 
          cropResult={cropResult}
          selectedPlan={selectedPlan}
        />
      )}

      {/* Tab 3: Yield & Production */}
      {activeTab === 'yield' && (
        <YieldProductionSection 
          selectedPlan={selectedPlan}
          profile={profile}
        />
      )}

      {/* Tab 4: Market & Storage */}
      {activeTab === 'market' && (
        <MarketStorageSection 
          selectedPlan={selectedPlan}
          customPrice={customPrice}
          setCustomPrice={setCustomPrice}
          onRecalculatePlan={handleRecalculateWithCustomPrice}
        />
      )}

      {/* Tab 5: Final Plan */}
      {activeTab === 'plan' && (
        <FinalPlanSection 
          selectedPlan={selectedPlan}
          alternativePlans={alternativePlans}
        />
      )}

      {/* Tab 6: What-If Analysis */}
      {activeTab === 'whatif' && (
        <WhatIfSection 
          selectedPlan={selectedPlan}
        />
      )}
    </div>
  );
}
