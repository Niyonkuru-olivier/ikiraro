"""
services/weather.py
WeatherAPI wrapper with caching, graceful fallbacks, and Vercel-safe imports.
Place this file at:  services/weather.py
"""

import os
import time
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Safe import of requests — gives a clear error on Vercel if still missing
# ---------------------------------------------------------------------------
try:
    import requests
    _REQUESTS_AVAILABLE = True
except ModuleNotFoundError:
    _REQUESTS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Safe import of ThreadPoolExecutor (stdlib — always available)
# ---------------------------------------------------------------------------
from concurrent.futures import ThreadPoolExecutor, as_completed


# ---------------------------------------------------------------------------
# Fallback payload used whenever we cannot reach the weather API
# ---------------------------------------------------------------------------
_UNAVAILABLE: Dict[str, Any] = {
    "error": "Weather service is currently unavailable.",
    "updated_at": None,
    "location": None,
    "current": None,
    "forecast": [],
    "alerts": [],
    "aqi": None,
    "districts": [],
    "districts_error": "Weather service is currently unavailable.",
    "districts_updated_at": None,
}


class WeatherService:
    """Simple WeatherAPI wrapper with in-process caching and graceful fallbacks."""

    API_URL          = "https://api.weatherapi.com/v1/forecast.json"
    DISTRICT_API_URL = "https://api.weatherapi.com/v1/current.json"
    DEFAULT_LOCATION = "Kigali,Rwanda"

    # Cache TTLs
    CACHE_TTL_SECONDS         = 600   # 10 minutes  – main forecast
    DISTRICT_CACHE_TTL_SECONDS = 1800  # 30 minutes – district snapshots

    MAX_DISTRICT_WORKERS = 8

    RWANDA_DISTRICTS: List[Dict[str, str]] = [
        {"name": "Nyarugenge",  "query": "Nyarugenge,Rwanda"},
        {"name": "Gasabo",      "query": "Gasabo,Rwanda"},
        {"name": "Kicukiro",    "query": "Kicukiro,Rwanda"},
        {"name": "Bugesera",    "query": "Bugesera,Rwanda"},
        {"name": "Gisagara",    "query": "Gisagara,Rwanda"},
        {"name": "Huye",        "query": "Huye,Rwanda"},
        {"name": "Kamonyi",     "query": "Kamonyi,Rwanda"},
        {"name": "Muhanga",     "query": "Muhanga,Rwanda"},
        {"name": "Nyamagabe",   "query": "Nyamagabe,Rwanda"},
        {"name": "Nyanza",      "query": "Nyanza,Rwanda"},
        {"name": "Nyaruguru",   "query": "Nyaruguru,Rwanda"},
        {"name": "Ruhango",     "query": "Ruhango,Rwanda"},
        {"name": "Burera",      "query": "Burera,Rwanda"},
        {"name": "Gakenke",     "query": "Gakenke,Rwanda"},
        {"name": "Gicumbi",     "query": "Gicumbi,Rwanda"},
        {"name": "Musanze",     "query": "Musanze,Rwanda"},
        {"name": "Rulindo",     "query": "Rulindo,Rwanda"},
        {"name": "Gatsibo",     "query": "Gatsibo,Rwanda"},
        {"name": "Kayonza",     "query": "Kayonza,Rwanda"},
        {"name": "Kirehe",      "query": "Kirehe,Rwanda"},
        {"name": "Ngoma",       "query": "Ngoma,Rwanda"},
        {"name": "Nyagatare",   "query": "Nyagatare,Rwanda"},
        {"name": "Rwamagana",   "query": "Rwamagana,Rwanda"},
        {"name": "Karongi",     "query": "Karongi,Rwanda"},
        {"name": "Ngororero",   "query": "Ngororero,Rwanda"},
        {"name": "Nyabihu",     "query": "Nyabihu,Rwanda"},
        {"name": "Nyamasheke",  "query": "Nyamasheke,Rwanda"},
        {"name": "Rubavu",      "query": "Rubavu,Rwanda"},
        {"name": "Rusizi",      "query": "Rusizi,Rwanda"},
        {"name": "Rutsiro",     "query": "Rutsiro,Rwanda"},
    ]

    def __init__(self) -> None:
        self._cache: Optional[Dict[str, Any]]          = None
        self._cache_timestamp: float                    = 0.0
        self._district_cache: Optional[Dict[str, Any]] = None
        self._district_cache_timestamp: float          = 0.0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _api_key() -> str:
        return (
            os.environ.get("WEATHER_API")
            or os.environ.get("NEXT_PUBLIC_WEATHER_API_KEY")
            or "d8ed3c5fc2aea1dcdf66896ebaf9195b"
        )

    def invalidate(self) -> None:
        self._cache                    = None
        self._cache_timestamp          = 0.0
        self._district_cache           = None
        self._district_cache_timestamp = 0.0

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def get_weather(self, force_refresh: bool = False) -> Dict[str, Any]:
        # If requests is not installed, return a clean fallback immediately
        if not _REQUESTS_AVAILABLE:
            return {
                **_UNAVAILABLE,
                "error": (
                    "The 'requests' package is not installed. "
                    "Add  requests==2.32.3  to requirements.txt and redeploy."
                ),
            }

        now = time.time()
        if (
            not force_refresh
            and self._cache
            and (now - self._cache_timestamp) < self.CACHE_TTL_SECONDS
        ):
            return self._cache

        key = self._api_key()
        if not key:
            return {
                **_UNAVAILABLE,
                "error": (
                    "Weather API key is missing. "
                    "Set WEATHER_API in your Vercel environment variables."
                ),
            }

        params = {
            "key":    key,
            "q":      self.DEFAULT_LOCATION,
            "days":   5,
            "aqi":    "yes",
            "alerts": "yes",
        }

        try:
            response = requests.get(self.API_URL, params=params, timeout=8)
            response.raise_for_status()
            payload = response.json()
            data    = self._normalize(payload)

            district_bundle         = self._get_rwanda_district_weather(key, force_refresh=force_refresh)
            data["districts"]          = district_bundle.get("districts", [])
            data["districts_error"]    = district_bundle.get("error")
            data["districts_updated_at"] = district_bundle.get("updated_at")

            self._cache           = data
            self._cache_timestamp = now
            return data

        except Exception as exc:
            friendly_error  = self._format_request_error(exc)
            district_bundle = self._cached_district_bundle()
            error_payload   = {
                **_UNAVAILABLE,
                "error":                  friendly_error,
                "districts":              district_bundle.get("districts", []),
                "districts_error":        district_bundle.get("error"),
                "districts_updated_at":   district_bundle.get("updated_at"),
            }
            # Still cache the error so we don't hammer the API
            self._cache           = error_payload
            self._cache_timestamp = now
            return error_payload

    # ------------------------------------------------------------------
    # Normalise raw WeatherAPI payload → clean dict
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize(payload: Dict[str, Any]) -> Dict[str, Any]:
        location      = payload.get("location", {})
        current       = payload.get("current", {})
        forecast_days = payload.get("forecast", {}).get("forecastday", [])
        alerts        = payload.get("alerts", {}).get("alert", [])

        forecast_data = [
            {
                "date":                  item.get("date"),
                "condition":             item.get("day", {}).get("condition", {}).get("text"),
                "icon":                  item.get("day", {}).get("condition", {}).get("icon"),
                "max_temp_c":            item.get("day", {}).get("maxtemp_c"),
                "min_temp_c":            item.get("day", {}).get("mintemp_c"),
                "avg_humidity":          item.get("day", {}).get("avghumidity"),
                "daily_chance_of_rain":  item.get("day", {}).get("daily_chance_of_rain"),
            }
            for item in forecast_days
        ]

        alerts_data = [
            {
                "headline":  alert.get("headline"),
                "severity":  alert.get("severity"),
                "areas":     alert.get("areas"),
                "category":  alert.get("category"),
                "note":      alert.get("note"),
                "effective": alert.get("effective"),
                "expires":   alert.get("expires"),
            }
            for alert in alerts
        ]

        return {
            "error":      None,
            "updated_at": current.get("last_updated"),
            "location": {
                "name":      location.get("name"),
                "region":    location.get("region"),
                "country":   location.get("country"),
                "lat":       location.get("lat"),
                "lon":       location.get("lon"),
                "localtime": location.get("localtime"),
            },
            "current": {
                "temp_c":      current.get("temp_c"),
                "feelslike_c": current.get("feelslike_c"),
                "condition":   current.get("condition", {}).get("text"),
                "icon":        current.get("condition", {}).get("icon"),
                "wind_kph":    current.get("wind_kph"),
                "wind_dir":    current.get("wind_dir"),
                "humidity":    current.get("humidity"),
                "cloud":       current.get("cloud"),
                "precip_mm":   current.get("precip_mm"),
                "pressure_mb": current.get("pressure_mb"),
                "uv":          current.get("uv"),
                "gust_kph":    current.get("gust_kph"),
            },
            "forecast": forecast_data,
            "alerts":   alerts_data,
            "aqi":      current.get("air_quality"),
        }

    # ------------------------------------------------------------------
    # District weather helpers
    # ------------------------------------------------------------------
    def _fetch_district_snapshot(self, key: str, district: Dict[str, str]) -> Dict[str, Any]:
        query = district.get("query") or f"{district['name']},Rwanda"
        try:
            response = requests.get(
                self.DISTRICT_API_URL,
                params={"key": key, "q": query},
                timeout=6,
            )
            response.raise_for_status()
            payload   = response.json()
            current   = payload.get("current", {}) or {}
            condition = current.get("condition", {}) or {}
            icon      = condition.get("icon")
            if icon and isinstance(icon, str) and icon.startswith("//"):
                icon = f"https:{icon}"

            return {
                "name":         district["name"],
                "temp_c":       current.get("temp_c"),
                "feelslike_c":  current.get("feelslike_c"),
                "condition":    condition.get("text"),
                "icon":         icon,
                "humidity":     current.get("humidity"),
                "wind_kph":     current.get("wind_kph"),
                "last_updated": current.get("last_updated"),
            }
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            return {
                "name":        district["name"],
                "error":       str(exc),
                "status_code": status,
            }

    def _get_rwanda_district_weather(
        self, key: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        if not key:
            return {
                "error":      "Weather API key is missing for district lookups.",
                "districts":  [],
                "updated_at": None,
            }

        now = time.time()
        if (
            not force_refresh
            and self._district_cache
            and (now - self._district_cache_timestamp) < self.DISTRICT_CACHE_TTL_SECONDS
        ):
            return self._district_cache

        order_map = {d["name"]: i for i, d in enumerate(self.RWANDA_DISTRICTS)}
        results:  List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []

        # Probe first district synchronously to catch auth errors early
        baseline = self._fetch_district_snapshot(key, self.RWANDA_DISTRICTS[0])
        if baseline.get("error"):
            if baseline.get("status_code") in (401, 403):
                payload = self._auth_error_payload()
                self._district_cache           = payload
                self._district_cache_timestamp = now
                return payload
            failures.append(baseline)
        else:
            results.append(baseline)

        remaining = self.RWANDA_DISTRICTS[1:]
        if remaining:
            with ThreadPoolExecutor(
                max_workers=min(self.MAX_DISTRICT_WORKERS, len(remaining))
            ) as executor:
                futures = {
                    executor.submit(self._fetch_district_snapshot, key, d): d
                    for d in remaining
                }
                for future in as_completed(futures):
                    result = future.result()
                    if result.get("error"):
                        failures.append(result)
                    else:
                        results.append(result)

        results.sort(key=lambda item: order_map.get(item["name"], 0))

        payload: Dict[str, Any] = {
            "error":      None,
            "districts":  results,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(now)),
        }
        if failures:
            payload["error"]    = (
                f"Partial Rwanda district data: {len(failures)} location(s) unavailable."
            )
            payload["failures"] = failures

        self._district_cache           = payload
        self._district_cache_timestamp = now
        return payload

    # ------------------------------------------------------------------
    # Small private helpers
    # ------------------------------------------------------------------
    def _auth_error_payload(self) -> Dict[str, Any]:
        return {
            "error": (
                "Weather provider rejected credentials. "
                "Update WEATHER_API in your Vercel environment variables "
                "with a valid WeatherAPI.com key."
            ),
            "districts":  [],
            "updated_at": None,
        }

    def _cached_district_bundle(self) -> Dict[str, Any]:
        return self._district_cache or {
            "error":      "District climate feed is currently unavailable.",
            "districts":  [],
            "updated_at": None,
        }

    @staticmethod
    def _format_request_error(exc: Exception) -> str:
        response = getattr(exc, "response", None)
        status   = getattr(response, "status_code", None)

        if status in (401, 403):
            return (
                "Weather provider rejected credentials. "
                "Update WEATHER_API in your environment with a valid WeatherAPI key."
            )
        if status == 429:
            return "Weather provider rate limit exceeded. Please wait a moment and try again."
        return f"Unable to reach weather service: {exc}"


# Module-level singleton — imported by app.py as:
#   from services.weather import weather_service
weather_service = WeatherService()