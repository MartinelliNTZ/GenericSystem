# -*- coding: utf-8 -*-
"""
VectorLayerProjection — CRS, reprojecao e conversao de unidades de camadas vetoriais
======================================================================================
Responsavel por CRS, conversao de unidades e reprojecao de camadas vetoriais.
Nao altera atributos — use VectorLayerAttributes para isso.
Nao salva camada em disco — use VectorLayerSource para isso.

Uso:
    from utils.vector.VectorLayerProjection import VectorLayerProjection
    reprojected = VectorLayerProjection.reproject_layer(layer, target_crs)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pyproj import CRS

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class VectorLayerProjection(BaseUtil):
    """
    Metodos estaticos para CRS, conversao de unidades e reprojecao.
    Nao valida regras de negocio.
    Nao altera atributos.

    Os metodos baseados em GeoDataFrame (``reproject_gdf``, ``is_geographic`` e
    ``crs_epsg``) estao IMPLEMENTADOS — os demais continuam stubs Qgs.
    """

    # CRS padrao do projeto (padrao unico de gravacao das bases).
    DEFAULT_CRS = "EPSG:4326"

    # ── API Publica — GeoDataFrame ───────────────────────────────────

    @staticmethod
    def reproject_gdf(
        gdf: Any,
        target_crs: Any = DEFAULT_CRS,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Reprojetar o GeoDataFrame para o CRS de destino.

        Args:
            gdf: GeoDataFrame de origem.
            target_crs: CRS de destino (ex.: ``"EPSG:4326"`` ou um CRS do pyproj).
            tool_key: Chave da ferramenta para logging.

        Returns:
            GeoDataFrame NOVO no CRS de destino (copia — a origem nao muda).

        Raises:
            ValueError: Camada vazia ou sem CRS definido.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerProjection")

        if gdf is None or len(gdf) == 0:
            raise ValueError("Camada vazia: nao e possivel reprojetar.")
        if gdf.crs is None:
            raise ValueError(
                "Camada sem CRS definido (sem .prj) — nao e possivel reprojetar."
            )

        target = CRS.from_user_input(target_crs)
        if gdf.crs.equals(target):
            return gdf.copy()

        result = gdf.to_crs(target)
        logger.info(
            f"Vetor reprojetado: {gdf.crs} -> {target}",
            code="PROJ_REPROJECT_DONE",
            n_features=int(len(result)),
        )
        return result

    @staticmethod
    def is_geographic(gdf: Any) -> bool:
        """Indica se o CRS da camada e geografico (lat/lon)."""
        return bool(gdf is not None and gdf.crs is not None and gdf.crs.is_geographic)

    @staticmethod
    def crs_epsg(gdf: Any) -> Optional[int]:
        """Codigo EPSG do CRS da camada (``None`` quando ausente/nao identificado)."""
        if gdf is None or gdf.crs is None:
            return None
        return gdf.crs.to_epsg()

    # ── API Publica — Qgs (stubs) ────────────────────────────────────

    @staticmethod
    def convert_distance_to_layer_units(
        layer: Any,
        distance_meters: float,
    ) -> float:
        """
        Converte distancia em metros para unidade da camada.

        Args:
            layer: QgsVectorLayer
            distance_meters: Distancia em metros

        Returns:
            Distancia convertida para unidades da camada.
        """
        return distance_meters

    @staticmethod
    def reproject_layer(
        layer: Any,
        target_crs: Any,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Cria nova camada em memoria reprojetada.

        Args:
            layer: QgsVectorLayer
            target_crs: QgsCoordinateReferenceSystem
            tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerProjection")
        logger.info("reproject_layer chamado — stub", code="PROJ_STUB")
        return None

    @staticmethod
    def ensure_crs(
        layer: Any,
        target_crs: Any,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Garante CRS desejado (reprojeta se necessario).

        Args:
            layer: QgsVectorLayer
            target_crs: QgsCoordinateReferenceSystem
            tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerProjection")
        logger.info("ensure_crs chamado — stub", code="PROJ_STUB")
        return None

    @staticmethod
    def is_geographic_crs(layer: Any) -> bool:
        """
        Verifica se CRS e geografico (lat/lon).

        Args:
            layer: QgsVectorLayer

        Returns:
            True se CRS geografico.
        """
        return False

    @staticmethod
    def reproject_features(
        features: List[Any],
        source_crs: Any,
        target_crs: Any,
        context: Any = None,
    ) -> List[Any]:
        """
        Reprojeta lista de features.

        Args:
            features: Lista de QgsFeature
            source_crs: QgsCoordinateReferenceSystem origem
            target_crs: QgsCoordinateReferenceSystem destino
            context: QgsCoordinateTransformContext (opcional)

        Returns:
            Lista de QgsFeature reprojetadas.
        """
        return features

    @staticmethod
    def get_coordinate_info(
        point: Any,
        canvas_crs: Any = None,
    ) -> Dict[str, Any]:
        """
        Informacoes de coordenada em multiplos formatos (WGS84, DMS, UTM).

        Args:
            point: QgsPointXY / QgsPoint
            canvas_crs: QgsCoordinateReferenceSystem do canvas (opcional)

        Returns:
            Dict com informacoes da coordenada.
        """
        return {
            "x": 0.0,
            "y": 0.0,
            "wgs84_lon": 0.0,
            "wgs84_lat": 0.0,
            "dms_lon": "",
            "dms_lat": "",
            "utm_zone": "",
            "utm_easting": 0.0,
            "utm_northing": 0.0,
        }