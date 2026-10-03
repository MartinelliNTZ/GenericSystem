# -*- coding: utf-8 -*-
"""
VectorToLasTask — Task for converting vector point files to LAS/LAZ
=====================================================================
Reads vector point files (SHP, GPKG, CSV, GeoJSON), extracts X/Y/Z
coordinates and attributes (RGB, intensity, classification), and
saves as LAS/LAZ point cloud.
Emits progress per file for HUD stage mode — each file = 1 stage.
"""

from __future__ import annotations

import os
from typing import Any

import laspy
import numpy as np

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.BaseTask import BaseTask
from utils.BaseUtil import BaseUtil


class VectorToLasTask(BaseTask):
    """
    Task that converts vector point files to LAS/LAZ.

    Args:
        files: List of vector file paths to process (.shp, .gpkg, .csv, .geojson).
        output_dir: Directory to save LAS files.
        crs_str: CRS string to embed in LAS header (e.g. 'EPSG:31982').
        csv_x_field: Column name for X coordinate (CSV only).
        csv_y_field: Column name for Y coordinate (CSV only).
        csv_z_field: Column name for Z coordinate (CSV only, optional).
    """

    def __init__(
        self,
        files: list[str],
        output_dir: str,
        crs_str: str = "EPSG:31982",
        csv_x_field: str = "x",
        csv_y_field: str = "y",
        csv_z_field: str = "",
    ):
        n_files = len(files)
        super().__init__(description=f"Convertendo {n_files} vetores para LAS/LAZ")
        self._files = files
        self._output_dir = output_dir
        self._crs_str = crs_str
        self._csv_x_field = csv_x_field
        self._csv_y_field = csv_y_field
        self._csv_z_field = csv_z_field
        self._signals = SignalManager.instance()
        self._logger = BaseUtil._get_logger(
            ToolKey.LAS_VECTOR_CONVERTER.value, "VectorToLasTask"
        )

    def _run(self) -> bool:
        """Executes the vector to LAS conversion."""
        os.makedirs(self._output_dir, exist_ok=True)

        all_output_files: list[str] = []
        total_input_features = 0
        total_output_points = 0
        n_files = len(self._files)

        for idx, file_path in enumerate(self._files):
            if self.is_cancelled:
                self._logger.warning("Task cancelled", code="TASK_CANCELLED")
                return False

            basename = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(self._output_dir, f"{basename}.las")

            # Cada arquivo é uma etapa
            self._signals.hud_update.emit({
                "message": f"Convertendo {basename}... ({idx + 1}/{n_files})",
                "progress": ((idx + 0.5) / n_files) * 100.0 if n_files > 0 else 50.0,
            })
            self._signals.progress_update.emit(
                ((idx + 0.5) / n_files) * 100.0 if n_files > 0 else 50.0
            )

            try:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == ".csv":
                    points, attributes = self._read_csv(file_path)
                else:
                    points, attributes = self._read_geo(file_path)

                n_points = len(points)
                total_input_features += n_points

                if n_points == 0:
                    self._logger.warning(
                        "Arquivo vazio, ignorando",
                        code="EMPTY_VECTOR",
                        path=file_path,
                    )
                    continue

                self._save_las(points, attributes, output_path)

                all_output_files.append(output_path)
                total_output_points += n_points

                self._logger.info(
                    "Arquivo convertido",
                    code="VECTOR_TO_LAS_DONE",
                    path=file_path,
                    output=output_path,
                    points=n_points,
                )

            except Exception as e:
                self._logger.error(
                    "Erro ao converter vetor para LAS",
                    code="VECTOR_TO_LAS_ERR",
                    path=file_path,
                    error=str(e),
                )
                raise

        self.result = {
            "n_input": total_input_features,
            "n_output": total_output_points,
            "output_files": all_output_files,
            "output_dir": self._output_dir,
            "direction": "vector_to_las",
        }
        return True

    def _read_csv(self, path: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        """Reads CSV file and extracts point data."""
        import pandas as pd

        df = pd.read_csv(path)

        if self._csv_x_field not in df.columns or self._csv_y_field not in df.columns:
            raise ValueError(
                f"Colunas X='{self._csv_x_field}' ou Y='{self._csv_y_field}' "
                f"não encontradas. Disponíveis: {list(df.columns)}"
            )

        n = len(df)
        x = df[self._csv_x_field].values.astype(np.float64)
        y = df[self._csv_y_field].values.astype(np.float64)

        if self._csv_z_field and self._csv_z_field in df.columns:
            z = df[self._csv_z_field].values.astype(np.float64)
        else:
            z = np.zeros(n, dtype=np.float64)

        points = np.column_stack((x, y, z))

        attributes: dict[str, np.ndarray] = {}
        for col in df.columns:
            if col in (self._csv_x_field, self._csv_y_field, self._csv_z_field):
                continue
            if df[col].dtype in (np.int64, np.float64):
                attributes[col] = df[col].values

        return points, attributes

    def _read_geo(self, path: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        """Reads vector file and extracts point data."""
        import geopandas as gpd

        gdf = gpd.read_file(path)

        if gdf.empty:
            raise ValueError(f"Arquivo vazio: {path}")

        xs: list[float] = []
        ys: list[float] = []
        zs: list[float] = []

        for geom in gdf.geometry:
            if geom is None:
                continue
            if geom.geom_type == "Point":
                xs.append(float(geom.x))
                ys.append(float(geom.y))
                zs.append(float(geom.z) if geom.has_z else 0.0)
            elif geom.geom_type == "MultiPoint":
                for pt in geom.geoms:
                    xs.append(float(pt.x))
                    ys.append(float(pt.y))
                    zs.append(float(pt.z) if pt.has_z else 0.0)

        if len(xs) == 0:
            raise ValueError("Nenhuma geometria Point ou MultiPoint encontrada.")

        points = np.column_stack((np.array(xs), np.array(ys), np.array(zs)))

        attributes: dict[str, np.ndarray] = {}
        for col in gdf.columns:
            if col == "geometry":
                continue
            if gdf[col].dtype in (np.int64, np.float64, np.int32, np.float32):
                attributes[col] = gdf[col].values

        return points, attributes

    @staticmethod
    def _las_dtype_for_array(arr: np.ndarray) -> np.dtype:
        """Returns the smallest appropriate LAS extra dim dtype for an array."""
        if np.issubdtype(arr.dtype, np.floating):
            return np.float64
        iinfo = np.iinfo(np.int32)
        if arr.min() >= 0 and arr.max() <= 255:
            return np.uint8
        if arr.min() >= 0 and arr.max() <= 65535:
            return np.uint16
        if arr.min() >= iinfo.min and arr.max() <= iinfo.max:
            return np.int32
        return np.float64

    def _save_las(self, points: np.ndarray, attributes: dict[str, np.ndarray], output_path: str) -> None:
        """Creates LAS file from point data."""
        n = len(points)

        header = laspy.LasHeader(point_format=3, version="1.2")
        header.offsets = np.min(points, axis=0)
        header.scales = np.array([0.001, 0.001, 0.001])

        las = laspy.LasData(header)

        las.x = points[:, 0]
        las.y = points[:, 1]
        las.z = points[:, 2]

        attr_lower = {k.lower(): k for k in attributes}

        # ── Standard LAS fields ──────────────────────────────────
        if "intensity" in attr_lower:
            las.intensity = attributes[attr_lower["intensity"]].astype(np.uint16)
        else:
            las.intensity = np.zeros(n, dtype=np.uint16)

        if "classification" in attr_lower:
            las.classification = attributes[attr_lower["classification"]].astype(np.uint8)

        if "returnnumber" in attr_lower or "return_number" in attr_lower:
            key = attr_lower.get("returnnumber") or attr_lower.get("return_number")
            las.return_number = attributes[key].astype(np.uint8)

        has_r = "r" in attr_lower or "red" in attr_lower
        has_g = "g" in attr_lower or "green" in attr_lower
        has_b = "b" in attr_lower or "blue" in attr_lower
        if has_r and has_g and has_b:
            r_key = attr_lower.get("r") or attr_lower.get("red")
            g_key = attr_lower.get("g") or attr_lower.get("green")
            b_key = attr_lower.get("b") or attr_lower.get("blue")
            las.red = attributes[r_key].astype(np.uint16)
            las.green = attributes[g_key].astype(np.uint16)
            las.blue = attributes[b_key].astype(np.uint16)

        # ── Extra dimensions: preserve all remaining attributes ──
        standard_keys = {"x", "y", "z", "intensity", "classification",
                         "returnnumber", "return_number",
                         "r", "g", "b", "red", "green", "blue"}
        used_keys = set(attr_lower.keys()) & standard_keys
        consumed = {attr_lower[k] for k in used_keys}

        extra_dims: list[tuple[str, np.ndarray]] = []
        for orig_key, arr in attributes.items():
            if orig_key in consumed:
                continue
            # Skip geometry-like columns that may come from geopandas
            if orig_key.lower() in ("geometry", "geom", "wkb_geometry", "shape"):
                continue
            extra_dims.append((orig_key, arr))

        if extra_dims:
            params_list = []
            for col_name, arr in extra_dims:
                las_dtype = self._las_dtype_for_array(arr)
                params_list.append(
                    laspy.ExtraBytesParams(
                        name=col_name,
                        type=las_dtype,
                        description=f"Atributo original: {col_name}",
                    )
                )
            las.add_extra_dims(params_list)

            # Write data into the new extra dims
            for col_name, arr in extra_dims:
                las[col_name] = arr.astype(las[col_name].dtype)

        las.write(output_path)
