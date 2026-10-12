"""AQI forecasting with TabPFN, plus an honest persistence baseline."""
import os

import numpy as np
import pandas as pd

FEATURES = [
    "hour", "dow", "temperature_2m", "relative_humidity_2m",
    "wind_speed_10m", "precipitation", "aqi_lag24",
]
HOLDOUT_HOURS = 48
HORIZON = 12
MAX_TRAIN_ROWS = 1000


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df["time"].dt.hour
    df["dow"] = df["time"].dt.dayofweek
    df["aqi_lag24"] = df["us_aqi"].shift(24)
    return df


def _make_regressor():
    """TabPFN via the Prior Labs API (default), local TabPFN, or a clearly-labelled fallback."""
    token = os.getenv("TABPFN_TOKEN")
    if token:
        try:
            import tabpfn_client
            tabpfn_client.set_access_token(token)
            return tabpfn_client.TabPFNRegressor(), "TabPFN (API)"
        except Exception as e:  # noqa: BLE001
            print("tabpfn-client unavailable:", e)
    try:
        from tabpfn import TabPFNRegressor
        return TabPFNRegressor(device="cpu"), "TabPFN (local CPU)"
    except Exception as e:  # noqa: BLE001
        print("local tabpfn unavailable:", e)
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(), "fallback GBM (TabPFN unavailable)"


def forecast(df: pd.DataFrame, now: pd.Timestamp) -> dict:
    """Fit on history, score last 48h vs persistence, predict next 12 hours from `now`."""
    df = build_features(df)
    past = df[(df["time"] <= now) & df["us_aqi"].notna() & df["aqi_lag24"].notna()]
    past = past.dropna(subset=FEATURES)
    future = df[df["time"] > now].head(HORIZON).copy()
    if len(past) < HOLDOUT_HOURS + 100 or future.empty:
        raise ValueError("Not enough data for this location")

    train = past.iloc[:-HOLDOUT_HOURS].tail(MAX_TRAIN_ROWS)
    test = past.iloc[-HOLDOUT_HOURS:]

    # aqi_lag24 for future hours comes from the known AQI 24h earlier
    future[FEATURES] = future[FEATURES].astype(float).fillna(
        {"precipitation": 0.0, "aqi_lag24": float(past["us_aqi"].iloc[-1])}
    )

    model, model_name = _make_regressor()
    try:
        model.fit(train[FEATURES], train["us_aqi"])
        # one predict call for holdout + future keeps API usage low
        preds = model.predict(pd.concat([test[FEATURES], future[FEATURES]]))
    except Exception as e:  # noqa: BLE001
        if not model_name.startswith("TabPFN"):
            raise
        print("TabPFN failed, using fallback:", e)
        from sklearn.ensemble import HistGradientBoostingRegressor
        model, model_name = HistGradientBoostingRegressor(), "fallback GBM (TabPFN error)"
        model.fit(train[FEATURES], train["us_aqi"])
        preds = model.predict(pd.concat([test[FEATURES], future[FEATURES]]))

    preds = np.clip(np.asarray(preds, dtype=float), 0, 500)
    test_pred, fut_pred = preds[: len(test)], preds[len(test):]

    mae_model = float(np.mean(np.abs(test_pred - test["us_aqi"].values)))
    mae_base = float(np.mean(np.abs(test["aqi_lag24"].values - test["us_aqi"].values)))

    hours = [
        {
            "time": t.isoformat(),
            "label": t.strftime("%-I %p"),
            "hour": int(t.hour),
            "aqi": round(float(p)),
            "temp": round(float(temp), 1),
            "precip": round(float(pr), 2),
            "wind": round(float(w), 1),
        }
        for t, p, temp, pr, w in zip(
            future["time"], fut_pred, future["temperature_2m"],
            future["precipitation"], future["wind_speed_10m"],
        )
    ]
    return {
        "model": model_name,
        "train_rows": int(len(train)),
        "mae_model": round(mae_model, 1),
        "mae_baseline": round(mae_base, 1),
        "hours": hours,
    }


def best_window(hours: list[dict]) -> dict | None:
    """Lowest predicted AQI between 6am and 7pm local time, with no rain."""
    ok = [h for h in hours if 6 <= h["hour"] <= 19 and h["precip"] < 0.1]
    return min(ok, key=lambda h: h["aqi"]) if ok else None
