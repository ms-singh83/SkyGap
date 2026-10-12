# SkyGap

Spend less time here, more time out there.

SkyGap tells you the best hour in the next 12 hours to go for a walk or run. Type a city, and it:

1. Pulls 60 days of hourly weather and air quality from [Open-Meteo](https://open-meteo.com) (no API key).
2. Trains **TabPFN** on that history and predicts US AQI for the next 12 hours from the weather forecast.
3. Picks the cleanest dry daylight hour (6am to 7pm, no rain).
4. Asks **Gemma** to write a 2-line plan, like "Go at 7am, AQI drops to 90. Carry a light jacket."

Hosted on **Render**.

## How the prediction works

- One hourly table: temperature, humidity, wind speed, precipitation, `us_aqi`, `pm2_5`.
- Features: hour of day, day of week, temperature, humidity, wind, precipitation, AQI 24h earlier.
- Target: `us_aqi`.
- `TabPFNRegressor` is fit on the most recent ~1000 hours (excluding the last 48), then predicts the
  48 held-out hours and the next 12 hours in a single call.
- **Honesty check:** the last 48 hours are scored against a persistence baseline ("AQI is the same as
  24h ago"). Both MAEs are shown in the page footer for every city you look up.

### MAE result

The page shows TabPFN MAE vs baseline MAE live for each city. Example run:

| City | TabPFN MAE | Persistence MAE |
|------|-----------:|----------------:|
| _fill in from the live app_ | _x_ | _y_ |

Run `python predict_cli.py "New Delhi"` to print it in your terminal.

Note: Open-Meteo's air quality history comes from the CAMS model, not ground stations, so this
predicts that series.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Python 3.11 recommended
pip install -r requirements.txt
export TABPFN_TOKEN=...        # from https://ux.priorlabs.ai
export GEMINI_API_KEY=...      # from https://aistudio.google.com/apikey
uvicorn app:app --reload
# open http://localhost:8000
```

### Fully local, no cloud AI

```bash
pip install tabpfn            # local TabPFN on CPU, no token needed (unset TABPFN_TOKEN)
ollama pull gemma3:4b
export GEMMA_PROVIDER=ollama
uvicorn app:app
```

## Environment variables

| Var | Default | What |
|-----|---------|------|
| `TABPFN_TOKEN` | none | Prior Labs API token for `tabpfn-client`. If unset, local `tabpfn` is used if installed. |
| `GEMMA_PROVIDER` | `google` | `google` (Gemma via Google AI Studio) or `ollama` (local). |
| `GEMINI_API_KEY` | none | Google AI Studio key, used for Gemma when provider is `google`. |
| `GEMMA_MODEL` | `gemma-3-27b-it` / `gemma3:4b` | Override the Gemma model. |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server. |

If TabPFN can't be reached, the app falls back to a gradient boosting model and **labels it** in
the footer. If Gemma fails, a plain templated sentence is used. The app never breaks.

## Deploy on Render

The repo has a `render.yaml` blueprint. New > Blueprint > pick this repo > fill in `TABPFN_TOKEN`
and `GEMINI_API_KEY` > Apply.

## Files

- `data.py` Open-Meteo geocoding, weather, air quality
- `model.py` features, TabPFN fit/predict, baseline MAE, best window
- `plan.py` Gemma plan (Google AI Studio or Ollama) with template fallback
- `app.py` FastAPI app, `/api/plan?city=...`
- `static/index.html` the one page
- `predict_cli.py` terminal check that prints MAE vs baseline
