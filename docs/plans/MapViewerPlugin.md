# 📍 Plano de Implementação — MapViewerPlugin

**Versão:** 1.0.0  
**Data:** 18/07/2026  
**Status:** 📋 Planejado  

---

## 1. Resumo

Plugin visualizador geoespacial que exibe um **basemap de satélite navegável** como fundo, permitindo **arrastar e soltar** arquivos `.las`/`.laz`/`.shp`/`.kml` para sobreposição. O comportamento é inspirado no **QGIS** — mapa interativo com zoom/pan via mouse, e camadas sobrepostas com imagem de satélite.

### Funcionalidades-Chave

| # | Funcionalidade | Descrição |
|---|---------------|-----------|
| 1 | **Basemap Satélite** | Tile map XYZ (Google Satellite / OSM) como fundo |
| 2 | **Navegação** | Pan (arrastar) e Zoom (roda do mouse) — suave e fluido |
| 3 | **InfoBar inferior** | `MapInfos` widget (em resources/widgets/) exibindo coordenadas, zoom, CRS lado a lado na parte inferior |
| 4 | **Drag & Drop** | Arrastar arquivos do Explorer para o mapa |
| 5 | **Renderização LAS/LAZ** | Nuvem de pontos colorida sobre o mapa |
| 6 | **Renderização SHP/GPKG** | Geometrias vetoriais sobre o mapa |
| 7 | **Renderização KML** | Geometrias KML sobre o mapa |
| 8 | **Suporte a Projeção** | Conversão de coordenadas para o CRS do basemap (WGS84 Pseudo-Mercator EPSG:3857) |

---

## 2. Arquitetura

### 2.1 Visão Geral

```
┌─────────────────────────────────────────────────────┐
│  MapViewerPlugin (BasePlugin)                        │
│  ┌─────────────────────────────────────────────────┐│
│  │  PluginPage (title + badge)                     ││
│  │  ┌───────────────────────────────────────────┐  ││
│  │  │  MapCanvasWidget (QWidget custom paint)   │  ││
│  │  │  ┌─────────────────────────────────────┐  │  ││
│  │  │  │  TileManager (XYZ tile loader/cache)│  │  ││
│  │  │  ├─────────────────────────────────────┤  │  ││
│  │  │  │  LayerManager (overlay layers)      │  │  ││
│  │  │  │  ├─ LasLayerRenderer                │  │  ││
│  │  │  │  ├─ VectorLayerRenderer             │  │  ││
│  │  │  │  └─ KmlLayerRenderer                │  │  ││
│  │  │  └─────────────────────────────────────┘  │  ││
│  │  └───────────────────────────────────────────┘  ││
│  │  ┌───────────────────────────────────────────┐  ││
│  │  │  MapInfos (coords, zoom, CRS, layers)    │  ││
│  │  └───────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### 2.2 Componentes

| Componente | Classe | Arquivo | Responsabilidade |
|------------|--------|---------|-----------------|
| Plugin principal | `MapViewerPlugin` | `plugins/map_viewer/MapViewerPlugin.py` | Ciclo de vida, prefs, drag & drop |
| Canvas do mapa | `MapCanvasWidget` | `plugins/map_viewer/MapCanvasWidget.py` | Paint, zoom, pan, transformação de coordenadas |
| Gerenciador de tiles | `TileManager` | `plugins/map_viewer/TileManager.py` | Download/ cache de tiles XYZ |
| Gerenciador de camadas | `LayerManager` | `plugins/map_viewer/LayerManager.py` | Lista de overlays, visibilidade, ordem |
| Renderizador de nuvem | `LasLayerRenderer` | `plugins/map_viewer/renderers/LasLayerRenderer.py` | Lê LAS/LAZ, projeta, desenha pontos |
| Renderizador vetorial | `VectorLayerRenderer` | `plugins/map_viewer/renderers/VectorLayerRenderer.py` | Lê SHP/GPKG, projeta, desenha geometrias |
| Renderizador KML | `KmlLayerRenderer` | `plugins/map_viewer/renderers/KmlLayerRenderer.py` | Lê KML, projeta, desenha geometrias |
| Modelo de camada | `MapLayer` | `plugins/map_viewer/model/MapLayer.py` | DTO: path, tipo, CRS, visível, bounding box |
| InfoBar inferior | `MapInfos` | `resources/widgets/MapInfos.py` | Widget reutilizável de info horizontal |

### 2.3 Hierarquia de Classes

```
MapViewerPlugin (BasePlugin)
  ├── PluginPage (title="Visualizador de Mapas", sem ExecutionButtons)
  │     ├── Header: Título | Badge
  │     └── Conteúdo (QVBoxLayout):
  │           ├── MapCanvasWidget (stretch=1 — ocupa todo espaço)
  │           └── MapInfos (widget reutilizável em resources/widgets/)
  │                 ├── TileManager (QThread para fetch)
  │                 ├── LayerManager
  │                 │     └── MapLayer[] (lista de camadas)
  │                 └── QTimer (render loop / redraw)
  └── _build_ui, load_prefs, save_prefs
