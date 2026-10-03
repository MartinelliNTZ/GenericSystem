# -*- coding: utf-8 -*-
"""
WeatherFetchStep — Step for fetching weather data
==================================================
Orchestrates the weather data pipeline:
1. Fetches current weather from WeatherStack API (or reads cache)
2. Stores WeatherData in context

This is a TRANSFORM step (advance_input=False, it just fetches data).
"""

from __future__ import annotations

from typing import Any

from ..ExecutionContext import ExecutionContext
from ..BaseStep import BaseStep
from ..task.WeatherFetchTask import WeatherFetchTask


class WeatherFetchStep(BaseStep):
    """
    Step that fetches weather data.

    No parameters needed — output dir and API key are resolved internally.
    """

    subfolder = ""
    _advance_input = False

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        return "weather_fetch"

    def create_task(self, context: ExecutionContext) -> WeatherFetchTask:
        return WeatherFetchTask()

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set_result("weather_fetch", result)

            weather_data = result.get("weather_data")
            logger = self.get_logger(context)
            if weather_data:
                logger.info(
                    "Weather fetch completed successfully",
                    code="WEATHER_STEP_DONE",
                    location=f"{weather_data.location}, {weather_data.region}",
                    temperature=weather_data.temperature,
                )
            else:
                logger.info(
                    "Weather fetch completed (no data)",
                    code="WEATHER_STEP_DONE_EMPTY",
                )

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)
        logger = self.get_logger(context)
        logger.error(
            "Weather fetch step failed",
            code="WEATHER_STEP_ERR",
            error=str(exception),
        )