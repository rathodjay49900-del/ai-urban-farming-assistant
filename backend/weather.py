"""Lightweight weather provider for watering recommendations.

Uses the free Open-Meteo API (no key required) when latitude/longitude are
configured, and falls back to a deterministic mock so the app always works
offline.  Swap ``get_current_weather`` for any provider you prefer.
"""

from __future__ import annotations

import json
import urllib.request

from config import WEATHER_LAT, WEATHER_LON

_MOCK = {
    "summary": "Partly cloudy",
    "temperature_c": 27.0,
    "rain_expected": False,
    "humidity": 60,
    "source": "mock",
}

_WMO = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers",
    81: "Rain showers", 82: "Violent rain showers", 95: "Thunderstorm",
    96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def get_current_weather() -> dict:
    if not (WEATHER_LAT and WEATHER_LON):
        return dict(_MOCK)
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={WEATHER_LAT}&longitude={WEATHER_LON}"
            "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code"
            "&hourly=precipitation_probability&forecast_days=1"
        )
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        current = data.get("current", {})
        code = int(current.get("weather_code", 0))
        rain_probs = data.get("hourly", {}).get("precipitation_probability", []) or [0]
        rain_expected = code >= 51 or max(rain_probs) >= 50
        return {
            "summary": _WMO.get(code, "Unknown"),
            "temperature_c": current.get("temperature_2m"),
            "rain_expected": rain_expected,
            "humidity": current.get("relative_humidity_2m"),
            "source": "open-meteo",
        }
    except Exception:
        return dict(_MOCK)
