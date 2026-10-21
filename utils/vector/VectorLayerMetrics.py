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
    def calculate_area_hectares(
        gdf: Any,
        field_name: str = "AREA_HA",
        precision: int = 4,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Calcula a area de poligonos em hectares e devolve uma COPIA do GeoDataFrame.

        Diferente dos metodos Qgs (stubs), este opera sobre GeoDataFrame (geopandas).
        Se o CRS for geografico, reprojeta para o UTM estimado do centroide da
        camada (fallback: EPSG:6933, area equivalente) antes de medir.

        Args:
            gdf: GeoDataFrame com coluna de geometria.
            field_name: Nome do campo que recebera a area em hectares.
            precision: Casas decimais do resultado.
            tool_key: Chave da ferramenta para logging.

        Returns:
            GeoDataFrame novo, com o campo de area preenchido.

        Raises:
            ValueError: Sem CRS, sem geometria ou com geometria nao poligonal.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerMetrics")

        if gdf is None or len(gdf) == 0:
            raise ValueError("Camada vazia: nao e possivel calcular area.")
        if gdf.crs is None:
            raise ValueError(
                "Camada sem CRS definido. Defina a projecao do arquivo antes de calcular a area."
            )

        geom_types = set(gdf.geom_type.dropna().unique())
        if not geom_types or not geom_types.issubset({"Polygon", "MultiPolygon"}):
            raise ValueError(
                "A camada deve conter apenas poligonos. Tipos encontrados: "
                + ", ".join(sorted(geom_types))
            )

        metric = gdf
        if gdf.crs.is_geographic:
            try:
                metric = gdf.to_crs(gdf.estimate_utm_crs())
            except Exception as e:
                logger.warning(
                    "estimate_utm_crs falhou — usando EPSG:6933",
                    code="METRIC_UTM_FALLBACK",
                    error=str(e),
                )
                metric = gdf.to_crs("EPSG:6933")

        result = gdf.copy()
        result[field_name] = (metric.geometry.area / 10000.0).round(precision)

        logger.info(
            "Area calculada em hectares",
            code="METRIC_AREA_DONE",
            field=field_name,
            n_features=len(result),
            total_ha=round(float(result[field_name].sum()), precision),
        )
        return result

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