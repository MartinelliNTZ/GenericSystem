# -*- coding: utf-8 -*-
"""
LasTilerTask — Task for splitting LAS/LAZ point clouds into parts
=====================================================================
Task that splits LAS/LAZ files into multiple smaller files
based on points per part.

Uses LasUtil.split_las() internally.
"""

from __future__ import annotations

import os as _os
from typing import Optional

from core.enum.ToolKey import ToolKey
from core.papeline.BaseTask import BaseTask
from utils.las.LasLayerSource import LasLayerSource


class LasTilerTask(BaseTask):
    """
    Task that splits LAS/LAZ files into parts.

    Args:
        files: List of LAS/LAZ file paths to process.
        output_dir: Directory where to save the parts.
        points_per_part: Maximum number of points per file.
        tool_key: ToolKey for logging (optional).
    """

    def __init__(
        self,
        files: list[str],
        output_dir: str,
        points_per_part: int = 5_000_000,
        tool_key: Optional[str] = None,
    ):
        super().__init__(
            description=f"Split: {len(files)} file(s)",
            tool_key=tool_key or ToolKey.UNTRACEABLE.value,
        )
        self._files = files
        self._output_dir = output_dir
        self._points_per_part = points_per_part

    def _run(self) -> bool:
        """Executes the split for all files."""
        logger = self.get_logger()

        _os.makedirs(self._output_dir, exist_ok=True)

        all_results = []
        total_parts = 0
        total_points = 0

        for file_path in self._files:
            logger.info(
                "Starting split",
                code="TILER_TASK_START",
                path=file_path,
                output=self._output_dir,
                points_per_part=self._points_per_part,
            )

            result = LasLayerSource.split_las(
                path=file_path,
                output_dir=self._output_dir,
                pontos_por_parte=self._points_per_part,
                tool_key=self._tool_key,
            )

            if result.get("error"):
                logger.error(
                    "Split failed",
                    code="TILER_TASK_ERR",
                    path=file_path,
                    error=result["error"],
                )
                return False

            all_results.append(result)
            total_parts += result.get("n_partes", 0)
            total_points += result.get("n_total", 0)

        self.result = {
            "results": all_results,
            "n_total": total_points,
            "n_parts": total_parts,
            "points_per_part": self._points_per_part,
            "files": self._files,
        }

        logger.info(
            "Split completed",
            code="TILER_TASK_DONE",
            n_parts=total_parts,
            n_total=total_points,
        )
        return True