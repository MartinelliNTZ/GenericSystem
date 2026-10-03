# -*- coding: utf-8 -*-
"""
RasterLayerRendering — Simbologia e visualizacao de rasters (estilo QML)
==========================================================================
Responsavel pela simbologia e visualizacao de rasters: estilo QML,
rampas de cor, transparencia, percentis.

Uso:f
    from utils.raster.RasterLayerRendering import RasterLayerRendering
    result = RasterLayerRendering.generate_percentil_multiband_style(
        raster_path="mosaico.tif", band_indices=[1,2,3], tool_key=...
    )
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class RasterLayerRendering(BaseUtil):
    """
    Metodos estaticos para simbologia e visualizacao de rasters.
    Nao processa pixels — use RasterLayerProcessing para isso.
    Nao salva/carrega rasters — use RasterLayerSource para isso.
    """

    # ── API Publica ──────────────────────────────────────────────────

    @staticmethod
    def save_sidecar_style(
        raster_path: str,
        qml_root: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[str]:
        """
        Salva QML sidecar (mesma pasta do raster).

        Args:
            raster_path: Caminho do raster
            qml_root: Conteudo QML
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do QML salvo ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerRendering")
        logger.info("save_sidecar_style chamado — stub", code="RENDER_STUB")
        return None

    @staticmethod
    def apply_qml_inplace(
        layer: Any,
        qml_path: str,
        feedback: Any = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Aplica QML em camada raster existente.

        Args:
            layer: QgsRasterLayer
            qml_path: Caminho do arquivo QML
            feedback: QgsProcessingFeedback (opcional)
            tool_key: Chave da ferramenta para logging

        Returns:
            True se sucesso.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerRendering")
        logger.info("apply_qml_inplace chamado — stub", code="RENDER_STUB")
        return False

    @staticmethod
    def apply_qml_to_layer(
        raster_path: str,
        qml_path: str,
        context: Any = None,
        feedback: Any = None,
        layer_name: Optional[str] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Carrega raster + aplica QML + registra no context.

        Args:
            raster_path: Caminho do raster
            qml_path: Caminho do arquivo QML
            context: QgsProcessingContext (opcional)
            feedback: QgsProcessingFeedback (opcional)
            layer_name: Nome da camada (opcional)
            tool_key: Chave da ferramenta para logging

        Returns:
            True se sucesso.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerRendering")
        logger.info("apply_qml_to_layer chamado — stub", code="RENDER_STUB")
        return False

    @staticmethod
    def generate_percentil_multiband_style(
        raster_path: str,
        band_indices: List[int],
        lower_pct: float = 2.0,
        upper_pct: float = 98.0,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        alpha_band: int = -1,
        opacity: float = 1.0,
        algorithm: Any = None,
        layer: Any = None,
        feedback: Any = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Pipeline completo: calcula percentis -> gera QML -> salva sidecar
        -> salva backup -> aplica estilo.

        Args:
            raster_path: Caminho do raster
            band_indices: Indices das bandas (1-based)
            lower_pct: Percentil inferior
            upper_pct: Percentil superior
            min_value: Valor minimo (opcional, override percentil)
            max_value: Valor maximo (opcional, override percentil)
            alpha_band: Banda alpha (-1 = sem alpha)
            opacity: Opacidade (0.0-1.0)
            algorithm: QgsProcessingAlgorithm (opcional)
            layer: QgsRasterLayer (opcional, aplicar in-place)
            feedback: QgsProcessingFeedback (opcional)
            tool_key: Chave da ferramenta para logging

        Returns:
            Dict com qml_path, backup_path, style_applied, global_min, global_max.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerRendering")
        logger.info("generate_percentil_multiband_style chamado — stub", code="RENDER_STUB")
        return {
            "qml_path": None,
            "backup_path": None,
            "style_applied": False,
            "global_min": 0.0,
            "global_max": 0.0,
        }

    @staticmethod
    def save_qml_backup(
        qml_root: str,
        output_base: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[str]:
        """
        Salva backup do QML em temp/styles.

        Args:
            qml_root: Conteudo QML
            output_base: Nome base para o arquivo
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do backup ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerRendering")
        logger.info("save_qml_backup chamado — stub", code="RENDER_STUB")
        return None