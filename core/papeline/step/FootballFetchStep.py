# -*- coding: utf-8 -*-
"""
FootballFetchStep — Step for fetching and filtering football fixtures
======================================================================
Orchestrates the football data pipeline:
1. Fetches today's and yesterday's fixtures from API
2. Applies team/competition filters from DictManager
3. Manages old files (moves to old/)
4. Logs the output directory contents

This is a TRANSFORM step (advance_input=False, it just downloads/filters
and stores results in context).
"""

from __future__ import annotations

from typing import Any

from ..ExecutionContext import ExecutionContext
from ..BaseStep import BaseStep
from ..task.FootballFetchTask import FootballFetchTask


class FootballFetchStep(BaseStep):
    """
    Step that fetches football fixtures and applies filters.

    Uses ExplorerUtils to resolve system temp folder.
    No parameters needed — output dir is resolved internally.
    """

    subfolder = ""
    _advance_input = False

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        return "football_fetch"

    def create_task(self, context: ExecutionContext) -> FootballFetchTask:
        return FootballFetchTask()

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set_result("football_fetch", result)

            # Expose individual fields for logging
            output_dir = result.get("output_dir", "")
            json_files = result.get("json_files", [])
            old_files = result.get("old_files", [])

            logger = self.get_logger(context)
            logger.info(
                "Football fetch completed successfully",
                code="FOOT_STEP_DONE",
                output_dir=output_dir,
                json_count=len(json_files),
                old_count=len(old_files),
                json_files=json_files,
                old_files=old_files,
                today_original=result.get("today_original", 0),
                today_filtered=result.get("today_filtered_count", 0),
                yesterday_original=result.get("yesterday_original", 0),
                yesterday_filtered=result.get("yesterday_filtered_count", 0),
            )

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)
        logger = self.get_logger(context)
        logger.error(
            "Football fetch step failed",
            code="FOOT_STEP_ERR",
            error=str(exception),
        )