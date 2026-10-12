"""Gemma writes a 2-line outdoor plan. Never breaks: falls back to a template."""
import os

import requests


def _prompt(city: str, best: dict, hours: list[dict]) -> str:
    strip = ", ".join(f"{h['label']}: AQI {h['aqi']}, {h['temp']}C" for h in hours)
    return (
        "You help people get outside. Write exactly 2 short lines, plain text, no emojis, "
        "no markdown, no dashes. Line 1: when to go for a walk or run and the predicted AQI. "
        "Line 2: one practical tip (clothing, mask, water) based on temperature, wind and AQI.\n"
        f"City: {city}\nBest hour: {best['label']}, predicted AQI {best['aqi']}, "
        f"temp {best['temp']}C, wind {best['wind']} km/h\n"
        f"Next 12 hours: {strip}"
    )


def _template(best: dict | None) -> str:
    if not best:
        return "No dry daylight hour in the next 12 hours.\nTry an indoor stretch now and check back later."
    tip = "carry water" if best["temp"] >= 28 else "carry a light jacket" if best["temp"] < 18 else "wear something comfy"
    mask = ", and consider a mask" if best["aqi"] > 150 else ""
    return f"Go at {best['label']}, AQI should be around {best['aqi']}.\nIt'll be about {best['temp']}C, {tip}{mask}."


def _google(prompt: str) -> str:
    key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("GEMMA_MODEL", "gemma-3-27b-it")
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": key},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0.6, "maxOutputTokens": 120}},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _ollama(prompt: str) -> str:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("GEMMA_MODEL", "gemma3:4b")
    r = requests.post(f"{host}/api/generate",
                      json={"model": model, "prompt": prompt, "stream": False}, timeout=60)
    r.raise_for_status()
    return r.json()["response"]


def write_plan(city: str, best: dict | None, hours: list[dict]) -> tuple[str, str]:
    """Returns (plan_text, source)."""
    if not best:
        return _template(best), "template"
    provider = os.getenv("GEMMA_PROVIDER", "google").lower()
    try:
        text = (_ollama if provider == "ollama" else _google)(_prompt(city, best, hours))
        lines = [ln.strip().replace("—", ",").replace("–", ",")
                 for ln in text.strip().splitlines() if ln.strip()]
        if lines:
            return "\n".join(lines[:2]), f"Gemma ({provider})"
    except Exception as e:  # noqa: BLE001
        print("Gemma failed, using template:", e)
    return _template(best), "template"
