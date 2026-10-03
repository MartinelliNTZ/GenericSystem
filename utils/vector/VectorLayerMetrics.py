# -*- coding: utf-8 -*-
"""
VectorLayerMetrics — Metricas espaciais de camadas vetoriais
==============================================================
Responsavel pela leitura e calculos espaciais.
NAO altera dados, apenas mede comprimento, area, perimetro.

Uso:
    from utils.vector.VectorLayerMetrics import VectorLayerMetrics
    VectorLayerMetrics.calculate_line_length(layer, "comp_eli", use_ellipsoidal=True)
"""

from __future__ import annotations

from typing import Any, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class VectorLayerMetrics(BaseUtil):
    """
    Metodos estaticos para calculo de metricas espaciais.
    Nao transforma geometrias — use VectorLayerGeometry para isso.
    Nao reprojeta — use VectorLayerProjection para isso.
    """

    # ── API Publica ──────────────────────────────────────────────────

    @staticmethod
    def calculate_line_length(
        layer: Any,
        field_name: str,
        use_ellipsoidal: bool = True,
        precision: int = 4,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        """
        Calcula comprimento de linhas (elipsoidal ou cartesiano).

        Args:
            layer: QgsVectorLayer
            field_name: Nome do campo para armazenar resultado
            use_ellipsoidal: Usar calculo elipsoidal
            precision: Precisao decimal
            tool_key: Chave da ferramenta para logging
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerMetrics")
        logger.info("calculate_line_length chamado — stub", code="METRIC_STUB")

    @staticmethod
    def calculate_polygon_area(
        layer: Any,
        field_name: str,
        use_ellipsoidal: bool = True,
        precision: int = 4,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        """
        Calcula area de poligonos em hectares.

        Args:
            layer: QgsVectorLayer
            field_name: Nome do campo para armazenar resultado
            use_ellipsoidal: Usar calculo elipsoidal
            precision: Precisao decimal
            tool_key: Chave da ferramenta para logging
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerMetrics")
        logger.info("calculate_polygon_area chamado — stub", code="METRIC_STUB")

    @staticmethod
    def calculate_polygon_perimeter(
        layer: Any,
        field_name: str,
        use_ellipsoidal: bool = True,
        precision: int = 4,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        """
        Calcula perimetro de poligonos.

        Args:
            layer: QgsVectorLayer
            field_name: Nome do campo para armazenar resultado
            use_ellipsoidal: Usar calculo elipsoidal
            precision: Precisao decimal
            tool_key: Chave da ferramenta para logging
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerMetrics")
        logger.info("calculate_polygon_perimeter chamado — stub", code="METRIC_STUB")