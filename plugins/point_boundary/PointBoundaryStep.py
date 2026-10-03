# -*- coding: utf-8 -*-
"""
PointBoundaryStep — Step que cria a PointBoundaryTask para execução em QThread
================================================================================
Step do pipeline que orquestra a extração de pontos e geração do limite
via PointBoundaryTask em background thread.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from core.papeline.BaseStep import BaseStep
from core.papeline.BaseTask import BaseTask
from core.papeline.ExecutionContext import ExecutionContext
from .PointBoundaryTask import PointBoundaryTask


class PointBoundaryStep(BaseStep):
    """Step que cria a Task de geração de limite de pontos."""

    def __init__(self, input_path: str = "", tool_key: str = "",
                 output_path: str = "", output_dir: str = "",
                 ratio_inicial: float = 0.10, ratio_step: float = 0.01,
                 limiar_escada: float = 12.0, suavisacao: float = 20.0,
                 n_amostras: int = 100_000, crs: str = "EPSG:31982",
                 salvar_intermediarios: bool = False,
                 csv_x_field: str = "x", csv_y_field: str = "y"):
        self._input_path = input_path
        self._tool_key = tool_key
        self._output_path = output_path
        self._output_dir = output_dir or (os.path.dirname(output_path) if output_path else "")
        self._ratio_inicial = ratio_inicial
        self._ratio_step = ratio_step
        self._limiar_escada = limiar_escada
        self._suavisacao = suavisacao
        self._n_amostras = n_amostras
        self._crs = crs
        self._salvar_intermediarios = salvar_intermediarios
        self._csv_x_field = csv_x_field
        self._csv_y_field = csv_y_field

    def name(self) -> str:
        return "PointBoundaryStep"

    def should_run(self, context: ExecutionContext) -> bool:
        """Só executa se houver file_path definido."""
        return bool(self._input_path or context.input_path)

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        """
        Cria a PointBoundaryTask com os parâmetros do construtor.
        """
        return PointBoundaryTask(
            file_path=self._input_path or context.input_path,
            ratio_inicial=self._ratio_inicial,
            ratio_step=self._ratio_step,
            limiar_escada=self._limiar_escada,
            suavisacao=self._suavisacao,
            n_amostras=self._n_amostras,
            crs=self._crs,
            output_dir=self._output_dir,
            output_path=self._output_path,
            salvar_intermediarios=self._salvar_intermediarios,
            tool_key=self._tool_key or context.tool_key or "Untraceable",
            csv_x_field=self._csv_x_field,
            csv_y_field=self._csv_y_field,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """Mescla os resultados da Task no context."""
        if isinstance(result, dict):
            for key, value in result.items():
                context.set_result(key, value)
