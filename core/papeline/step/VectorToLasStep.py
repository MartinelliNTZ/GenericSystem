# -*- coding: utf-8 -*-
"""
VectorToLasStep — Step for converting vector point files to LAS/LAZ
=====================================================================
Step that reads vector point files (SHP, GPKG, CSV, GeoJSON) and
converts them to LAS/LAZ point clouds.
"""

from __future__ import annotations

import os as _os
from typing import Any, Optional

from ..ExecutionContext import ExecutionContext
from ..BaseStep import BaseStep
from ..BaseTask import BaseTask
from ..task.VectorToLasTask import VectorToLasTask


class VectorToLasStep(BaseStep):
    """
    Step that converts vector point files to LAS/LAZ.

    Context requires:
        - input_path: Directory with vector files to process
        - output_path: Base directory to save results

    Context produces:
        - results["conversion_result"]: Dict with conversion results
    """

    subfolder = "lasvectorconverter"
    _advance_input = True

    def __init__(
        self,
        crs_str: str = "EPSG:31982",
        csv_x_field: str = "x",
        csv_y_field: str = "y",
        csv_z_field: str = "",
        advance_input: bool = True,
        input_path: str = "",
    ):
        self._crs_str = crs_str
        self._csv_x_field = csv_x_field
        self._csv_y_field = csv_y_field
        self._csv_z_field = csv_z_field
        self._advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "vectortolas"

    def should_run(self, context: ExecutionContext) -> bool:
        logger = self.get_logger(context)
        path = self._custom_input_path or context.input_path
        # If context.files is set, specific files are provided - path just needs to exist
        if context.files is not None:
            return bool(path)
        # Otherwise path must be a directory with files
        if not path or not _os.path.isdir(path):
            logger.warning("Input directory not found", code="VEC2LAS_STEP_NO_DIR", path=path)
            return False
        return True

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".shp", ".gpkg", ".csv", ".geojson", ".kml")
        if not files:
            logger = self.get_logger(context)
            logger.warning("No vector files found", code="VEC2LAS_STEP_NO_FILES")
            return None
        return VectorToLasTask(
            files=files,
            output_dir=self.output_subdir(context),
            crs_str=self._crs_str,
            csv_x_field=self._csv_x_field,
            csv_y_field=self._csv_y_field,
            csv_z_field=self._csv_z_field,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        logger = self.get_logger(context)
        if isinstance(result, dict):
            context.set_result("conversion_result", result)
            for key in ("n_input", "n_output", "output_files", "output_dir", "direction"):
                if key in result:
                    context.set_result(key, result[key])
        logger.info(
            "Vector to LAS conversion completed",
            code="VEC2LAS_STEP_DONE",
            n_input=result.get("n_input", 0) if isinstance(result, dict) else 0,
            n_output=result.get("n_output", 0) if isinstance(result, dict) else 0,
        )
        self.advance_input(context)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        logger = self.get_logger(context)
        logger.error("Error in vector to LAS conversion", code="VEC2LAS_STEP_ERR", error=str(exception))
        context.add_error(exception)