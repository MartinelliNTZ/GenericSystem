# -*- coding: utf-8 -*-
"""
InterpolatorUtils — Utilitários genéricos para interpolação de nuvens de pontos
=================================================================================
Atualmente suporta IDW (Inverse Distance Weighting).
Futuramente: Kriging, Spline, Nearest Neighbor.

Métodos:
    idw_tile_para_disco()           — interpola um tile via IDW e salva em disco
    calcular_tiles_por_densidade()   — divide área em tiles baseado na densidade
    mesclar_banda()                 — mescla tiles em banda completa via memmap
    salvar_tile_tif()               — salva array 2D como GeoTIFF tile
"""

from __future__ import annotations

import math
import os
import time
from typing import Optional

import numpy as np
from scipy.spatial import cKDTree
from rasterio.transform import from_origin, rowcol
import rasterio

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class InterpolatorUtils(BaseUtil):
    """
    Métodos estáticos para interpolação de nuvens de pontos em grid regular.
    """

    @staticmethod
    def salvar_tile_tif(
        path: str,
        arr: np.ndarray,
        transform,
        crs_str: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        nodata: Optional[float] = None,
    ):
        """
        Salva array 2D como GeoTIFF de 1 banda.
        BIGTIFF=YES para suportar arquivos >4GB.

        Args:
            nodata: Valor nodata para o GeoTIFF. Se None, nao define.
        """
        logger = BaseUtil._get_logger(tool_key, "InterpolatorUtils")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            profile = dict(
                driver="GTiff",
                height=arr.shape[0],
                width=arr.shape[1],
                count=1,
                dtype=arr.dtype,
                crs=crs_str,
                transform=transform,
                BIGTIFF="YES",
            )
            if nodata is not None:
                profile["nodata"] = nodata
            with rasterio.open(path, "w", **profile) as dst:
                dst.write(arr, 1)
        except Exception as e:
            logger.error(
                f"Erro ao salvar tile GeoTIFF: {path} -> {e}",
            )
            raise

    @staticmethod
    def calcular_tiles_por_densidade(
        x_pts: np.ndarray,
        y_pts: np.ndarray,
        min_x_g: float,
        max_x_g: float,
        min_y_g: float,
        max_y_g: float,
        resol: float,
        pontos_por_chunk: int,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        max_tile_pixels: int = 0,
    ) -> list:
        """
        Divide a area em tiles com ~pontos_por_chunk pontos cada.

        Quando `max_tile_pixels > 0`, a grade tambem considera o numero maximo
        de pixels por tile para evitar OOM em np.meshgrid (idw_tile_para_disco).
        O numero final de tiles eh o maior entre o necessario por pontos e por pixels.

        Args:
            max_tile_pixels: Limite maximo de pixels (tile_h * tile_w) por tile.
                             0 = desabilitado (comportamento anterior).

        Returns:
            Lista de (x0, x1, y0, y1, row, col) — bounds geograficos + indices.
        """
        logger = BaseUtil._get_logger(tool_key, "InterpolatorUtils")
        n_total = len(x_pts)

        # Tiles baseados em pontos
        n_alvo_pontos = max(1, int(math.ceil(n_total / pontos_por_chunk)))
        lado = max(1, int(math.ceil(math.sqrt(n_alvo_pontos))))
        n_cols = lado
        n_rows = int(math.ceil(n_alvo_pontos / n_cols))

        # Tiles baseados em pixels
        if max_tile_pixels > 0 and resol > 0:
            grid_w = max(1, int(math.ceil((max_x_g - min_x_g) / resol)))
            grid_h = max(1, int(math.ceil((max_y_g - min_y_g) / resol)))
            total_pixels = grid_w * grid_h
            n_alvo_pixels = max(1, int(math.ceil(total_pixels / max_tile_pixels)))

            if n_alvo_pixels > n_alvo_pontos:
                n_cols = int(math.ceil(math.sqrt(n_alvo_pixels)))
                n_rows = int(math.ceil(n_alvo_pixels / n_cols))
                logger.info(
                    f"Pixel-constrained tiles: {n_alvo_pixels} tiles "
                    f"(pts: {n_alvo_pontos}) | "
                    f"grid: {grid_w}x{grid_h} px | "
                    f"max_pixels/tile: {max_tile_pixels:,}",
                )

        dx = (max_x_g - min_x_g) / n_cols
        dy = (max_y_g - min_y_g) / n_rows

        tiles = []
        for row in range(n_rows):
            for col in range(n_cols):
                x0 = min_x_g + col * dx
                x1 = min_x_g + (col + 1) * dx
                y0 = min_y_g + row * dy
                y1 = min_y_g + (row + 1) * dy
                tiles.append((x0, x1, y0, y1, row, col))

        px_per_tile = (int(math.ceil(dx / resol)), int(math.ceil(dy / resol)))
        logger.info(
            f"Grade de tiles calculada: {n_cols}x{n_rows} = {len(tiles)} tiles, "
            f"{pontos_por_chunk:,} pts/tile, "
            f"~{px_per_tile[0]}x{px_per_tile[1]} px/tile",
        )
        return tiles

    @staticmethod
    def idw_tile_para_disco(
        chunk_idx: int,
        total_chunks: int,
        tile_tag: str,
        tile_bounds: tuple,
        grid_bounds: tuple,
        resol: float,
        x_pts: np.ndarray,
        y_pts: np.ndarray,
        r_pts: Optional[np.ndarray],
        g_pts: Optional[np.ndarray],
        b_pts: Optional[np.ndarray],
        z_pts: Optional[np.ndarray],
        k: int,
        power: float,
        raio_max: float,
        overlap: float,
        crs_str: str,
        path_r_out: str,
        path_g_out: str,
        path_b_out: str,
        path_z_out: Optional[str],
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> tuple:
        """
        Interpola um tile com IDW e salva em disco.

        Retomada automatica: se os arquivos de saida existem, pula.

        Returns:
            (chunk_idx, tile_tag, row0, row1, col0, col1, status)
        """
        t0 = time.perf_counter()

        paths_exist = True
        for p in (path_r_out, path_g_out, path_b_out, path_z_out):
            if p and not os.path.exists(p):
                paths_exist = False
                break

        if paths_exist:
            with rasterio.open(path_r_out) as src:
                r0, c0 = rowcol(src.transform, src.bounds.left, src.bounds.top)
                row0, col0 = int(r0), int(c0)
                row1, col1 = row0 + src.height, col0 + src.width
            elapsed = time.perf_counter() - t0
            logger = BaseUtil._get_logger(tool_key, "InterpolatorUtils")
            logger.info(
                f"Tile {chunk_idx+1:>4}/{total_chunks} [{tile_tag}] | PULADO ({elapsed:.1f}s)",
            )
            return (chunk_idx, tile_tag, row0, row1, col0, col1, 'PULADO')

        x0_tile, x1_tile, y0_tile, y1_tile = tile_bounds
        min_x_g, max_x_g, min_y_g, max_y_g = grid_bounds

        col0 = int(round((x0_tile - min_x_g) / resol))
        col1 = int(round((x1_tile - min_x_g) / resol))
        row0 = int(round((max_y_g - y1_tile) / resol))
        row1 = int(round((max_y_g - y0_tile) / resol))
        tile_w = col1 - col0
        tile_h = row1 - row0

        if tile_w <= 0 or tile_h <= 0:
            return (chunk_idx, tile_tag, row0, row1, col0, col1, 'VAZIO')

        # Query com overlap
        x0_q = x0_tile - overlap
        x1_q = x1_tile + overlap
        y0_q = y0_tile - overlap
        y1_q = y1_tile + overlap

        mask = (
            (x_pts >= x0_q) & (x_pts <= x1_q) &
            (y_pts >= y0_q) & (y_pts <= y1_q)
        )
        n_locais = int(np.sum(mask))

        xi = min_x_g + (col0 + 0.5 + np.arange(tile_w)) * resol
        yi = max_y_g - (row0 + 0.5 + np.arange(tile_h)) * resol
        xi_grid, yi_grid = np.meshgrid(xi, yi)
        query_pts = np.column_stack((xi_grid.ravel(), yi_grid.ravel()))

        tile_transform = from_origin(
            min_x_g + col0 * resol, max_y_g - row0 * resol, resol, resol
        )

        if n_locais < k:
            z = np.zeros((tile_h, tile_w), dtype=np.uint8)
            if path_r_out:
                InterpolatorUtils.salvar_tile_tif(path_r_out, z, tile_transform, crs_str, nodata=0)
            if path_g_out:
                InterpolatorUtils.salvar_tile_tif(path_g_out, z, tile_transform, crs_str, nodata=0)
            if path_b_out:
                InterpolatorUtils.salvar_tile_tif(path_b_out, z, tile_transform, crs_str, nodata=0)
            if path_z_out:
                z_f32 = np.zeros((tile_h, tile_w), dtype=np.float32)
                InterpolatorUtils.salvar_tile_tif(path_z_out, z_f32, tile_transform, crs_str, nodata=-9999.0)
            return (chunk_idx, tile_tag, row0, row1, col0, col1, 'VAZIO')

        # IDW
        pts_locais = np.column_stack((x_pts[mask], y_pts[mask]))
        tree = cKDTree(pts_locais)
        dist, idx = tree.query(query_pts, k=k, workers=1)

        valido = dist[:, 0] <= raio_max
        exato = dist == 0.0
        hit_exato = exato.any(axis=1)

        with np.errstate(divide='ignore', invalid='ignore'):
            pesos = 1.0 / np.power(dist, power)
        if hit_exato.any():
            pesos[hit_exato] = np.where(exato[hit_exato], 1.0, 0.0)

        soma_pesos = pesos.sum(axis=1, keepdims=True)
        soma_pesos = np.where(soma_pesos == 0, 1.0, soma_pesos)
        pesos_norm = pesos / soma_pesos

        # Interpola bandas RGB (uint8)
        if path_r_out and r_pts is not None:
            r_vals = r_pts[mask][idx].astype(np.float64)
            r_interp = (pesos_norm * r_vals).sum(axis=1)
            r_interp[~valido] = 0
            r_tile = np.clip(r_interp, 0, 255).astype(np.uint8).reshape(tile_h, tile_w)
            InterpolatorUtils.salvar_tile_tif(path_r_out, r_tile, tile_transform, crs_str, nodata=0)

        if path_g_out and g_pts is not None:
            g_vals = g_pts[mask][idx].astype(np.float64)
            g_interp = (pesos_norm * g_vals).sum(axis=1)
            g_interp[~valido] = 0
            g_tile = np.clip(g_interp, 0, 255).astype(np.uint8).reshape(tile_h, tile_w)
            InterpolatorUtils.salvar_tile_tif(path_g_out, g_tile, tile_transform, crs_str, nodata=0)

        if path_b_out and b_pts is not None:
            b_vals = b_pts[mask][idx].astype(np.float64)
            b_interp = (pesos_norm * b_vals).sum(axis=1)
            b_interp[~valido] = 0
            b_tile = np.clip(b_interp, 0, 255).astype(np.uint8).reshape(tile_h, tile_w)
            InterpolatorUtils.salvar_tile_tif(path_b_out, b_tile, tile_transform, crs_str, nodata=0)

        # Interpola Z (float32)
        if path_z_out and z_pts is not None:
            z_vals = z_pts[mask][idx].astype(np.float64)
            z_interp = (pesos_norm * z_vals).sum(axis=1)
            z_interp[~valido] = np.nan
            z_tile = z_interp.astype(np.float32).reshape(tile_h, tile_w)
            InterpolatorUtils.salvar_tile_tif(path_z_out, z_tile, tile_transform, crs_str, nodata=-9999.0)

        elapsed = time.perf_counter() - t0
        logger = BaseUtil._get_logger(tool_key, "InterpolatorUtils")
        logger.info(
            f"Tile {chunk_idx+1:>4}/{total_chunks} [{tile_tag}] | pts={n_locais:>8} | {elapsed:.1f}s",
        )
        return (chunk_idx, tile_tag, row0, row1, col0, col1, 'OK')

    @staticmethod
    def mesclar_banda(
        nome_banda: str,
        tile_paths: list[str],
        height: int,
        width: int,
        transform,
        crs_str: str,
        out_path: str,
        dtype: np.dtype = np.uint8,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        nodata: Optional[float] = None,
    ) -> str:
        """
        Le todos os tiles de uma banda e os escreve num GeoTIFF completo via memmap.
        Usa rowcol() para calcular posicao de cada tile no grid global.
        """
        tic = time.perf_counter()
        logger = BaseUtil._get_logger(tool_key, "InterpolatorUtils")
        logger.info(f"[{nome_banda}] Mesclando {len(tile_paths)} tiles", code="IDW_MERGE_START", banda=nome_banda, n_tiles=len(tile_paths), output=out_path)

        bin_path = out_path.replace(".tif", ".bin")
        mm = np.memmap(bin_path, dtype=dtype, mode="w+", shape=(height, width))

        for tp in tile_paths:
            if not os.path.exists(tp):
                continue
            with rasterio.open(tp) as src:
                data = src.read(1)
                r0, c0 = rowcol(transform, src.bounds.left, src.bounds.top)
                r0, c0 = int(r0), int(c0)
                r1, c1 = r0 + data.shape[0], c0 + data.shape[1]

                r0c, r1c = max(0, r0), min(height, r1)
                c0c, c1c = max(0, c0), min(width, c1)
                if r1c <= r0c or c1c <= c0c:
                    continue
                th = r1c - r0c
                tw = c1c - c0c
                mm[r0c:r1c, c0c:c1c] = data[:th, :tw]

        mm.flush()

        profile = dict(
            driver="GTiff",
            height=height, width=width,
            count=1, dtype=dtype,
            crs=crs_str, transform=transform,
            compress="lzw", predictor=2,
            tiled=True, blockxsize=512, blockysize=512,
            BIGTIFF="YES",
        )
        if nodata is not None:
            profile["nodata"] = nodata
        with rasterio.open(out_path, "w", **profile) as dst:
            chunk_linhas = 2048
            for rs in range(0, height, chunk_linhas):
                re = min(rs + chunk_linhas, height)
                win = rasterio.windows.Window(0, rs, width, re - rs)
                dst.write(mm[rs:re, :], 1, window=win)

        del mm
        try:
            os.remove(bin_path)
        except OSError:
            pass

        elapsed = time.perf_counter() - tic
        logger.info(
            f"[{nome_banda}] Mesclagem concluida ({elapsed:.1f}s)",
            code="IDW_MERGE_DONE",
            banda=nome_banda,
            elapsed_s=round(elapsed, 1),
            output=out_path,
        )
        return out_path