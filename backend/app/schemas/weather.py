from typing import Optional
from pydantic import BaseModel, Field

class WeatherRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    district: Optional[str] = Field(None, description="District name for lookup")

class WeatherResponse(BaseModel):
    temperature: float = Field(..., description="Mean Temperature in °C")
    humidity: float = Field(..., description="Relative Humidity in %")
    rainfall: float = Field(..., description="Annual or Seasonal Rainfall in mm")
    source: str = Field(..., description="Source of data (NASA POWER API or District Agro-Climate Norm)")
    district: Optional[str] = None
