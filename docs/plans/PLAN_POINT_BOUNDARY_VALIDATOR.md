# Plano de Ação: PointBoundaryPlugin

> **Ferramenta:** Geração de Limite (Envoltória) de Pontos com detecção de "escada"
> **Baseada em:** `docs/implementacoes/EST3.PY` (bloco `# ── VALIDACAO CONCAVE HULL`, linhas ~260–350)
> **Expansão:** Aceita LAS/LAZ + vetores de pontos (SHP, GPKG, KML, CSV, GeoJSON)
> **Nome:** `PointBoundary` — Geração de Limite de Pontos
> **Prioridade:** Alta

---

## 📋 Visão Geral

Criar um plugin que gera o **limite (boundary)** de uma nuvem de pontos a partir de múltiplas fontes (LAS/LAZ ou vetores de pontos), com validação iterativa via `concave_hull` e detecção automática de "escada" (queda abrupta de área entre iterações).

### Função Alvo (do EST3)

```
Amostra 100k pontos → Gera concave hull com ratio decrescente (0.10 passo 0.01)
→ Detecta "escada" quando queda de área > 12%
→ Suaviza polígono com buffer(20).buffer(-20)
→ Salva GPKGs de cada iteração
→ Exporta JSON com resultados
```

### Fontes Suportadas

| Fonte | Classe de Leitura | Método a Implementar |
|-------|-------------------|----------------------|
| LAS/LAZ | `LasUtil` (já existe) | `LasUtil.extract_points()` — extrai coordenadas (x, y) |
| SHP / GPKG / KML / GeoJSON | `VectorLayerSource` (já existe) | Expandir `_SUPPORTED_EXTENSIONS` + `VectorLayerSource.extract_point_coordinates()` |
| CSV (x,y) | `VectorLayerSource` (já existe) | `VectorLayerSource.extract_point_coordinates()` — com colunas x,y configuráveis |

### Distribuição dos Métodos nas Classes Existentes

| Classe | Arquivo | Métodos a Adicionar |
|--------|---------|---------------------|
| `LasUtil` | `utils/LasUtil.py` | `extract_points(path, tool_key)` → retorna (x, y, metadata) para LAS/LAZ |
| `VectorLayerSource` | `utils/vector/VectorLayerSource.py` | Expandir `_SUPPORTED_EXTENSIONS` (+KML, +GeoJSON); `extract_point_coordinates(path, tool_key)` → retorna (x, y, metadata) |
| `VectorLayerGeometry` | `utils/vector/VectorLayerGeometry.py` | `generate_concave_boundary(x, y, ratio, ...)` → gera polígono côncavo; `smooth_polygon(polygon, distance)` → buffer suavizante |

**NENHUM arquivo `ConcaveHullValidatorUtil.py` será criado.** As responsabilidades são distribuídas nas classes existentes.

---

## 🧱 Estrutura de Arquivos do Plugin

```
plugins/point_boundary/                  ← Nome novo (sem "concavehull")
├── __init__.py
├── PointBoundaryPlugin.py               # Widget principal (herda BasePlugin)
├── PointBoundaryStep.py                 # Step do pipeline (herda BaseStep)
└── PointBoundaryTask.py                 # Task OBRIGATÓRIA (herda BaseTask)
```

---

## 📦 Dependências

| Pacote | Uso | Já instalado? |
|--------|-----|---------------|
| `laspy` | Leitura de LAS/LAZ | ✅ Sim |
| `shapely` | `concave_hull`, `MultiPoint`, `buffer` | ✅ Sim |
| `fiona` | Escrita GPKG | ✅ Sim |
| `geopandas` | Leitura SHP/GPKG/KML/GeoJSON | ✅ Sim |
| `pandas` | Leitura CSV | ✅ Sim |
| `numpy` | Amostragem, arrays | ✅ Sim |

---

## 🏗 Passo 1: Expandir Classes Utilitárias Existentes

### 1A. `LasUtil.extract_points()` — Extração de pontos de LAS/LAZ

