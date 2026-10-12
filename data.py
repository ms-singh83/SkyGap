"""Fetch hourly weather + air quality history and forecast from Open-Meteo (no API key)."""
import pandas as pd
import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL = "https://api.open-meteo.com/v1/forecast"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_VARS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation"]
PAST_DAYS = 60
FORECAST_DAYS = 2  # 2 so "next 12 hours" still works late in the day


def geocode(city: str) -> dict:
    r = requests.get(GEO_URL, params={"name": city, "count": 1}, timeout=15)
    r.raise_for_status()
    results = r.json().get("results") or []
    if not results:
        raise ValueError(f"City not found: {city}")
    g = results[0]
    return {
        "name": g["name"],
        "country": g.get("country", ""),
        "lat": g["latitude"],
        "lon": g["longitude"],
    }


def _hourly(url: str, lat: float, lon: float, variables: list[str]) -> tuple[pd.DataFrame, str]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(variables),
        "past_days": PAST_DAYS,
        "forecast_days": FORECAST_DAYS,
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()
    df = pd.DataFrame(j["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df, j.get("timezone", "UTC")


def fetch_table(lat: float, lon: float) -> tuple[pd.DataFrame, str]:
    """One hourly table: weather + us_aqi + pm2_5, local time. Future rows have weather only (AQI unknown)."""
    wx, tz = _hourly(WX_URL, lat, lon, WX_VARS)
    aq, _ = _hourly(AQ_URL, lat, lon, ["us_aqi", "pm2_5"])
    df = wx.merge(aq, on="time", how="left").sort_values("time").reset_index(drop=True)
    return df, tz
