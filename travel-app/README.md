# Travel Itinerary Generator (Structured LLM Output with Pydantic)

A practice exercise demonstrating how to use an LLM (Google Gemini) with **Pydantic** in Python to produce validated, structured JSON output adhering to a fixed schema, rendered as a clean terminal UI with **Rich**.

## Practice Prompt

> Use an LLM with Pydantic in Python to generate a structured travel itinerary in JSON with fields. No other input, take a random source city and destination city, and create this using the model's own knowledge. The aim is to understand how to use Pydantic to create structured output adhering to a fixed schema:
>
> - `destination: str`
> - `trip_duration_days: int`
> - `budget_category: str`
> - `top_attractions: list[str]`
> - `daily_plan: list[{day: int, activities: list[str]}]`

## Schema

Defined in [`travel-itenary.py`](./travel-itenary.py) using nested Pydantic `BaseModel` classes:

```python
class DailyPlan(BaseModel):
    day: int
    activities: List[str]

class TravelItenary(BaseModel):
    destination: str
    trip_duration_days: int
    budget_category: str
    top_attractions: List[str]
    daily_plan: List[DailyPlan]
```

The schema is passed to Gemini via `response_mime_type="application/json"` and `response_schema=TravelItenary.model_json_schema()`, and the response is validated back into a `TravelItenary` instance using `TravelItenary.model_validate_json(response.text)`.

## Setup

1. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv pip install google-genai pydantic python-dotenv rich
   ```

3. Add your Gemini API key in a `.env` file in this directory:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

```bash
python travel-itenary.py
```

Enter a destination, trip duration (in days), and budget category (`Budget`, `Mid-range`, `Luxury`, or `All`). The app queries Gemini for a schema-constrained JSON response, validates it with Pydantic, and displays the itinerary in styled panels and a day-by-day table.
