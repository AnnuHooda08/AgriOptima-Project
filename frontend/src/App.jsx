import React, { useState, useEffect, useRef } from "react";
import {
  Sprout,
  LayoutDashboard,
  MapPin,
  Wheat,
  TrendingUp,
  Store,
  FileText,
  SlidersHorizontal,
  ArrowUpRight,
  ArrowRight,
  ChevronRight,
  Download,
  Bookmark,
  Menu,
  X,
  Sun,
  Droplets,
  Wind,
  Check,
  CircleHelp,
  Layers,
  Trash2,
  Printer,
  RefreshCw,
} from "lucide-react";
import FarmProfileSection, { DISTRICTS } from "./components/FarmProfileSection";
import CropRecommendationsSection from "./components/CropRecommendationsSection";
import YieldProductionSection from "./components/YieldProductionSection";
import PredictionSection from "./components/PredictionSection";

import { fetchHealth, generatePlan, fetchCropRecommendation } from "./api";
const DEFAULT = {
  cultivation_cost_per_ha: 45000,
  transport_cost_per_quintal: 35,
  storage_cost_per_quintal_month: 45,
  packaging_cost_per_quintal: 20,
  loss_override_pct: null,
  loss_estimation_method: "model",
  state: "Haryana",
  district: "AMBALA",
  area_ha: 2,
  season: "Kharif",
  N: 90,
  P: 42,
  K: 43,
  temperature: 24.5,
  humidity: 78,
  ph: 6.5,
  rainfall: 250,
  storage_months: 0,
  user_price_override: null,
};
const tabs = [
  ["dashboard", "Overview", LayoutDashboard],
  ["profile", "My field", MapPin],
  ["crop", "Crop suitability", Wheat],
  ["yield", "Yield & production", TrendingUp],
  ["market", "Market prices", Store],
  ["loss", "Post-harvest loss", FileText],

];
const number = (value) =>
  value != null && Number.isFinite(Number(value))
    ? new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 }).format(value)
    : "—";
const money = (value) => (value == null ? "—" : `₹${number(value)}`);
const title = (value) =>
  value?.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()) || "Your field";
