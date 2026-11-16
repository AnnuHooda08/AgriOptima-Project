import React, { useState } from "react";
import {
  ArrowRight,
  MapPin,
  FlaskConical,
  CloudSun,
  RotateCcw,
} from "lucide-react";
export const DISTRICTS = {
  Haryana: [
    "AMBALA",
    "BHIWANI",
    "CHARKI DADRI",
    "FARIDABAD",
    "FATEHABAD",
    "GURGAON",
    "HISAR",
    "JHAJJAR",
    "JIND",
    "KAITHAL",
    "KARNAL",
    "KURUKSHETRA",
    "MAHENDRAGARH",
    "MEWAT",
    "PALWAL",
    "PANCHKULA",
    "PANIPAT",
    "REWARI",
    "ROHTAK",
    "SIRSA",
    "SONIPAT",
    "YAMUNANAGAR",
  ],
  Punjab: [
    "AMRITSAR",
    "BARNALA",
    "BATHINDA",
    "FARIDKOT",
    "FATEHGARH SAHIB",
    "FAZILKA",
    "FIROZEPUR",
    "GURDASPUR",
    "HOSHIARPUR",
    "JALANDHAR",
    "KAPURTHALA",
    "LUDHIANA",
    "MANSA",
    "MOGA",
    "MUKTSAR",
    "NAWANSHAHR",
    "PATHANKOT",
    "PATIALA",
    "RUPNAGAR",
    "SANGRUR",
    "SHAHID BHAGAT SINGH NAGAR",
    "TARN TARAN",
  ],
};
export default function FarmProfileSection({
  profile,
  setProfile,
  onGeneratePlan,
  loading,
  supportedDistricts = [],
  onReset,
}) {
  const [step, setStep] = useState(0);
  const change = (key, value) =>
    setProfile((previous) => ({ ...previous, [key]: value }));
  const districts = DISTRICTS[profile.state].filter(
    (d) => !supportedDistricts.length || supportedDistricts.includes(d),
  );
  const fields =
    step === 0
      ? [["area_ha", "Cultivated area", "hectares", 0.1, 1000, 0.1]]
      : step === 1
        ? [
            ["N", "Nitrogen (N)", "dataset units", 0, 300, 1],
            ["P", "Phosphorus (P)", "dataset units", 0, 300, 1],
            ["K", "Potassium (K)", "dataset units", 0, 300, 1],
            ["ph", "Soil pH", "pH", 0, 14, 0.1],
          ]
        : [
            ["temperature", "Temperature", "°C", -10, 60, 0.1],
            ["humidity", "Relative humidity", "%", 0, 100, 1],
            ["rainfall", "Rainfall", "mm", 0, 2000, 1],
          ];
  return (
    <section className="card profile-editor">
      <div className="section-heading">
        <div>
          <span className="eyebrow">YOUR STARTING POINT</span>
          <h2>Let’s get to know your field.</h2>
          <p>
            Use measurements from your soil report and the relevant growing
            season.
          </p>
        </div>
        <button className="btn btn-secondary" type="button" onClick={onReset}>
          <RotateCcw size={15} /> Example values
        </button>
      </div>
      <div className="form-steps">
        {[
          [MapPin, "The field"],
          [FlaskConical, "The soil"],
          [CloudSun, "The climate"],
        ].map(([Icon, label], i) => (
          <button
            key={label}
            type="button"
            aria-current={step === i ? "step" : undefined}
            className={step === i ? "current" : ""}
            onClick={() => setStep(i)}
          >
            <span>{i + 1}</span>
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (step < 2) setStep(step + 1);
          else onGeneratePlan();
        }}
      >
        <div className="grid-2">
          {step === 0 && (
            <>
              <label className="form-group">
                <span className="form-label">State</span>
                <select
                  className="form-control"
                  aria-label="State"
                  value={profile.state}
                  onChange={(e) =>
                    setProfile((p) => ({
                      ...p,
                      state: e.target.value,
                      district:
                        DISTRICTS[e.target.value].find(
                          (d) =>
                            !supportedDistricts.length ||
                            supportedDistricts.includes(d),
                        ) || DISTRICTS[e.target.value][0],
                    }))
                  }
                >
                  {Object.keys(DISTRICTS).map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
              <label className="form-group">
                <span className="form-label">District</span>
                <select
                  className="form-control"
                  aria-label="District"
                  value={profile.district}
                  onChange={(e) => change("district", e.target.value)}
                >
                  {districts.map((d) => (
                    <option key={d} value={d}>
                      {d.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-group">
                <span className="form-label">Growing season</span>
                <select
                  className="form-control"
                  aria-label="Growing season"
                  value={profile.season}
                  onChange={(e) => change("season", e.target.value)}
                >
                  <option>Kharif</option>
                  <option>Rabi</option>
                  <option value="Whole Year" disabled>
                    Whole Year — reporting category only
                  </option>
                </select>
              </label>
            </>
          )}
          {fields.map(([key, label, unit, min, max, stepSize]) => (
            <label className="form-group" key={key}>
              <span className="form-label">
                {label}
                <small>{unit}</small>
              </span>
              <input
                required
                className="form-control"
                type="number"
                aria-label={label}
                value={profile[key]}
                min={min}
                max={max}
                step={stepSize}
                onChange={(e) =>
                  change(
                    key,
                    e.target.value === "" ? "" : Number(e.target.value),
                  )
                }
              />
            </label>
          ))}
          {step === 2 && (
            <label className="form-group">
              <span className="form-label">
                Storage before sale<small>months</small>
              </span>
              <select
                className="form-control"
                aria-label="Storage before sale"
                value={profile.storage_months}
                onChange={(e) =>
                  change("storage_months", Number(e.target.value))
                }
              >
                {[0, 1, 2, 3, 6, 12].map((m) => (
                  <option key={m} value={m}>
                    {m === 0
                      ? "Sell at harvest"
                      : `${m} month${m > 1 ? "s" : ""}`}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        {profile.season === "Whole Year" && (
          <div className="alert alert-warning">
            Choose Kharif or Rabi in The field. “Whole Year” is a historical
            reporting label, not a third planting season. Summer planning
            requires separate seasonal data.
          </div>
        )}
        {step === 2 && (
          <details className="optional-costs">
            <summary>Add your farming expenses (optional)</summary>
            <p>Know your costs? Enter them here for a better estimate of your earnings. The amounts below are examples, not local rates.</p>
            <div className="grid-2">
              {[
                ["cultivation_cost_per_ha", "Growing the crop", "₹ per hectare", "Seeds, fertiliser, labour and other growing expenses.", 10000000],
                ["transport_cost_per_quintal", "Taking the crop to market", "₹ per quintal", "What you pay to transport 100 kg of produce.", 100000],
                ["storage_cost_per_quintal_month", "Keeping the crop in storage", "₹ per quintal each month", "What you pay to store 100 kg for one month.", 100000],
                ["packaging_cost_per_quintal", "Bags and packing", "₹ per quintal", "What you pay to pack 100 kg of produce.", 100000],
              ].map(([key, label, unit, help, max]) => (
                <label className="form-group" key={key}>
                  <span className="form-label">{label}<small>{unit}</small></span>
                  <input className="form-control" aria-label={label} type="number" min="0" max={max} step="0.01" required value={profile[key]} onChange={e => change(key, e.target.value === "" ? "" : Number(e.target.value))} />
                  <small>{help}</small>
                </label>
              ))}
            </div>
          </details>
        )}
        <div className="field-note">
          {step === 0
            ? "One hectare is about 2.47 acres."
            : step === 1
              ? "Enter the N, P and K values in the source dataset’s scale. Check the units on your soil report before using them."
              : "Enter the expected weather for the growing season. For rainfall, enter the total for the season, not just today’s rain."}
        </div>
        <div className="form-footer">
          <span>Step {step + 1} of 3 · Saved on this browser</span>
          <div>
            {step > 0 && (
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => setStep(step - 1)}
              >
                Back
              </button>
            )}
            <button
              className="btn btn-primary"
              disabled={loading || profile.season === "Whole Year"}
              type="submit"
            >
              {loading
                ? "Preparing your plan…"
                : step < 2
                  ? "Continue"
                  : "Generate farm plan"}
              <ArrowRight size={17} />
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
