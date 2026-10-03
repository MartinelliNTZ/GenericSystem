# -*- coding: utf-8 -*-
"""
MrkSteps — Concrete steps for MRK processing pipeline
========================================================
Steps that compose a complete MRK substitution pipeline.

Pipeline:
    1. MrkLoadDataStep → Validates data file exists
    2. MrkProcessStep → Processes MRK against loaded data
    3. MrkFindDataStep → Auto-finds data file matching MRK
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ExecutionContext import ExecutionContext
from ..BaseTask import BaseTask
from ..BaseStep import BaseStep
from ..task.MrkSinglePipelineTask import MrkSinglePipelineTask


class MrkLoadDataStep(BaseStep):
    """
    Step that validates the data file exists.
    Does NOT load data into memory - loading is done by MrkProcessStep
    which reads directly from the file.

    Context requires:
        - results["data_path"]: Path to data file

    Context produces:
        - (only validates, doesn't load anything)
    """
    def name(self) -> str:
        return "mrk_load_data"

    def create_task(self, context: ExecutionContext) -> None:
        return None  # Synchronous

    def run_inline(self, context: ExecutionContext) -> Optional[bool]:
        data_path = str(context.get_result("data_path", ""))
        if not data_path or not Path(data_path).is_file():
            return False
        return True

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        pass  # Data will be loaded by MrkProcessStep directly from disk


class MrkProcessStep(BaseStep):
    """
    Step that processes ONE MRK file against data loaded in context.

    Context requires:
        - results["data_path"]: Path to data file
        - results["mrk_path"]: Path to .MRK file
        - results["mapping"]: Dict mapping mrk_field -> data_column
        - results["output_dir"]: Output directory

    Context produces:
        - results["replacements"]: Total replacements made
        - results["output_path"]: Path to processed MRK
    """
    def name(self) -> str:
        return "mrk_process"

    def should_run(self, context: ExecutionContext) -> bool:
        return bool(context.get_result("data_path")) and bool(context.get_result("mrk_path"))

    def create_task(self, context: ExecutionContext) -> MrkSinglePipelineTask:
        return MrkSinglePipelineTask(
            mrk_path=str(context.get_result("mrk_path")),
            data_path=str(context.get_result("data_path", "")),
            mapping=context.get_result("mapping", {}),
            output_dir=str(context.get_result("output_dir")),
            emit_console=True,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set_result("replacements", result.get("replacements", 0))
            context.set_result("output_path", result.get("output_path", ""))

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)


class MrkFindDataStep(BaseStep):
    """
    Step that automatically finds the data file corresponding to the MRK
    (same directory, same base name).

    Context requires:
        - results["mrk_path"]: Path to .MRK file

    Context produces:
        - results["data_path"]: Path to found data file
    """
    def name(self) -> str:
        return "mrk_find_data"

    def create_task(self, context: ExecutionContext) -> None:
        return None  # Synchronous

    def run_inline(self, context: ExecutionContext) -> Optional[str]:
        mrk_path = Path(str(context.get_result("mrk_path", "")))
        if not mrk_path.exists():
            return None

        base_name = mrk_path.stem
        directory = mrk_path.parent
        if not directory.is_dir():
            return None

        for ext in [".gpkg", ".shp", ".csv"]:
            candidate = directory / f"{base_name}{ext}"
            if candidate.is_file():
                return str(candidate)

        # Fallback: search by similar name
        candidates = []
        for ext in [".gpkg", ".shp", ".csv"]:
            for f in directory.glob(f"*{ext}"):
                if f.is_file() and base_name.lower() in f.stem.lower():
                    candidates.append(f)
        if candidates:
            best = min(candidates, key=lambda p: (
                0 if p.suffix.lower() == ".gpkg"
                else 1 if p.suffix.lower() == ".shp"
                else 2
            ))
            return str(best)
        return None

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if result:
            context.set_result("data_path", result)