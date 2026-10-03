# -*- coding: utf-8 -*-
"""
RasterLayerProcessing — Processamento raster pixel a pixel
============================================================
Responsavel pelo processamento raster destrutivo e operacoes pixel a pixel:
extracao de bandas, mascaras, composicao multibanda.

Uso:
    from utils.raster.RasterLayerProcessing import RasterLayerProcessing
    band_path = RasterLayerProcessing.extract_band("mosaico.tif", 1, tool_key=...)
"""

from __future__ import annotations

from typing import List, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class RasterLayerProcessing(BaseUtil):
    """
    Metodos estaticos para processamento raster pixel a pixel.
    Nao reprojeta — use RasterLayerProjection para isso.
    Nao calcula estatisticas — use RasterLayerMetrics para isso.
    """

    # ── API Publica ──────────────────────────────────────────────────

    @staticmethod
    def extract_band(
        raster_path: str,
        band_num: int,
        output_path: Optional[str] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Extrai banda especifica para GeoTIFF.

        Args:
            raster_path: Caminho do raster
            band_num: Numero da banda (1-based)
            output_path: Caminho de saida (opcional, usa temp se None)
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do arquivo extraido.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerProcessing")
        logger.info("extract_band chamado — stub", code="RASTER_PROC_STUB")
        return output_path or ""

    @staticmethod
    def create_alpha_mask(
        raster_path: str,
        nodata_value: Optional[float] = None,
        output_path: Optional[str] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Cria mascara alpha (byte: 0/255) a partir de NoData.

        Args:
            raster_path: Caminho do raster
            nodata_value: Valor NoData (usa do raster se None)
            output_path: Caminho de saida (opcional)
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho da mascara alpha.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerProcessing")
        logger.info("create_alpha_mask chamado — stub", code="RASTER_PROC_STUB")
        return output_path or ""

    @staticmethod
    def compose_multiband_raster(
        band_files: List[str],
        output_path: Optional[str] = None,
        create_alpha: bool = False,
        alpha_band_path: Optional[str] = None,
        creation_options: str = "",
        nodata: Optional[float] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Compõe múltiplos GeoTIFFs single-band em um raster multibanda.

        Usado pelo IdwInterpolatorPlugin para gerar:
        - mosaico_rgb.tif (3 bandas: R, G, B)
        - mosaico_rgbz.tif (4 bandas: R, G, B, Z)

        Compressão LZW, tiled 512x512, BIGTIFF=YES.
        Chunked processing (2048 linhas) para evitar estouro de RAM.

        Args:
            band_files: Lista de caminhos das bandas individuais.
            output_path: Caminho de saída do raster composto.
            create_alpha: Se True, cria banda alpha (0/255) a partir do NoData.
            alpha_band_path: Caminho da mascara alpha (se create_alpha=True).
            creation_options: Opcoes GDAL extras (string, ignorado por enquanto).
            nodata: Valor nodata para o raster composto. Se None, nao define.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho do raster composto, ou string vazia se erro.
        """
        import rasterio
        from rasterio.windows import Window
        import numpy as np
        import os

        logger = BaseUtil._get_logger(tool_key, "RasterLayerProcessing")

        if not band_files:
            logger.error("Nenhuma banda fornecida", code="RASTER_COMPOSE_NO_BANDS")
            return ""

        if not output_path:
            logger.error("Nenhum caminho de saida", code="RASTER_COMPOSE_NO_OUTPUT")
            return ""

        logger.info(
            "Compondo raster multibanda",
            code="RASTER_COMPOSE_START",
            n_bands=len(band_files),
            output=output_path,
        )

        try:
            # Abre primeira banda para obter metadados
            with rasterio.open(band_files[0]) as src_first:
                height = src_first.height
                width = src_first.width
                transform = src_first.transform
                crs = src_first.crs
                dtype = src_first.dtypes[0]

            n_bands = len(band_files)
            if create_alpha and alpha_band_path:
                n_bands += 1

            meta = {
                "driver": "GTiff",
                "height": height,
                "width": width,
                "count": n_bands,
                "dtype": dtype,
                "crs": crs,
                "transform": transform,
                "compress": "lzw",
                "predictor": 2,
                "tiled": True,
                "blockxsize": 512,
                "blockysize": 512,
                "BIGTIFF": "YES",
            }
            if nodata is not None:
                meta["nodata"] = nodata

            # Se 3 bandas RGB, define photometric
            if len(band_files) == 3 and not create_alpha:
                meta["photometric"] = "RGB"
            elif len(band_files) == 4 and not create_alpha:
                # R+G+B+Z — sem photometric específico
                pass

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with rasterio.open(output_path, "w", **meta) as dst:
                chunk_linhas = 2048
                for banda_idx, bf in enumerate(band_files, start=1):
                    logger.debug(
                        f"Escrevendo banda {banda_idx}/{len(band_files)}",
                        code="RASTER_COMPOSE_BAND",
                        file=bf,
                    )
                    with rasterio.open(bf) as src_band:
                        for rs in range(0, height, chunk_linhas):
                            re = min(rs + chunk_linhas, height)
                            win = Window(0, rs, width, re - rs)
                            data = src_band.read(1, window=win)
                            dst.write(data, banda_idx, window=win)

                # Banda alpha opcional
                if create_alpha and alpha_band_path:
                    logger.debug("Escrevendo banda alpha", code="RASTER_COMPOSE_ALPHA")
                    with rasterio.open(alpha_band_path) as src_alpha:
                        for rs in range(0, height, chunk_linhas):
                            re = min(rs + chunk_linhas, height)
                            win = Window(0, rs, width, re - rs)
                            alpha = src_alpha.read(1, window=win)
                            dst.write(alpha, n_bands, window=win)

            sz = os.path.getsize(output_path) / 1e6
            logger.info(
                "Raster multibanda composto",
                code="RASTER_COMPOSE_DONE",
                output=output_path,
                size_mb=round(sz, 1),
                n_bands=n_bands,
            )
            return output_path

        except Exception as e:
            logger.error(
                "Erro ao compor raster multibanda",
                code="RASTER_COMPOSE_ERR",
                error=str(e),
            )
            return ""

    @staticmethod
    def apply_nodata_mask(
        raster_path: str,
        mask_path: str,
        output_path: Optional[str] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Aplica mascara NoData em um raster.

        Args:
            raster_path: Caminho do raster
            mask_path: Caminho da mascara (byte: 0/255)
            output_path: Caminho de saida (opcional)
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do raster com mascara aplicada.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerProcessing")
        logger.info("apply_nodata_mask chamado — stub", code="RASTER_PROC_STUB")
        return output_path or ""