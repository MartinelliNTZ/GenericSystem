from __future__ import annotations

import math
import threading
from time import perf_counter
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import psutil
import rasterio
from rasterio.windows import Window

from .hardware_manager import calculate_chunk_lines


class RasterPredictor:
    def __init__(
        self,
        batch_size: int = 4096,
        use_mask: bool = True,
        zero_as_nodata: bool = False,
        nodata_threshold: int = 250,
        ram_limit_bytes: Optional[int] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        logger: Optional[Callable[[str], None]] = None,
        cancel_event: Optional[threading.Event] = None,
    ):
        self.batch_size = batch_size
        self.use_mask = use_mask
        self.zero_as_nodata = zero_as_nodata
        self.nodata_threshold = nodata_threshold
        self.ram_limit_bytes = ram_limit_bytes
        self.progress_callback = progress_callback
        self.logger = logger
        self.cancel_event = cancel_event or threading.Event()

    def _report_progress(self, percent: int, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(percent, message)

    def _log(self, message: str) -> None:
        if self.logger:
            self.logger(message)

    def predict(
        self,
        source_path: Path,
        model,
        n_bands_feature: int,
        output_path: Path,
    ) -> Path:
        source_path = Path(source_path)
        output_path = Path(output_path)
        self._validate_paths(source_path, output_path)

        with rasterio.open(str(source_path)) as src:
            height = src.height
            width = src.width
            n_bands_total = src.count
            out_meta = src.meta.copy()

        has_alpha_band = self.use_mask and n_bands_total == (n_bands_feature + 1)
        n_feat_classif = n_bands_total - 1 if has_alpha_band else n_bands_total
        if n_feat_classif != n_bands_feature:
            raise ValueError(
                f"Incompatibilidade de bandas: treino usou {n_bands_feature} bandas, "
                f"mas imagem de classificacao possui {n_feat_classif} bandas de feature."
            )

        ram_available = psutil.virtual_memory().available
        ram_to_use = min(ram_available, self.ram_limit_bytes) if self.ram_limit_bytes else ram_available
        chunk_lines = max(256, calculate_chunk_lines(width, n_bands_feature, ram_to_use) // 12)
        num_chunks = math.ceil(height / chunk_lines)
        total_pixels = height * width

        self._log(
            f"RasterPredictor: {width}x{height} | bands={n_bands_total} | feat={n_bands_feature} | "
            f"RAM disponivel={ram_available / (1024 ** 3):.2f}GB | "
            f"RAM limite uso={ram_to_use / (1024 ** 3):.2f}GB | chunk_lines={chunk_lines} | chunks={num_chunks}"
        )
        if has_alpha_band:
            self._log(f"RasterPredictor: estrategia de validacao=alpha (alpha >= {self.nodata_threshold})")
        else:
            self._log(
                "RasterPredictor: estrategia de validacao=multibanda "
                f"(todas as bandas > {self.nodata_threshold} => nodata)"
            )
        if self.zero_as_nodata:
            self._log("RasterPredictor: regra adicional ativa (todas as bandas == 0 => nodata)")
        self._log("RasterPredictor: loop de chunks sequencial; paralelismo interno via GDAL threads + TensorFlow threads.")

        out_meta.update(
            {
                "driver": "GTiff",
                "count": 1,
                "dtype": "uint8",
                "compress": "lzw",
                "nodata": 255,
                "height": height,
                "width": width,
                "tiled": True,
                "blockxsize": 512,
                "blockysize": 512,
            }
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        pixels_ok = 0
        predicted_pixels = 0
        started_at = perf_counter()
        tasks = []
        for i in range(num_chunks):
            row_start = i * chunk_lines
            row_end = min(row_start + chunk_lines, height)
            tasks.append((row_start, row_end - row_start))

        with rasterio.open(str(output_path), "w", **out_meta) as dst:
            with rasterio.open(str(source_path)) as src:
                for chunk_index, (row_start, n_rows) in enumerate(tasks):
                    if self.cancel_event.is_set():
                        self._log("> CANCELAMENTO: Predicao interrompida pelo usuario")
                        break
                    chunk_started_at = perf_counter()
                    window = Window(0, row_start, width, n_rows)
                    read_started_at = perf_counter()
                    chunk_data = src.read(window=window)
                    read_seconds = perf_counter() - read_started_at

                    if has_alpha_band:
                        mask_band = chunk_data[-1]
                        features = chunk_data[:n_bands_feature]
                    else:
                        mask_band = None
                        features = chunk_data

                    flattened = features.transpose(1, 2, 0).reshape(-1, n_bands_feature).astype(np.float32)
                    valid_mask = np.ones(flattened.shape[0], dtype=bool)
                    if mask_band is not None:
                        valid_mask = mask_band.reshape(-1) >= self.nodata_threshold
                    else:
                        valid_mask = ~np.all(flattened > float(self.nodata_threshold), axis=1)
                    if self.zero_as_nodata:
                        valid_mask &= ~np.all(flattened == 0.0, axis=1)

                    result_arr = np.full(flattened.shape[0], 255, dtype=np.uint8)
                    num_valid = int(valid_mask.sum())
                    infer_started_at = perf_counter()
                    if num_valid > 0:
                        pred_raw = model.predict(flattened[valid_mask], batch_size=self.batch_size, verbose=0)
                        if pred_raw.ndim == 2 and pred_raw.shape[1] == 1:
                            pred_cls = np.round(pred_raw).astype(np.uint8).flatten()
                        else:
                            pred_cls = np.argmax(pred_raw, axis=1).astype(np.uint8)
                        result_arr[valid_mask] = pred_cls
                        predicted_pixels += int(pred_cls.size)
                    infer_seconds = perf_counter() - infer_started_at

                    write_started_at = perf_counter()
                    dst.write(result_arr.reshape(1, n_rows, width), window=window)
                    write_seconds = perf_counter() - write_started_at
                    pixels_ok += num_valid
                    percent = int((chunk_index + 1) / num_chunks * 100)
                    self._report_progress(percent, f"Chunk {chunk_index + 1}/{num_chunks}")
                    chunk_total_seconds = perf_counter() - chunk_started_at
                    row_end = row_start + n_rows - 1
                    self._log(
                        f"Chunk {chunk_index + 1}/{num_chunks}: rows={row_start}-{row_end} | "
                        f"valid={num_valid:,} | read={read_seconds:.3f}s | "
                        f"infer={infer_seconds:.3f}s | write={write_seconds:.3f}s | total={chunk_total_seconds:.3f}s"
                    )
                    mem = psutil.virtual_memory()
                    self._log(
                        f"Chunk {chunk_index + 1}/{num_chunks}: RAM usada={mem.percent:.1f}% | "
                        f"disponivel={mem.available / (1024 ** 3):.2f}GB"
                    )

        if pixels_ok == 0 or predicted_pixels == 0:
            try:
                output_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise ValueError(
                "Nenhum pixel valido foi classificado. Saida resultaria em raster vazio/nodata. "
                "Verifique mascara/limiar nodata."
            )

        with rasterio.open(str(output_path), "r+") as dst:
            overviews = [2, 4, 8, 16, 32, 64]
            dst.build_overviews(overviews, rasterio.enums.Resampling.nearest)
            dst.update_tags(ns="rio_overview", resampling="nearest")

        total_seconds = max(perf_counter() - started_at, 1e-9)
        self._log(
            f"RasterPredictor concluido: pixels_validos={pixels_ok:,} | pixels_preditos={predicted_pixels:,} | "
            f"tempo_total={total_seconds:.2f}s | throughput={total_pixels / total_seconds:.2f} px/s"
        )
        self._report_progress(100, "Predicao concluida")
        return output_path

    def _validate_paths(self, source_path: Path, output_path: Path) -> None:
        if not source_path.is_file():
            raise FileNotFoundError(f"Imagem de classificacao nao encontrada: {source_path}")
        if source_path.resolve() == output_path.resolve():
            raise ValueError("Imagem de saida nao pode ser igual a imagem de classificacao.")
