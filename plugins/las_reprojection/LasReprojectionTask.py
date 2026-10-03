# -*- coding: utf-8 -*-
"""
LasReprojectionTask — Task de reprojeção LAS/LAZ
==================================================
Executa a reprojeção de coordenadas de um arquivo LAS/LAZ
usando LasLayerProjection.reproject_las().
"""

from __future__ import annotations

from core.papeline.BaseTask import BaseTask
from utils.las.LasLayerProjection import LasLayerProjection


class LasReprojectionTask(BaseTask):
    """
    Task que reprojeta um arquivo LAS/LAZ.

    Parâmetros:
        input_path: Caminho do LAS de entrada.
        output_path: Caminho do LAS de saída.
        source_crs: CRS de origem.
        target_crs: CRS de destino.
        tool_key: ToolKey para logging.
    """

    def __init__(
        self,
        input_path: str,
        output_path: str,
        source_crs: str,
        target_crs: str,
        tool_key: str = "",
    ):
        super().__init__(description=f"Reprojetando: {input_path}")
        self._input_path = input_path
        self._output_path = output_path
        self._source_crs = source_crs
        self._target_crs = target_crs
        self._tool_key = tool_key

    def _run(self) -> bool:
        """Executa a reprojeção em background."""
        result = LasLayerProjection.reproject_las(
            input_path=self._input_path,
            output_path=self._output_path,
            source_crs=self._source_crs,
            target_crs=self._target_crs,
            tool_key=self._tool_key,
        )

        if result.get("error"):
            raise RuntimeError(result["error"])

        self.result = result
        return True