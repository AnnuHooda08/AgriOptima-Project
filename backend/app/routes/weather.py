from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.weather import WeatherResponse
from app.services.weather_service import weather_service

router = APIRouter()

@router.get("/weather", response_model=WeatherResponse)
def get_weather_data(
    latitude: float = Query(30.3782, description="Latitude"),
    longitude: float = Query(76.7767, description="Longitude"),
    district: Optional[str] = Query("Ambala", description="District name")
):
    """
    Fetches temperature, humidity, and rainfall from NASA POWER or regional climate baseline.
    """
    return weather_service.get_weather(latitude, longitude, district)
