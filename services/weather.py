import os
import time
from typing import Any, Dict, Optional

import requests


class WeatherService:
    """Simple WeatherAPI wrapper with caching and graceful fallbacks."""

    API_URL = "https://api.weatherapi.com/v1/forecast.json"
    DEFAULT_LOCATION = "Kigali,Rwanda"
    CACHE_TTL_SECONDS = 600  # 10 minutes

    def __init__(self) -> None:
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0

    @staticmethod
    def _api_key() -> str:
        return os.environ.get("NEXT_PUBLIC_WEATHER_API_KEY", "d8ed3c5fc2aea1dcdf66896ebaf9195b")

    def invalidate(self) -> None:
        self._cache = None
        self._cache_timestamp = 0.0

    def get_weather(self, force_refresh: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force_refresh and self._cache and (now - self._cache_timestamp) < self.CACHE_TTL_SECONDS:
            return self._cache

        key = self._api_key()
        if not key:
            return {
                "error": "Weather API key is missing. Set NEXT_PUBLIC_WEATHER_API_KEY.",
                "updated_at": None,
            }

        params = {
            "key": key,
            "q": self.DEFAULT_LOCATION,
            "days": 5,
            "aqi": "yes",
            "alerts": "yes",
        }

        try:
            response = requests.get(self.API_URL, params=params, timeout=8)
            response.raise_for_status()
            payload = response.json()
            data = self._normalize(payload)
            self._cache = data
            self._cache_timestamp = now
            return data
        except requests.RequestException as exc:
            error_payload = {
                "error": f"Unable to reach weather service: {exc}",
                "updated_at": None,
            }
            self._cache = error_payload
            self._cache_timestamp = now
            return error_payload

    @staticmethod
    def _normalize(payload: Dict[str, Any]) -> Dict[str, Any]:
        location = payload.get("location", {})
        current = payload.get("current", {})
        forecast_days = payload.get("forecast", {}).get("forecastday", [])
        alerts = payload.get("alerts", {}).get("alert", [])

        forecast_data = []
        for item in forecast_days:
            day = item.get("day", {})
            forecast_data.append(
                {
                    "date": item.get("date"),
                    "condition": day.get("condition", {}).get("text"),
                    "icon": day.get("condition", {}).get("icon"),
                    "max_temp_c": day.get("maxtemp_c"),
                    "min_temp_c": day.get("mintemp_c"),
                    "avg_humidity": day.get("avghumidity"),
                    "daily_chance_of_rain": day.get("daily_chance_of_rain"),
                }
            )

        alerts_data = [
            {
                "headline": alert.get("headline"),
                "severity": alert.get("severity"),
                "areas": alert.get("areas"),
                "category": alert.get("category"),
                "note": alert.get("note"),
                "effective": alert.get("effective"),
                "expires": alert.get("expires"),
            }
            for alert in alerts
        ]

        return {
            "error": None,
            "updated_at": payload.get("current", {}).get("last_updated"),
            "location": {
                "name": location.get("name"),
                "region": location.get("region"),
                "country": location.get("country"),
                "lat": location.get("lat"),
                "lon": location.get("lon"),
                "localtime": location.get("localtime"),
            },
            "current": {
                "temp_c": current.get("temp_c"),
                "feelslike_c": current.get("feelslike_c"),
                "condition": current.get("condition", {}).get("text"),
                "icon": current.get("condition", {}).get("icon"),
                "wind_kph": current.get("wind_kph"),
                "wind_dir": current.get("wind_dir"),
                "humidity": current.get("humidity"),
                "cloud": current.get("cloud"),
                "precip_mm": current.get("precip_mm"),
                "pressure_mb": current.get("pressure_mb"),
                "uv": current.get("uv"),
                "gust_kph": current.get("gust_kph"),
            },
            "forecast": forecast_data,
            "alerts": alerts_data,
            "aqi": current.get("air_quality"),
        }


weather_service = WeatherService()

