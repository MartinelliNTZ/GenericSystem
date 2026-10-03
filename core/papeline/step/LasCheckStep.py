# -*- coding: utf-8 -*-
"""
LasCheckStep — Step that runs quality checks on LAS/LAZ point clouds
======================================================================
Runs a configurable battery of checks via context and returns
consolidated results under "check_results" key.
"""

from __future__ import annotations

from typing import Any

import os

import laspy
import numpy as np

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.BaseStep import BaseStep
from core.papeline.ExecutionContext import ExecutionContext
from utils.BaseUtil import BaseUtil
from utils.las.LasLayerSource import LasLayerSource


class LasCheckStep(BaseStep):
    """Step that runs quality checks on LAS/LAZ point clouds."""

    subfolder = "lascheck"
    _advance_input = False

    _CHECK_NAMES: dict[str, str] = {
        "point_count": "Point Count",
        "bbox": "Bounding Box",
        "rgb": "RGB Bands",
        "classification": "Classification",
        "zero_coords": "Zero Coordinates",
        "duplicates": "XY Duplicates",
        "density": "Density / Gaps",
        "intensity": "Intensity",
    }

    def __init__(self, advance_input: bool = False, input_path: str = "", checks_enabled: dict[str, bool] | None = None):
        self._advance_input = advance_input
        self._custom_input_path = input_path
        self._checks_enabled = checks_enabled or {}

    def name(self) -> str:
        return "lascheck"

    def should_run(self, context: ExecutionContext) -> bool:
        path = self._custom_input_path or context.input_path
        return bool(path)

    def create_task(self, context: ExecutionContext) -> None:
        return None

    def run_inline(self, context: ExecutionContext) -> dict[str, Any]:
        path = self._custom_input_path or context.input_path
        tool_key = context.tool_key or ToolKey.UNTRACEABLE.value
        logger = BaseUtil._get_logger(tool_key, "LasCheckStep")
        checks_enabled = self._checks_enabled

        signals = SignalManager.instance()

        logger.info("Starting quality checks", code="LASCHECK_START", path=path)

        # Open LAS/LAZ
        try:
            laz_backends = tuple(
                b for b in laspy.LazBackend
                if b.name in ("LazrsParallel", "Lazrs", "Laszip")
            )
            if laz_backends:
                logger.debug("Available LAZ backends", code="LASCHECK_LAZ_BACKENDS",
                             backends=[b.name for b in laz_backends])
            else:
                laz_backends = None
        except AttributeError:
            laz_backends = None

        try:
            las = laspy.read(path, laz_backend=laz_backends)
            logger.info("File opened successfully", code="LASCHECK_FILE_OPEN_OK",
                        path=path, ext=os.path.splitext(path)[1].lower(),
                        total_points=len(las.points))
            signals.console_message.emit(
                f"[LasCheck] File opened: {os.path.basename(path)} ({len(las.points):,} points)")
        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to open LAS/LAZ file", code="LASCHECK_FILE_OPEN_ERR",
                         path=path, error=error_msg)
            if "No LazBackend selected" in error_msg or "cannot decompress" in error_msg or "is not available" in error_msg:
                return {"check_results": {}, "summary": {"pass": 0, "warning": 0, "fail": 1, "total": 0, "error": True},
                        "error_type": "laz_backend", "error": "Error opening .LAZ. Install lazrs backend."}
            raise

        n_total = len(las.points)
        check_order = ["point_count", "bbox", "rgb", "classification",
                       "zero_coords", "duplicates", "density", "intensity", "statistics"]
        check_methods = {
            "point_count": self._check_point_count, "bbox": self._check_bbox,
            "rgb": self._check_rgb, "classification": self._check_classification,
            "zero_coords": self._check_zero_coords, "duplicates": self._check_duplicates,
            "density": self._check_density, "intensity": self._check_intensity,
            "statistics": self._check_statistics,
        }

        results: dict[str, dict] = {}
        stage_idx = 0
        for check_name in check_order:
            enabled = checks_enabled.get(check_name, True)
            if not enabled:
                results[check_name] = {"status": "skipped", "message": "Check disabled by user", "detail": "", "suggestion": ""}
                continue

            display = self._CHECK_NAMES.get(check_name, check_name)
            signals.hud_update.emit({"message": f"Checking: {display}..."})

            try:
                result = check_methods[check_name](las, n_total)
                results[check_name] = result
            except Exception as e:
                logger.error(f"Error in check '{display}'", code="LASCHECK_CHECK_EXEC_ERR", check=check_name, error=str(e))
                results[check_name] = {"status": "fail", "message": f"Error: {str(e)}", "detail": str(e), "suggestion": ""}

            signals.hud_stage_done.emit(stage_idx)
            stage_idx += 1

        pass_count = sum(1 for r in results.values() if r.get("status") == "pass")
        warn_count = sum(1 for r in results.values() if r.get("status") == "warning")
        fail_count = sum(1 for r in results.values() if r.get("status") == "fail")
        signals.progress_update.emit(100.0)

        return {"check_results": results, "summary": {"pass": pass_count, "warning": warn_count, "fail": fail_count, "total": len(check_order)}}

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            for key, value in result.items():
                context.set_result(key, value)

    @staticmethod
    def _check_point_count(las, n_total):
        if n_total == 0:
            return {"status": "fail", "message": "No points found", "detail": "0", "suggestion": ""}
        elif n_total < 1000:
            return {"status": "warning", "message": f"Only {n_total:,} points", "detail": str(n_total), "suggestion": ""}
        return {"status": "pass", "message": f"{n_total:,} points", "detail": str(n_total), "suggestion": ""}

    @staticmethod
    def _check_bbox(las, n_total):
        x_min, x_max = float(np.min(las.x)), float(np.max(las.x))
        y_min, y_max = float(np.min(las.y)), float(np.max(las.y))
        z_min, z_max = float(np.min(las.z)), float(np.max(las.z))
        return {"status": "pass", "message": f"X[{x_min:.1f},{x_max:.1f}] Y[{y_min:.1f},{y_max:.1f}] Z[{z_min:.1f},{z_max:.1f}]",
                "detail": f"{x_min:.1f} {x_max:.1f} {y_min:.1f} {y_max:.1f} {z_min:.1f} {z_max:.1f}", "suggestion": ""}

    @staticmethod
    def _check_rgb(las, n_total):
        has = hasattr(las, "red") and hasattr(las, "green") and hasattr(las, "blue")
        if not has:
            return {"status": "warning", "message": "LAS has no RGB bands", "detail": "", "suggestion": ""}
        return {"status": "pass", "message": "RGB present", "detail": "", "suggestion": ""}

    @staticmethod
    def _check_classification(las, n_total):
        if not hasattr(las, "classification"):
            return {"status": "warning", "message": "No classification field", "detail": "", "suggestion": ""}
        classes = np.unique(las.classification)
        valid = sorted(classes[classes > 0].tolist())
        return {"status": "pass", "message": f"Valid codes: {valid}", "detail": str(valid), "suggestion": ""}

    @staticmethod
    def _check_zero_coords(las, n_total):
        mask = (las.x == 0) & (las.y == 0) & (las.z == 0)
        n_zero = int(np.sum(mask))
        if n_zero == 0:
            return {"status": "pass", "message": "No zero coordinates", "detail": "0", "suggestion": ""}
        pct = n_zero / n_total * 100
        return {"status": "warning" if pct < 1 else "fail", "message": f"{n_zero:,} points with X=Y=Z=0 ({pct:.2f}%)", "detail": str(n_zero), "suggestion": ""}

    @staticmethod
    def _check_duplicates(las, n_total):
        sample = min(n_total, 50000)
        if n_total > sample:
            idx = np.random.default_rng().choice(n_total, sample, replace=False)
        else:
            idx = slice(None)
        coords = np.column_stack((las.x[idx], las.y[idx]))
        _, counts = np.unique(coords, axis=0, return_counts=True)
        dup = int(np.sum(counts > 1))
        if dup == 0:
            return {"status": "pass", "message": "No duplicates", "detail": "0", "suggestion": ""}
        return {"status": "warning", "message": f"{dup} duplicates in sample", "detail": str(dup), "suggestion": ""}

    @staticmethod
    def _check_density(las, n_total):
        area = (float(np.max(las.x)) - float(np.min(las.x))) * (float(np.max(las.y)) - float(np.min(las.y)))
        if area <= 0:
            return {"status": "warning", "message": "Zero planar area", "detail": "", "suggestion": ""}
        return {"status": "pass", "message": f"Density: {n_total/area:.2f} pts/m²", "detail": f"{n_total/area:.2f}", "suggestion": ""}

    @staticmethod
    def _check_intensity(las, n_total):
        if not hasattr(las, "intensity"):
            return {"status": "warning", "message": "No intensity field", "detail": "", "suggestion": ""}
        return {"status": "pass", "message": f"Range [{int(np.min(las.intensity))}, {int(np.max(las.intensity))}]", "detail": "", "suggestion": ""}

    @staticmethod
    def _check_statistics(las, n_total):
        import json
        x, y, z = np.asarray(las.x, dtype=np.float64), np.asarray(las.y, dtype=np.float64), np.asarray(las.z, dtype=np.float64)
        x_min, x_max = float(np.min(x)), float(np.max(x))
        y_min, y_max = float(np.min(y)), float(np.max(y))
        z_min, z_max = float(np.min(z)), float(np.max(z))
        area = (x_max - x_min) * (y_max - y_min)
        density = n_total / area if area > 0 else 0
        spacing = 1.0 / (density ** 0.5) if density > 0 else 0
        pixel = max(spacing * 0.75, 0.01) if density > 0 else 0.01

        # ── Scan Angle ──────────────────────────────────────────────
        scan_angle_stats = None
        if hasattr(las, "scan_angle_rank") and las.scan_angle_rank.dtype.kind in ("i", "u", "f"):
            arr = np.asarray(las.scan_angle_rank, dtype=np.float64)
            scan_angle_stats = {
                "min": round(float(np.min(arr)), 2),
                "max": round(float(np.max(arr)), 2),
                "mean": round(float(np.mean(arr)), 2),
            }
        elif hasattr(las, "scan_angle") and las.scan_angle.dtype.kind in ("i", "u", "f"):
            arr = np.asarray(las.scan_angle, dtype=np.float64)
            scan_angle_stats = {
                "min": round(float(np.min(arr)), 2),
                "max": round(float(np.max(arr)), 2),
                "mean": round(float(np.mean(arr)), 2),
            }

        # ── GPS Time ────────────────────────────────────────────────
        gps_time_stats = None
        if hasattr(las, "gps_time") and las.gps_time.dtype.kind in ("i", "u", "f"):
            arr = np.asarray(las.gps_time, dtype=np.float64)
            gps_time_stats = {
                "min": round(float(np.min(arr)), 4),
                "max": round(float(np.max(arr)), 4),
                "mean": round(float(np.mean(arr)), 4),
            }

        stats = {
            "point_count": n_total,
            "bounding_box": {"x": {"min": round(x_min,4), "max": round(x_max,4)},
                             "y": {"min": round(y_min,4), "max": round(y_max,4)},
                             "z": {"min": round(z_min,4), "max": round(z_max,4)}},
            "altimetry": {"min": round(z_min,4), "max": round(z_max,4), "mean": round(float(np.mean(z)),4),
                          "p5": round(float(np.percentile(z,5)),4), "p95": round(float(np.percentile(z,95)),4)},
            "density_pts_per_m2": round(density, 4),
            "ideal_pixel_m": round(pixel, 6), "ideal_pixel_cm": round(pixel*100, 2),
            "scan_angle": scan_angle_stats,
            "gps_time": gps_time_stats,
        }
        return {"status": "pass", "message": f"Dens:{density:.2f}pts/m² Pixel:{pixel*100:.2f}cm",
                "detail": json.dumps(stats, ensure_ascii=False), "suggestion": ""}
