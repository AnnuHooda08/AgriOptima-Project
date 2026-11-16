const API_BASE = "/api";
async function request(path, payload) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      signal: controller.signal,
      ...(payload === undefined
        ? {}
        : {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = data?.detail;
      throw new Error(
        Array.isArray(detail)
          ? detail
              .map((item) => `${item.loc?.slice(1).join(".")}: ${item.msg}`)
              .join("; ")
          : typeof detail === "string"
            ? detail
            : `Request failed (${response.status}). Please try again.`,
      );
    }
    if (!data)
      throw new Error(
        "The server returned an empty response. Please try again.",
      );
    return data;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error(
        "The request took too long. Check the connection and try again.",
      );
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
export const fetchHealth = () => request("/health");
export const fetchWeather = (lat, lon, district) =>
  request(
    `/weather?${new URLSearchParams({ latitude: lat, longitude: lon, district })}`,
  );
export const fetchCropRecommendation = (features) =>
  request("/crop-recommendation", features);
export const fetchYieldPrediction = (payload) =>
  request("/yield-prediction", payload);
export const generatePlan = (profile) => request("/plan", profile);
export const fetchMandiAnalysis = (
  crop,
  state = "All",
  user_price_override = null,
) => request("/mandi-analysis", { crop, state, user_price_override });
export const simulateWhatIf = (
  base_plan,
  price_change_pct,
  yield_shock_pct,
  storage_months,
  area_override,
) =>
  request("/what-if", {
    base_plan,
    price_change_pct: Number(price_change_pct),
    yield_shock_pct: Number(yield_shock_pct),
    storage_months: Number(storage_months),
    ...(area_override > 0 ? { area_override: Number(area_override) } : {}),
  });
