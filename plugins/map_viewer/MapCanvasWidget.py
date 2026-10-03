# -*- coding: utf-8 -*-
"""
MapCanvasWidget — Canvas do mapa com tiles, zoom, pan e drag & drop
=====================================================================
Widget custom QPainter que renderiza tiles de satélite como fundo e
camadas sobrepostas (LAS, SHP, KML) com navegação via mouse.
"""

from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import QPoint, QPointF, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from utils.BaseUtil import BaseUtil
from plugins.map_viewer.TileManager import TileManager, tile_bounds, TILE_SIZE
from plugins.map_viewer.LayerManager import LayerManager
from plugins.map_viewer.model.MapLayer import MapLayer
from plugins.map_viewer.renderers.LasLayerRenderer import LasLayerRenderer
from plugins.map_viewer.renderers.VectorLayerRenderer import VectorLayerRenderer
from plugins.map_viewer.renderers.KmlLayerRenderer import KmlLayerRenderer


# ── Constantes de navegação ────────────────────────────────────────

MIN_ZOOM = 2
MAX_ZOOM = 19
INITIAL_ZOOM = 5
INITIAL_LAT = -15.8   # Brasil Central
INITIAL_LON = -48.0

# Web Mercator para o centro inicial
def _lat_lon_to_web_mercator(lat: float, lon: float) -> tuple[float, float]:
    """Converte WGS84 (lat/lon) para Web Mercator (EPSG:3857)."""
    origin = 20037508.342789244
    wx = lon * origin / 180.0
    wy = math.log(math.tan((90 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    wy = wy * origin / 180.0
    return (wx, wy)


class MapCanvasWidget(QWidget):
    """
    Canvas do mapa com renderização de tiles + overlays.

    Mouse:
        - Arrastar: pan (arrasta o mapa)
        - Roda do mouse: zoom in/out
        - Mouse move: atualiza coordenadas na barra de informações

    Drag & Drop:
        - Aceita .las, .laz, .shp, .gpkg, .kml
    """

    SUPPORTED_EXTENSIONS = frozenset({".las", ".laz", ".shp", ".gpkg", ".kml"})

    def __init__(
        self,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tool_key = tool_key
        self._logger = BaseUtil._get_logger(tool_key, "MapCanvasWidget")

        # Centro em Web Mercator (Brasil Central)
        cx, cy = _lat_lon_to_web_mercator(INITIAL_LAT, INITIAL_LON)
        self._center = (cx, cy)
        self._zoom = INITIAL_ZOOM

        # Tile manager
        self._tile_manager = TileManager(tool_key=tool_key)
        self._tile_manager.tile_ready.connect(self._on_tile_ready)

        # Layer manager
        self._layer_manager = LayerManager(tool_key=tool_key)

        # Navegação
        self._is_dragging = False
        self._drag_start = QPointF(0, 0)
        self._drag_start_center = (0.0, 0.0)

        # Mouse tracking para coordenadas
        self._mouse_world = (0.0, 0.0)

        # Placeholder background
        self._bg_color = QColor(20, 20, 30)

        # Config
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(200, 200)

        # Redraw timer (30fps)
        self._redraw_timer = QTimer(self)
        self._redraw_timer.timeout.connect(self.update)
        self._redraw_timer.start(33)  # ~30fps

        # Callback para info bar
        self.on_info_changed: Any = None  # callable(coord_x, coord_y, zoom, crs)

        self._logger.info(
            "Canvas inicializado",
            code="CANVAS_READY",
            zoom=self._zoom,
            center=(round(cx, 2), round(cy, 2)),
        )

    # ── API Pública ────────────────────────────────────────────────

    @property
    def layer_manager(self) -> LayerManager:
        return self._layer_manager

    def center_on(self, lat: float, lon: float, zoom: int | None = None) -> None:
        """Centraliza o mapa em uma coordenada WGS84."""
        cx, cy = _lat_lon_to_web_mercator(lat, lon)
        self._center = (cx, cy)
        if zoom is not None:
            self._zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        self.update()

    def set_zoom(self, zoom: int) -> None:
        """Define nível de zoom."""
        self._zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        self._emit_info()
        self.update()

    def get_zoom(self) -> int:
        return self._zoom

    def get_center_wgs84(self) -> tuple[float, float]:
        """Retorna centro em WGS84 (lat, lon)."""
        origin = 20037508.342789244
        lon = self._center[0] / origin * 180.0
        lat = self._center[1] / origin * 180.0
        lat = 180.0 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
        return (lat, lon)

    def save_state(self) -> dict[str, Any]:
        """Retorna estado atual para persistência."""
        lat, lon = self.get_center_wgs84()
        return {"lat": lat, "lon": lon, "zoom": self._zoom}

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restaura estado previamente salvo."""
        lat = state.get("lat", INITIAL_LAT)
        lon = state.get("lon", INITIAL_LON)
        zoom = state.get("zoom", INITIAL_ZOOM)
        self.center_on(lat, lon, zoom)

    def _zoom_to_bounds(self, bounds: tuple[float, float, float, float]) -> None:
        """
        Ajusta zoom e centro para enquadrar uma bounding box.

        bounds: (min_x, min_y, max_x, max_y) em Web Mercator (EPSG:3857).
        """
        min_x, min_y, max_x, max_y = bounds

        # Centro da bounding box
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        self._center = (cx, cy)

        # Calcular zoom para enquadrar a bbox
        w, h = self.width(), self.height()
        if w < 1 or h < 1:
            w, h = 800, 600  # fallback

        # Largura/altura da bbox em metros
        bbox_w = max_x - min_x
        bbox_h = max_y - min_y
        if bbox_w <= 0 or bbox_h <= 0:
            return

        # Resolução do tile em metros/pixel no zoom ideal
        # Margem de 20% nas bordas
        margin = 1.2
        res_x = (bbox_w * margin) / w
        res_y = (bbox_h * margin) / h
        res = max(res_x, res_y)

        # Calcular zoom a partir da resolução
        # Earth circumference em metros ≈ 40075016.686
        # resolution = (2 * origin / 2^zoom) / TILE_SIZE
        origin = 20037508.342789244
        if res > 0:
            zoom = math.log2((2 * origin) / (res * TILE_SIZE))
            self._zoom = max(MIN_ZOOM, min(MAX_ZOOM, int(round(zoom))))

        self._emit_info()
        self.update()

        self._logger.info(
            "Zoom ajustado para bounds",
            code="ZOOM_TO_BOUNDS",
            bounds=bounds,
            zoom=self._zoom,
        )

    # ── Paint ──────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        if w < 1 or h < 1:
            painter.end()
            return

        # Fundo
        painter.fillRect(0, 0, w, h, self._bg_color)

        # Desenhar tiles
        self._draw_tiles(painter, w, h)

        # Desenhar camadas
        self._draw_layers(painter, w, h)

        # Placeholder se vazio
        if self._layer_manager.count() == 0:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(
                QRect(0, h // 2 - 20, w, 40),
                Qt.AlignmentFlag.AlignCenter,
                "📥 Arraste arquivos LAS, SHP ou KML aqui",
            )

        painter.end()

    def _draw_tiles(self, painter: QPainter, w: int, h: int) -> None:
        """Calcula e desenha os tiles visíveis."""
        n_tiles = 2 ** self._zoom
        scale = self._get_scale()

        # Centro em pixels
        center_px_x = self.width() / 2
        center_px_y = self.height() / 2

        # Centro em tile coords (float)
        origin = 20037508.342789244
        center_tile_x = (self._center[0] + origin) / (2 * origin) * n_tiles
        center_tile_y = (origin - self._center[1]) / (2 * origin) * n_tiles

        # Quantos tiles cabem na tela
        tiles_w = w / TILE_SIZE + 2
        tiles_h = h / TILE_SIZE + 2

        start_x = int(center_tile_x - tiles_w / 2)
        start_y = int(center_tile_y - tiles_h / 2)
        end_x = int(center_tile_x + tiles_w / 2)
        end_y = int(center_tile_y + tiles_h / 2)

        for tx in range(start_x, end_x + 1):
            for ty in range(start_y, end_y + 1):
                # Wrap horizontal
                wx = tx % n_tiles
                if wx < 0:
                    wx += n_tiles

                # Skip tiles Y inválidos
                if ty < 0 or ty >= n_tiles:
                    continue

                pixmap = self._tile_manager.get_tile(self._zoom, wx, ty)
                if pixmap is not None and not pixmap.isNull():
                    # Calcular posição na tela
                    tile_px = (wx + 0.5 - center_tile_x) * TILE_SIZE + center_px_x
                    tile_py = (ty + 0.5 - center_tile_y) * TILE_SIZE + center_px_y
                    painter.drawPixmap(
                        int(tile_px - TILE_SIZE / 2),
                        int(tile_py - TILE_SIZE / 2),
                        TILE_SIZE, TILE_SIZE, pixmap,
                    )

    def _draw_layers(self, painter: QPainter, w: int, h: int) -> None:
        """Desenha todas as camadas visíveis."""
        for layer in self._layer_manager.get_visible_layers():
            if layer.layer_type == "las":
                LasLayerRenderer.render(painter, layer.data, self._world_to_pixel, self._zoom)
            elif layer.layer_type == "vector":
                VectorLayerRenderer.render(painter, layer.data, self._world_to_pixel, self._zoom)
            elif layer.layer_type == "kml":
                KmlLayerRenderer.render(painter, layer.data, self._world_to_pixel, self._zoom)

    # ── Transformações de Coordenadas ──────────────────────────

    def _get_scale(self) -> float:
        """Pixels por metro no zoom atual."""
        return TILE_SIZE * (2 ** self._zoom) / (2 * 20037508.342789244)

    def _world_to_pixel(self, wx: float, wy: float) -> QPointF:
        """Converte Web Mercator para pixel no canvas."""
        scale = self._get_scale()
        px = (wx - self._center[0]) * scale + self.width() / 2
        py = -(wy - self._center[1]) * scale + self.height() / 2
        return QPointF(px, py)

    def _pixel_to_world(self, px: float, py: float) -> tuple[float, float]:
        """Converte pixel para Web Mercator."""
        scale = self._get_scale()
        wx = (px - self.width() / 2) / scale + self._center[0]
        wy = -(py - self.height() / 2) / scale + self._center[1]
        return (wx, wy)

    def _emit_info(self) -> None:
        """Emite informações atuais para a barra de status."""
        lat, lon = self.get_center_wgs84()
        if self.on_info_changed:
            self.on_info_changed(lat, lon, self._zoom, "EPSG:3857")

    # ── Eventos do Mouse ───────────────────────────────────────────

    def wheelEvent(self, event) -> None:
        """Zoom in/out com a roda do mouse."""
        delta = event.angleDelta().y()
        old_zoom = self._zoom

        if delta > 0:
            self._zoom = min(MAX_ZOOM, self._zoom + 1)
        else:
            self._zoom = max(MIN_ZOOM, self._zoom - 1)

        if self._zoom != old_zoom:
            # Zoom em direção ao cursor do mouse
            mouse_px = event.position().x()
            mouse_py = event.position().y()

            # Posição do mouse em Web Mercator antes do zoom
            world_before = self._pixel_to_world(mouse_px, mouse_py)

            # Aplica zoom
            # Recalcula center para manter o ponto do mouse fixo
            scale_new = self._get_scale()
            scale_old = TILE_SIZE * (2 ** old_zoom) / (2 * 20037508.342789244)

            if scale_old > 0:
                ratio = scale_new / scale_old
                self._center = (
                    world_before[0] - (world_before[0] - self._center[0]) / ratio,
                    world_before[1] - (world_before[1] - self._center[1]) / ratio,
                )

            self._emit_info()
        event.accept()

    def mousePressEvent(self, event) -> None:
        """Inicia arrasto do mapa."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start = event.position()
            self._drag_start_center = self._center
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Atualiza pan ou coordenadas do mouse."""
        if self._is_dragging:
            delta = event.position() - self._drag_start
            scale = self._get_scale()
            if scale > 0:
                self._center = (
                    self._drag_start_center[0] - delta.x() / scale,
                    self._drag_start_center[1] + delta.y() / scale,
                )
            event.accept()
            return

        # Atualiza coordenadas do mouse
        self._mouse_world = self._pixel_to_world(event.position().x(), event.position().y())
        self._emit_info()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Finaliza arrasto."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """Duplo clique centraliza e dá zoom."""
        if event.button() == Qt.MouseButton.LeftButton:
            world = self._pixel_to_world(event.position().x(), event.position().y())
            self._center = world
            self._zoom = min(MAX_ZOOM, self._zoom + 1)
            self._emit_info()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    # ── Drag & Drop ────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Aceita arquivos com extensões suportadas."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile().lower()
                if any(path.endswith(ext) for ext in self.SUPPORTED_EXTENSIONS):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Processa arquivos soltos no canvas."""
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            self._load_file(path)
        event.acceptProposedAction()

    def _load_file(self, path: str) -> None:
        """Carrega um arquivo como camada."""
        path_lower = path.lower()
        data = None
        layer_type = ""
        crs = ""

        try:
            if path_lower.endswith((".las", ".laz")):
                data = LasLayerRenderer.read(path, tool_key=self._tool_key)
                layer_type = "las"
            elif path_lower.endswith((".shp", ".gpkg")):
                data = VectorLayerRenderer.read(path, tool_key=self._tool_key)
                layer_type = "vector"
            elif path_lower.endswith(".kml"):
                data = KmlLayerRenderer.read(path, tool_key=self._tool_key)
                layer_type = "kml"
        except Exception as e:
            self._logger.error("Erro ao carregar arquivo", code="FILE_LOAD_ERR", error=str(e), path=path)
            return

        if data is None:
            self._logger.warning("Nenhum dado carregado", code="FILE_NO_DATA", path=path)
            return

        layer = MapLayer(
            path=path,
            layer_type=layer_type,
            data=data,
            bounds=data["bounds"],
            crs=crs,
        )

        if self._layer_manager.add_layer(layer):
            self._logger.info("Camada adicionada ao mapa", code="LAYER_ADDED", name=layer.name)

            # Auto-zoom para a bounding box da camada
            bbox = data["bounds"]
            if bbox and bbox != (0, 0, 0, 0):
                self._zoom_to_bounds(bbox)

            SignalManager.instance().console_message.emit(
                f"Camada carregada: {layer.name} ({layer.layer_type}) — "
                f"{data.get('count', 0)} feições"
            )

    # ── Tile callback ──────────────────────────────────────────────

    def _on_tile_ready(self, x: int, y: int, z: int, pixmap: QPixmap) -> None:
        """Tile foi baixado — redesenha canvas."""
        self.update()