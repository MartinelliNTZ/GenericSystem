# -*- coding: utf-8 -*-
"""
LasReprojectionStep — Step de reprojeção LAS/LAZ
==================================================
Step que cria uma LasReprojectionTask para reprojetar
um arquivo LAS/LAZ de um CRS de origem para um CRS de destino.
"""

from __future__ import annotations

from core.papeline.BaseStep import BaseStep
from core.papeline.BaseTask import BaseTask
from core.papeline.ExecutionContext import ExecutionContext
from plugins.las_reprojection.LasReprojectionTask import LasReprojectionTask


class LasReprojectionStep(BaseStep):
    """
    Step que reprojeta um arquivo LAS/LAZ.

    Parâmetros do construtor:
        source_crs: CRS de origem (ex: "EPSG:4326").
        target_crs: CRS de destino (ex: "EPSG:31983").
        output_path: Caminho completo do arquivo de saída (se vazio, usa output_subdir).
        advance_input: Se False (padrão), não avança input_path.
        input_path: Caminho específico (opcional, sobrescreve context.input_path).
    """

    subfolder = "lasreprojection"
    advance_input = False

    def __init__(
        self,
        source_crs: str,
        target_crs: str,
        output_path: str = "",
        advance_input: bool = False,
        input_path: str = "",
    ):
        self._source_crs = source_crs
        self._target_crs = target_crs
        self._custom_output_path = output_path
        self.advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "lasreprojection"

    def should_run(self, context: ExecutionContext) -> bool:
        path = self._custom_input_path or context.input_path
        return bool(path) and bool(self._source_crs) and bool(self._target_crs)

    def create_task(self, context: ExecutionContext) -> BaseTask | None:
        path = self._custom_input_path or context.input_path

        if self._custom_output_path:
            output_path = self._custom_output_path
        else:
            output = self.output_subdir(context)
            basename = context.get_result("input_basename", "output")
            output_path = f"{output}/{basename}_reprojected.las"

        return LasReprojectionTask(
            input_path=path,
            output_path=output_path,
            source_crs=self._source_crs,
            target_crs=self._target_crs,
            tool_key=context.tool_key,
        )

    def on_success(self, context: ExecutionContext, result: any) -> None:
        if isinstance(result, dict):
            context.set_result("reprojection_result", result)
        if self.advance_input:
            self.advance_input(context)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)