```python
# utils/LasUtil.py

class LasUtil(BaseUtil):
    @staticmethod
    def extract_points(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        sample: int = 0,
    ) -> tuple[np.ndarray, np.ndarray, dict]:
        """
        Extrai coordenadas (x, y) de um arquivo LAS/LAZ.

        Args:
            path: Caminho do arquivo .las ou .laz.
            tool_key: ToolKey para logging.
            sample: Se > 0, retorna no máximo 'sample' pontos (amostragem uniforme).

        Returns:
            (x_array, y_array, metadata) onde metadata contém:
                - n_total: total de pontos no arquivo
                - n_extraidos: pontos extraídos (após amostragem)
                - has_rgb: se tem bandas RGB
                - crs: CRS em formato WKT ou string (se disponível)
        """
```

### 1B. `VectorLayerSource` — Expandir extensões + extração de pontos

```python
# utils/vector/VectorLayerSource.py

class VectorLayerSource(BaseUtil):
    _SUPPORTED_EXTENSIONS = frozenset({".shp", ".gpkg", ".csv", ".kml", ".geojson"})  # ← expandido
    
    @staticmethod
    def extract_point_coordinates(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        sample: int = 0,
        csv_x_field: str = "x",
        csv_y_field: str = "y",
    ) -> tuple[np.ndarray, np.ndarray, dict]:
        """
        Extrai coordenadas (x, y) de arquivos vetoriais de pontos.

        Suporta: .shp, .gpkg, .kml, .geojson, .csv
        
        Para CSV: usa csv_x_field e csv_y_field para identificar colunas.
        Para KML/GeoJSON: extrai geometrias Point e MultiPoint.
        
        Args:
            path: Caminho do arquivo.
            tool_key: ToolKey para logging.
            sample: Se > 0, amostragem uniforme.
            csv_x_field: Nome da coluna X (CSV).
            csv_y_field: Nome da coluna Y (CSV).

        Returns:
            (x_array, y_array, metadata) mesmo formato do LasUtil.extract_points.
        """
```

### 1C. `VectorLayerGeometry` — Geração do concave hull + suavização

```python
# utils/vector/VectorLayerGeometry.py

class VectorLayerGeometry(BaseUtil):
    @staticmethod
    def generate_concave_boundary(
        x: np.ndarray,
        y: np.ndarray,
        ratio: float = 0.10,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ):
        """
        Gera um polígono côncavo (concave hull) a partir de arrays de coordenadas.
        
        Usa shapely.concave_hull internamente.
        
        Args:
            x: Array 1D de coordenadas X.
            y: Array 1D de coordenadas Y.
            ratio: Ratio do concave hull (0..1, menor = mais detalhe).
            tool_key: ToolKey para logging.
            
        Returns:
            shapely.geometry.Polygon ou MultiPolygon.
        """
    
    @staticmethod
    def smooth_polygon(
        polygon,
        distance: float = 20.0,
        resolution: int = 16,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ):
        """
        Suaviza um polígono usando buffer positivo e negativo.
        
        Equivalente a: polygon.buffer(distance, resolution).buffer(-distance, resolution)
        
        Args:
            polygon: shapely.geometry.Polygon
            distance: Distância do buffer em metros.
            resolution: Resolução do buffer (default 16).
            tool_key: ToolKey para logging.
            
        Returns:
            shapely.geometry.Polygon suavizado.
        """
    
    @staticmethod
    def detect_escada(
        areas: list[float],
        ratios: list[float],
        limiar: float = 12.0,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> tuple[float, float, bool]:
        """
        Detecta "escada" em uma sequência de áreas decrescentes.
        
        Args:
            areas: Lista de áreas em m² (do maior ratio para o menor).
            ratios: Lista de ratios correspondentes.
            limiar: Percentual de queda que dispara detecção (%).
            tool_key: ToolKey para logging.
            
        Returns:
            (ratio_ideal, ratio_escada, encontrou)
            ratio_ideal: Último ratio antes da escada.
            ratio_escada: Ratio onde a escada foi detectada.
            encontrou: True se escada detectada.
        """
```

---

## 🏗 Passo 2: ToolKey + ToolRegistry

### `core/enum/ToolKey.py` — Adicionar:

