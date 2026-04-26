from .toolkit import tool, toolset
import requests

def city_to_coords(city):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": city, "count": 1})
    data = r.json()

    if data.get("results"):
        loc = data["results"][0]
        return loc["latitude"], loc["longitude"]



def get_weather_summary(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation",
            "cloud_cover",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m"
        ]
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()["current"]

    return {
        "temperature_c": data["temperature_2m"],
        "feels_like_c": data["apparent_temperature"],
        "humidity_percent": data["relative_humidity_2m"],
        "wind": {
            "speed_kmh": data["wind_speed_10m"],
            "direction_deg": data["wind_direction_10m"],
            "gusts_kmh": data["wind_gusts_10m"]
        },
        "precipitation_mm": data["precipitation"],
        "cloud_cover_percent": data["cloud_cover"],
        "pressure_hpa": data["surface_pressure"]
    }



@toolset
class WeatherTool():
    @tool
    def getInformation(self, cityname):
        """Input a city name from anywhere in the world and get weather-related information back. 
        Example:
        {
            "temperature_c": 14.1,
            "feels_like_c": 13.4,
            "humidity_percent": 72,
            "wind": {
                "speed_kmh": 12.6,
                "direction_deg": 210,
                "gusts_kmh": 18.4
            },
            "precipitation_mm": 0.0,
            "cloud_cover_percent": 65,
            "pressure_hpa": 1013.2
        }"""

        cords, cords2 = city_to_coords(cityname.lower())

        return {'return': str(get_weather_summary(cords, cords2)), 'note': ["Data is pulled from the 'open-meteo' API and may be inaccurate."]}