```

---

## 3. Dependências Externas

| Biblioteca | Uso | Requer `pip install` |
|------------|-----|----------------------|
| `laspy` | Leitura de arquivos LAS/LAZ | ✅ |
| `numpy` | Arrays de pontos, transformações | ✅ (já existe) |
| `PIL/Pillow` | Decodificação de tiles PNG | ✅ (já existe) |
| `geopandas` | Leitura de SHP/GPKG | ⚠️ Já existe no projeto |
| `shapely` | Geometrias (SHP/GPKG/KML) | ⚠️ Já existe no projeto |
| `fastkml` ou `pykml` | Parsing de KML | ✅ |

> **Contrato 8:** Todas as novas dependências devem ser registradas em `requirements.txt`.

---

## 4. Fluxo de Dados

### 4.1 Inicialização

```
1. MapViewerPlugin.__init__()
2.   → BasePlugin.__init__(tool_key="MapViewer")
3.     → _build_ui()
4.       → Cria PluginPage("Visualizador de Mapas") — sem buttons_config
5.       → Cria MapCanvasWidget
6.         → TileManager inicia cache vazio
7.         → LayerManager inicia lista vazia
8.         → Carrega tile central (lat=-15.8, lon=-48.0 ≈ Brasil Central)
9.         → Inicia QTimer de redraw (30fps)
10.      → Cria MapInfos e adiciona ao final do layout
11.    → load_prefs() restaura última posição/zoom
```

### 4.2 Drag & Drop

```
1. Usuário arrasta .las do Explorer para MapCanvasWidget
2. QWidget.dragEnterEvent → verifica extensão
3. QWidget.dropEvent → obtém path
4.   → Se .las/.laz: LasLayerRenderer.read(path)
5.   → Se .shp/.gpkg: VectorLayerRenderer.read(path)
6.   → Se .kml: KmlLayerRenderer.read(path)
7.   → Cria MapLayer, adiciona ao LayerManager
8.   → Calcula bounding box da layer
9.   → Ajusta zoom para encaixar a camada (opcional)
10.  → Atualiza MapInfos com contagem de camadas
```

### 4.3 Render Loop (paintEvent do MapCanvasWidget)

```
1. Calcular extent visível baseado em center + zoom
2. Calcular quais tiles XYZ estão visíveis
3. Para cada tile visível:
     a. Se está em cache → QPixmap pronto
     b. Se não → enfileirar download (TileManager envia sinal quando pronto)
4. Desenhar tiles na ordem Z (esquerda→direita, cima→baixo)
5. Para cada MapLayer em LayerManager (se visível):
     a. Transformar coordenadas da layer para EPSG:3857
     b. Calcular screen coordinates (world → pixel)
     c. Desenhar geometrias/pontos com QPainter
