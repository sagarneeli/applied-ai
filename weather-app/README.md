# Weather App (LLM Tool Calling with Pydantic & Rich)

A practice exercise demonstrating the simplest "hello world" implementation of **tool calling** with an LLM (Google Gemini Interactions API), returning validated structured output via **Pydantic**, rendered in the terminal with **Rich**.

## Practice Prompt

> Use an LLM with tool calling in Python to fetch and display the current weather for a city. No other input - pick a random city using the model's own knowledge, call a weather tool, and return the result in a structured format. The aim is to understand the simplest possible "hello world" implementation of tool calling with an LLM.
>
> **Tool:**
> `get_weather(city: str) -> {temperature_c: float, condition: str, humidity: int}`
>
> **Expected structured output:**
> - `city: str`
> - `temperature_c: float`
> - `condition: str`
> - `humidity: int`
> - `weather_summary: str`

*(Extended in [`weather.py`](./weather.py) with `wind_speed`, `forecast_days`, and a multi-day `forecast` table, plus optional CLI city input.)*

## How It Works

1. **Tool definition (`weather_tool`)**: Registers `get_weather(city: str)` with `client.interactions.create(...)` using the global `MODEL_ID` constant.
2. **Tool-calling loop (`run`)**: When Gemini responds with a `function_call` step, the app runs `get_weather(**step.arguments)` locally and sends the `function_result` back using `previous_interaction_id`.
3. **Structured output (`WeatherReport`)**: Constrains the final response with `response_format=WeatherReport.model_json_schema()` and validates it via `WeatherReport.model_validate_json(interaction.output_text)`.
4. **Terminal output (`display_weather`)**: Renders a current weather panel, summary panel, and rounded multi-day forecast table using `rich`.

## Setup

1. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv pip install google-genai pydantic rich
   ```

3. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

## Usage

Pass a city from the command line:
```bash
python weather.py Tokyo
```

Or run without arguments to enter a city interactively (leave blank to let the model pick a random city):
```bash
python weather.py
```
