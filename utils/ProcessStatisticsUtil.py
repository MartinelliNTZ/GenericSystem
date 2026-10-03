# -*- coding: utf-8 -*-
"""
ProcessStatisticsUtil — Processing Statistics Utility
=======================================================
Monitors execution time, item count, and estimates ETA for long
operations. Data is persisted via `Preferences` in
`config/preferences.json` under the tool's key section.

Usage:
    stats = ProcessStatisticsUtil(tool_key="LasBlackFilter")
    stats.start(n=0, ntype=ProcessStatisticsUtil.POINTS, ntotal=50000)
    # ... processing ...
    stats.end()

    print(stats.eta_str)             # "10:35:08"
    print(stats.remaining_str)       # "30.0s"
    print(stats.total_time_str)      # "0.0s"
    print(stats.elapsed_str)         # "25.3s"
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.FormatUtils import FormatUtils
from utils.Preferences import Preferences


class ProcessStatisticsUtil(BaseUtil):
    """
    Processing statistics monitor per tool.

    Attributes:
        tool_key (str): Associated tool key.
        eta (datetime | None): Estimated time of completion.
    """

    # ── NType constants ─────────────────────────────────────────────
    PIXELS = "pixels"
    FEATURES = "features"
    MBYTES = "mbytes"
    POINTS = "points"
    FILES = "files"
    LINES = "lines"
    ITEMS = "items"
    STATISTICS_TOOLKEY = ToolKey.STATISTICS.value

    # ── Fallback for first execution ─────────────────────────────────
    _DEFAULT_ETA_SECONDS: float = 30.0

    # ══════════════════════════════════════════════════════════════════
    # Constructor
    # ══════════════════════════════════════════════════════════════════

    def __init__(
        self,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        """
        Initializes the statistics monitor.

        Loads persisted statistics from Preferences automatically.

        Args:
            tool_key: Tool key used to load/save preferences.
        """
        self.tool_key: str = tool_key
        self._start_time: Optional[float] = None
        self._n: int = 0
        self._ntype: str = "items"
        self._ntotal: int = 0
        self._last_elapsed: float = 0.0

        # ── Load persisted data from Preferences ─────────────────────
        self._history: Dict[str, Any] = self._load_prefs()

        # ── Derived data ─────────────────────────────────────────────
        self._eta: Optional[datetime] = None

        self._logger = self._get_logger(
            self.tool_key, "ProcessStatisticsUtil"
        )

    # ══════════════════════════════════════════════════════════════════
    # Public API
    # ══════════════════════════════════════════════════════════════════

    def start(
        self,
        n: int,
        ntype: str = ITEMS,
        ntotal: int = 0,
    ) -> None:
        """
        Starts timing and calculates ETA.

        Args:
            n: Current / already processed count (e.g. 0 if starting fresh).
            ntype: Counter type constant (PIXELS, FEATURES, POINTS, etc.).
            ntotal: Total items to process in this run.
        """
        self._n = n
        self._ntype = ntype
        self._ntotal = ntotal
        self._start_time = time.time()

        self._calculate_eta()
        self._logger.info(
            "Processing started",
            code="STATS_START",
            n=self._n,
            ntype=self._ntype,
            ntotal=self._ntotal,
            eta=self.eta_str if self._eta else "N/A",
        )

    def end(self) -> float:
        """
        Stops timing, calculates elapsed time and persists accumulated
        statistics via Preferences.

        Returns:
            Elapsed time in seconds since start().
        """
        if self._start_time is None:
            self._logger.warning("end() called without start()", code="STATS_NO_START")
            return 0.0

        elapsed = time.time() - self._start_time
        self._last_elapsed = elapsed
        self._save_statistics(elapsed)

        self._logger.info(
            "Processing finished",
            code="STATS_END",
            elapsed_s=round(elapsed, 3),
            total_accumulated_s=round(self.total_time, 3),
            usages=self.usages,
        )

        self._start_time = None
        return elapsed

    # ── Formatted string properties ─────────────────────────────────

    @property
    def eta_str(self) -> str:
        """ETA formatted as 'HH:MM:SS' or 'N/A' if not available."""
        if self._eta is None:
            return "N/A"
        return self._eta.strftime("%H:%M:%S")

    @property
    def remaining_str(self) -> str:
        """Remaining time as '<seconds>s' (e.g. '30.0s')."""
        return f"{self.remaining_time:.1f}s"

    @property
    def total_time_str(self) -> str:
        """Total accumulated time as '<seconds>s' (e.g. '49.9s')."""
        return f"{self.total_time:.1f}s"

    @property
    def elapsed_str(self) -> str:
        """Last elapsed time as '<seconds>s' (e.g. '25.3s')."""
        return f"{self._last_elapsed:.1f}s"

    # ── Raw properties ──────────────────────────────────────────────

    @property
    def eta(self) -> Optional[datetime]:
        """Estimated completion datetime (None if never started)."""
        return self._eta

    @property
    def remaining_time(self) -> float:
        """
        Remaining seconds until ETA.

        Returns:
            Seconds left (0 if past ETA or no ETA).
        """
        if self._eta is None:
            return 0.0
        remaining = (self._eta - datetime.now()).total_seconds()
        return max(remaining, 0.0)

    @property
    def total_time(self) -> float:
        """
        Total accumulated time from history (sum of all executions).

        Returns:
            Total seconds accumulated.
        """
        return self._history.get("total_time", 0.0)

    @property
    def usages(self) -> int:
        """Number of executions registered in history."""
        return self._history.get("usages", 0)

    @property
    def ntotal_history(self) -> int:
        """Total accumulated items processed in history."""
        return self._history.get("ntotal", 0)

    @property
    def summary(self) -> str:
        """
        One-line summary string for console display.

        Example:
            "ETA: 10:35:08 (restam 30.0s, media historica: 0.0s)"
        """
        return (
            f"ETA: {self.eta_str} "
            f"(restam {self.remaining_str}, "
            f"media historica: {self.total_time_str})"
        )

    # ══════════════════════════════════════════════════════════════════
    # Internal Methods
    # ══════════════════════════════════════════════════════════════════

    def _calculate_eta(self) -> None:
        """
        Calculates ETA based on historical average.

        If no history exists (first run), assumes 30s as total estimate.

        Formula:
            time_per_item = total_time / ntotal_history
            estimated_total = time_per_item * self._ntotal
            eta = now + estimated_total
        """
        usages = self._history.get("usages", 0)
        ntotal_hist = self._history.get("ntotal", 0)
        total_time_hist = self._history.get("total_time", 0.0)

        if usages == 0 or ntotal_hist == 0 or total_time_hist == 0:
            estimate_seconds = self._DEFAULT_ETA_SECONDS
            self._logger.info(
                "No historical data — using 30s fallback",
                code="STATS_NO_HISTORY",
            )
        else:
            time_per_item = total_time_hist / ntotal_hist
            estimate_seconds = time_per_item * self._ntotal
            self._logger.info(
                "ETA calculated from history",
                code="STATS_ETA_CALC",
                time_per_item_ms=round(time_per_item * 1000, 3),
                estimate_seconds=round(estimate_seconds, 3),
            )

        self._eta = datetime.now() + timedelta(seconds=estimate_seconds)

    def _save_statistics(self, elapsed: float) -> None:
        """
        Accumulates processing data via Preferences.

        Args:
            elapsed: Elapsed time in seconds for this execution.
        """
        usages = self._history.get("usages", 0) + 1
        ntotal = self._history.get("ntotal", 0) + self._ntotal
        total_time = self._history.get("total_time", 0.0) + elapsed

        self._history = {
            "usages": usages,
            "ntotal": ntotal,
            "total_time": round(total_time, 4),
            "last_ntype": self._ntype,
            "last_n": self._n,
            "last_ntotal": self._ntotal,
            "last_elapsed_s": round(elapsed, 4),
        }
        self._save_prefs()

    def _load_prefs(self) -> Dict[str, Any]:
        """Loads statistics from Preferences."""
        return Preferences.load_tool_prefs(
            self.tool_key,
            caller_tool_key=self.tool_key,
        )

    def _save_prefs(self) -> None:
        """Persists current statistics via Preferences."""
        Preferences.save_tool_prefs(
            self.tool_key,
            self._history,
            caller_tool_key=self.tool_key,
        )