6. Aplicar clipping se necessário
```

---

## 5. Sistema de Coordenadas

### 5.1 Convenção

| Sistema | EPSG | Uso |
|---------|------|-----|
| **Web Mercator** | EPSG:3857 | CRS interno do canvas e tiles |
| **WGS84** | EPSG:4326 | Entrada do usuário (lat/lon) |
| **UTM / Local** | Variado | Arquivos LAS/SHP podem vir em outros CRS |

### 5.2 Transformações

- **Tile → Web Mercator:** Cálculo padrão XYZ (zoom, x, y → bounds em EPSG:3857)
- **Web Mercator → Pixel:** `px = (world_x - center_x) * zoom_scale + canvas_w/2`
- **Layer CRS → EPSG:3857:** Usar `pyproj.Transformer` para reprojeção de geometrias/pontos
- **Pixel → WGS84:** Para exibir coordenadas do mouse na MapInfos

---

## 6. Tile Manager

### 6.1 Fonte de Tiles

| Fonte | URL Template | Padrão |
|-------|-------------|--------|
| **Google Satellite** | `https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}` | ✅ Sim |
| **OSM** | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | ❌ Fallback |
| **Google Hybrid** | `https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}` | 🔧 Configurável |

### 6.2 Cache

- **Memória:** LRU cache com limite de 200 tiles (QPixmap)
- **Disco:** Usar `ExplorerUtils.get_system_temp_dir("aetheris/map_viewer/tiles")` para cache persistente entre sessões
- **Política:** Tiles com mais de 24h são re-baixados

### 6.3 Download

- **Síncrono (padrão):** `urllib.request.urlopen` em thread separada via `QThread`
- **Sinal:** `tile_ready(x, y, z, QPixmap)` → MapCanvasWidget faz `update()`
- **Rate limit:** Máx 10 downloads simultâneos

---

## 7. Renderizadores

### 7.1 LasLayerRenderer

```python
class LasLayerRenderer:
    @staticmethod
    def read(path: str) -> dict:
        """Lê LAS/LAZ, retorna dict com pontos, cores, bounds."""
        # Usa laspy para ler
        # Extrai X, Y, Z, R, G, B
        # Converte para EPSG:3857 se CRS conhecido
        # Retorna {points: np.ndarray(2D), colors: np.ndarray(RGBA), bounds: tuple}

    @staticmethod
    def render(painter: QPainter, data: dict,
               transform: Callable, zoom: float) -> None:
        """Desenha pontos no canvas."""
        # Aplica transformação de coordenadas world → pixel
        # Desenha cada ponto como um pixel (ou círculo pequeno se zoom alto)
        # Usa QPainter.drawPoint com cor do ponto
```

### 7.2 VectorLayerRenderer

```python
class VectorLayerRenderer:
    @staticmethod
    def read(path: str) -> dict:
        """Lê SHP/GPKG via geopandas, retorna geometrias + atributos."""
        # Usa VectorLayerSource.read (Contrato 25)
        # Converte para EPSG:3857
        # Retorna {geometries: list[shapely], attributes: list[dict], bounds: tuple}

    @staticmethod
    def render(painter: QPainter, data: dict,
               transform: Callable, zoom: float) -> None:
        """Desenha polígonos/linhas/pontos."""
        # Para cada geometria:
        #   Polygon → QPainter.drawPolygon (preenchido, contorno)
        #   LineString → QPainter.drawPolyline
        #   Point → QPainter.drawEllipse
        # Cor e estilo definidos por tipo de geometria
```

### 7.3 KmlLayerRenderer

```python
class KmlLayerRenderer:
    @staticmethod
    def read(path: str) -> dict:
        """Parseia KML, extrai geometrias."""
        # Usa fastkml ou pykml
        # Converte coordenadas para EPSG:3857
        # Extrai Placemarks, Polygon, LineString, Point
        # Retorna {geometries: list[shapely], names: list[str], bounds: tuple}

    @staticmethod
    def render(painter: QPainter, data: dict,
               transform: Callable, zoom: float) -> None:
        """Desenha geometrias KML."""
        # Similar ao VectorLayerRenderer, mas com estilo próprio
