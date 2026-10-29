import logging
from typing import Dict, Any, Optional
import requests
from app.schemas.weather import WeatherResponse

logger = logging.getLogger(__name__)

# Known district coordinates and climatological averages (offline resilient)
DISTRICT_WEATHER_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "AMBALA": {"lat": 30.3782, "lon": 76.7767, "temperature": 24.5, "humidity": 65.0, "rainfall": 950.0},
    "KARNAL": {"lat": 29.6857, "lon": 76.9905, "temperature": 25.1, "humidity": 62.0, "rainfall": 750.0},
    "HISAR": {"lat": 29.1492, "lon": 75.7217, "temperature": 25.8, "humidity": 52.0, "rainfall": 450.0},
    "ROHTAK": {"lat": 28.8955, "lon": 76.6066, "temperature": 25.4, "humidity": 58.0, "rainfall": 550.0},
    "KURUKSHETRA": {"lat": 29.9695, "lon": 76.8783, "temperature": 24.8, "humidity": 64.0, "rainfall": 800.0},
    "SIRSA": {"lat": 29.5349, "lon": 75.0298, "temperature": 25.6, "humidity": 50.0, "rainfall": 350.0},
    "LUDHIANA": {"lat": 30.9010, "lon": 75.8573, "temperature": 24.3, "humidity": 62.0, "rainfall": 700.0},
    "AMRITSAR": {"lat": 31.6340, "lon": 74.8723, "temperature": 23.9, "humidity": 66.0, "rainfall": 680.0},
    "PATIALA": {"lat": 30.3398, "lon": 76.3869, "temperature": 24.7, "humidity": 61.0, "rainfall": 720.0},
    "BATHINDA": {"lat": 30.2110, "lon": 74.9455, "temperature": 25.3, "humidity": 54.0, "rainfall": 420.0},
    "JALANDHAR": {"lat": 31.3260, "lon": 75.5762, "temperature": 24.1, "humidity": 63.0, "rainfall": 710.0},
}

class WeatherService:
    @staticmethod
    def get_weather(latitude: float, longitude: float, district: Optional[str] = None) -> WeatherResponse:
        """
        Attempts to fetch live climatological data from NASA POWER API.
        Falls back gracefully to agro-climatic district baseline if offline/sandboxed.
        """
        norm_district = district.strip().upper() if district else None
        
        # Check district defaults first for matching coords if district provided
        default_info = DISTRICT_WEATHER_DEFAULTS.get(norm_district) if norm_district else None
        
        url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
        params = {
            "parameters": "T2M,RH2M,PRECTOTCORR",
            "community": "AG",
            "longitude": round(longitude, 4),
            "latitude": round(latitude, 4),
            "format": "JSON"
        }

        try:
            response = requests.get(url, params=params, timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                params_data = data.get("properties", {}).get("parameter", {})
                
                # Annual averages from NASA POWER
                t2m_dict = params_data.get("T2M", {})
                rh2m_dict = params_data.get("RH2M", {})
                prec_dict = params_data.get("PRECTOTCORR", {})

                ann_t2m = t2m_dict.get("ANN", 24.5)
                ann_rh2m = rh2m_dict.get("ANN", 62.0)
                ann_prec = prec_dict.get("ANN", 2.2)  # mm/day in NASA POWER

                annual_rainfall = round(ann_prec * 365.0, 1)

                return WeatherResponse(
                    temperature=round(float(ann_t2m), 1),
                    humidity=round(float(ann_rh2m), 1),
                    rainfall=round(float(annual_rainfall), 1),
                    source="NASA POWER Agroclimatology API",
                    district=district
                )
        except Exception as e:
            logger.info(f"NASA POWER API unreachable ({e}). Using district agro-climatic baseline.")

        # Fallback to district baseline or default Indian agricultural plane average
        if default_info:
            return WeatherResponse(
                temperature=default_info["temperature"],
                humidity=default_info["humidity"],
                rainfall=default_info["rainfall"],
                source="District Agro-Climatic Normal (Offline Fallback)",
                district=district
            )
        
        return WeatherResponse(
            temperature=25.0,
            humidity=65.0,
            rainfall=750.0,
            source="Regional Agricultural Baseline (Default)",
            district=district
        )

weather_service = WeatherService()
