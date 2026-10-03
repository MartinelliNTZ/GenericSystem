# -*- coding: utf-8 -*-
"""
LasTilerStep — Step for splitting LAS/LAZ point clouds into parts
====================================================================
Step that splits LAS/LAZ files into multiple smaller files
based on points per part.
"""

from __future__ import annotations

import os as _os
from typing import Any, Optional

from ..ExecutionContext import ExecutionContext
from ..BaseStep import BaseStep
from ..BaseTask import BaseTask
from ..task.LasTilerTask import LasTilerTask


class LasTilerStep(BaseStep):
    """Step that splits LAS/LAZ files into parts."""

    subfolder = "lastiler"
    _advance_input = True

    def __init__(self, points_per_part: int = 5_000_000,
                 advance_input: bool = True, input_path: str = ""):
        self._points_per_part = points_per_part
        self._advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "lastiler"

    def should_run(self, context: ExecutionContext) -> bool:
        logger = self.get_logger(context)
        path = self._custom_input_path or context.input_path
        if not path or not _os.path.isdir(path):
            logger.warning("Input directory not found", code="TILER_STEP_NO_DIR", path=path)
            return False
        return True

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        if not files:
            logger = self.get_logger(context)
            logger.warning("No LAS files found", code="TILER_STEP_NO_FILES")
            return None
        return LasTilerTask(
            files=files,
            output_dir=self.output_subdir(context),
            points_per_part=self._points_per_part,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        logger = self.get_logger(context)
        if isinstance(result, dict):
            context.set_result("split_result", result)
            for key in ("n_total", "n_parts", "points_per_part", "files"):
                if key in result:
                    context.set_result(key, result[key])
        logger.info("Split completed successfully", code="TILER_STEP_DONE")
        self.advance_input(context)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        logger = self.get_logger(context)
        logger.error("Error in split", code="TILER_STEP_ERR", error=str(exception))
        context.add_error(exception)