function read(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}
function store(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}
function getProfile() {
  const p = read("agrioptima-field", null);
  return p && DISTRICTS[p.state]?.includes(p.district)
    ? { ...DEFAULT, ...p }
    : DEFAULT;
}
export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard"),
    [mobile, setMobile] = useState(false),
    [health, setHealth] = useState(null),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [profile, setProfile] = useState(getProfile),
    [generatedProfile, setGeneratedProfile] = useState(null),
    [generatedPrice, setGeneratedPrice] = useState(null),
    [cropResult, setCropResult] = useState(null),
    [selectedPlan, setSelectedPlan] = useState(null),
    [alternativePlans, setAlternativePlans] = useState([]),
    [customPrice, setCustomPrice] = useState(""),
    [saved, setSaved] = useState(() => {
      const rows = read("agrioptima-plans", []);
      return Array.isArray(rows)
        ? rows.filter((x) => x?.id && x?.plan && x?.profile).slice(0, 10)
        : [];
    }),
    [savedView, setSavedView] = useState(false);
  const requestId = useRef(0),
    initial = useRef(false),
    sidebarRef = useRef(null);
  useEffect(() => {
    if (!mobile) return;
    const previous = document.activeElement;
    const panel = sidebarRef.current;
    const items = () =>
      [...panel.querySelectorAll("a,button")].filter(
        (x) => x.offsetParent !== null,
      );
    items()[0]?.focus();
    const key = (e) => {
      if (e.key === "Escape") setMobile(false);
      if (e.key === "Tab") {
        const list = items();
        if (e.shiftKey && document.activeElement === list[0]) {
          e.preventDefault();
          list.at(-1)?.focus();
        } else if (!e.shiftKey && document.activeElement === list.at(-1)) {
          e.preventDefault();
          list[0]?.focus();
        }
      }
    };
    document.addEventListener("keydown", key);
    const old = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", key);
      document.body.style.overflow = old;
      previous?.focus();
    };
  }, [mobile]);
  const navigate = (tab) => {
    setActiveTab(tab);
    setSavedView(false);
    setMobile(false);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const dirty =
    generatedProfile &&
    (JSON.stringify(profile) !== JSON.stringify(generatedProfile) ||
      (customPrice === "" ? null : Number(customPrice)) !== generatedPrice);
  useEffect(() => {
    store("agrioptima-field", profile);
  }, [profile]);
  useEffect(() => {
    if (initial.current) return;
    initial.current = true;
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "offline" }));
    handleGeneratePlan(DEFAULT === profile);
  }, []);
  const handleGeneratePlan = async (example = false, resetPrice = false) => {
    const priceInput = resetPrice ? "" : customPrice;
    if (resetPrice) setCustomPrice("");
    for (const [key, min, max] of [
      ["area_ha", 0.1, 1000],
      ["N", 0, 300],
      ["P", 0, 300],
      ["K", 0, 300],
      ["ph", 0, 14],
      ["temperature", -10, 60],
      ["humidity", 0, 100],
      ["rainfall", 0, 2000],
    ]) {
      if (
        profile[key] === "" ||
        !Number.isFinite(Number(profile[key])) ||
        profile[key] < min ||
        profile[key] > max
      ) {
        setError(`Enter a valid ${key} value between ${min} and ${max}.`);
        return;
      }
    }
    if (
      priceInput !== "" &&
      (!Number.isFinite(Number(priceInput)) || Number(priceInput) < 0.01)
    ) {
      setError(
        "Enter a market price of at least ₹0.01, or leave it blank to use the reference price.",
      );
      return;
    }
    const id = ++requestId.current;
    setLoading(true);
    setError("");
    setNotice("");
    // Choose the loss estimate automatically; farmers do not need to select a model.
    const snapshot = { ...profile, loss_estimation_method: "model", loss_override_pct: null };
    try {
      const [planRes, cropRes] = await Promise.all([
        generatePlan({
          ...snapshot,
          user_price_override: priceInput === "" ? null : Number(priceInput),
        }),
        fetchCropRecommendation(
          Object.fromEntries(
            ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"].map(
              (key) => [key, snapshot[key]],
            ),
          ),
        ).catch(() => null),
      ]);
      if (id !== requestId.current) return;
      if (health?.status !== "healthy")
        fetchHealth()
          .then(setHealth)
          .catch(() => {});
      setSelectedPlan(planRes.selected_plan);
      setAlternativePlans(planRes.alternative_plans || []);
      setCropResult(
        cropRes
          ? {
              ...cropRes,
              seasonal_candidates: planRes.seasonal_suitability_labels,
            }
          : null,
      );
      setGeneratedProfile(snapshot);
      setGeneratedPrice(priceInput === "" ? null : Number(priceInput));
      setNotice(
        example
          ? "Example field loaded. Add your own measurements in My field."
          : "Your farm plan has been updated.",
      );
      if (!cropRes)
        setNotice(
          "Your plan is ready. The detailed crop ranking is temporarily unavailable.",
        );
    } catch (err) {
      if (id === requestId.current) setError(err.message);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  };
  // Refresh a changed location/season instead of leaving the previous crop visible.
  useEffect(() => {
    if (!generatedProfile || profile.season === "Whole Year") return;
    if (
      ["state", "district", "season"].every(
        (key) => profile[key] === generatedProfile[key],
      )
    )
      return;
    const timer = setTimeout(() => handleGeneratePlan(false, true), 350);
    return () => clearTimeout(timer);
  }, [profile.state, profile.district, profile.season]);

  const exportPlan = () => {
    if (!selectedPlan) return;
    const blob = new Blob(
      [
        JSON.stringify(
          {
            profile: generatedProfile,
            priceOverride: generatedPrice,
            plan: selectedPlan,
            alternatives: alternativePlans,
            exported_at: new Date().toISOString(),
            note: "Research estimate. Prices are planning references, not live quotes.",
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `AgriOptima-${generatedProfile.district}-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const savePlan = () => {
    if (!selectedPlan) return;
    const entry = {
      id: Date.now(),
      date: new Date().toISOString(),
      profile: generatedProfile,
      priceOverride: generatedPrice,
      plan: selectedPlan,
      alternatives: alternativePlans,
      cropResult,
    };
    const next = [entry, ...saved].slice(0, 10);
    if (store("agrioptima-plans", next)) {
      setSaved(next);
      setNotice("Plan saved on this browser. Find it in Saved plans.");
    } else
      setError(
        "Browser storage is full or unavailable. Export your plan instead.",
      );
  };
  const restore = (entry) => {
    ++requestId.current;
    setLoading(false);
    setProfile(entry.profile);
    setGeneratedProfile(entry.profile);
    setSelectedPlan(entry.plan);
    setAlternativePlans(entry.alternatives || []);
    setCropResult(entry.cropResult);
    setCustomPrice(
      entry.priceOverride == null ? "" : String(entry.priceOverride),
    );
    setGeneratedPrice(entry.priceOverride ?? null);
    navigate("crop");
    setNotice("Saved snapshot opened. Recalculate to use current settings.");
  };
  const p = selectedPlan,
    field = generatedProfile || profile;
  const overview = (
    <>
      <div className="overview-top">
        <section className="field-hero">
          <img
            src="/images/farmland.jpg"
            alt="Sunlight across cultivated rolling fields"
          />
          <div className="hero-shade" />
          <div className="hero-content">
            <span className="hero-tag">
              <span className="live-dot" /> YOUR FIELD, IN FOCUS
            </span>
            <h2>
              Good decisions.
              <br />
              <em>Better growing.</em>
            </h2>
            <p>
              A little understanding today.
              <br />A more considered harvest tomorrow.
            </p>
            <button
              className="btn btn-light"
              onClick={() => navigate("profile")}
            >
              Explore your field <ArrowUpRight size={17} />
            </button>
          </div>
          <div className="hero-caption">
            <MapPin size={14} />
            {title(field.district)}, {field.state}
            <span>{field.season} season</span>
          </div>
        </section>
        <section className="field-snapshot">
          <div className="section-heading">
            <span className="eyebrow">FIELD SNAPSHOT</span>
            <Layers size={18} />
          </div>
          <h3>
            {title(field.district)}
            <span>
              {field.state} · {number(field.area_ha)} hectares
            </span>
          </h3>
          <div
            className="soil-dial"
            style={{
              "--soil-angle": `${(Math.max(0, Math.min(14, Number(field.ph))) / 14) * 360}deg`,
            }}
          >
            <div>
              <span>Soil pH</span>
              <strong>{field.ph}</strong>
              <small>Entered measurement</small>
            </div>
          </div>
          <div className="snapshot-nutrients">
            {["N", "P", "K"].map((k) => (
              <div key={k}>
                <strong>{field[k]}</strong>
                <span>
                  {k === "N"
                    ? "Nitrogen"
                    : k === "P"
                      ? "Phosphorus"
                      : "Potassium"}
                </span>
              </div>
            ))}
          </div>
          <button className="text-button" onClick={() => navigate("profile")}>
            View soil inputs <ArrowRight size={15} />
          </button>
        </section>
      </div>
      <div className="overview-label">
        <h2>Your season at a glance</h2>
        <span>
          <span className="olive-dot" />{" "}
          {p ? "Calculated from your plan" : "Preparing example plan"}
        </span>
      </div>
      <div className="stat-grid">
        {[
          [
            Wheat,
            "Planning crop",
            p?.crop || "—",
            "Regional yield-model coverage",
            "crop",
          ],
          [
            TrendingUp,
            "Estimated yield",
            p ? `${number(p.predicted_yield_tonnes_per_ha)} t/ha` : "—",
            "Model estimate, not a guarantee",
            "yield",
          ],
          [
            Store,
            "Marketable harvest",
            p ? `${number(p.marketable_production_quintals)} qtl` : "—",
            "After estimated handling losses",
            "market",
          ],
          [
            ArrowUpRight,
            "Estimated net return",
            money(p?.net_return_rs),
            "After included planning costs",
            "plan",
          ],
        ].map(([Icon, label, value, sub, tab], i) => (
          <button
            className={`stat-card stat-${i}`}
            key={label}
            onClick={() => navigate(tab)}
          >
            <span className="stat-top">
              {label}
              <Icon size={18} />
            </span>
            <strong>{value}</strong>
            <span className="stat-sub">
              {sub}
              <ArrowUpRight size={14} />
            </span>
          </button>
        ))}
      </div>
      <div className="overview-bottom">
        <section className="card crop-comparison">
          <div className="section-heading">
            <div>
              <span className="eyebrow">LOOK AT YOUR OPTIONS</span>
              <h2>A crop worth considering.</h2>
            </div>
            <button
              className="icon-button"
              aria-label="View crop comparison"
              onClick={() => navigate("crop")}
            >
              <ArrowUpRight size={20} />
            </button>
          </div>
          <p>Estimated net returns for the same field and assumptions.</p>
          <div className="comparison-chart">
            {p ? (
              [p, ...alternativePlans].filter(row => row.net_return_rs != null).slice(0, 4).map((row, i) => (
                <div className="comparison-row" key={row.crop}>
                  <span>
                    {row.crop}
                    <small>
                      {number(row.predicted_yield_tonnes_per_ha)} t/ha
                    </small>
                  </span>
                  <div className="bar-track">
                    <div
                      className={i === 0 ? "selected-bar" : ""}
                      style={{
                        width: `${Math.max(2, (Math.abs(row.net_return_rs) / Math.max(...[p, ...alternativePlans].map((r) => Math.abs(r.net_return_rs)), 1)) * 100)}%`,
                      }}
                    />
                  </div>
                  <strong className={row.net_return_rs < 0 ? "negative" : ""}>
                    {money(row.net_return_rs)}
                  </strong>
                </div>
              ))
            ) : (
              <div className="empty-state">
                {loading
                  ? "Calculating your crop options…"
                  : "Generate a farm plan to compare crops."}
              </div>
            )}
          </div>
          <div className="chart-footnote">
            <span className="olive-dot" /> Current planning choice{" "}
            <span>
              Bar length shows return magnitude; signed amounts show losses.
            </span>
          </div>
        </section>
        <section className="card season-card">
          <span className="eyebrow">THE NEXT RIGHT STEP</span>
          <h2>
            A plan for
            <br />
            <em>what comes next.</em>
          </h2>
          <ol>
            {[
              [
                "Know your soil",
                "Add field and seasonal measurements.",
                "profile",
              ],
              [
                "Find your crop",
                "Explore suitability and yield estimates.",
                "crop",
              ],
              [
                "Plan your harvest",
                "Estimate the crop lost after harvest.",
                "loss",
              ],
            ].map(([t, d, tab], i) => (
              <li key={t}>
                <button onClick={() => navigate(tab)}>
                  <span className="step-number">0{i + 1}</span>
                  <span>
                    <strong>{t}</strong>
                    <small>{d}</small>
                  </span>
                  <ChevronRight size={16} />
                </button>
              </li>
            ))}
          </ol>
        </section>
      </div>
      <div className="climate-strip">
        <div>
          <Sun size={24} />
          <span>
            <strong>{field.temperature}°C</strong>Entered temperature
          </span>
        </div>
        <div>
          <Droplets size={24} />
          <span>
            <strong>{field.rainfall} mm</strong>Entered rainfall
          </span>
        </div>
        <div>
          <Wind size={24} />
          <span>
            <strong>{field.humidity}%</strong>Entered humidity
          </span>
        </div>
        <p>
          Seasonal inputs for your scenario.
          <br />
          These are not live weather readings.
        </p>
      </div>
    </>
  );
  return (
    <div className="workspace">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      {mobile && (
        <button
          className="nav-overlay"
          aria-label="Close navigation"
          onClick={() => setMobile(false)}
        />
      )}
      <aside ref={sidebarRef} className={`sidebar ${mobile ? "is-open" : ""}`}>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate("dashboard");
          }}
        >
          <span className="brand-symbol">
            <Sprout size={26} />
          </span>
          <span>
            AgriOptima<small>ROOTED IN UNDERSTANDING</small>
          </span>
        </a>
        <button
          className="mobile-close icon-button"
          aria-label="Close menu"
          onClick={() => setMobile(false)}
        >
          <X />
        </button>
        <div className="workspace-label">YOUR WORKSPACE</div>
        <nav aria-label="Main navigation">
          {tabs.map(([id, label, Icon]) => (
            <button
              key={id}
              aria-current={activeTab === id && !savedView ? "page" : undefined}
              className={activeTab === id && !savedView ? "active" : ""}
              onClick={() => navigate(id)}
            >
              <Icon size={18} />
              {label}
              {activeTab === id && !savedView && (
                <span className="nav-marker" />
              )}
            </button>
          ))}
        </nav>
        <div className="nav-divider" />
        <button
          className={`saved-nav ${savedView ? "active" : ""}`}
          onClick={() => {
            setSavedView(true);
            setMobile(false);
          }}
        >
          <Bookmark size={18} />
          Saved plans<span className="count-badge">{saved.length}</span>
        </button>
        <button className="saved-nav" onClick={() => navigate("sources")}>
          <CircleHelp size={18} />
          About the data
        </button>
        <div className="sidebar-bottom">
          <div className="growing-note">
            <Sprout size={24} />
            <strong>Grow with understanding.</strong>
            <p>
              Every field has a story.
              <br />
              Start with yours.
            </p>
          </div>
          <div className="research-label">
            <span
              className={
                health?.status === "healthy" ? "olive-dot" : "offline-dot"
              }
            />
            {health?.status === "healthy"
              ? "Planning service connected"
              : health
                ? "Service unavailable"
                : "Connecting to service…"}
          </div>
          <div className="user-stamp">
            <span>AO</span>
            <div>
              Your farm workspace<small>Haryana & Punjab</small>
            </div>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            <button
              className="mobile-menu icon-button"
              aria-label="Open navigation"
              onClick={() => setMobile(true)}
            >
              <Menu />
            </button>
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>
              {savedView
                ? "Saved plans"
                : tabs.find((t) => t[0] === activeTab)?.[1] || "About the data"}
            </strong>
          </div>
          <div className="topbar-right">
            <span className="region-pill">
              <MapPin size={13} />
              {title(profile.district)}, {profile.state}
            </span>
            <span className="avatar">AS</span>
          </div>
        </header>
        <main id="main" tabIndex="-1">
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                {savedView
                  ? "YOUR PLANNING LIBRARY"
                  : activeTab === "dashboard"
                    ? "A LITTLE CLARITY FOR YOUR NEXT HARVEST"
                    : "AGRICULTURAL PLANNING WORKSPACE"}
              </span>
              <h1>
                {savedView
                  ? "Your saved plans."
                  : {
                      dashboard: "A better view of your farm.",
                      profile: "Your field. Your starting point.",
                      crop: "Find your next crop.",
                      yield: "Understand your harvest.",
                      market: "From harvest to market.",
                      plan: "Bring the numbers together.",
                      loss: "Understand post-harvest loss.",
                      sources: "Understand what’s behind the plan.",
                    }[activeTab]}
              </h1>
              <p>
                {activeTab === "dashboard"
                  ? "Soil, season and possibilities. All in one place."
                  : "Explore your field with transparent inputs and practical comparisons."}
              </p>
            </div>
            <div className="heading-actions">
              <button
                className="btn btn-secondary"
                disabled={!p || loading}
                onClick={exportPlan}
              >
                <Download size={16} />
                Export plan
              </button>
              <button
                className="btn btn-primary"
                onClick={() => navigate("profile")}
              >
                <Sprout size={16} />
                My field
                <ArrowUpRight size={15} />
              </button>
            </div>
          </div>
          {error && (
            <div className="alert alert-error" role="alert">
              <span>{error}</span>
              <button
                className="text-button"
                disabled={loading}
                onClick={() => handleGeneratePlan()}
              >
                Retry
              </button>
            </div>
          )}
          {notice && (
            <div className="status-message" role="status">
              <Check size={14} />
              {notice}
              <button
                aria-label="Dismiss notification"
                className="icon-button"
                onClick={() => setNotice("")}
              >
                <X size={14} />
              </button>
            </div>
          )}
          {dirty && (
            <div className="alert alert-warning">
              Your field inputs have changed. Results still reflect the last
              generated plan.
              <button
                className="text-button"
                disabled={loading}
                onClick={() => handleGeneratePlan()}
              >
                Update results <RefreshCw size={13} />
              </button>
            </div>
          )}
          {loading && (
            <div className="loading-line" role="status">
              Updating crop, yield and financial estimates…
            </div>
          )}
          {savedView ? (
            <section className="card">
              <h2>Plans saved on this browser</h2>
              <p>
                Up to ten snapshots. Export a copy to keep it outside this
                browser.
              </p>
              {!saved.length ? (
                <div className="empty-state">
                  <Bookmark size={28} />
                  <h3>A little planning goes a long way.</h3>
                  <p>
                    Generate a plan, then choose “Save this plan” in Farm plan.
                  </p>
                  <button
                    className="btn btn-primary"
                    onClick={() => navigate("crop")}
                  >
                    Go to farm plan
                    <ArrowRight size={16} />
                  </button>
                </div>
              ) : (
                saved.map((entry) => (
                  <div className="saved-plan-row" key={entry.id}>
                    <Wheat size={24} />
                    <div>
                      <strong>
                        {entry.plan.crop} · {title(entry.profile.district)}
                      </strong>
                      <small>
                        {new Date(entry.date).toLocaleString("en-IN")} ·{" "}
                        {entry.profile.area_ha} ha
                      </small>
                    </div>
                    <strong>{money(entry.plan.net_return_rs)}</strong>
                    <button
                      className="btn btn-secondary"
                      onClick={() => restore(entry)}
                    >
                      Open
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`Delete saved ${entry.plan.crop} plan`}
                      onClick={() => {
                        const next = saved.filter((x) => x.id !== entry.id);
                        if (store("agrioptima-plans", next)) setSaved(next);
                        else setError("Unable to update browser storage.");
                      }}
                    >
                      <Trash2 size={17} />
                    </button>
                  </div>
                ))
              )}
            </section>
          ) : (
            <>
              {activeTab === "dashboard" && overview}
              {activeTab === "profile" && (
                <FarmProfileSection
                  profile={profile}
                  setProfile={setProfile}
                  loading={loading}
                  onGeneratePlan={() => handleGeneratePlan()}
                  supportedDistricts={
                    health?.metadata?.supported_districts || []
                  }
                  onReset={() => {
                    setProfile({ ...DEFAULT });
                    setCustomPrice("");
                    setNotice(
                      "Example inputs restored. Generate a plan when ready.",
                    );
                  }}
                />
              )}
              {activeTab === "crop" && (
                <CropRecommendationsSection
                  cropResult={cropResult}
                  selectedPlan={p}
                  season={field.season}
                  state={field.state}
                />
              )}
              {activeTab === "yield" && (
                <YieldProductionSection selectedPlan={p} profile={field} />
              )}
              {activeTab === "market" && <PredictionSection key="market" kind="market" />}
              {activeTab === "loss" && <PredictionSection key="loss" kind="loss" />}
              {activeTab === "sources" && (
                <section className="card sources-card">
                  <span className="eyebrow">A CLEARER PICTURE</span>
                  <h2>Research estimates, with context.</h2>
                  <p>
                    This workspace combines measured model outputs with explicit
                    planning assumptions. It is a student research project for
                    Haryana and Punjab.
                  </p>
                  <div className="grid-2">
                    {[
                      [
                        "Crop suitability",
                        "Seven soil and climate inputs predict a crop label. Historical test accuracy is about 79.9%; it does not guarantee agronomic or financial suitability.",
                      ],
                      [
                        "Yield estimates",
                        "A Random Forest estimates tonnes per hectare. Historical mean absolute error is approximately 2.10 t/ha, with larger errors for some crops.",
                      ],
                      [
                        "Market prices",
                        "Planning uses historical dataset prices or your local offer. A separate maize research estimate is available on the market page. Neither is a live quote.",
                      ],
                      [
                        "Post-harvest and costs",
                        "Loss rates are read from the published study extract, with clearly labelled proxies when needed. Costs are editable estimates under My field.",
                      ],
                    ].map(([h, d]) => (
                      <article className="source-item" key={h}>
                        <h3>{h}</h3>
                        <p>{d}</p>
                      </article>
                    ))}
                  </div>
                  <h3>Keep the scope in mind</h3>
                  <p>
                    Predictions are estimates and should be checked against local
                    growing conditions. Saved plans stay in this browser and can
                    be deleted or exported. Field photos are illustrative, not
                    satellite images of your land.
                  </p>
                  <p className="photo-credit">
                    Field photograph:{" "}
                    <a
                      href="https://unsplash.com"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Unsplash
                    </a>
                    .
                  </p>
                </section>
              )}
            </>
          )}
          <footer className="page-footer">
            <span>
              <Sprout size={15} />
              AgriOptima <span className="footer-dot">·</span> A more considered
              harvest.
            </span>
            <span>Research estimates · Planning prices, not live quotes</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