```

---

## 8. Widgets Reutilizáveis (Contrato 11)

Antes de criar UI nova, verificar widgets existentes em `resources/widgets/`:

| Necessidade | Widget Existente | Decisão |
|-------------|-----------------|---------|
| Canvas com zoom/pan | `ImagePreviewPanel` | ❌ Não serve (é para imagens estáticas, não tiles) |
| Container scroll | `ScrollWidget` | ❌ Não necessário (canvas ocupa todo espaço) |
| Container de seção | `GroupPainel` + `GridGroupPainel` | ❌ Não necessário |
| Notificação | `ToastNotification` | ✅ Usar para feedback de drop/erro |

**Novos widgets a criar:**

| Widget | Arquivo | Motivo |
|--------|---------|--------|
| `MapInfos` | `resources/widgets/MapInfos.py` | Widget reutilizável de info horizontal (coords, zoom, CRS, camadas) — genérico, vai em resources/widgets/ |
| `MapCanvasWidget` | `plugins/map_viewer/MapCanvasWidget.py` | Canvas customizado com tiles + overlays (específico do plugin) |

### 8.1 Especificação do Widget `MapInfos`

Widget horizontal que exibe informações lado a lado com separadores verticais. Fica na **parte inferior** do plugin.

```python
class MapInfos(QWidget):
    """
    Barra de informações horizontais para visualizadores geoespaciais.
    
    Exibe labels lado a lado no formato:
    [📍 Lat: -15.78  Lon: -47.93] | [🔍 Zoom: 12] | [🗺 EPSG:3857] | [📦 3 camadas]
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        
        self._labels: dict[str, QLabel] = {}
        fields = [
            ("coords", "📍 Lat: —  Lon: —"),
            ("zoom", "🔍 Zoom: —"),
            ("crs", "🗺 EPSG:3857"),
            ("layers", "📦 0 camadas"),
        ]
        for i, (key, text) in enumerate(fields):
            if i > 0:
                sep = SeparatorWidget(orientation="vertical")
                sep.setFixedHeight(16)
                layout.addWidget(sep)
            label = QLabel(text)
            label.setStyleSheet("color: #aaa; font-size: 11px;")
            self._labels[key] = label
            layout.addWidget(label)
        layout.addStretch()

    def set_coords(self, lat: float, lon: float) -> None:
        self._labels["coords"].setText(f"📍 Lat: {lat:.4f}  Lon: {lon:.4f}")

    def set_zoom(self, zoom: int) -> None:
        self._labels["zoom"].setText(f"🔍 Zoom: {zoom}")

    def set_crs(self, crs: str) -> None:
        self._labels["crs"].setText(f"🗺 {crs}")

    def set_layer_count(self, count: int) -> None:
        self._labels["layers"].setText(f"📦 {count} camada(s)")
```

> ⚠️ Este widget vai em `resources/widgets/MapInfos.py` por ser genérico e reutilizável. Deve ser registrado em `SKILL_WIDGETS.md` após criação.

---

## 9. Estrutura de Arquivos

```
plugins/map_viewer/
├── __init__.py
├── MapViewerPlugin.py            # Plugin principal (herda BasePlugin)
├── MapCanvasWidget.py            # Canvas com paintEvent, zoom, pan, drop
├── TileManager.py                # Download / cache de tiles XYZ
├── LayerManager.py               # Gerenciamento de camadas overlay
├── model/
│   ├── __init__.py
│   └── MapLayer.py               # DTO de camada
├── renderers/
│   ├── __init__.py
│   ├── LasLayerRenderer.py       # Renderizador LAS/LAZ
│   ├── VectorLayerRenderer.py    # Renderizador SHP/GPKG
│   └── KmlLayerRenderer.py       # Renderizador KML

resources/widgets/
├── MapInfos.py                   # Widget reutilizável de info horizontal
```

---

## 10. Cronograma de Implementação

### Fase 1 — Infraestrutura do Canvas ⭐ Prioridade Máxima

| # | Tarefa | Arquivos | Esforço |
|---|--------|----------|---------|
| 1.1 | Criar `ToolKey.MAP_VIEWER` | `core/enum/ToolKey.py` | 5min |
| 1.2 | Criar `MapViewerPlugin` (esqueleto BasePlugin) | `MapViewerPlugin.py` | 15min |
| 1.3 | Registrar no `ToolRegistry` (CategoryTool.CENTRAL) | `core/config/ToolRegistry.py` | 5min |
| 1.4 | Criar dependências no `requirements.txt` | `requirements.txt` | 5min |
| 1.5 | Implementar `MapCanvasWidget` com zoom/pan via QPainter | `MapCanvasWidget.py` | 2h |
| 1.6 | Implementar `TileManager` com cache e download | `TileManager.py` | 2h |
| 1.7 | Integrar canvas + tiles no plugin | `MapViewerPlugin.py`, `MapCanvasWidget.py` | 30min |
| **Resultado:** | Basemap de satélite navegável funcional ✅ |

### Fase 2 — Drag & Drop

| # | Tarefa | Arquivos | Esforço |
|---|--------|----------|---------|
| 2.1 | Implementar `dragEnterEvent`/`dropEvent` no canvas | `MapCanvasWidget.py` | 30min |
| 2.2 | Criar `LayerManager` com lista de camadas | `LayerManager.py`, `model/MapLayer.py` | 30min |
| 2.3 | Feedback visual (highlight no drag over) | `MapCanvasWidget.py` | 15min |
| **Resultado:** | Canvas aceita arquivos arrastados ✅ |

### Fase 3 — Renderizadores

| # | Tarefa | Arquivos | Esforço |
|---|--------|----------|---------|
| 3.1 | Implementar `LasLayerRenderer` | `renderers/LasLayerRenderer.py` | 2h |
| 3.2 | Implementar `VectorLayerRenderer` | `renderers/VectorLayerRenderer.py` | 2h |
| 3.3 | Implementar `KmlLayerRenderer` | `renderers/KmlLayerRenderer.py` | 1h |
| 3.4 | Sistema de projeção (pyproj.Transformer) | `MapCanvasWidget.py` + renderers | 1h |
| **Resultado:** | Arquivos LAS/SHP/KML são exibidos sobre o mapa ✅ |

### Fase 4 — Finalização

| # | Tarefa | Arquivos | Esforço |
|---|--------|----------|---------|
| 4.1 | Criar `MapInfos` widget em resources/widgets/ | `resources/widgets/MapInfos.py` | 30min |
| 4.2 | Integrar `MapInfos` no plugin (parte inferior) | `MapViewerPlugin.py` | 15min |
| 4.3 | `load_prefs()` / `save_prefs()` (última posição/zoom) | `MapViewerPlugin.py` | 15min |
| 4.4 | Mensagens de sucesso/erro padronizadas | `MapViewerPlugin.py` | 15min |
| 4.5 | Testes e ajustes de performance | Todos | 1h |
| 4.6 | Atualizar changelog | `docs/data/changelog.txt` | 5min |
| 4.7 | Atualizar SKILL_WIDGETS.md com MapInfos | `docs/skills/SKILL_WIDGETS.md` | 5min |
| **Resultado:** | Plugin completo e funcional ✅ |

---

## 11. Contratos e Skills Aplicáveis

### 11.1 Contratos a Respeitar

| Contrato | Descrição | Como Atender |
|----------|-----------|--------------|
| **1** | Sem QMessageBox direto | Usar `MessageBox` de `utils.MessageBox` |
| **2** | Todo except com `as e` + logger | Capturar e logar todas as exceções |
| **3** | Usar logger, não print | `self.logger` do BasePlugin |
| **4** | Preferências via self.preferences | `load_prefs()` / `save_prefs()` |
| **5** | Import via ToolRegistry | Registrar no `_TOOLS` |
| **6** | Herdar de BasePlugin | ✅ Feito |
| **7** | Comunicação via SignalManager | Usar `console_message`, `progress_update` |
| **8** | Dependências em requirements.txt | Adicionar laspy, fastkml |
| **9** | Sem código morto | Remover imports não usados |
| **10** | CategoryTool.CENTRAL | Ferramenta central em abas |
| **11** | Verificar widgets existentes | Consultar SKILL_WIDGETS.md |
| **12** | Documentação reflexiva | Atualizar SKILL_WIDGETS.md com MapInfos |
| **13** | ToolRegistry é única fonte | ✅ Registro lá |
| **17** | QFileDialog via ExplorerUtils | Usar `ExplorerUtils.get_system_temp_dir()` para cache |
| **20** | SignalManager para progresso | Emitir durante carregamento de arquivos |
| **23** | Utilitários compartilhados | Usar FormatUtils, ExplorerUtils |
| **25** | I/O vetorial via VectorLayerSource | Usar no VectorLayerRenderer |
| **26** | ToolKey.value em logs | ✅ `self.tool_key` |
| **27** | Não testar com python -c + Qt | Usar `ast.parse` |

### 11.2 Skills Aplicáveis

| Skill | Como Usar |
|-------|-----------|
| `SKILL_CREATE_TOOL.md` | Template de criação do plugin |
| `SKILL_COMUNICATION.md` | Sinais do SignalManager |
| `SKILL_PREFERENCES.md` | Salvar/restaurar posição do mapa |
| `SKILL_UTILS.md` | Helpers existentes (ExplorerUtils.get_system_temp_dir) |
| `SKILL_HUD_PROGRESS.md` | HUD durante carregamento LAS pesado |
| `SKILL_VECTOR_RASTER_LAYER_UTILS.md` | VectorLayerSource para SHP/GPKG |

---

## 12. Detalhamento Técnico

### 12.1 MapCanvasWidget — Zoom e Pan

Inspirado no `ImagePreviewPanel` mas adaptado para tiles:

```python
class MapCanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._center = (0.0, 0.0)          # Web Mercator (EPSG:3857)
        self._zoom = 5                     # Nível de zoom (0-19)
        self._tile_manager = TileManager()
        self._layer_manager = LayerManager()
        self._is_dragging = False
        self._drag_start = QPointF(0, 0)
        self._drag_start_center = (0.0, 0.0)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

    def _world_to_pixel(self, wx: float, wy: float) -> QPointF:
        """Converte coordenada Web Mercator para pixel no canvas."""
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

    def _get_scale(self) -> float:
        """Pixels por metro no zoom atual."""
        return 256 * (2 ** self._zoom) / 40075016.686
```

### 12.2 Tile Manager — Cálculo de Tiles

```python
def _tile_bounds(self, z: int, x: int, y: int) -> tuple:
    origin = 20037508.342789244
    tile_size = 2 * origin / (2 ** z)
    min_x = x * tile_size - origin
    max_x = (x + 1) * tile_size - origin
    min_y = origin - (y + 1) * tile_size
    max_y = origin - y * tile_size
    return (min_x, min_y, max_x, max_y)
```

### 12.3 Drag & Drop — Validação de Extensões

```python
def dragEnterEvent(self, event: QDragEnterEvent) -> None:
    if event.mimeData().hasUrls():
        for url in event.mimeData().urls():
            path = url.toLocalFile().lower()
            if any(path.endswith(ext) for ext in [".las", ".laz", ".shp", ".gpkg", ".kml"]):
                event.acceptProposedAction()
                return
    event.ignore()

def dropEvent(self, event: QDropEvent) -> None:
    for url in event.mimeData().urls():
        path = url.toLocalFile()
        self._load_file(path)
    event.acceptProposedAction()
```

### 12.4 Carregamento LAS (LasLayerRenderer)

```python
import laspy
import numpy as np
from pyproj import Transformer

class LasLayerRenderer:
    @staticmethod
    def read(path: str, tool_key: str) -> dict | None:
        try:
            las = laspy.read(path)
            x = las.x
            y = las.y
            has_color = hasattr(las, 'red') and las.red.max() > 0
            transformer = None
            if transformer:
                x, y = transformer.transform(x, y)
            bounds = (x.min(), y.min(), x.max(), y.max())
            colors = None
            if has_color:
                colors = np.column_stack([
                    las.red // 256, las.green // 256, las.blue // 256,
                    np.full(len(las), 255, dtype=np.uint8)
                ])
            return {
                "points": np.column_stack([x, y]).astype(np.float64),
                "colors": colors,
                "bounds": bounds,
                "count": len(las),
            }
        except Exception as e:
            return None

    @staticmethod
    def render(painter: QPainter, data: dict,
               world_to_pixel: callable, zoom: float) -> None:
        points = data["points"]
        colors = data["colors"]
        for i in range(0, len(points), max(1, len(points) // 100000)):
            px, py = world_to_pixel(points[i][0], points[i][1])
            if 0 <= px < painter.device().width() and 0 <= py < painter.device().height():
                if colors is not None:
                    painter.setPen(QColor(*colors[i]))
                else:
                    painter.setPen(QColor(255, 255, 255))
                painter.drawPoint(QPointF(px, py))
```

> **Performance:** Para nuvens grandes (>1M pts), usar estratégia de **subsampling** baseada no zoom.

---

## 13. UI do Plugin

```
┌─────────────────────────────────────────────────────────┐
│  🔍 Visualizador de Mapas    [● Pronto]                │ ← Header com badge (sem ExecutionButtons)
├─────────────────────────────────────────────────────────┤
│                                                         │
│        ┌───┬───┬───┐                                   │
│        │ T │ T │ T │   ← Tiles de satélite             │
│        ├───┼───┼───┤                                   │
│        │ T │ ⬤ │ T │   ← Pontos LAS sobre tile         │
│        ├───┼───┼───┤                                   │
│        │ T │ T │ T │                                   │
│        └───┴───┴───┘                                   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ 📍 Lat: -15.78  Lon: -47.93 | 🔍 Zoom: 12 | 🗺 EPSG:3857 | 📦 3 camadas │ ← MapInfos
└─────────────────────────────────────────────────────────┘
```

---

## 14. Informações na AppBar / Toolbar

- **ToolType sugerido:** `ToolType.POINTS`
- **Ícone:** `resources/icons/MapViewer.ico` (globo/mapa mundi)
- **Tooltip:** "Visualizador de mapas com basemap de satélite"

---

## 15. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Performance com LAS de 100M+ pontos | Alta | Alto | Subsampling adaptativo por zoom; QThread para carregamento |
| Tile download lento | Média | Médio | Cache em disco via ExplorerUtils; indicador de carregamento |
| CRS desconhecido no LAS | Média | Alto | Fallback para EPSG:4326 (assumir WGS84) + aviso ao usuário |
| Memória com muitas camadas | Baixa | Médio | Limite de 10 camadas simultâneas; liberar dados não visíveis |
| Google bloqueia tile requests | Baixa | Alto | Fallback para OSM; cache longo |

---

## 16. Checklist de Verificação Pré-Implementação

- [ ] Skill `SKILL_AGENT` autoriza uso das demais skills
- [ ] Contratos 1-27 revisados e aplicáveis identificados
- [ ] `ToolKey.MAP_VIEWER` adicionado ao enum
- [ ] `ToolRegistry._TOOLS` atualizado com entrada MapViewer
- [ ] `requirements.txt` atualizado com laspy, fastkml
- [ ] `resources/icons/MapViewer.ico` criado
- [ ] Widgets existentes consultados (SKILL_WIDGETS.md)
- [ ] `VectorLayerSource` usada para SHP/GPKG (Contrato 25)
- [ ] **Sem ExecutionButtons** (ferramenta não executa nada)
- [ ] `MapInfos` criado em `resources/widgets/` (Contrato 11)
- [ ] `ExplorerUtils.get_system_temp_dir()` usado para cache de tiles
- [ ] `MessageBox` usado para diálogos (Contrato 1)
- [ ] `load_prefs()`/`save_prefs()` implementados (Contrato 6)
- [ ] Changelog atualizado ao final (Contrato 12)
- [ ] SKILL_WIDGETS.md atualizado com MapInfos (Contrato 12)

---

## 17. Referências

- `docs/ia/contracts.md` — Contratos imutáveis do sistema
- `docs/skills/SKILL_CREATE_TOOL.md` — Skill de criação de plugins
- `docs/skills/SKILL_WIDGETS.md` — Catálogo de widgets reutilizáveis
- `docs/skills/SKILL_VECTOR_RASTER_LAYER_UTILS.md` — Utilitários de camadas
- `docs/skills/SKILL_PREFERENCES.md` — Sistema de preferências
- `docs/skills/SKILL_UTILS.md` — Utilitários compartilhados
- `core/config/ToolRegistry.py` — Registro de ferramentas
- `core/enum/ToolKey.py` — Enum de chaves
- `plugins/BasePlugin.py` — Classe base