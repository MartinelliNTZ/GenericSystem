# -*- coding: utf-8 -*-
"""
WeatherFetchTask — Task for fetching weather data from WeatherStack API
=======================================================================
Fetches current weather, saves to system temp folder with daily cache.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests

from core.config.ApiKeys import ApiKeys
from core.model.WeatherModel import WeatherData
from ..BaseTask import BaseTask
from utils.ExplorerUtils import ExplorerUtils
from utils.JsonUtil import JsonUtil


class WeatherFetchTask(BaseTask):
    """
    Task that fetches weather data from WeatherStack API.

    Cache: saves raw JSON to temp/aetheris/weather/weather_YYYYMMDD.json.
    If today's file exists, reads cache instead of calling API.
    """

    _API_URL = "https://api.weatherstack.com/current"
    _TIMEOUT = 30

    def __init__(self):
        super().__init__(description="Weather data fetch")
        self._output_dir = ExplorerUtils.get_system_temp_dir(
            subfolder="aetheris/weather",
            tool_key="WeatherFetch",
        )

    @property
    def output_dir(self) -> str:
        return self._output_dir

    def _run(self) -> bool:
        try:
            logger = self.get_logger()

            now = datetime.now()
            today_compact = now.strftime("%Y%m%d")
            out_dir = Path(self._output_dir)
            cache_file = out_dir / f"weather_{today_compact}.json"

            # ── Check cache ────────────────────────────────────────
            if cache_file.exists():
                logger.info(
                    "Weather cache hit, reading cached file",
                    code="WEATHER_CACHE_HIT",
                    path=str(cache_file),
                )
                payload = JsonUtil.read_json(str(cache_file), tool_key="WeatherFetch")
            else:
                logger.info(
                    "No cache found, fetching from WeatherStack API",
                    code="WEATHER_FETCH_START",
                )
                payload = self._fetch()
                JsonUtil.write_json(str(cache_file), payload, tool_key="WeatherFetch")
                logger.info(
                    "Weather data saved to cache",
                    code="WEATHER_CACHE_SAVED",
                    path=str(cache_file),
                )

            # ── Parse data ─────────────────────────────────────────
            weather_data = WeatherData.from_api_response(payload)

            logger.info(
                "Weather fetch complete",
                code="WEATHER_DONE",
                location=f"{weather_data.location}, {weather_data.region}",
                temperature=weather_data.temperature,
            )

            self.result = {
                "weather_data": weather_data,
                "cache_path": str(cache_file),
            }
            return True

        except Exception as e:
            self.exception = RuntimeError(f"Weather fetch failed: {e}")
            return False

    def _fetch(self) -> Dict[str, Any]:
        """Fetch current weather from WeatherStack API."""
        params = {
            "access_key": ApiKeys.WEATHER_API_KEY,
            "query": "-10.1840,-48.3336",
        }
        resp = requests.get(self._API_URL, params=params, timeout=self._TIMEOUT)
        resp.raise_for_status()
        return resp.json()