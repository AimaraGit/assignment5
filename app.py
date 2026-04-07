
import requests
from database import get_user, save_order

#Weather API
def get_weather(city: str) -> dict:
    url = f"https://fake-weather-api.example.com/weather?city={city}"
    response = requests.get(url, timeout=5)   
    response.raise_for_status()               
    data = response.json()
    if "temperature" not in data or "condition" not in data:
        raise ValueError(f"Invalid API response: {data}")
    return {
        "temperature": data["temperature"],
        "condition": data["condition"],  # "rain" | "sunny" | "snow"
    }

#Business Logic
def suggest_product(weather: dict) -> str:
    condition = weather.get("condition", "").lower()
    if condition == "rain":
        return "umbrella"
    elif condition == "sunny":
        return "sunglasses"
    elif condition == "snow":
        return "jacket"
    else:
        return "unknown"

def create_order(user_id: int) -> dict:
    user = get_user(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    weather = get_weather(user["city"])
    product = suggest_product(weather)
    order_id = save_order(user_id=user_id, product=product)
    return {
        "order_id": order_id,
        "user_id": user_id,
        "product": product,
        "weather": weather,
    }