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
export const fetchCropRecommendation = (features) =>
  request("/crop-recommendation", features);
export const fetchYieldPrediction = (payload) =>
  request("/yield-prediction", payload);
export const generatePlan = (profile) => request("/plan", profile);
