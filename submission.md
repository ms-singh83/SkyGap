*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built

SkyGap answers one small question: when should I go outside today?

You type your city. SkyGap predicts the air quality for the next 12 hours, finds the cleanest dry hour between 6am and 7pm, and gives you a 2 line plan:

> Go at 7am, AQI should drop to around 90.
> It'll be about 17C, carry a light jacket.

It's for anyone who keeps meaning to go for a walk or run but either forgets, or lives somewhere like Delhi where the wrong hour can mean breathing AQI 200 instead of 90. The page is built to be used for ten seconds and then closed. There's no feed, no streak and no reason to stay. The best outcome is that you put the phone down and go.

## Demo

Live app: https://YOUR-APP.onrender.com

![SkyGap showing the best hour and a 12 hour AQI strip](SCREENSHOT_URL)

Here's the reason it exists, a photo from the walk I took at the hour it picked:

![Photo from my walk](WALK_PHOTO_URL)

## Code

{% embed https://github.com/ms-singh83/SkyGap %}

## How I Built It

There are three parts: an open tabular foundation model to predict, an open-weight LLM to talk, and a small FastAPI app on Render.

**1. Data (Open-Meteo, no API key).** For any city I pull 60 days of hourly weather (temperature, humidity, wind, rain) and hourly US AQI, plus today's weather forecast, and join them into one table.

**2. Prediction (TabPFN).** TabPFN is a foundation model for tabular data. You give it a table and it predicts in one forward pass, with no training loop and no hyperparameter tuning. The features are hour of day, day of week, temperature, humidity, wind, rain, and the AQI from 24 hours earlier. It fits on the past ~1000 hours and predicts AQI for the next 12 hours using the forecast weather. I use `tabpfn-client` so it runs on Render's free tier. The same code also works with the local `tabpfn` package on a laptop CPU.

**3. Keeping it honest.** A forecast is only worth something if it beats the obvious guess. So I hold out the last 48 hours and compare TabPFN against a persistence baseline, "AQI will be the same as 24 hours ago". Both numbers are shown in the footer for every city you search, so you can check it yourself. For CITY, TabPFN's MAE was **X** and the baseline's was **Y**.

**4. Picking the hour.** The rule is simple: the lowest predicted AQI between 6am and 7pm local time, with no rain.

**5. The plan (Gemma).** Gemma 3 gets the best hour, the temperature and wind, and the full 12 hour strip. It writes two short lines: when to go, and one practical tip (jacket, water, mask). By default it's `gemma-3-27b-it` through Google AI Studio. Setting `GEMMA_PROVIDER=ollama` switches to `gemma3:4b` running locally. If Gemma is unreachable, a template sentence fills in, so the app never shows an error instead of an answer.

**6. Hosting (Render).** FastAPI plus one static HTML page with plain JS and no build step. It deploys from a `render.yaml` blueprint as a free Render web service, with the tokens set as environment variables. Results are cached per city for 30 minutes to keep API calls low.

## Why Does Open Innovation Matter?

Nothing in SkyGap needs a paid, closed API.

- **It runs on a laptop.** TabPFN and Gemma both have open weights. Install `tabpfn`, pull `gemma3:4b` in Ollama, and the whole app runs offline apart from the weather data.
- **Your data stays with you.** In Ollama mode your city and your plan never go to a model provider. That matters for something that knows where you are and when you go out.
- **The model is swappable.** A bigger Gemma, a smaller one, or a different open model is one environment variable away. Nothing is tied to a vendor.
- **Anyone can fork it.** Open models plus open weather data means someone can adapt it for their own city, their dog walks, or a school run, without signing up for anything.

With a closed API, this would be a demo that stops working when a free trial ends. With open models, it's a small tool that anyone can keep running.

## My Agent Session

I built SkyGap with Claude Code in one session against a 90 minute deadline. It covered data fetching, the TabPFN pipeline with the baseline check, the Gemma prompt with its fallback, the page, and the Render config.

{% agent_session AGENT_SESSION_URL %}

## Prize Categories

- **Best Use of TabPFN:** TabPFN is the core forecaster, predicting 12 hours of AQI from weather. Its accuracy is shown live against a persistence baseline on every request.
- **Best Use of Gemma:** Gemma turns the numbers into a 2 line human plan, via Google AI Studio or fully local with Ollama.
- **Best Use of Render:** SkyGap is deployed as a Render web service from a `render.yaml` blueprint on the free tier.
