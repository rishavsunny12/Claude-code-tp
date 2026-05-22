"""
Open-Meteo API integration for historical and forecast weather data.
Completely free, no API key required.
Docs: https://open-meteo.com/en/docs
"""

import httpx
import logging
from dataclasses import dataclass
from datetime import date, timedelta

logger = logging.getLogger(__name__)

OPEN_METEO_HISTORICAL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"


@dataclass
class MonthlyWeather:
    date: date
    total_precipitation_mm: float
    mean_temperature_c: float
    mean_relative_humidity_pct: float


@dataclass
class WeatherForecast:
    latitude: float
    longitude: float
    daily_precip_mm: list[float]
    daily_dates: list[str]
    total_14day_precip: float


async def fetch_monthly_rainfall(
    lat: float,
    lon: float,
    start: date,
    end: date,
) -> list[MonthlyWeather]:
    """Fetch monthly aggregated rainfall and temperature from Open-Meteo historical archive."""
    # Open-Meteo archive has a ~2 day lag — cap end at yesterday to avoid 400 errors
    yesterday = date.today() - timedelta(days=2)
    end = min(end, yesterday)
    if start > end:
        return []

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "precipitation_sum,temperature_2m_mean,relative_humidity_2m_mean",
        "timezone": "UTC",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(OPEN_METEO_HISTORICAL, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error("Open-Meteo historical request failed for (%s, %s): %s", lat, lon, e)
            return []

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    precip = daily.get("precipitation_sum", [])
    temp = daily.get("temperature_2m_mean", [])
    humidity = daily.get("relative_humidity_2m_mean", [])

    monthly: dict[str, list] = {}
    for i, d in enumerate(dates):
        key = d[:7]  # YYYY-MM
        if key not in monthly:
            monthly[key] = {"precip": [], "temp": [], "humidity": []}
        if i < len(precip) and precip[i] is not None:
            monthly[key]["precip"].append(precip[i])
        if i < len(temp) and temp[i] is not None:
            monthly[key]["temp"].append(temp[i])
        if i < len(humidity) and humidity[i] is not None:
            monthly[key]["humidity"].append(humidity[i])

    result = []
    for key, vals in sorted(monthly.items()):
        y, m = key.split("-")
        result.append(MonthlyWeather(
            date=date(int(y), int(m), 1),
            total_precipitation_mm=sum(vals["precip"]),
            mean_temperature_c=sum(vals["temp"]) / len(vals["temp"]) if vals["temp"] else 0,
            mean_relative_humidity_pct=sum(vals["humidity"]) / len(vals["humidity"]) if vals["humidity"] else 0,
        ))
    return result


async def fetch_14day_forecast(lat: float, lon: float) -> WeatherForecast:
    """Fetch 14-day precipitation forecast for a location."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "forecast_days": 14,
        "timezone": "UTC",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.get(OPEN_METEO_FORECAST, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error("Open-Meteo forecast failed for (%s, %s): %s", lat, lon, e)
            return WeatherForecast(lat, lon, [], [], 0.0)

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    precip = [p or 0.0 for p in daily.get("precipitation_sum", [])]

    return WeatherForecast(
        latitude=lat,
        longitude=lon,
        daily_precip_mm=precip,
        daily_dates=dates,
        total_14day_precip=sum(precip),
    )
