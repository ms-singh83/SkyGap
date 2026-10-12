"""SkyGap: the best hour today to go outside."""
import time

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from data import fetch_table, geocode
from model import best_window, forecast
from plan import write_plan

app = FastAPI(title="SkyGap")
_cache: dict[str, tuple[float, dict]] = {}
CACHE_SECONDS = 1800


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/healthz")
def health():
    return {"ok": True}


@app.get("/api/plan")
def plan(city: str = Query(..., min_length=1, max_length=80)):
    key = city.strip().lower()
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    try:
        place = geocode(city)
        df, tz = fetch_table(place["lat"], place["lon"])
        now = pd.Timestamp.now(tz=tz).tz_localize(None).floor("h")
        fc = forecast(df, now)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Upstream error: {e}")
    best = best_window(fc["hours"])
    city_name = f"{place['name']}, {place['country']}".strip(", ")
    text, source = write_plan(city_name, best, fc["hours"])
    result = {"city": city_name, "timezone": tz, "best": best, "plan": text, "plan_source": source, **fc}
    _cache[key] = (time.time(), result)
    return result