```python
POINT_BOUNDARY = "PointBoundary"
```

### `core/config/ToolRegistry.py` — Adicionar entrada:

```python
ToolKey.POINT_BOUNDARY.value: Tool(
    name=ToolKey.POINT_BOUNDARY.value,
    title="Limite de Pontos",
    widget_factory=_make_factory(
        "plugins.point_boundary.PointBoundaryPlugin",
        "PointBoundaryPlugin",
    ),
    tooltip="Gera limite (envoltória) de nuvens LAS/LAZ ou vetores de pontos com validação iterativa",
    tool_type=ToolType.VECTOR,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
```

---

## 🏗 Passo 3: PointBoundaryStep — Step do Pipeline

**Arquivo:** `plugins/point_boundary/PointBoundaryStep.py`

### Comportamento

```python
class PointBoundaryStep(BaseStep):
    def name(self) -> str:
        return "PointBoundaryStep"

    def should_run(self, context) -> bool:
        return bool(context.get("file_path"))

    def create_task(self, context) -> PointBoundaryTask:
        """Cria a Task que será executada na QThread."""
        return PointBoundaryTask(context.to_dict())
```

### Context (entrada)

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `file_path` | str | Caminho do arquivo de entrada |
| `ratio_inicial` | float | Ratio inicial do concave hull |
| `ratio_step` | float | Decremento do ratio |
| `limiar_escada` | float | % queda para detectar escada |
| `suavisacao` | float | Buffer de suavização (m) |
| `n_amostras` | int | Pontos para amostragem |
| `crs` | str | CRS de saída (ex: "EPSG:31982") |
| `output_dir` | str | Diretório de saída |
| `tool_key` | str | Chave da ferramenta |
| `csv_x_field` | str | Nome coluna X (CSV) |
| `csv_y_field` | str | Nome coluna Y (CSV) |

### Context (saída)

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `hull_result` | dict | Resultado completo do validate_hull() |
| `hull_summary` | dict | Resumo para exibição no GridLabel |

---

## 🏗 Passo 4: PointBoundaryTask — Task Obrigatória

**Arquivo:** `plugins/point_boundary/PointBoundaryTask.py`

A Task executa em QThread dedicada e contém a lógica pesada. **É OBRIGATÓRIA** porque o processamento de LAS com milhões de pontos é pesado.

### Fluxo da Task

```
_run():
  1. Emite hud_update (5%) "Extraindo pontos da fonte..."
  2. Detecta extensão do arquivo:
     - .las/.laz → LasUtil.extract_points()
     - .shp/.gpkg/.kml/.geojson/.csv → VectorLayerSource.extract_point_coordinates()
  3. Emite hud_update (30%) "Gerando concave hull iterativo..."
  4. Loop iterativo com ratio decrescente:
     - Para cada ratio: VectorLayerGeometry.generate_concave_boundary()
     - Calcula área
     - Salva GPKG da iteração
     - VectorLayerGeometry.detect_escada() ao final
  5. Emite hud_update (70%) "Suavizando polígono..."
  6. VectorLayerGeometry.smooth_polygon()
  7. Emite hud_update (90%) "Exportando resultados..."
  8. Salva GPKG final + JSON
  9. Preenche self.result com dict de resultados
  10. Emite hud_update (100%)
  11. return True
```

### Uso do SignalManager (thread-safe)

```python
from core.manager.SignalManager import SignalManager

class PointBoundaryTask(BaseTask):
    def _run(self) -> bool:
        signals = SignalManager.instance()
        
        signals.hud_update.emit({"message": "Extraindo pontos...", "progress": 5.0})
        signals.progress_update.emit(5.0)
        
        try:
            # ... lógica ...
            
            signals.hud_update.emit({"message": "Hull gerado!", "progress": 100.0})
            signals.progress_update.emit(100.0)
            
            self.result = {...}
            return True
        except Exception as e:
            # ... tratamento ...
            return False
```

---

## 🏗 Passo 5: PointBoundaryPlugin — Widget Principal

**Arquivo:** `plugins/point_boundary/PointBoundaryPlugin.py`

