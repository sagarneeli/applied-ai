import os
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.tree import Tree

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_ID = "gemini-3.5-flash-lite"
console = Console()


class DailyPlan(BaseModel):
    day: int
    activities: List[str]


class TravelItenary(BaseModel):
    destination: str
    trip_duration_days: int
    budget_category: str
    top_attractions: List[str]
    daily_plan: List[DailyPlan]


def display_itinerary(itinerary: TravelItenary) -> None:
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]{itinerary.destination}[/bold cyan]\n"
            f"[dim]Duration:[/dim] [bold]{itinerary.trip_duration_days} days[/bold]   "
            f"[dim]Budget:[/dim] [bold green]{itinerary.budget_category}[/bold green]",
            title="✈️  Travel Itinerary",
            border_style="cyan",
        )
    )

    tree = Tree(f"🌍 [bold cyan]{itinerary.destination}[/bold cyan]")

    attractions_branch = tree.add("⭐ [bold yellow]Top Attractions[/bold yellow]")
    for attraction in itinerary.top_attractions:
        attractions_branch.add(attraction)

    plan_branch = tree.add("📅 [bold magenta]Daily Plan[/bold magenta]")
    for plan in itinerary.daily_plan:
        day_branch = plan_branch.add(f"[bold cyan]Day {plan.day}[/bold cyan]")
        for activity in plan.activities:
            day_branch.add(activity)

    console.print(tree)


if __name__ == "__main__":
    console.print(
        Panel.fit(
            f"[bold white]Plan your next trip with Gemini[/bold white] [dim]({MODEL_ID})[/dim]",
            title="🌍 Travel Itinerary Planner",
            border_style="bright_blue",
        )
    )

    client = genai.Client(api_key=GEMINI_API_KEY)
    destination = Prompt.ask("[bold cyan]Destination[/bold cyan]")
    trip_duration_days = IntPrompt.ask(
        "[bold cyan]Trip duration (days)[/bold cyan]", default=5
    )
    budget_category = Prompt.ask(
        "[bold cyan]Budget category[/bold cyan]",
        choices=["Budget", "Mid-range", "Luxury", "All"],
        default="All",
    )

    prompt = f"""
    Create a travel itinerary for the following:
    Destination: {destination}
    Trip Duration: {trip_duration_days} days
    Budget Category: {budget_category}

    Return the response strictly in the following JSON format:
    {TravelItenary.model_json_schema()}
    """
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=TravelItenary.model_json_schema(),
    )

    with console.status(
        f"[bold green]Generating itinerary with {MODEL_ID}...[/bold green]",
        spinner="dots",
    ):
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=config,
        )

    itinerary = TravelItenary.model_validate_json(response.text)
    display_itinerary(itinerary)
