# -*- coding: utf-8 -*-
"""
TileManager — Gerenciador de tiles XYZ com cache em memória e disco
=====================================================================
Faz download de tiles de satélite (Google Satellite / OSM), mantém
cache LRU em memória e persiste em disco via ExplorerUtils.
"""

from __future__ import annotations

import os
import time
import urllib.request
from collections import OrderedDict
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QPixmap

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ExplorerUtils import ExplorerUtils


# ── Constantes ─────────────────────────────────────────────────────

TILE_SIZE = 256
ORIGIN = 20037508.342789244  # Metade da circunferência terrestre
CACHE_MAX_MEMORY = 200       # Máx tiles em memória
CACHE_MAX_AGE = 86400        # 24h em segundos

TILE_URLS: dict[str, str] = {
    "google_satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    "google_hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    "osm": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
}


def tile_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """
    Retorna bounds (min_x, min_y, max_x, max_y) em Web Mercator
    para o tile (z, x, y).
    """
    tile_size = 2 * ORIGIN / (2 ** z)
    min_x = x * tile_size - ORIGIN
    max_x = (x + 1) * tile_size - ORIGIN
    min_y = ORIGIN - (y + 1) * tile_size
    max_y = ORIGIN - y * tile_size
    return (min_x, min_y, max_x, max_y)


class TileDownloader(QThread):
    """
    Thread para download de um tile em background.
    """
    finished = Signal(int, int, int, str)  # x, y, z, file_path

    def __init__(self, x: int, y: int, z: int, url: str, save_path: str) -> None:
        super().__init__()
        self._x = x
        self._y = y
        self._z = z
        self._url = url
        self._save_path = save_path

    def run(self) -> None:
        try:
            data = urllib.request.urlopen(self._url, timeout=10).read()
            os.makedirs(os.path.dirname(self._save_path), exist_ok=True)
            with open(self._save_path, "wb") as f:
                f.write(data)
            self.finished.emit(self._x, self._y, self._z, self._save_path)
        except Exception:
            pass  # Tile falhou, será ignorado


class TileManager(QObject):
    """
    Gerencia download e cache de tiles XYZ.

    Sinais:
        tile_ready(x, y, z, QPixmap) — emitido quando um tile é carregado.
    """

    tile_ready = Signal(int, int, int, QPixmap)

    def __init__(
        self,
        source: str = "google_satellite",
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        super().__init__()
        self._tool_key = tool_key
        self._logger = BaseUtil._get_logger(tool_key, "TileManager")
        self._source = source
        self._url_template = TILE_URLS.get(source, TILE_URLS["google_satellite"])

        # Cache em memória (LRU)
        self._memory_cache: OrderedDict[tuple[int, int, int], QPixmap] = OrderedDict()

        # Cache em disco
        self._disk_cache_dir = ExplorerUtils.get_system_temp_dir(
            "aetheris/map_viewer/tiles", tool_key=tool_key
        )

        # Downloaders ativos
        self._active_downloads: dict[tuple[int, int, int], TileDownloader] = {}

        self._logger.info(
            "TileManager inicializado",
            code="TILE_MGR_READY",
            source=source,
            cache_dir=str(self._disk_cache_dir),
        )

    # ── API Pública ────────────────────────────────────────────────

    def get_tile(self, z: int, x: int, y: int) -> QPixmap | None:
        """
        Retorna o tile do cache (memória ou disco).
        Se não estiver em cache, inicia download assíncrono.
        """
        key = (z, x, y)

        # 1. Memória
        if key in self._memory_cache:
            self._memory_cache.move_to_end(key)
            return self._memory_cache[key]

        # 2. Disco
        disk_path = self._disk_path(z, x, y)
        if os.path.exists(disk_path):
            age = time.time() - os.path.getmtime(disk_path)
            if age < CACHE_MAX_AGE:
                pixmap = QPixmap(disk_path)
                if not pixmap.isNull():
                    self._add_to_memory(key, pixmap)
                    return pixmap
            else:
                # Tile expirado, remove para redownload
                try:
                    os.remove(disk_path)
                except Exception:
                    pass

        # 3. Download assíncrono
        if key not in self._active_downloads:
            url = self._url_template.format(z=z, x=x, y=y)
            downloader = TileDownloader(x, y, z, url, disk_path)
            downloader.finished.connect(self._on_tile_downloaded)
            self._active_downloads[key] = downloader
            downloader.start()

        return None

    def set_source(self, source: str) -> None:
        """Altera a fonte de tiles."""
        self._source = source
        self._url_template = TILE_URLS.get(source, TILE_URLS["google_satellite"])
        self._memory_cache.clear()
        self._logger.info("Fonte de tiles alterada", code="TILE_SRC_CHG", source=source)

    # ── Internos ───────────────────────────────────────────────────

    def _disk_path(self, z: int, x: int, y: int) -> str:
        return os.path.join(str(self._disk_cache_dir), str(z), str(x), f"{y}.png")

    def _add_to_memory(self, key: tuple[int, int, int], pixmap: QPixmap) -> None:
        if len(self._memory_cache) >= CACHE_MAX_MEMORY:
            self._memory_cache.popitem(last=False)
        self._memory_cache[key] = pixmap

    def _on_tile_downloaded(self, x: int, y: int, z: int, file_path: str) -> None:
        key = (z, x, y)
        self._active_downloads.pop(key, None)

        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            self._add_to_memory(key, pixmap)
            self.tile_ready.emit(x, y, z, pixmap)