### UI Layout

```
┌─────────────────────────────────────────────┐
│  PluginPage (title="Limite de Pontos")       │
│                                               │
│  ┌─ GroupPainel "Arquivo de Entrada" ──────┐ │
│  │  SelectorGrid:                           │ │
│  │    "Arquivo de Pontos"                   │ │
│  │    file_filter: "LAS/LAZ (*.las *.laz);;  │ │
│  │      Shapefile (*.shp);; GeoPackage       │ │
│  │      (*.gpkg);; KML (*.kml);; CSV        │ │
│  │      (*.csv);; GeoJSON (*.geojson)"       │ │
│  │  SimpleLabel: info da fonte detectada     │ │
│  │  (se CSV) GridLineEdit: nome coluna X/Y   │ │
│  └───────────────────────────────────────────┘ │
│                                               │
│  ┌─ GroupPainel "Parâmetros" ───────────────┐ │
│  │  GridDoubleSpinBox:                       │ │
│  │    "ratio_inicial": 0.10 (step 0.01)     │ │
│  │    "ratio_step":    0.01 (step 0.001)    │ │
│  │    "limiar_escada": 12.0 (step 0.5)      │ │
│  │    "suavisacao":    20.0 (step 1.0)      │ │
│  │    "n_amostras":    100000 (step 10000)  │ │
│  │  GridLineEdit:                            │ │
│  │    "crs": "EPSG:31982" (placeholder)      │ │
│  └───────────────────────────────────────────┘ │
│                                               │
│  ┌─ GroupPainel "Resultados" ───────────────┐ │
│  │  GridLabel (columns=2):                   │ │
│  │    "fonte":        "Fonte"               │ │
│  │    "n_pontos":     "Total Pontos"        │ │
│  │    "n_amostrados": "Pontos Amostrados"   │ │
│  │    "ratio_ideal":  "Ratio Ideal"         │ │
│  │    "area_hull":    "Área Hull"           │ │
│  │    "area_suav":    "Área Suavizada"      │ │
│  │    "escada":       "Escada Detectada"    │ │
│  │    "crs_utilizado":"CRS"                 │ │
│  │    "status":       "Status"              │ │
│  └───────────────────────────────────────────┘ │
│                                               │
│  ┌─ ExecutionButtons ───────────────────────┐ │
│  │  [SALVAR JSON] [EXECUTAR]                │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Widgets Reutilizáveis

| Widget | Arquivo | Uso |
|--------|---------|-----|
| `SelectorGrid` | `resources/widgets/SelectorGrid.py` | Seleção do arquivo de entrada |
| `GridDoubleSpinBox` | `resources/widgets/GridDoubleSpinBox.py` | Parâmetros numéricos |
| `GridLineEdit` | `resources/widgets/GridLineEdit.py` | CRS + colunas CSV |
| `GridLabel` | `resources/widgets/GridLabel.py` | Exibição de resultados |
| `ExecutionButtons` | `resources/widgets/ExecutionButtons.py` | Botões EXECUTAR + SALVAR JSON |
| `GroupPainel` | `resources/widgets/GroupPainel.py` | Containers de seção |
| `SimpleLabel` | `resources/widgets/SimpleLabel.py` | Info da fonte detectada |

### Fluxo de Execução (com HUD + Statistics)

```
1. load_prefs() — restaura último diretório + parâmetros

2. Usuário seleciona arquivo → _on_input_path_changed()
   ├── Detecta extensão (.las, .shp, .gpkg, .kml, .csv, .geojson)
   ├── Extrai metadados via LasUtil ou VectorLayerSource
   ├── Se CSV: mostra campos extras para nome das colunas X/Y
   └── Atualiza GridLabel com info da fonte

3. Usuário clica EXECUTAR → _on_executar()
   ├── Valida parâmetros
   ├── self.statistics.start(n=0, ntype=POINTS, ntotal=n_pontos)
   ├── Calcula tempo estimado via statistics.remaining_time
   ├── Emite execution_started → MainWindow mostra HUD
   ├── Emite hud_show({"message": "Validando limite...", "stages": [total_estimate, n_stages]})
   ├── Cria PipelineRunner + PointBoundaryStep
   └── Executa em background (QThread)

