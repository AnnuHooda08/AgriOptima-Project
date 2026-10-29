import React, { useState } from 'react';
import { CloudSun, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import { fetchWeather } from '../api';

export default function FarmProfileSection({ 
  profile, 
  setProfile, 
  onGeneratePlan, 
  loading, 
  supportedDistricts = [] 
}) {
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherMsg, setWeatherMsg] = useState(null);

  const handleInputChange = (field, value) => {
    setProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleFetchWeather = async () => {
    setWeatherLoading(true);
    setWeatherMsg(null);
    try {
      // Ambala reference lat/lon or lookup
      const lat = profile.district.toUpperCase() === 'KARNAL' ? 29.6857 : 30.3782;
      const lon = profile.district.toUpperCase() === 'KARNAL' ? 76.9905 : 76.7767;
      
      const res = await fetchWeather(lat, lon, profile.district);
      setProfile((prev) => ({
        ...prev,
        temperature: res.temperature,
        humidity: res.humidity,
        rainfall: res.rainfall,
      }));
      setWeatherMsg(`Retrieved from ${res.source}: ${res.temperature}°C, ${res.humidity}% humidity, ${res.rainfall}mm rainfall.`);
    } catch (err) {
      setWeatherMsg('Using regional agro-climatic baseline for selected district.');
    } finally {
      setWeatherLoading(false);
    }
  };

  const districts = supportedDistricts.length > 0 
    ? supportedDistricts 
    : ['AMBALA', 'AMRITSAR', 'BARNALA', 'BATHINDA', 'BHIWANI', 'FARIDABAD', 'FATEHGARH SAHIB', 'FAZILKA', 'FIROZEPUR', 'GURGAON', 'HISAR', 'JALANDHAR', 'JIND', 'KAITHAL', 'KARNAL', 'KURUKSHETRA', 'LUDHIANA', 'MANSA', 'MOGA', 'MUKTSAR', 'PALWAL', 'PANCHKULA', 'PANIPAT', 'PATIALA', 'REWARI', 'ROHTAK', 'RUPNAGAR', 'SANGRUR', 'SIRSA', 'SONIPAT', 'TARN TARAN', 'YAMUNANAGAR'];

  return (
    <div className="card">
      <h2 className="card-title">
        <CloudSun size={22} color="#059669" />
        Section 1: Farm & Field Profile
      </h2>
      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
        Enter your geographic location, cultivated land size, soil nutrient levels, and seasonal climate conditions.
      </p>

      {weatherMsg && (
        <div className="alert alert-info">
          <AlertCircle size={18} />
          <span>{weatherMsg}</span>
        </div>
      )}

      <div className="grid-3">
        {/* Geography & Season */}
        <div className="form-group">
          <label className="form-label">State</label>
          <select 
            className="form-control"
            value={profile.state}
            onChange={(e) => handleInputChange('state', e.target.value)}
          >
            <option value="Haryana">Haryana</option>
            <option value="Punjab">Punjab</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">District</label>
          <select 
            className="form-control"
            value={profile.district.toUpperCase()}
            onChange={(e) => handleInputChange('district', e.target.value)}
          >
            {districts.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Cultivated Area (Hectares)</label>
          <input 
            type="number"
            step="0.5"
            min="0.1"
            max="1000"
            className="form-control"
            value={profile.area_ha}
            onChange={(e) => handleInputChange('area_ha', parseFloat(e.target.value) || 1.0)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Agricultural Season</label>
          <select 
            className="form-control"
            value={profile.season}
            onChange={(e) => handleInputChange('season', e.target.value)}
          >
            <option value="Kharif">Kharif (Monsoon / Autumn)</option>
            <option value="Rabi">Rabi (Winter / Spring)</option>
            <option value="Whole Year">Whole Year</option>
          </select>
        </div>

        {/* Soil Nutrients */}
        <div className="form-group">
          <label className="form-label">Nitrogen (N) kg/ha</label>
          <input 
            type="number"
            step="1"
            min="0"
            max="300"
            className="form-control"
            value={profile.N}
            onChange={(e) => handleInputChange('N', parseFloat(e.target.value) || 0)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Phosphorus (P) kg/ha</label>
          <input 
            type="number"
            step="1"
            min="0"
            max="300"
            className="form-control"
            value={profile.P}
            onChange={(e) => handleInputChange('P', parseFloat(e.target.value) || 0)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Potassium (K) kg/ha</label>
          <input 
            type="number"
            step="1"
            min="0"
            max="300"
            className="form-control"
            value={profile.K}
            onChange={(e) => handleInputChange('K', parseFloat(e.target.value) || 0)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Soil pH (0 - 14)</label>
          <input 
            type="number"
            step="0.1"
            min="3.0"
            max="10.0"
            className="form-control"
            value={profile.ph}
            onChange={(e) => handleInputChange('ph', parseFloat(e.target.value) || 6.5)}
          />
        </div>

        {/* Climate & Weather */}
        <div className="form-group">
          <label className="form-label">Temperature (°C)</label>
          <input 
            type="number"
            step="0.5"
            className="form-control"
            value={profile.temperature}
            onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value) || 25)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Relative Humidity (%)</label>
          <input 
            type="number"
            step="1"
            min="0"
            max="100"
            className="form-control"
            value={profile.humidity}
            onChange={(e) => handleInputChange('humidity', parseFloat(e.target.value) || 60)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Rainfall (mm)</label>
          <input 
            type="number"
            step="10"
            min="0"
            className="form-control"
            value={profile.rainfall}
            onChange={(e) => handleInputChange('rainfall', parseFloat(e.target.value) || 200)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Storage Holding (Months)</label>
          <select
            className="form-control"
            value={profile.storage_months}
            onChange={(e) => handleInputChange('storage_months', parseInt(e.target.value, 10) || 0)}
          >
            <option value="0">0 Months (Sell Immediately at Harvest)</option>
            <option value="1">1 Month (Warehousing)</option>
            <option value="2">2 Months (Cold Storage)</option>
            <option value="3">3 Months (Off-Season Sale)</option>
            <option value="6">6 Months (Extended Hold)</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', flexWrap: 'wrap' }}>
        <button 
          className="btn btn-secondary" 
          onClick={handleFetchWeather}
          disabled={weatherLoading}
        >
          <RefreshCw size={16} className={weatherLoading ? 'spin' : ''} />
          {weatherLoading ? 'Fetching NASA Weather...' : 'Fetch NASA POWER Weather'}
        </button>

        <button 
          className="btn btn-primary"
          onClick={onGeneratePlan}
          disabled={loading}
          style={{ flex: 1 }}
        >
          <Sparkles size={18} />
          {loading ? 'Evaluating Models & Generating Plan...' : 'Generate Complete Connected Plan'}
        </button>
      </div>
    </div>
  );
}
