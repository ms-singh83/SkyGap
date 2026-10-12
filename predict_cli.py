"""Quick check from the terminal: python predict_cli.py "New Delhi" """
import sys

import pandas as pd

from data import fetch_table, geocode
from model import best_window, forecast

city = sys.argv[1] if len(sys.argv) > 1 else "New Delhi"
place = geocode(city)
df, tz = fetch_table(place["lat"], place["lon"])
now = pd.Timestamp.now(tz=tz).tz_localize(None).floor("h")
fc = forecast(df, now)
print(f"{place['name']} ({tz}) model={fc['model']} train_rows={fc['train_rows']}")
print(f"MAE on last 48h: {fc['model']} {fc['mae_model']} vs persistence baseline {fc['mae_baseline']}")
for h in fc["hours"]:
    print(f"  {h['label']:>5}  AQI {h['aqi']:>3}  {h['temp']}C  rain {h['precip']}")
print("Best:", best_window(fc["hours"]))
