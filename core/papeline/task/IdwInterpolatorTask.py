# -*- coding: utf-8 -*-
"""
IdwInterpolatorTask — Task para interpolacao IDW de arquivos LAS
==================================================================
Task que recebe um diretorio com arquivos LAS, le todos e executa
interpolacao IDW, gerando rasters.

Utiliza InterpolatorUtils internamente.
"""

from __future__ import annotations

import glob
import json
import os as _os
import shutil
from typing import Optional

import numpy as np
from joblib import Parallel, delayed

from core.governor.CpuGovernor import CpuGovernor
from core.governor.ResourceGovernor import ResourceGovernor
from core.manager.SignalManager import SignalManager
from core.papeline.BaseTask import BaseTask
from utils.raster.InterpolatorUtils import InterpolatorUtils
from utils.raster.RasterLayerProcessing import RasterLayerProcessing


class IdwInterpolatorTask(BaseTask):
    """Task IDW que interpola todos os .las/.laz de um diretorio."""

    BYTES_PER_POINT: int = 32
    MAX_TILE_PIXELS: int = 10_000_000

    def __init__(
        self,
        input_dir: str,
        output_path: str,
        target_bands: dict,
        merge_bands: bool = True,
        resolution_m: float = 0.01,
        idw_k: int = 5,
        idw_power: float = 2.0,
        idw_max_radius: float = 0.5,
        idw_overlap: float = 3.0,
        crs_str: str = "EPSG:31982",
        delete_tiles: bool = True,
        save_las: bool = False,
        governor: Optional[ResourceGovernor] = None,
    ):
        super().__init__(
            description=f"IDW: {_os.path.basename(input_dir)}",
            governor=governor,
        )
        self._input_dir = input_dir
        self._output_path = output_path
        self._target_bands = target_bands
        self._merge_bands = merge_bands
        self._resolution_m = resolution_m
        self._idw_k = idw_k
        self._idw_power = idw_power
        self._idw_max_radius = idw_max_radius
        self._idw_overlap = idw_overlap
        self._crs_str = crs_str
        self._delete_tiles = delete_tiles
        self._save_las = save_las
        self._temp_dir: str | None = None
        self._n_pontos_total: int = 0

    @property
    def estimated_ram(self) -> int:
        """RAM estimada: n_pontos * 32 bytes."""
        n = max(self._n_pontos_total, 1_000_000)
        return n * self.BYTES_PER_POINT

    def _obter_arquivos_las(self) -> list[str]:
        """Escaneia o diretorio de entrada por arquivos .las/.laz."""
        return sorted(
            glob.glob(_os.path.join(self._input_dir, "*.las"))
            + glob.glob(_os.path.join(self._input_dir, "*.laz"))
        )

    def _log_memory_status(self, stage: str, estimated_ram_extra: int = 0) -> None:
        """Loga status de RAM via governor."""
        if self._governor is not None:
            snap = self._governor.snapshot(estimated_ram=self.estimated_ram + estimated_ram_extra)
            self.get_logger().debug(
                f"[RAM] {stage}: "
                f"Sys {snap.get('used_system_human', '?')}/"
                f"{snap.get('total_human', '?')} | "
                f"Proc {snap.get('process_human', '?')} | "
                f"Headroom {snap.get('headroom_human', '?')} | "
                f"Pressao {snap.get('memory_pressure', 0):.2f}",
                code="IDW_TASK_RAM", stage=stage,
            )

    def _estimar_ram_por_tile(self, tile_pixels: int, n_bandas: int) -> int:
        """Estima RAM necessaria para processar UM tile raster."""
        k = self._idw_k
        bytes_por_pixel = 8 + 8 + 16 + k * 8 + k * 8 + k * 8
        bytes_por_pixel += n_bandas * k * 8
        return tile_pixels * bytes_por_pixel

    def _check_pixel_ram(self, width: int, height: int, n_cpus: int, n_bandas: int) -> bool:
        """Verifica se ha RAM suficiente para processar tiles no grid."""
        if self._governor is None:
            return True
        total_pixels = width * height
        n_tiles_min = max(1, (total_pixels + self.MAX_TILE_PIXELS - 1) // self.MAX_TILE_PIXELS)
        tile_pixels = (total_pixels + n_tiles_min - 1) // n_tiles_min
        ram_por_tile = self._estimar_ram_por_tile(tile_pixels, n_bandas)
        ram_paralela = ram_por_tile * min(n_cpus, 8)
        can, reason = self._governor.can_execute(estimated_ram=ram_paralela)
        if not can:
            self.get_logger().error(
                "RAM insuficiente para tiles no grid",
                code="IDW_TASK_OOM_PIXEL",
                width=width, height=height,
                tile_pixels=tile_pixels,
                ram_por_tile=ram_por_tile,
                ram_paralela=ram_paralela,
                reason=reason,
            )
            return False
        return True

    def _limpar_temp(self):
        """Remove pastas de tiles raster."""
        if not self._temp_dir or not _os.path.isdir(self._temp_dir):
            return
        if not self._delete_tiles:
            self.get_logger().info("Tiles raster mantidos", code="IDW_TASK_KEEP_TILES")
            return
        for sub in ("r", "g", "b", "z"):
            subp = _os.path.join(self._temp_dir, sub)
            if _os.path.isdir(subp):
                try:
                    shutil.rmtree(subp, ignore_errors=True)
                except Exception as e:
                    self.get_logger().warning(
                        f"Falha ao limpar subpasta {sub}",
                        code="IDW_TASK_TILE_CLEAN_ERR", error=str(e),
                    )
        self.get_logger().info("Tiles raster removidos", code="IDW_TASK_TEMP_CLEAN_DONE")

    def _limpar_las(self):
        """Remove os arquivos .las originais se save_las=False."""
        if self._save_las:
            return
        las_files = self._obter_arquivos_las()
        for path in las_files:
            try:
                if _os.path.isfile(path):
                    _os.remove(path)
                    self.get_logger().debug(
                        f"LAS removido: {path}",
                        code="IDW_TASK_LAS_REMOVED",
                    )
            except Exception as e:
                self.get_logger().warning(
                    f"Falha ao remover LAS {path}",
                    code="IDW_TASK_LAS_REMOVE_ERR", error=str(e),
                )

    def _run(self) -> bool:
        """Pipeline IDW: le arquivos LAS do diretorio e interpola."""
        logger = self.get_logger()
        signals = SignalManager.instance()

        input_dir = self._input_dir
        output_path = self._output_path
        target = self._target_bands
        merge_bands = self._merge_bands
        resol_m = self._resolution_m
        k = self._idw_k
        power = self._idw_power
        raio_max = self._idw_max_radius
        overlap = self._idw_overlap
        crs_str = self._crs_str

        las_files = self._obter_arquivos_las()
        if not las_files:
            logger.error(
                "Nenhum arquivo LAS encontrado no diretorio",
                code="IDW_TASK_NO_FILES",
                input_dir=input_dir,
            )
            return False

        logger.info(
            "Iniciando interpolacao IDW",
            code="IDW_TASK_START",
            n_files=len(las_files),
            input_dir=input_dir,
        )
        self._log_memory_status("inicio")

        # --- Estagio 1: Leitura dos LAS ---
        signals.hud_update.emit({"message": "Lendo arquivos LAS..."})
        signals.progress_update.emit(0.0)

        if not self._check_during_execution():
            return False

        from utils.las.LasLayerSource import LasLayerSource

        all_x, all_y = [], []
        all_r, all_g, all_b, all_z = [], [], [], []
        n_pontos_total = 0

        for i, las_path in enumerate(las_files):
            if not self._check_during_execution():
                return False

            signals.hud_update.emit({
                "message": f"Lendo {_os.path.basename(las_path)} ({i+1}/{len(las_files)})..."
            })

            arrays = LasLayerSource.extract_point_arrays(
                las_path, target, tool_key=self._tool_key,
            )
            n = arrays["n_points"]
            n_pontos_total += n
            all_x.append(arrays["x"])
            all_y.append(arrays["y"])
            if target.get("r"): all_r.append(arrays["red"])
            if target.get("g"): all_g.append(arrays["green"])
            if target.get("b"): all_b.append(arrays["blue"])
            if target.get("z"): all_z.append(arrays["z"])

            logger.debug(
                f"Lido: {_os.path.basename(las_path)} ({n} pts)",
                code="IDW_TASK_FILE_READ", file=i+1, pontos=n,
            )

        self._n_pontos_total = n_pontos_total

        x_pts = np.concatenate(all_x)
        y_pts = np.concatenate(all_y)
        r_pts = np.concatenate(all_r) if all_r else np.array([], dtype=np.uint16)
        g_pts = np.concatenate(all_g) if all_g else np.array([], dtype=np.uint16)
        b_pts = np.concatenate(all_b) if all_b else np.array([], dtype=np.uint16)
        z_pts = np.concatenate(all_z) if all_z else np.array([], dtype=np.float64)

        logger.info(f"Total: {n_pontos_total} pontos", code="IDW_TASK_LAS_READ")
        self._log_memory_status("apos_leitura")

        del all_x, all_y, all_r, all_g, all_b, all_z

        if not self._check_during_execution():
            return False

        # --- Estagio 2: Calculo do Grid Global ---
        signals.hud_update.emit({"message": "Calculando grid..."})

        min_x_g, max_x_g = float(np.min(x_pts)), float(np.max(x_pts))
        min_y_g, max_y_g = float(np.min(y_pts)), float(np.max(y_pts))
        width = int(np.ceil((max_x_g - min_x_g) / resol_m))
        height = int(np.ceil((max_y_g - min_y_g) / resol_m))

        from rasterio.transform import from_origin
        transform = from_origin(min_x_g, max_y_g, resol_m, resol_m)
        logger.info(f"Grid: {width}x{height} px", code="IDW_TASK_GRID")

        if not self._check_during_execution():
            return False

        # --- Verificacao de RAM ---
        n_cpus = CpuGovernor.max_workers()
        n_bandas = sum(1 for b in ('r', 'g', 'b', 'z') if target.get(b, False))
        n_bandas = max(1, n_bandas)
        if not self._check_pixel_ram(width, height, n_cpus, n_bandas):
            logger.error("RAM insuficiente para processar grid", code="IDW_TASK_OOM_GRID")
            return False

        # --- Estagio 3: Divisao em Tiles Raster ---
        signals.hud_update.emit({"message": "Dividindo tiles raster..."})

        pontos_por_tile = max(1_000_000, n_pontos_total // max(1, n_cpus * 2))
        tiles = InterpolatorUtils.calcular_tiles_por_densidade(
            x_pts, y_pts, min_x_g, max_x_g, min_y_g, max_y_g,
            resol_m, pontos_por_tile, tool_key=self._tool_key,
            max_tile_pixels=self.MAX_TILE_PIXELS,
        )
        total_tiles = len(tiles)
        self._log_memory_status("apos_tiles")

        if not self._check_during_execution():
            return False

        # --- Pastas de saida ---
        basename_out = _os.path.splitext(_os.path.basename(output_path))[0]
        output_dir = _os.path.dirname(output_path)
        interp_dir = _os.path.join(output_dir, "Interpolator")
        self._temp_dir = interp_dir
        for banda in ("r", "g", "b", "z"):
            banda_dir = _os.path.join(interp_dir, banda)
            _os.makedirs(banda_dir, exist_ok=True)

        grid_bounds = (min_x_g, max_x_g, min_y_g, max_y_g)

        # --- Estagio 4: IDW Paralelo ---
        signals.hud_update.emit({"message": "Interpolando (IDW)..."})
        signals.progress_update.emit(45.0)

        if not self._check_during_execution():
            self._limpar_temp()
            return False

        dir_r = _os.path.join(self._temp_dir, "r")
        dir_g = _os.path.join(self._temp_dir, "g")
        dir_b = _os.path.join(self._temp_dir, "b")
        dir_z = _os.path.join(self._temp_dir, "z")

        tile_jobs = []
        for idx, (x0, x1, y0, y1, t_row, t_col) in enumerate(tiles):
            tag = f"{t_row:04d}_{t_col:04d}"
            pr = _os.path.join(dir_r, f"tile_{tag}.tif") if target.get("r", False) else ""
            pg = _os.path.join(dir_g, f"tile_{tag}.tif") if target.get("g", False) else ""
            pb = _os.path.join(dir_b, f"tile_{tag}.tif") if target.get("b", False) else ""
            pz = _os.path.join(dir_z, f"tile_{tag}.tif") if target.get("z", False) else None
            tile_jobs.append((idx, tag, (x0, x1, y0, y1), pr, pg, pb, pz))

        results = Parallel(n_jobs=CpuGovernor.n_jobs(), verbose=0)(
            delayed(InterpolatorUtils.idw_tile_para_disco)(
                idx, total_tiles, tag, tb, grid_bounds, resol_m,
                x_pts, y_pts, r_pts, g_pts, b_pts, z_pts,
                k, power, raio_max, overlap, crs_str,
                pr, pg, pb, pz, self._tool_key,
            )
            for idx, tag, tb, pr, pg, pb, pz in tile_jobs
        )

        n_ok = sum(1 for r in results if r[6] == 'OK')
        n_pulado = sum(1 for r in results if r[6] == 'PULADO')
        logger.info(f"IDW OK: {n_ok}, Pulado: {n_pulado}", code="IDW_TASK_IDW_DONE")
        self._log_memory_status("apos_idw")

        signals.hud_update.emit({"message": "Mesclando bandas..."})

        if self.is_cancelled or not self._check_during_execution():
            self._limpar_temp()
            return False

        # --- Estagio 5: Merge ---
        signals.hud_update.emit({"message": "Mesclando bandas..."})

        band_files = []
        merge_jobs = []

        def _add_merge(modo, src_dir, dtype):
            paths = sorted(glob.glob(_os.path.join(src_dir, "tile_*.tif")))
            if not paths:
                return
            out = _os.path.join(interp_dir, f"{basename_out}_{modo}.tif")
            merge_jobs.append((modo, paths, out, dtype))
            band_files.append(out)

        if target.get("r"): _add_merge("R", dir_r, np.uint8)
        if target.get("g"): _add_merge("G", dir_g, np.uint8)
        if target.get("b"): _add_merge("B", dir_b, np.uint8)
        if target.get("z"): _add_merge("Z", dir_z, np.float32)

        Parallel(n_jobs=CpuGovernor.n_jobs(), verbose=0)(
            delayed(InterpolatorUtils.mesclar_banda)(
                nome, paths, height, width, transform, crs_str,
                out_path, dtype, self._tool_key,
                nodata=0 if dtype == np.uint8 else -9999.0,
            )
            for nome, paths, out_path, dtype in merge_jobs
        )

        signals.hud_update.emit({"message": "Montando saida..."})

        if self.is_cancelled or not self._check_during_execution():
            self._limpar_temp()
            return False

        # --- Estagio 6: Montagem ---
        signals.hud_update.emit({"message": "Montando saida..."})

        has_rgb = target.get("r") and target.get("g") and target.get("b")
        final_outputs = list(band_files)

        if merge_bands and has_rgb:
            merged_path = output_path
            _os.makedirs(_os.path.dirname(merged_path), exist_ok=True)
            RasterLayerProcessing.compose_multiband_raster(
                band_files[:3], merged_path, tool_key=self._tool_key,
                nodata=0,
            )
            final_outputs.append(merged_path)
            logger.info("Mosaico RGB gerado", code="IDW_TASK_MOSAIC_DONE")
        elif merge_bands and not has_rgb:
            logger.warning(
                "Mosaico nao gerado: requer R, G e B",
                code="IDW_TASK_MOSAIC_SKIP",
            )

        signals.hud_update.emit({"message": "Salvando metadados..."})

        # --- Estagio 7: Metadados ---
        metadata = {
            "input_dir": input_dir,
            "output_path": str(output_path),
            "parametros": {
                "resolucao_m": resol_m, "resolucao_cm": round(resol_m * 100, 2),
                "idw_k": k, "idw_power": power,
                "idw_raio_max_m": raio_max, "idw_overlap_m": overlap,
                "crs": crs_str, "merge_bands": merge_bands, "target_bands": target,
            },
            "grid": {"width_px": width, "height_px": height,
                     "bounds": {"x_min": min_x_g, "x_max": max_x_g,
                                "y_min": min_y_g, "y_max": max_y_g}},
            "nuvem": {"n_pontos": n_pontos_total},
            "tiles": {"total": total_tiles, "ok": n_ok, "pulado": n_pulado},
            "arquivos_gerados": final_outputs,
        }

        meta_path = _os.path.join(interp_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.result = metadata
        logger.info(
            "Pipeline IDW concluido com sucesso",
            code="IDW_TASK_DONE",
            output_paths=final_outputs,
            grid_size=f"{width}x{height}",
            tiles_total=total_tiles,
            tiles_ok=n_ok,
        )

        out_link = output_dir.replace(chr(92), "/")
        band_link = interp_dir.replace(chr(92), "/")
        SignalManager.instance().console_html.emit(
            f"<span style='color:#4FC3F7;'>&#x2713; Mosaico: </span>"
            f"<a href='file:///{out_link}' style='color:#4FC3F7;'>{output_dir}</a>"
        )
        SignalManager.instance().console_html.emit(
            f"<span style='color:#4FC3F7;'>&#x2713; Bandas: </span>"
            f"<a href='file:///{band_link}' style='color:#4FC3F7;'>{interp_dir}</a>"
        )
        self._log_memory_status("final")

        signals.progress_update.emit(100.0)
        signals.hud_update.emit({"message": "Concluido!"})

        self._limpar_temp()
        self._limpar_las()

        return True