4. Pipeline completa → _on_done()
   ├── self.statistics.end() → persiste histórico
   ├── Atualiza GridLabel com resultados
   ├── Habilita botão SALVAR JSON
   ├── Emite execution_finished → MainWindow esconde HUD
   └── Emite console_message

5. _on_runner_finished()
   ├── Emite hud_hide + progress_update(0)
   └── Restaura botões

6. Usuário clica SALVAR JSON → _on_salvar_json()
   └── Salva JSON com resultados completos

7. AO FECHAR O PLUGIN → BasePlugin.closeEvent() chama save_prefs()
   ├── Salva último diretório
   └── Salva parâmetros atuais (ratio, step, limiar, suavização, n_amostras, CRS)
```

### Tratamento de CRS (Ordem de Prioridade)

1. **Tentar extrair CRS da fonte de entrada** — via `laspy.header` para LAS ou `geopandas.crs` para vetores
2. **Se não encontrado, usar CRS configurado pelo usuário** no campo `GridLineEdit["crs"]`
3. **Se vazio, usar EPSG:4326** (WGS84) como padrão

---

## 📊 Detecção de "Escada" — Algoritmo

```
area_ref = concave_hull(mp, ratio=RATIO_INICIAL)
area_anterior = area_ref

para cada ratio em [RATIO_INICIAL - RATIO_STEP, ..., 0]:
    hull = concave_hull(mp, ratio=ratio_atual)
    area = hull.area
    queda_pct = ((area_anterior - area) / area_anterior) * 100
    
    se queda_pct > LIMIAR_ESCADA E ratio_atual < RATIO_INICIAL:
        ESCADA DETECTADA!
        ratio_ideal = ultimo_ratio_processado
        break
    
    area_anterior = area
    ultimo_ratio_processado = ratio_atual
    Salva GPKG da iteração

se não encontrou escada:
    ratio_ideal = ultimo_ratio_processado

