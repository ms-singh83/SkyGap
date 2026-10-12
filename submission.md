---
title: SkyGap, the best hour today to go outside
published: false
tags: devchallenge, opensourceai, hacktoberfest, python
---

*This is a submission for the DEV Hacktoberfest Open-Source AI Challenge, Week 1: Touch Grass.*

## What I Built

SkyGap answers one question: when should I go for a walk today?

You type your city. It predicts air quality for the next 12 hours, picks the cleanest dry daylight hour, and gives you a 2 line plan, something like "Go at 7am, AQI drops to 90. Carry a light jacket."

That's it. One page, one answer, then you close the tab and go outside.

## Demo

Live app: https://YOUR-APP.onrender.com

![SkyGap screenshot](SCREENSHOT_URL)

And the point of it all, a photo from the walk I took using it:

![Photo from my walk](WALK_PHOTO_URL)

## Code

https://github.com/ms-singh83/SkyGap

## How I Built It

- **Data:** Open-Meteo for geocoding, hourly weather and hourly air quality. No API key, 60 days of history per city.
- **Prediction:** TabPFN regressor. Features are hour of day, day of week, temperature, humidity, wind, rain, and the AQI from 24 hours earlier. It fits on the past and predicts the next 12 hours from the weather forecast. TabPFN is a foundation model for tables, so there's no training loop or tuning, it just fits in context.
- **Keeping it honest:** I hold out the last 48 hours and compare TabPFN against a dumb baseline, "AQI is the same as 24 hours ago". Both numbers show up in the page footer for every city. For CITY it was TabPFN MAE X vs baseline MAE Y.
- **The plan:** Gemma 3 (27B via Google AI Studio, or gemma3:4b on Ollama) gets the best hour plus the 12 hour strip and writes two short lines with a practical tip. If Gemma is down, a template sentence takes over so the app never breaks.
- **Hosting:** FastAPI plus one static HTML page, deployed on Render's free tier from a `render.yaml` blueprint.

## Why Does Open Innovation Matter?

None of this needs a paid closed API. TabPFN and Gemma both have open weights, so the whole thing can run on a laptop. Switch `GEMMA_PROVIDER=ollama`, install `tabpfn` locally, and your location and the plan never leave your machine. The model is swappable too, any Gemma size or a different open model is one env var away. The data is open as well. That makes a small tool like this easy for anyone to fork for their own city, their own sport, or their own kid's school run.

## My Agent Session

I built this with Claude Code in a single session against a hard 90 minute deadline. Agent session link: AGENT_SESSION_URL

## Prize Categories

- **Best Use of TabPFN:** TabPFN is the core forecaster, with its MAE shown live against a persistence baseline.
- **Best Use of Gemma:** Gemma writes the human plan, via Google AI Studio or fully local with Ollama.
- **Best Use of Render:** the app is deployed as a Render web service from a `render.yaml` blueprint.
