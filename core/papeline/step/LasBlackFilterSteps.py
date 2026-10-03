# -*- coding: utf-8 -*-
"""
LasBlackFilterSteps — Concrete steps for LAS black point filter pipeline
==========================================================================
Steps that compose a complete pipeline for filtering black points
in LAS/LAZ files.
"""

from __future__ import annotations

from typing import Any

from ..ExecutionContext import ExecutionContext
from ..BaseStep import BaseStep
from ..task.LasBlackFilterTask import LasBlackFilterTask


class LasBlackFilterStep(BaseStep):
    """
    Step that filters black points from LAS/LAZ files.

    Context requires:
        - input_path: Directory with LAS/LAZ files to process
        - output_path: Base directory to save results

    Context produces:
        - results["filter_result"]: Dict with filter results
    """

    subfolder = "lasblackfilter"
    _advance_input = True

    def __init__(self, threshold: int = 0, save_black_points: bool = False,
                 advance_input: bool = True, input_path: str = ""):
        self._threshold = threshold
        self._save_black_points = save_black_points
        self._advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "lasblackfilter"

    def create_task(self, context: ExecutionContext) -> LasBlackFilterTask:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        return LasBlackFilterTask(
            files=files,
            output_dir=self.output_subdir(context),
            threshold=self._threshold,
            save_black_points=self._save_black_points,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set_result("filter_result", result)
            for key in ("n_total", "n_removed", "n_kept", "n_black",
                        "output_clean", "output_black"):
                if key in result:
                    context.set_result(key, result[key])
        self.advance_input(context)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)