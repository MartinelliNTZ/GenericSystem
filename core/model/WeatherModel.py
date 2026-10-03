# -*- coding: utf-8 -*-
"""
WeatherModel — Dataclass de dados climáticos
==============================================
Representa os dados retornados pela API WeatherStack.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WeatherData:
    """Dados climáticos de uma localização."""

    location: str
    region: str
    country: str
    temperature: float
    feelslike: float
    weather_desc: str
    weather_icon: str
    wind_speed: float
    wind_dir: str
    pressure: int
    precip: float
    humidity: int
    cloudcover: int
    uv_index: float
    visibility: int
    sunrise: str
    sunset: str
    air_index: str

    @classmethod
    def from_api_response(cls, data: dict) -> "WeatherData":
        """Cria instância a partir do JSON da WeatherStack."""
        location = data.get("location", {})
        current = data.get("current", {})
        astro = current.get("astro", {}) if "astro" in current else data.get("astro", {})
        air_quality = current.get("air_quality", {})

        weather_icon = current.get("weather_icons", [""])[0] if current.get("weather_icons") else ""
        weather_icon = weather_icon.replace("\\/", "/")

        return cls(
            location=location.get("name", "N/A"),
            region=location.get("region", "N/A"),
            country=location.get("country", "N/A"),
            temperature=current.get("temperature", 0),
            feelslike=current.get("feelslike", 0),
            weather_desc=current.get("weather_descriptions", ["N/A"])[0] if current.get("weather_descriptions") else "N/A",
            weather_icon=weather_icon,
            wind_speed=current.get("wind_speed", 0),
            wind_dir=current.get("wind_dir", "N/A"),
            pressure=current.get("pressure", 0),
            precip=current.get("precip", 0),
            humidity=current.get("humidity", 0),
            cloudcover=current.get("cloudcover", 0),
            uv_index=current.get("uv_index", 0),
            visibility=current.get("visibility", 0),
            sunrise=astro.get("sunrise", "N/A"),
            sunset=astro.get("sunset", "N/A"),
            air_index=str(air_quality.get("us-epa-index", air_quality.get("gb-defra-index", "N/A"))),
        )