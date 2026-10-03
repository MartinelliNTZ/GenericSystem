# -*- coding: utf-8 -*-
"""
LasToVectorTask — Task for converting LAS/LAZ point clouds to vector points
=============================================================================
Reads LAS/LAZ files, extracts X/Y/Z and attributes (RGB, intensity,
classification, return number), and saves as vector point layer
(SHP, GPKG, GeoJSON, CSV).
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


class LasToVectorTask(BaseTask):
    """
    Task that converts LAS/LAZ files to vector point files.

    Args:
        files: List of LAS/LAZ file paths to process.
        output_dir: Directory to save output files.
        output_format: Vector format ('gpkg', 'shp', 'geojson', 'csv').
        crs_str: CRS string for the output vector (e.g. 'EPSG:31982').
    """

    def __init__(
        self,
        files: list[str],
        output_dir: str,
        output_format: str = "gpkg",
        crs_str: str = "EPSG:31982",
    ):
        n_files = len(files)
        super().__init__(description=f"Convertendo {n_files} LAS/LAZ para {output_format.upper()}")
        self._files = files
        self._output_dir = output_dir
        self._output_format = output_format.lower()
        self._crs_str = crs_str
        self._signals = SignalManager.instance()
        self._logger = BaseUtil._get_logger(
            ToolKey.LAS_VECTOR_CONVERTER.value, "LasToVectorTask"
        )

    def _run(self) -> bool:
        """Executes the LAS to vector conversion."""
        os.makedirs(self._output_dir, exist_ok=True)

        all_output_files: list[str] = []
        total_input_points = 0
        total_output_points = 0
        n_files = len(self._files)

        for idx, file_path in enumerate(self._files):
            if self.is_cancelled:
                self._logger.warning("Task cancelled", code="TASK_CANCELLED")
                return False

            basename = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(
                self._output_dir, f"{basename}.{self._output_format}"
            )

            # Cada arquivo é uma etapa — sinaliza conclusão para o HUD
            self._signals.hud_update.emit({
                "message": f"Convertendo {basename}... ({idx + 1}/{n_files})",
                "progress": ((idx + 0.5) / n_files) * 100.0 if n_files > 0 else 50.0,
            })
            self._signals.progress_update.emit(
                ((idx + 0.5) / n_files) * 100.0 if n_files > 0 else 50.0
            )

            try:
                las = laspy.read(file_path)
                n_points = len(las.points)
                total_input_points += n_points

                if n_points == 0:
                    self._logger.warning(
                        "Arquivo vazio, ignorando",
                        code="EMPTY_LAS",
                        path=file_path,
                    )
                    continue

                x = las.x
                y = las.y
                z = las.z

                # Extrai TODAS as dimensões do LAS, incluindo extra dimensions
                data: dict[str, np.ndarray] = {
                    "X": x,
                    "Y": y,
                    "Z": z,
                }

                # Dimensões padrão do LAS PointFormat
                standard_dims = {
                    "intensity": ("Intensity", np.uint16),
                    "classification": ("Classification", np.uint8),
                    "return_number": ("ReturnNumber", np.uint8),
                    "red": ("R", np.uint16),
                    "green": ("G", np.uint16),
                    "blue": ("B", np.uint16),
                }
                for las_field, (col_name, default_dtype) in standard_dims.items():
                    if hasattr(las, las_field) and getattr(las, las_field) is not None:
                        data[col_name] = getattr(las, las_field)
                    elif col_name not in ("R", "G", "B"):  # só cria default para campos obrigatórios
                        data[col_name] = np.zeros(n_points, dtype=default_dtype)

                # Extra dimensions: tudo que não for padrão
                las_dim_names = {d.name.lower() for d in las.point_format.dimensions}
                consumed = set(standard_dims.keys())
                for dim_name in las_dim_names:
                    if dim_name.lower() in consumed:
                        continue
                    if dim_name.lower() in ("x", "y", "z"):
                        continue
                    try:
                        data[dim_name] = getattr(las, dim_name)
                    except (AttributeError, TypeError):
                        pass

                if self._output_format == "csv":
                    self._save_csv(data, output_path)
                else:
                    self._save_geo(data, output_path)

                all_output_files.append(output_path)
                total_output_points += n_points

                self._logger.info(
                    "Arquivo convertido",
                    code="LAS_TO_VECTOR_DONE",
                    path=file_path,
                    output=output_path,
                    points=n_points,
                )

            except Exception as e:
                self._logger.error(
                    "Erro ao converter LAS para vetor",
                    code="LAS_TO_VECTOR_ERR",
                    path=file_path,
                    error=str(e),
                )
                raise

        self.result = {
            "n_input": total_input_points,
            "n_output": total_output_points,
            "output_files": all_output_files,
            "output_dir": self._output_dir,
            "direction": "las_to_vector",
        }
        return True

    def _save_csv(self, data: dict[str, np.ndarray], output_path: str) -> None:
        """Saves data as CSV."""
        import csv

        n = len(data["X"])
        fieldnames = list(data.keys())

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(n):
                row = {k: float(v[i]) for k, v in data.items()}
                writer.writerow(row)

    def _save_geo(self, data: dict[str, np.ndarray], output_path: str) -> None:
        """Saves data as vector file using geopandas."""
        import geopandas as gpd
        from shapely.geometry import Point

        n = len(data["X"])
        geometries = [Point(float(data["X"][i]), float(data["Y"][i]), float(data["Z"][i])) for i in range(n)]

        gdf = gpd.GeoDataFrame(geometry=geometries, crs=self._crs_str)

        for col in data:
            if col in ("X", "Y", "Z"):
                continue
            gdf[col] = [float(v) if isinstance(v, (np.floating,)) else int(v) for v in data[col]]

        gdf.to_file(output_path, driver=self._driver_name())

    def _driver_name(self) -> str:
        """Returns the OGR driver name for the output format."""
        drivers = {
            "gpkg": "GPKG",
            "shp": "ESRI Shapefile",
            "geojson": "GeoJSON",
        }
        return drivers.get(self._output_format, "GPKG")