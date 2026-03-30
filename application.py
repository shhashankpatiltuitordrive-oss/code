# Food Consumption Predictor Backend
# This FastAPI application processes grocery data, integrates multiple APIs,
# and returns predictions related to food usage, budget, and spoilage risk.

from budget_lib import calculate_budget
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from enum import IntEnum
import requests
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Required for Elastic Beanstalk
application = app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
# Enum to represent household size (1–6 members)


class HouseholdSize(IntEnum):
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5
    six = 6

# Model representing each grocery item entered by user

class GroceryItem(BaseModel):
    name: str
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)

# Request model containing all user input data

class GroceryRequest(BaseModel):
    household_size: HouseholdSize
    grocery_logs: list[GroceryItem]
    budget: float

# --- Main Endpoints ---
# Endpoint to analyze whether total grocery cost is within budget

@app.post("/budget-analysis")
def budget_analysis(data: GroceryRequest):

    # Calculate total cost of groceries


    total_cost = sum(item.price * item.quantity for item in data.grocery_logs)

    status = "within_budget"
    suggestion = "Good job managing budget"

    if total_cost > data.budget:
        status = "over_budget"
        suggestion = "Reduce quantity or choose cheaper items"

    return {
        "total_cost": total_cost,
        "status": status,
        "suggestion": suggestion
    }
# Main prediction endpoint integrating multiple services

@app.post("/predict")
def predict_food_usage(data: GroceryRequest):
    # Calculate total cost of all grocery items
    try:
        # Total cost calculation
        total_cost = sum(item.price * item.quantity for item in data.grocery_logs)

        # Weather API
        # Call public weather API to get current temperature
        weather_res = requests.get(
    "https://api.open-meteo.com/v1/forecast?latitude=53.35&longitude=-6.26&current_weather=true",
            timeout=5
        )
        print(weather_res.url)
        print(weather)
        
        weather_res.raise_for_status()
        weather = weather_res.json()
        temperature = weather["current_weather"]["temperature"]

        # Classmate API
        # Call classmate API to analyze user behaviour and usage patterns
        try:
            classmate_res = requests.post(
                "http://Screensense-api-env.eba-axpayxy8.us-east-1.elasticbeanstalk.com/api/v1/analysis/usage",
                json={
                    "userId": "user123",
                    "usageLogs": [
                        {
                            "appName": item.name,
                            "category": "other",
                            "startTime": "2025-01-15T10:00:00",
                            "endTime": "2025-01-15T11:00:00"
                        } for item in data.grocery_logs
                    ]
                },
                timeout=5
            )
            classmate_res.raise_for_status()
            classmate = classmate_res.json()
            print("Classmate response:", classmate)

            behavior = classmate.get("data", {}).get("summary", {}).get("wellnessLevel", "unknown")     
            total_minutes = classmate.get("data", {}).get("summary", {}).get("totalMinutes", 0)

            budget_data = calculate_budget(data.grocery_logs, data.budget)

# Handle errors from external API calls gracefully

        except Exception as e:
            print("Classmate API error:", str(e))
            classmate = {
    "data": {
        "summary": {
            "wellnessLevel": "unknown",
            "totalMinutes": 0
        }
    },
    "discount": 0,
    "tip": 0
}
        
            behavior = "unknown"

        discount = classmate.get("discount", 0)
        tip = classmate.get("tip", 0)

        # Spoilage logic
        spoilage = "low"
        if temperature > 30:
            spoilage = "high"
        elif temperature > 20:
            spoilage = "medium"

            

        # Response
        return {
            "behavior_type": behavior,
            "temperature": temperature,
            "humidity": 50,
            "spoilage_risk": spoilage,
            "estimated_food_days": max(1, int(7 - data.household_size.value)),
            "budget_warning": total_cost > data.budget,
            "recommendation": "Adjust spending or quantities if needed",
                "budget_status": budget_data.get("status"),
    "budget_suggestion": budget_data.get("suggestion"),
            "discount": discount,
            "extra_tip": tip,
            "api_sources": ["weather_api", "classmate_api", "budget_api"],
            "total_usage_minutes": total_minutes,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html") as f:
        return f.read()
