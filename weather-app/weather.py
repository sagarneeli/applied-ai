import json
import sys
import urllib.parse
import urllib.request

from google import genai
from pydantic import BaseModel, Field
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

MODEL_ID = "gemini-3.5-flash-lite"
console = Console()


# 1. Define the expected structured output schema
class DailyForecast(BaseModel):
    day: str = Field(description="Day name or date, e.g. Tomorrow")
    temperature_c: float = Field(description="Forecast temperature in Celsius")
    condition: str = Field(description="Forecast weather condition")
    humidity: int = Field(description="Forecast humidity percentage")
    wind_speed: float = Field(description="Forecast wind speed in km/h")


class WeatherReport(BaseModel):
    city: str = Field(description="Name of the city")
    temperature_c: float = Field(description="Current temperature in Celsius")
    condition: str = Field(description="Current weather condition")
    humidity: int = Field(description="Humidity percentage")
    wind_speed: float = Field(description="Wind speed in km/h")
    forecast_days: int = Field(description="Number of days to forecast")
    forecast: list[DailyForecast] = Field(description="Forecast for the next few days")
    weather_summary: str = Field(description="Short human-friendly summary of the weather")


# 2. Define the tool schema for the LLM
weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Fetch the current weather for a given city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The name of the city, e.g. Tokyo",
            },
        },
        "required": ["city"],
    },
}


# 3. Implement the tool function using the free Open-Meteo API (no API key needed)
WMO_CONDITIONS = {
    0: "Clear",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    80: "Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
}


def _fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_weather(city: str) -> dict:
    """Fetch live current weather and 3-day forecast from Open-Meteo."""
    geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
        {"name": city, "count": 1}
    )
    geo = _fetch_json(geo_url)
    results = geo.get("results")
    if not results:
        return {"error": f"City '{city}' not found."}

    place = results[0]
    forecast_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "daily": (
                "weather_code,temperature_2m_max,relative_humidity_2m_mean,wind_speed_10m_max"
            ),
            "forecast_days": 4,
            "timezone": "auto",
        }
    )
    data = _fetch_json(forecast_url)
    cur = data["current"]
    daily = data["daily"]

    forecast = [
        {
            "day": daily["time"][i],
            "temperature_c": daily["temperature_2m_max"][i],
            "condition": WMO_CONDITIONS.get(daily["weather_code"][i], "Cloudy"),
            "humidity": int(daily["relative_humidity_2m_mean"][i]),
            "wind_speed": daily["wind_speed_10m_max"][i],
        }
        for i in range(1, len(daily["time"]))
    ]

    return {
        "city": f"{place['name']}, {place.get('country', '')}".strip(", "),
        "temperature_c": cur["temperature_2m"],
        "condition": WMO_CONDITIONS.get(cur["weather_code"], "Cloudy"),
        "humidity": int(cur["relative_humidity_2m"]),
        "wind_speed": cur["wind_speed_10m"],
        "forecast": forecast,
    }


def display_weather(report: WeatherReport) -> None:
    console.print()

    current_panel = Panel(
        f"[bold cyan]{report.city}[/bold cyan]\n"
        f"[bold yellow]{report.temperature_c:.1f}°C[/bold yellow]  •  "
        f"[bold white]{report.condition}[/bold white]\n"
        f"[dim]Humidity:[/dim] [bold blue]{report.humidity}%[/bold blue]   "
        f"[dim]Wind:[/dim] [bold green]{report.wind_speed:.1f} km/h[/bold green]",
        title="🌤️  Current Weather",
        border_style="cyan",
    )
    summary_panel = Panel(
        report.weather_summary,
        title="📝 Summary",
        border_style="green",
    )

    top_grid = Table.grid(expand=True, padding=(0, 1))
    top_grid.add_column(ratio=1)
    top_grid.add_column(ratio=2)
    top_grid.add_row(current_panel, summary_panel)
    console.print(top_grid)

    if report.forecast:
        console.print(f"\n[bold magenta]📅 {report.forecast_days}-Day Forecast[/bold magenta]")
        cards = [
            Panel(
                f"[bold yellow]{day.temperature_c:.1f}°C[/bold yellow]\n"
                f"[white]{day.condition}[/white]\n"
                f"[dim]💧 {day.humidity}%  💨 {day.wind_speed:.1f} km/h[/dim]",
                title=f"[bold cyan]{day.day}[/bold cyan]",
                border_style="magenta",
            )
            for day in report.forecast
        ]
        console.print(Columns(cards, equal=True, expand=True))


def run(city: str | None = None) -> WeatherReport:
    client = genai.Client()

    prompt = (
        f"Get the current weather for {city}."
        if city
        else "Pick a random city in the world and get its current weather."
    )

    with console.status(
        f"[bold green]Fetching weather with {MODEL_ID}...[/bold green]",
        spinner="dots",
    ) as status:
        # Step 1: Ask the model to call get_weather
        interaction = client.interactions.create(
            model=MODEL_ID,
            input=prompt,
            tools=[weather_tool],
            response_format=WeatherReport.model_json_schema(),
        )

        # Step 2: Execute any requested tool calls and send results back
        while True:
            tool_results = []
            for step in interaction.steps:
                if step.type == "function_call" and step.name == "get_weather":
                    console.log(
                        f"[dim]Tool called:[/dim] [cyan]{step.name}({step.arguments})[/cyan]"
                    )
                    status.update(
                        f"[bold yellow]Running {step.name}({step.arguments})...[/bold yellow]"
                    )
                    result = get_weather(**step.arguments)
                    tool_results.append(
                        {
                            "type": "function_result",
                            "name": step.name,
                            "call_id": step.id,
                            "result": json.dumps(result),
                        }
                    )

            if not tool_results:
                break

            status.update(
                f"[bold green]Generating structured report with {MODEL_ID}...[/bold green]"
            )
            interaction = client.interactions.create(
                model=MODEL_ID,
                previous_interaction_id=interaction.id,
                input=tool_results,
                response_format=WeatherReport.model_json_schema(),
            )

    # Step 3: Validate the final JSON into the Pydantic model
    return WeatherReport.model_validate_json(interaction.output_text)


if __name__ == "__main__":
    console.print(
        Panel.fit(
            f"[bold white]Tool-Calling Weather Lookup[/bold white] [dim]({MODEL_ID})[/dim]",
            title="🌍 Weather App",
            border_style="bright_blue",
        )
    )
    city = (
        " ".join(sys.argv[1:]).strip()
        or Prompt.ask(
            "[bold cyan]Enter a city[/bold cyan] [dim](leave blank for random)[/dim]",
            default="",
        ).strip()
    )
    report = run(city or None)
    display_weather(report)
