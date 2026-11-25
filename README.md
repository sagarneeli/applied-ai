# Applied AI — Hands-On LLM Practice Projects

A collection of small, focused Python projects built to practice core **Applied AI / LLM engineering** concepts using the **Google Gemini API**, **Pydantic**, and **Rich**.

## Projects

| Project | Focus Area | Description |
| --- | --- | --- |
| [`travel-app/`](./travel-app) | **Structured Output (Pydantic)** | Prompts Gemini to generate a travel itinerary strictly adhering to a nested Pydantic schema (`TravelItenary` + `DailyPlan`) and renders it as a Rich `Tree` in the terminal. |
| [`weather-app/`](./weather-app) | **Tool Calling + Live APIs** | Minimal "hello world" implementation of LLM tool calling using the Gemini Interactions API. Calls a live `get_weather(city)` tool backed by the free Open-Meteo API, validates the response into a `WeatherReport` Pydantic model, and displays it with Rich dashboard panels and forecast cards. |

## Prerequisites

- Python 3.12+ (managed with [`uv`](https://docs.astral.sh/uv/))
- A Google Gemini API key exported as `GEMINI_API_KEY` (or stored in a local `.env` file)

## Quick Start

Each project is self-contained with its own README and setup instructions:

```bash
# Travel Itinerary Generator (Structured Output)
cd travel-app
uv venv && source .venv/bin/activate
uv pip install google-genai pydantic python-dotenv rich
python travel-itenary.py

# Weather App (Tool Calling + Live Open-Meteo API)
cd weather-app
uv venv && source .venv/bin/activate
uv pip install google-genai pydantic rich
python weather.py Tokyo
```
