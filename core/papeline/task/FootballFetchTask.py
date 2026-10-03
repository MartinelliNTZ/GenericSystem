# -*- coding: utf-8 -*-
"""
FootballFetchTask — Task for fetching football fixtures from API
=================================================================
Fetches fixtures for today and yesterday from api-football, saves to
system temp folder, filters using DictManager clubs/competitions,
and manages old file cleanup.

Uses only ExplorerUtils (for dirs) and JsonUtil (for JSON I/O).
No direct os/tempfile/shutil calls.

Output files in system temp aetheris/football/:
    - response_{today_yyyymmdd}.json         — Raw today response
    - response_{yesterday_yyyymmdd}_final.json — Raw yesterday response
    - response_{today_yyyymmdd}_filtrado.json — Filtered today
    - response_{yesterday_yyyymmdd}_final_filtrado.json — Filtered yesterday
    - old/ — Moved previous response files
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import requests

from core.config.ApiKeys import ApiKeys
from ..BaseTask import BaseTask
from utils.DictManager import DictManager
from utils.ExplorerUtils import ExplorerUtils
from utils.JsonUtil import JsonUtil


class FootballFetchTask(BaseTask):
    """
    Task that fetches football fixtures, saves raw JSON, applies filters
    based on DictManager clubs/competitions, and cleans old files.

    Uses Windows system TEMP folder via ExplorerUtils:
        C:\\Users\\<user>\\AppData\\Local\\Temp\\aetheris\\football\\
    """

    # API base URL
    _API_URL = "https://v3.football.api-sports.io/fixtures"
    _TIMEOUT = 30

    def __init__(self):
        super().__init__(description="Football fixtures fetch & filter")
        # Resolve output dir via ExplorerUtils (the only class allowed to use os)
        self._output_dir = ExplorerUtils.get_system_temp_dir(
            subfolder="aetheris/football",
            tool_key="FootballFetch",
        )

    # ── Public accessors for result ────────────────────────────────

    @property
    def output_dir(self) -> str:
        return self._output_dir

    # ── BaseTask implementation ────────────────────────────────────

    def _run(self) -> bool:
        try:
            logger = self.get_logger()

            # ── Determine dates ────────────────────────────────────
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            today_str = now.strftime("%Y-%m-%d")
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            today_compact = now.strftime("%Y%m%d")
            yesterday_compact = yesterday.strftime("%Y%m%d")

            # Output dirs (ExplorerUtils.ensure_directory for old/)
            out_dir = Path(self._output_dir)
            old_dir_path = str(out_dir / "old")
            ExplorerUtils.ensure_directory(old_dir_path, tool_key="FootballFetch")
            old_dir = Path(old_dir_path)

            # File paths
            today_raw = out_dir / f"response_{today_compact}.json"
            yesterday_raw = out_dir / f"response_{yesterday_compact}_final.json"
            today_filt = out_dir / f"response_{today_compact}_filtrado.json"
            yesterday_filt = out_dir / f"response_{yesterday_compact}_final_filtrado.json"

            keep_names = {
                f"response_{today_compact}.json",
                f"response_{today_compact}_filtrado.json",
                f"response_{yesterday_compact}_final.json",
                f"response_{yesterday_compact}_final_filtrado.json",
            }

            # ── STEP 1: Move old files to old/ ─────────────────────
            logger.info(
                "Moving old response files to old/",
                code="FOOT_MOVE_OLD",
                output_dir=self._output_dir,
            )

            for f in out_dir.iterdir():
                if f.is_file() and f.name.startswith("response_") and f.suffix == ".json":
                    if f.name not in keep_names:
                        dest = old_dir / f.name
                        f.rename(dest)
                        logger.info(
                            "Moved old file", code="FOOT_MOVED",
                            file=f.name, dest=str(dest),
                        )

            # ── STEP 2: Fetch today if needed ──────────────────────
            if not today_raw.exists():
                logger.info(
                    "Fetching today fixtures", code="FOOT_FETCH_TODAY",
                    date=today_str,
                )
                payload_today = self._fetch(today_str)
                JsonUtil.write_json(str(today_raw), payload_today, tool_key="FootballFetch")
                logger.info(
                    "Today fixtures saved", code="FOOT_TODAY_SAVED",
                    path=str(today_raw),
                )
            else:
                logger.info(
                    "Today file exists, skipping fetch", code="FOOT_TODAY_EXISTS",
                    path=str(today_raw),
                )
                payload_today = JsonUtil.read_json(str(today_raw), tool_key="FootballFetch")

            # ── STEP 3: Fetch yesterday if needed ──────────────────
            if not yesterday_raw.exists():
                logger.info(
                    "Fetching yesterday fixtures", code="FOOT_FETCH_YESTERDAY",
                    date=yesterday_str,
                )
                payload_yesterday = self._fetch(yesterday_str)
                JsonUtil.write_json(str(yesterday_raw), payload_yesterday, tool_key="FootballFetch")
                logger.info(
                    "Yesterday fixtures saved", code="FOOT_YESTERDAY_SAVED",
                    path=str(yesterday_raw),
                )
            else:
                logger.info(
                    "Yesterday file exists, skipping fetch", code="FOOT_YESTERDAY_EXISTS",
                    path=str(yesterday_raw),
                )
                payload_yesterday = JsonUtil.read_json(str(yesterday_raw), tool_key="FootballFetch")

            # ── STEP 4: Apply filters ──────────────────────────────
            logger.info("Applying football filters", code="FOOT_FILTERING")

            today_filtered = self._filter_payload(payload_today)
            yesterday_filtered = self._filter_payload(payload_yesterday)

            JsonUtil.write_json(str(today_filt), today_filtered, tool_key="FootballFetch")
            JsonUtil.write_json(str(yesterday_filt), yesterday_filtered, tool_key="FootballFetch")

            # ── STEP 5: List all JSON files in output dir ──────────
            json_files = sorted(f.name for f in out_dir.iterdir()
                                if f.is_file() and f.suffix == ".json")
            old_files = sorted(f.name for f in old_dir.iterdir()
                               if f.is_file() and f.suffix == ".json")

            logger.info(
                "Football fetch complete",
                code="FOOT_COMPLETE",
                today_raw=today_raw.name,
                yesterday_raw=yesterday_raw.name,
                today_filtered=today_filt.name,
                yesterday_filtered=yesterday_filt.name,
                today_original=today_filtered.get("original_results", 0),
                today_filtered_count=today_filtered.get("filtered_results", 0),
                yesterday_original=yesterday_filtered.get("original_results", 0),
                yesterday_filtered_count=yesterday_filtered.get("filtered_results", 0),
                output_dir=self._output_dir,
                json_files=json_files,
                old_files=old_files,
            )

            # Store result
            self.result = {
                "output_dir": self._output_dir,
                "today_raw": str(today_raw),
                "yesterday_raw": str(yesterday_raw),
                "today_filtered": str(today_filt),
                "yesterday_filtered": str(yesterday_filt),
                "today_original": today_filtered.get("original_results", 0),
                "today_filtered_count": today_filtered.get("filtered_results", 0),
                "yesterday_original": yesterday_filtered.get("original_results", 0),
                "yesterday_filtered_count": yesterday_filtered.get("filtered_results", 0),
                "json_files": json_files,
                "old_files": old_files,
            }

            return True

        except Exception as e:
            self.exception = RuntimeError(f"Football fetch failed: {e}")
            return False

    # ── Private helpers ────────────────────────────────────────────

    def _fetch(self, date_str: str) -> Dict[str, Any]:
        """Fetch fixtures from API for a given date."""
        headers = {"x-apisports-key": ApiKeys.FOOTBALL_API_KEY}
        url = f"{self._API_URL}?date={date_str}"
        resp = requests.get(url, headers=headers, timeout=self._TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def _norm(self, s: Any) -> str:
        """Normalize string for comparison (uppercase, strip)."""
        if s is None:
            return ""
        return str(s).strip().upper()

    def _filter_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter API payload keeping only teams/competitions from DictManager.
        Returns a new dict with response filtered + metadata.
        """
        allowed_labels = {self._norm(x) for x in DictManager.football_filter_labels()}
        response = payload.get("response") or []
        allowed_fixtures = []

        for item in response:
            teams = item.get("teams") or {}
            league = item.get("league") or {}
            home = self._norm((teams.get("home") or {}).get("name"))
            away = self._norm((teams.get("away") or {}).get("name"))
            league_name = self._norm(league.get("name"))

            keep = (
                home in allowed_labels
                or away in allowed_labels
                or league_name in allowed_labels
            )

            if keep:
                allowed_fixtures.append(item)

        out = dict(payload)
        out["response"] = allowed_fixtures
        out["filtered_results"] = len(allowed_fixtures)
        out["original_results"] = len(response)
        return out