hull_suavizado = hull_final.buffer(SUAVISACAO).buffer(-SUAVISACAO)
Salva GPKG final suavizado
Gera JSON com resultados de todas as iterações
```

---

## 🔧 Correções do EST3 Aplicáveis

| ID | Correção | Aplicação |
|----|----------|-----------|
| V2 | nodata=255 | Não se aplica (sem raster) |
| V5 | BIGTIFF=YES | Não se aplica (sem raster) |
| — | CRS hierárquico | 1º CRS da fonte → 2º configurado → 3º EPSG:4326 |
| — | GPKG com CRS | `fiona.open(..., crs=CRS)` para todos GPKGs |

---

## ✅ Checklist de Implementação

### Fase 0 — Expandir Utilitários Existentes
- [ ] `LasUtil.extract_points()` — extração de coordenadas de LAS/LAZ com metadados
- [ ] `VectorLayerSource._SUPPORTED_EXTENSIONS` — adicionar .kml e .geojson
- [ ] `VectorLayerSource.extract_point_coordinates()` — extração de coordenadas de vetores + CSV
- [ ] `VectorLayerGeometry.generate_concave_boundary()` — geração do concave hull
- [ ] `VectorLayerGeometry.smooth_polygon()` — suavização via buffer duplo
- [ ] `VectorLayerGeometry.detect_escada()` — detecção de escada em sequência de áreas

### Fase 1 — Estrutura Base do Plugin
- [ ] Criar diretório `plugins/point_boundary/`
- [ ] Criar `plugins/point_boundary/__init__.py`
- [ ] Adicionar `POINT_BOUNDARY = "PointBoundary"` em `core/enum/ToolKey.py`
- [ ] Registrar em `core/config/ToolRegistry.py` com `ToolType.VECTOR`

### Fase 2 — Step do Pipeline
- [ ] Criar `PointBoundaryStep.py`
  - [ ] `should_run()` — valida file_path
  - [ ] `create_task()` — instancia PointBoundaryTask com context
  - [ ] `on_success()` — mescla resultados no context

### Fase 3 — Task (Obrigatória)
- [ ] Criar `PointBoundaryTask.py`
  - [ ] `_run()` — fluxo completo:
    - [ ] Extração de pontos (LasUtil ou VectorLayerSource)
    - [ ] Amostragem
    - [ ] Loop iterativo do concave hull
    - [ ] Detecção de escada
    - [ ] Suavização
    - [ ] Exportação GPKG por iteração + final
    - [ ] Geração do JSON de resultados
  - [ ] Emissão de `hud_update` + `progress_update` durante execução
  - [ ] Tratamento de erros com log

### Fase 4 — Plugin Widget
- [ ] Criar `PointBoundaryPlugin.py`
  - [ ] `_build_ui()` — SelectorGrid + GridDoubleSpinBox + GridLineEdit + GridLabel + ExecutionButtons
  - [ ] `_on_input_path_changed()` — detecta tipo de arquivo, extrai metadados
  - [ ] `_on_csv_fields_changed()` — mostra campos extras se CSV
  - [ ] `_on_executar()` — valida, statistics.start(), hud_show(), cria PipelineRunner
  - [ ] `_on_done()` — statistics.end(), atualiza UI, execution_finished
  - [ ] `_on_error()` — log + hud_hide
  - [ ] `_on_runner_finished()` — hud_hide + progress_update(0)
  - [ ] `_on_salvar_json()` — exporta JSON
  - [ ] `load_prefs()` — restaura último diretório + parâmetros
  - [ ] `save_prefs()` — persiste último diretório + parâmetros

### Fase 5 — Validação e Testes
- [ ] Testar com arquivo LAS/LAZ
- [ ] Testar com Shapefile de pontos
- [ ] Testar com GeoPackage de pontos
- [ ] Testar com KML de pontos
- [ ] Testar com GeoJSON de pontos
- [ ] Testar com CSV (x, y)
- [ ] Testar detecção de escada (ratio baixo)
- [ ] Testar sem escada (ratio ideal = último)
- [ ] Testar CRS: fonte com CRS
- [ ] Testar CRS: fonte sem CRS → usa configurado
- [ ] Testar CRS: vazio → EPSG:4326
- [ ] Verificar GPKGs de saída
- [ ] Verificar JSON de resultados
- [ ] Verificar logs em todos os pontos críticos
- [ ] Verificar HUD (execution_started → hud_update → hud_hide)
- [ ] Verificar statistics (start → end → histórico)

### Fase 6 — Documentação
- [ ] Atualizar `docs/implementacoes/FERRAMENTAS_EXTRAIDAS_EST3.md` (marcar como implementado)
- [ ] Remover plano antigo `docs/plans/PLAN_CONCAVE_HULL_VALIDATOR.md`

---

## 🔗 Relação com Outras Ferramentas

```
LAS/LAZ / SHP / GPKG / KML / CSV / GeoJSON
    │
    └──► [3] PointBoundaryPlugin
            │
            ├──► GPKG do polígono suavizado (usado por RasterPolygonClipperPlugin)
            ├──► JSON com resultados das iterações
            └──► Área suavizada (usada por LasStatisticsPlugin para densidade real)
```

---

## ⚠️ Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| LAS muito grande (>100M pts) | Amostragem automática para N amostras configurável |
| CSV sem colunas x/y padrão | Campos extras aparecem quando CSV é selecionado |
| KML sem pontos (linhas/polígonos) | Validar geometria: extrair apenas Point/MultiPoint |
| CRS ausente na fonte | Hierarquia: fonte → configurado → EPSG:4326 |
| `concave_hull` lento em muitos pontos | Amostragem para N configurável (default 100k) |
| Task bloqueia UI sem progresso | `hud_update` + `progress_update` emitidos a cada etapa |

---

> **Plano gerado em:** 23/06/2026
> **Baseado em:** EST3.PY v5, FERRAMENTAS_EXTRAIDAS_EST3.md, SKILL_CREATE_TOOL.md, SKILL_WIDGETS.md, SKILL_VECTOR_RASTER_LAYER_UTILS.md, SKILL_HUD_PROGRESS.md, agent.md