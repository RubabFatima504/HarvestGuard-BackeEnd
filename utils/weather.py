"""Open-Meteo API se weather data laata hai — FREE, no API key"""
import requests


def get_current_weather(lat: float, lng: float) -> dict:
    """
    Returns: {"temperature": 38.5, "humidity": 45, "apparent_temp": 42.1}
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature"
        f"&timezone=Asia/Karachi"
    )
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        current = data.get("current", {})
        return {
            "temperature": current.get("temperature_2m", 35.0),
            "humidity": current.get("relative_humidity_2m", 50),
            "apparent_temp": current.get("apparent_temperature", 38.0),
        }
    except Exception as e:
        print(f"[WARNING] Weather API error: {e}, using defaults")
        return {"temperature": 35.0, "humidity": 50, "apparent_temp": 38.0}


def get_forecast(lat: float, lng: float, days: int = 7) -> list:
    """7 din ka forecast — hourly temperature"""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        f"&hourly=temperature_2m,relative_humidity_2m"
        f"&forecast_days={days}&timezone=Asia/Karachi"
    )
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        humids = hourly.get("relative_humidity_2m", [])
        
        forecast = []
        for i in range(0, len(times), 24):  # Daily average (har 24 hours)
            day_temps = temps[i:i+24]
            day_humids = humids[i:i+24]
            if day_temps:
                forecast.append({
                    "date": times[i][:10],
                    "avg_temp": round(sum(day_temps) / len(day_temps), 1),
                    "max_temp": round(max(day_temps), 1),
                    "avg_humidity": round(sum(day_humids) / len(day_humids), 1),
                })
        return forecast
    except Exception:
        return []