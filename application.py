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

class HouseholdSize(IntEnum):
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5
    six = 6

class GroceryItem(BaseModel):
    name: str
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)

class GroceryRequest(BaseModel):
    household_size: HouseholdSize
    grocery_logs: list[GroceryItem]
    budget: float

# --- Internal Helper Endpoints ---

@app.get("/classmate-api")
def get_classmate_data():
    """Mock endpoint to provide discount and tip data"""
    return {"discount": 5.0, "tip": 2.5}

# --- Main Endpoints ---

@app.post("/predict")
def predict_food_usage(data: GroceryRequest):
    try:
        # 🧮 Total cost calculation
        total_cost = sum(item.price * item.quantity for item in data.grocery_logs)

        # 🌦️ Call weather API
        # Using a timeout is best practice for external calls
        weather_res = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=28.6&longitude=77.2&current_weather=true",
            timeout=5
        )
        weather_res.raise_for_status()
        weather = weather_res.json()
        temperature = weather["current_weather"]["temperature"]

        # 🤝 Call classmate API
        # NOTE: In production, use a full URL or a helper function instead of an HTTP call to self.
        # For local testing, ensure your server is running on port 8000.
        try:
            classmate = get_classmate_data()
        except Exception:
            # Fallback if the internal call fails
            classmate = {"discount": 0, "tip": 0}

        discount = classmate.get("discount", 0)
        tip = classmate.get("tip", 0)

        # 🧠 Spoilage logic
        spoilage = "low"
        if temperature > 30:
            spoilage = "high"
        elif temperature > 20:
            spoilage = "medium"

        # 📤 Return response
        return {
            "behavior_type": "normal",
            "temperature": temperature,
            "humidity": 50,
            "spoilage_risk": spoilage,
            "estimated_food_days": max(1, int(7 - data.household_size.value)),
            "budget_warning": total_cost > data.budget,
            "recommendation": "Adjust spending or quantities if needed",
            "discount": discount,
            "extra_tip": tip
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html") as f:
        return f.read()
