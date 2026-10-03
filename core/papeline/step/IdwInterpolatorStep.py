# -*- coding: utf-8 -*-
"""
IdwInterpolatorStep — Step that interpolates LAS files via IDW
================================================================
Step that receives a directory with LAS files (from whoever produced them)
and executes IDW interpolation, generating rasters.

DOES NOT know what tiles are. Only reads from context:
    - input_path: Directory with .las/.laz files to interpolate

Context requires:
    - input_path: Directory with LAS files
    - output_path: Base directory to save results

Context produces:
    - results["idw_result"]: Dict with complete interpolation result
"""

from __future__ import annotations

import os as _os
from typing import Any, Optional

from core.governor.ResourceGovernor import ResourceGovernor
from core.papeline.BaseStep import BaseStep
from core.papeline.BaseTask import BaseTask
from core.papeline.ExecutionContext import ExecutionContext
from core.papeline.task.IdwInterpolatorTask import IdwInterpolatorTask


class IdwInterpolatorStep(BaseStep):
    """Step that interpolates LAS files via IDW."""

    subfolder = "idwtiles"
    _advance_input = True

    def __init__(self, target_bands: dict = None, merge_bands: bool = True,
                 resolution_m: float = 0.01, idw_k: int = 5, idw_power: float = 2.0,
                 idw_max_radius: float = 0.5, idw_overlap: float = 3.0,
                 crs_str: str = "EPSG:31982", delete_tiles: bool = True,
                 save_las: bool = False,
                 advance_input: bool = True, input_path: str = ""):
        self._target_bands = target_bands or {}
        self._merge_bands = merge_bands
        self._resolution_m = resolution_m
        self._idw_k = idw_k
        self._idw_power = idw_power
        self._idw_max_radius = idw_max_radius
        self._idw_overlap = idw_overlap
        self._crs_str = crs_str
        self._delete_tiles = delete_tiles
        self._save_las = save_las
        self._advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "idwtiles"

    def should_run(self, context: ExecutionContext) -> bool:
        logger = self.get_logger(context)
        path = self._custom_input_path or context.input_path
        if not path or not _os.path.isdir(path):
            logger.warning("Input directory not found", code="IDW_STEP_NO_DIR")
            return False

        target = self._target_bands
        if not any(target.values()):
            logger.warning("No bands selected", code="IDW_STEP_NO_BANDS")
            return False

        merge = self._merge_bands
        if merge:
            has_rgb = target.get("r", False) and target.get("g", False) and target.get("b", False)
            has_any_rgb = target.get("r", False) or target.get("g", False) or target.get("b", False)
            if not has_rgb and has_any_rgb:
                logger.warning("Mosaic requires R, G and B", code="IDW_STEP_MOSAIC_INCOMPLETE")
                return False

        return True

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        governor: Optional[ResourceGovernor] = getattr(context, "_governor", None)
        path = self._custom_input_path or context.input_path

        return IdwInterpolatorTask(
            input_dir=path,
            output_path=_os.path.join(self.output_subdir(context), "merged.tif"),
            target_bands=self._target_bands,
            merge_bands=self._merge_bands,
            resolution_m=self._resolution_m,
            idw_k=self._idw_k,
            idw_power=self._idw_power,
            idw_max_radius=self._idw_max_radius,
            idw_overlap=self._idw_overlap,
            crs_str=self._crs_str,
            delete_tiles=self._delete_tiles,
            save_las=self._save_las,
            governor=governor,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        logger = self.get_logger(context)
        if isinstance(result, dict):
            context.set_result("idw_result", result)
            for key in ("grid", "parametros", "tiles", "arquivos_gerados"):
                if key in result:
                    context.set_result(key, result[key])
        logger.info("IDW completed successfully", code="IDW_STEP_DONE")
        self.advance_input(context)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        logger = self.get_logger(context)
        logger.error("Error in IDW interpolation", code="IDW_STEP_ERR", error=str(exception))
        context.add_error(exception)