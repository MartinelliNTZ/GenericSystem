# -*- coding: utf-8 -*-
"""
LasToVectorStep — Step for converting LAS/LAZ point clouds to vector points
=============================================================================
Step that reads LAS/LAZ files and converts them to vector point layers
(SHP, GPKG, GeoJSON, CSV).
"""

from __future__ import annotations

import os as _os
from typing import Any, Optional

from ..ExecutionContext import ExecutionContext
from ..BaseStep import BaseStep
from ..BaseTask import BaseTask
from ..task.LasToVectorTask import LasToVectorTask


class LasToVectorStep(BaseStep):
    """
    Step that converts LAS/LAZ files to vector point files.

    Context requires:
        - input_path: Directory with LAS/LAZ files to process
        - output_path: Base directory to save results

    Context produces:
        - results["conversion_result"]: Dict with conversion results
    """

    subfolder = "lasvectorconverter"
    _advance_input = True

    def __init__(
        self,
        output_format: str = "gpkg",
        crs_str: str = "EPSG:31982",
        advance_input: bool = True,
        input_path: str = "",
    ):
        self._output_format = output_format
        self._crs_str = crs_str
        self._advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "lastovector"

    def should_run(self, context: ExecutionContext) -> bool:
        logger = self.get_logger(context)
        path = self._custom_input_path or context.input_path
        # If context.files is set, specific files are provided - path just needs to exist
        if context.files is not None:
            return bool(path)
        # Otherwise path must be a directory with files
        if not path or not _os.path.isdir(path):
            logger.warning("Input directory not found", code="LAS2VEC_STEP_NO_DIR", path=path)
            return False
        return True

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        if not files:
            logger = self.get_logger(context)
            logger.warning("No LAS/LAZ files found", code="LAS2VEC_STEP_NO_FILES")
            return None
        return LasToVectorTask(
            files=files,
            output_dir=self.output_subdir(context),
            output_format=self._output_format,
            crs_str=self._crs_str,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        logger = self.get_logger(context)
        if isinstance(result, dict):
            context.set_result("conversion_result", result)
            for key in ("n_input", "n_output", "output_files", "output_dir", "direction"):
                if key in result:
                    context.set_result(key, result[key])
        logger.info(
            "LAS to vector conversion completed",
            code="LAS2VEC_STEP_DONE",
            n_input=result.get("n_input", 0) if isinstance(result, dict) else 0,
            n_output=result.get("n_output", 0) if isinstance(result, dict) else 0,
        )
        self.advance_input(context)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        logger = self.get_logger(context)
        logger.error("Error in LAS to vector conversion", code="LAS2VEC_STEP_ERR", error=str(exception))
        context.add_error(exception)