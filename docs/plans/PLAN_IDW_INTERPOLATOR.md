# Plano de Implementação — IdwInterpolatorPlugin (v2)

> **Fonte:** `docs/implementacoes/FERRAMENTAS_EXTRAIDAS_EST3.md` — Ferramenta #5
> **Arquivo base:** `docs/implementacoes/EST3.PY`
> **Plugins de referência:** `plugins/las_check/`, `plugins/point_boundary/`
> **Skills:** `SKILL_CREATE_TOOL.md`, `SKILL_WIDGETS.md`, `SKILL_UTILS.md`
> **Contratos:** `docs/ia/contracts.md`

---

## 1. Visão Geral

Extrair do EST3.PY o sistema de **Interpolação IDW** (Inverse Distance Weighting), transformando-o em um plugin independente que gera grids regulares a partir de nuvens de pontos LAS/LAZ.

### Funcionalidades solicitadas

| Funcionalidade | Widget | Descrição |
|---------------|--------|-----------|
| **Alvo da Interpolação** | **GridCheckBox** | check R, check G, check B, check Altura (Z) — checkboxes individuais |
| **Separar Bandas?** | **GridCheckBox** | Default false. Se true: banda_R.tif + banda_G.tif + banda_B.tif. Se false: mosaico_rgb.tif |
| **Botão "Pixel Ideal"** | **SimplePrimaryButton** | Na barra ExecutionButtons. Calcula `1/sqrt(densidade)` e carrega no GridDoubleSpinBox resolução |
| **GridDoubleSpinBox IDW** | k, power, raio_max, overlap, pontos_por_tile, fator_conversao | Parâmetros da interpolação |

### Regras de Negócio
- **Não** aplicar filtro de pontos pretos — isso é responsabilidade do LasBlackFilterPlugin
- **Fator 0.75** não é mais fixo — é um GridDoubleSpinBox editável pelo usuário (Fator de Conversão)
- **Pixel ideal**: `pixel_ideal_m = max(espacamento * fator_conversao, PIXEL_MINIMO_M)` — fator é digitado pelo usuário
- **NÃO existe RGB+Altura em raster**: o raster ou é RGB (3 bandas) ou Altura (1 banda) ou R+G+B+Z (4 bandas)
- **Só gera mosaico** se TODOS os checks RGB estiverem setados. Se faltar 1, ignora "separar bandas = false" (não tem como fazer mosaico RGB faltando banda)
- **Execução em Task** (não apenas Step) — processamento pesado merece Task dedicada

---

## 2. Arquitetura do Plugin

### 2.1 Estrutura de Arquivos

```
plugins/idw_interpolator/
    __init__.py
    IdwInterpolatorPlugin.py      # Widget principal (herda BasePlugin)
    IdwInterpolatorStep.py         # Step do pipeline (herda BaseStep)
    IdwInterpolatorTask.py         # Task executada pelo step
```

```
utils/raster/
    InterpolatorUtils.py           # Utilitário genérico de interpolação (IDW agora, Kriging/Spline futuro)
```

### 2.2 Registro no Sistema

#### `core/enum/ToolKey.py`
```python
IDW_INTERPOLATOR = "IdwInterpolator"
```

#### `core/config/ToolRegistry.py`
```python
ToolKey.IDW_INTERPOLATOR.value: Tool(
    name=ToolKey.IDW_INTERPOLATOR.value,
    title="Interpolação IDW",
    widget_factory=_make_factory(
        "plugins.idw_interpolator.IdwInterpolatorPlugin",
        "IdwInterpolatorPlugin",
    ),
    tooltip="Interpola nuvem LAS/LAZ em grid regular via IDW (RGB e/ou Altura)",
    tool_type=ToolType.POINTS,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
```

---

## 3. UI — Widgets

### 3.1 Layout da Interface

```
┌───────────────────────────────────────────────────────────┐
│  ExecutionButtons:                                         │
│  [CALCULAR PIXEL IDEAL]  [EXECUTAR]  [CANCELAR]           │
├───────────────────────────────────────────────────────────┤
│  GroupPainel: "Arquivo de Entrada"                         │
│    ┌──────────────────────────────────────────────────┐    │
│    │ SelectorGrid: "LAS/LAZ de Entrada"               │    │
│    │ SelectorGrid: "Salvar Raster em" (save_file)     │    │
│    │                                                  │    │
│    │ SimpleLabel: "Pontos: 1.234.567 | RGB: sim"      │    │
│    │ SimpleLabel: "BBox: X[300.0, 400.0]..."          │ ← só aparece após calcular pixel │
│    │ SimpleLabel: "Densidade: 12.34 pts/m²"           │ ← só aparece após calcular pixel │
│    │ SimpleLabel: "Espaçamento: 8.50 cm/ponto"        │ ← só aparece após calcular pixel │
│    └──────────────────────────────────────────────────┘    │
├───────────────────────────────────────────────────────────┤
│  GroupPainel: "Target da Interpolação"                     │
│    ┌──────────────────────────────────────────────────┐    │
│    │ GridCheckBox (4 colunas):                         │    │
│    │   ☑ R    ☑ G    ☑ B    ☐ Altura (Z)             │    │
│    │                                                  │    │
│    │ GridCheckBox: "Separar Bandas?" = false          │    │PODE SER UMA GRID CHECKBOX UNICA COM 4COLUNAS 
                                                                1PAINEL APENAS
│    │ GridDoubleSpinBox:                                │    │
│    │   Resolução (cm):    1.00  [0.1–100]   passo 0.01│    │
│    │   Fator Conversão:   0.75  [0.1–5.0]   passo 0.01│    │
│    │   Vizinhos (k):      5     [1–50]       passo 1   │    │ADICIONE DESCRIPTION A CADA ITEM POR FAVOR DESCRIPTION BEM COERENTE QUE UM INUTIL CONSIGA ENTENDER 
│    │   Potência (p):      2.0   [0.5–5.0]    passo 0.1 │    │
│    │   Raio Máx (m):      0.50  [0.01–10]    passo 0.05│    │
│    │   Overlap (m):       3.0   [0–10]        passo 0.5 │    │
│    │   Pontos/Tile:    10.000.000 [100k–100M] passo 1M │    │
│    └──────────────────────────────────────────────────┘    │
├───────────────────────────────────────────────────────────┤
│  GroupPainel: "Resultados"                                │
│    ┌──────────────────────────────────────────────────┐    │
│    │ GridLabel:                                        │    │
│    │   grid_dims    → "12.345 x 8.765 px"             │    │
│    │   resolucao    → "1.00 cm"                       │    │
│    │   n_tiles      → "48"                            │    │
│    │   tempo_idw    → "02:34:15"                      │    │
│    │   output_path  → "C:/saida/mosaico_rgb.tif"     │    │
│    │   status       → "Concluído ✅"        
        LINK DO ARQUIVO DE SAIDA COM HREF NO PAINEL E NO CONSOLE          │    │
│    └──────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────┘
```

### 3.2 GridCheckBox — Target da Interpolação

```python
TARGET_CONFIG = {
    "r": {
        "label": "R (Vermelho)",
        "description": "Interpola banda vermelha",
        "default": True,
    },
    "g": {
        "label": "G (Verde)",
        "description": "Interpola banda verde",
        "default": True,
    },
    "b": {
        "label": "B (Azul)",
        "description": "Interpola banda azul",
        "default": True,
    },
    "z": {
        "label": "Altura (Z)",
        "description": "Interpola altitude Z",
        "default": False,
    },
}

self._target_grid = GridCheckBox(TARGET_CONFIG, num_columns=4)
self._target_grid.changed.connect(self._on_target_changed)
```

### 3.3 GridCheckBox — Separar Bandas NAO PRECISA BOTA 1 GRID SO 

```python
SEPARAR_CONFIG = {
    "separate": {
        "label": "Separar Bandas?",
        "description": "Se true: banda_R/G/B/Z.tif individuais. Se false: mosaico_rgb.tif",
        "default": False,
    },
}

self._separar_grid = GridCheckBox(SEPARAR_CONFIG, num_columns=1)
```

### 3.4 GridDoubleSpinBox — Parâmetros Completos

```python
self._params_grid = GridDoubleSpinBox({
    "resolution": {
        "label": "Resolução (cm)",
        "description": "Tamanho do pixel em centímetros",
        "decimal": 2,
        "default": 1.00,
        "min": 0.1,
        "max": 100.0,
        "step": 0.01,
        "suffix": "cm",
    },
    "fator_conversao": {
        "label": "Fator Conversão",
        "description": "Multiplicador do espaçamento para cálculo do pixel ideal",
        "decimal": 2,
        "default": 0.75,
        "min": 0.1,
        "max": 5.0,
        "step": 0.01,
    },
    "k": {
        "label": "Vizinhos (k)",
        "description": "Número de vizinhos mais próximos para IDW",
        "decimal": 0,
        "default": 5,
        "min": 1,
        "max": 50,
        "step": 1,
    },
    "power": {
        "label": "Potência (p)",
        "description": "Expoente da distância (2 = inverso quadrático)",
        "decimal": 1,
        "default": 2.0,
        "min": 0.5,
        "max": 5.0,
        "step": 0.1,
    },
    "raio_max": {
        "label": "Raio Máx (m)",
        "description": "Raio máximo de busca em metros",
        "decimal": 2,
        "default": 0.50,
        "min": 0.01,
        "max": 10.0,
        "step": 0.05,
        "suffix": "m",
    },
    "overlap": {
        "label": "Overlap (m)",
        "description": "Sobreposição entre tiles para evitar artefatos de borda",
        "decimal": 1,
        "default": 3.0,
        "min": 0.0,
        "max": 10.0,
        "step": 0.5,
        "suffix": "m",
    },
    "pontos_por_tile": {
        "label": "Pontos/Tile",
        "description": "Número alvo de pontos por tile para divisão da grade",
        "decimal": 0,
        "default": 10_000_000,
        "min": 100_000,
        "max": 100_000_000,
        "step": 1_000_000,
    },
})
```

### 3.5 ExecutionButtons

```python
self._btns = ExecutionButtons(self, {
    "pixel_ideal": {
        "text": "CALCULAR PIXEL IDEAL",
        "callback": self._on_calc_ideal_pixel,
        "type": "secondary",
        "description": "Calcula pixel ideal pela densidade da nuvem",
    },
    "executar": {
        "text": "EXECUTAR",
        "callback": self._on_executar,
        "type": "primary",
        "description": "Executa interpolação IDW",
    },
    "cancelar": {
        "text": "CANCELAR",
        "callback": self._on_cancelar,
        "type": "danger",
        "description": "Cancela execução em andamento",
    },
})
self._btns.set_enabled("executar", False)
self._btns.set_enabled("cancelar", False)
```

### 3.6 SelectorGrid — Entrada + Saída

```python
self._selector_grid = SelectorGrid({
    "LAS/LAZ de Entrada": {
        "file_filter": "LAS/LAZ (*.las *.laz)",
        "browse_mode": "open_file",
        "placeholder": "Selecione o arquivo LAS/LAZ...",
    },
    "Salvar Raster em": {
        "file_filter": "GeoTIFF (*.tif)",
        "browse_mode": "save_file",
        "placeholder": "Selecione onde salvar o raster...",
    },
})
```

---

## 4. Fluxo de Execução

### 4.1 Botão "CALCULAR PIXEL IDEAL"

```python
def _on_calc_ideal_pixel(self):
    """
    Calcula pixel ideal baseado na densidade da nuvem.
    Só executa se houver LAS carregado.
    
    Fórmula:
        area_bbox = (x_max - x_min) * (y_max - y_min)
        densidade = n_pontos / area_bbox
        espacamento = 1 / sqrt(densidade)
        fator = self._params_grid.get("fator_conversao")
        pixel_ideal_m = max(espacamento * fator, PIXEL_MINIMO_M)
        pixel_ideal_cm = pixel_ideal_m * 100
    
    Após calcular:
    - Atualiza GridDoubleSpinBox "resolution" com o valor
    - Exibe SimpleLabels: BBox, Densidade, Espaçamento
    """
```

**Observação:** `calcular_pixel_ideal()` é responsabilidade do **LasUtil**, não do InterpolatorUtils.

### 4.2 Pipeline — Execução

```
[Estágio 1] Leitura do LAS
    ├── Carrega LAS com laspy
    ├── NÃO aplica filtro de pontos pretos (responsabilidade do LasBlackFilterPlugin)
    └── Extrai arrays conforme target checks:
        ├── Se R checked → red
        ├── Se G checked → green
        ├── Se B checked → blue
        └── Se Z checked → z

[Estágio 2] Cálculo do Grid Global
    ├── Só executa se usuário já calculou pixel ideal (ou definiu resolução manualmente)
    ├── Resolução = self._params_grid.get("resolution") / 100 (converte cm → m)
    ├── Calcula bounds do grid a partir dos pontos
    ├── width/height = ceil((max - min) / resol)
    └── Cria transform from_origin(min_x, max_y, resol, resol)

[Estágio 3] Divisão em Tiles
    ├── InterpolatorUtils.calcular_tiles_por_densidade()
    └── Grade N×M baseada em self._params_grid.get("pontos_por_tile")

[Estágio 4] Interpolação IDW Paralela (Task)
    ├── IdwInterpolatorTask executa em background
    ├── joblib.Parallel + InterpolatorUtils.idw_tile_para_disco()
    ├── Para cada tile: cKDTree → IDW → salva GeoTIFF
    ├── Tiles salvos em pasta TEMPORÁRIA (ExplorerUtils.get_plugin_config_dir ou tempfile)
    │   └── tiles/R/, tiles/G/, tiles/B/, tiles/Z/
    ├── Retomada automática: se tile já existe, pula
    └── Emite progresso via SignalManager

[Estágio 5] Mescla Tiles → Bandas Completas (ParalelStep)
    ├── Cada banda (R, G, B, Z) é mesclada em paralelo (não dependentes)
    │   └── InterpolatorUtils.mesclar_banda() → banda_R.tif, banda_G.tif, etc.
    └── Aguarda todas as bandas ficarem prontas

[Estágio 6] Montagem da Saída
    ├── Se "Separar Bandas?" = true:
    │   ├── Cada banda → arquivo individual (banda_R.tif, banda_G.tif, banda_B.tif, banda_Z.tif)
    │   └── Renomeia/copia para diretório de saída definitivo
    │
    ├── Se "Separar Bandas?" = false (mosaico):
    │   ├── Só gera mosaico RGB se R, G, B TODOS setados
    │   │   └── RasterLayerProcessing.compose_multiband_raster() → mosaico_rgb.tif
    │   ├── Se só Z: copia banda_Z.tif → mosaico_altura.tif
    │   └── Se R+G+B+Z: RasterLayerProcessing.compose_multiband_raster() → mosaico_rgbz.tif (4 bandas)
    │
    └── Limpa pasta temporária de tiles

[Estágio 7] Geração de Metadados
    └── Salva metadata.json com parâmetros, dimensões, tempo, etc.
```

---

## 5. Utilitário: `utils/raster/InterpolatorUtils.py` (NOVO)

Nome genérico para suportar futuros interpoladores (Kriging, Spline, etc.).

```python
class InterpolatorUtils(BaseUtil):
    """
    Utilitários genéricos para interpolação de nuvens de pontos em grid regular.
    
    Atualmente suporta IDW (Inverse Distance Weighting).
    Futuramente: Kriging, Spline, Nearest Neighbor.
    
    Métodos:
        idw_tile_para_disco()       — interpola um tile via IDW e salva em disco
        calcular_tiles_por_densidade() — divide área em tiles baseado na densidade
        mesclar_banda()             — mescla tiles em banda completa via memmap
        salvar_tile_tif()           — salva array 2D como GeoTIFF tile
    """
```

### 5.1 Métodos do InterpolatorUtils

| Método | Descrição | Responsabilidade |
|--------|-----------|-----------------|
| `idw_tile_para_disco()` | Interpola um tile com cKDTree + IDW | Cálculo IDW puro |
| `calcular_tiles_por_densidade()` | Divide área em grade N×M | Gradeamento |
| `mesclar_banda()` | Mescla tiles individuais em banda completa via memmap | Merge de tiles |
| `salvar_tile_tif()` | Escreve array 2D como GeoTIFF com BIGTIFF=YES | Escrita GeoTIFF |

### 5.2 O que NÃO vai no InterpolatorUtils

| Funcionalidade | Onde vai | Motivo |
|---------------|----------|--------|
| `calcular_pixel_ideal()` | **LasUtil** | Cálculo de densidade é sobre a nuvem, não sobre interpolação |
| `filtrar_pontos_pretos()` | LasBlackFilterPlugin (já existe) | Responsabilidade de outro plugin |
| `compor_mosaico()` | **RasterLayerProcessing.compose_multiband_raster()** | União de bandas é processamento raster, não interpolação |

---

## 6. Task: `IdwInterpolatorTask`

### 6.1 Interface

```python
class IdwInterpolatorTask(BaseTask):
    """
    Task que executa a interpolação IDW em background.
    
    A task é responsável pelo Estágios 4–7 do pipeline.
    Executa em QThread via PipelineRunner.
    Emite progresso via SignalManager para HUD + ProgressBar.
    
    Parâmetros (context):
        file_path               — caminho do LAS
        output_dir              — diretório de saída
        target_bands            — {"r": bool, "g": bool, "b": bool, "z": bool}
        separate_bands          — bool (separar ou mosaico)
        resol_m                 — resolução em metros
        idw_k, idw_power, idw_raio_max, idw_overlap
        pontos_por_tile
        crs_str
        tool_key
    """
```

### 6.2 Estágios da Task

```
execute():
    ├── Estágio 4: Interpolação IDW Paralela
    │   ├── joblib.Parallel(n_jobs=-1) + idw_tile_para_disco()
    │   ├── Emite progresso por tile
    │   └── Salva tiles em pasta temp
    │
    ├── Estágio 5: Mescla Tiles → Bandas (ParalelStep)
    │   ├── Para cada banda ativa: mesclar_banda() em paralelo
    │   └── Resultado: banda_R.tif, banda_G.tif, etc.
    │
    ├── Estágio 6: Montagem Saída
    │   ├── Se separate_bands: copia bandas individuais
    │   ├── Se !separate_bands: RasterLayerProcessing.compose_multiband_raster()
    │   └── Limpa temp
    │
    └── Estágio 7: Metadados
        └── Salva metadata.json
```

---

## 7. Step: `IdwInterpolatorStep`

Step leve que apenas orquestra a Task:

```python
class IdwInterpolatorStep(BaseStep):
    """
    Step que orquestra a IdwInterpolatorTask.
    
    Valida parâmetros, instancia a task e coleta resultados.
    """
    
    def execute(self, context: dict) -> dict:
        # Validações
        file_path = context.get("file_path", "")
        if not file_path or not os.path.isfile(file_path):
            raise ValueError("Arquivo LAS não encontrado")
        
        target = context.get("target_bands", {})
        if not any(target.values()):
            raise ValueError("Selecione ao menos uma banda para interpolar")
        
        # Se não tem RGB completo e quer mosaico, avisa
        if not context.get("separate_bands", False):
            has_rgb = target.get("r", False) and target.get("g", False) and target.get("b", False)
            if not has_rgb and (target.get("r", False) or target.get("g", False) or target.get("b", False)):
                raise ValueError(
                    "Para gerar mosaico, é necessário selecionar R, G e B simultaneamente. "
                    "Selecione 'Separar Bandas' para bandas individuais."
                )
        
        # Instancia e executa task
        task = IdwInterpolatorTask(context)
        result = task.execute()
        
        return result
```

---

## 8. Atualizações em Utilitários Existentes

### 8.1 `utils/LasUtil.py` — NOVOS métodos

```python
@staticmethod
def extract_point_arrays(
    path: str,
    bands: dict,  # {"r": bool, "g": bool, "b": bool, "z": bool}
    tool_key: str = ToolKey.UNTRACEABLE.value,
) -> dict:
    """
    Extrai arrays de coordenadas do LAS conforme bandas solicitadas.
    
    Returns:
        {
            "x": np.ndarray,
            "y": np.ndarray,
            "z": np.ndarray | None,    # se bands["z"]
            "red": np.ndarray | None,   # se bands["r"]
            "green": np.ndarray | None, # se bands["g"]
            "blue": np.ndarray | None,  # se bands["b"]
            "n_points": int,
        }
    """

@staticmethod
def calcular_pixel_ideal(
    path: str,
    fator_conversao: float = 0.75,
    tool_key: str = ToolKey.UNTRACEABLE.value,
) -> dict:
    """
    Calcula pixel ideal baseado na densidade da nuvem.
    
    Returns:
        {
            "n_pontos": int,
            "area_bbox_m2": float,
            "densidade_pts_m2": float,
            "espacamento_m": float,
            "espacamento_cm": float,
            "pixel_ideal_m": float,
            "pixel_ideal_cm": float,
            "bbox": {"x_min": ..., "x_max": ..., "y_min": ..., "y_max": ...},
        }
    """
```

### 8.2 `utils/raster/RasterLayerProcessing.py` — IMPLEMENTAR compose_multiband_raster()

O método `compose_multiband_raster()` atualmente é stub. Implementar:

```python
@staticmethod
def compose_multiband_raster(
    band_files: List[str],
    output_path: Optional[str] = None,
    create_alpha: bool = False,
    alpha_band_path: Optional[str] = None,
    creation_options: str = "",
    tool_key: str = ToolKey.UNTRACEABLE.value,
) -> str:
    """
    Compõe múltiplos GeoTIFFs single-band em um raster multibanda.
    
    Usado pelo IdwInterpolatorPlugin para gerar:
    - mosaico_rgb.tif (3 bandas: R, G, B)
    - mosaico_rgbz.tif (4 bandas: R, G, B, Z)
    
    Compressão LZW, tiled 512x512, BIGTIFF=YES.
    Chunked processing (2048 linhas) para evitar estouro de RAM.
    """
```

---

## 9. Tratamento de Z (Altura)

### 9.1 Interpolação

- Array `z` extraído como `np.float64`
- Interpolação IDW idêntica à RGB
- Saída: **float32** (padrão, sem escala/offset complexo)

### 9.2 Armazenamento

| Cenário | Banda(s) | Formato | dtype |
|---------|----------|---------|-------|
| Só Z | 1 banda (altura) | GeoTIFF single-band | float32 |
| RGB | 3 bandas (R, G, B) | GeoTIFF | uint8 |
| RGB + Z | 4 bandas (R, G, B, Z) | GeoTIFF | misto: uint8 + float32 |
| Separado: R | 1 banda | GeoTIFF | uint8 |
| Separado: Z | 1 banda | GeoTIFF | float32 |

**Nota:** Raster multibanda com dtypes mistos (uint8 + float32) não é suportado nativamente por GeoTIFF. Solução:
- RGB fica uint8 + Z fica float32 separado → 2 arquivos
- Ou normaliza Z para uint16 com offset + scale (similar a DEM)

---

## 10. Configuração de Saída

### 10.1 Estrutura Final

```
{output_dir}/
    metadata.json                       ← parâmetros, dimensões, tempo
    
    ## Modo "Separado" (separate_bands=true):
    banda_R.tif                         ← se R checked
    banda_G.tif                         ← se G checked
    banda_B.tif                         ← se B checked
    banda_Z.tif                         ← se Z checked
    
    ## Modo "Mosaico" (separate_bands=false) — só se R+G+B ativos:
    mosaico_rgb.tif                     ← 3 bandas (R, G, B)
    mosaico_rgbz.tif                    ← 4 bandas (R, G, B, Z) — se Z também ativo
    mosaico_altura.tif                  ← só se apenas Z ativo
```

### 10.2 Pasta Temporária de Tiles

Usar `ExplorerUtils.get_plugin_config_dir("idw_interpolator")` + `temp_tiles/`:
```
{config_dir}/idw_interpolator/temp_tiles/
    R/
        tile_0000_0000.tif
        ...
    G/
        ...
    B/
        ...
    Z/
        ...
```

Limpa após finalizar (sucesso ou erro).

---

## 11. Dependências (já existentes)

- `laspy` — leitura LAS/LAZ ✅
- `numpy` — arrays ✅
- `scipy` — cKDTree ✅
- `rasterio` — GeoTIFF ✅
- `joblib` — paralelismo ✅
- `shapely` — geometria (caso necessário para polígono de recorte) ✅

---

## 12. Checklist de Implementação

### Fase 1 — Base e Utilitários
- [ ] Criar `plugins/idw_interpolator/__init__.py`
- [ ] Criar `utils/raster/InterpolatorUtils.py` com:
  - [ ] `idw_tile_para_disco()` — extraído do EST3 com suporte a Z
  - [ ] `calcular_tiles_por_densidade()` — gradeamento por pontos/tile
  - [ ] `mesclar_banda()` — merge de tiles via memmap chunked
  - [ ] `salvar_tile_tif()` — escrita GeoTIFF com BIGTIFF=YES
- [ ] Adicionar `extract_point_arrays()` em `utils/LasUtil.py`
- [ ] Adicionar `calcular_pixel_ideal()` em `utils/LasUtil.py`
- [ ] Implementar `compose_multiband_raster()` em `utils/raster/RasterLayerProcessing.py`

### Fase 2 — Plugin
- [ ] Atualizar `core/enum/ToolKey.py` → adicionar `IDW_INTERPOLATOR`
- [ ] Atualizar `core/config/ToolRegistry.py` → registrar a tool
- [ ] Criar `IdwInterpolatorPlugin.py`:
  - [ ] `_build_ui()` com todos os widgets (SelectorGrid entrada+saída, GridCheckBox target, GridCheckBox separar, GridDoubleSpinBox params, ExecutionButtons, GridLabel)
  - [ ] `_on_input_path_changed()` — carrega metadados do LAS
  - [ ] `_on_target_changed()` — valida regras de RGB completo para mosaico
  - [ ] `_on_calc_ideal_pixel()` — calcula pixel ideal via LasUtil
  - [ ] `_on_executar()` — valida parâmetros, inicia PipelineRunner
  - [ ] `_on_cancelar()` — cancela execução
  - [ ] `_on_done()` / `_on_error()` / `_on_runner_finished()`
  - [ ] `load_prefs()` / `save_prefs()`

### Fase 3 — Step + Task
- [ ] Criar `IdwInterpolatorStep.py`:
  - [ ] Validações de entrada (arquivo existe, bandas selecionadas, mosaico requer RGB completo)
  - [ ] Orquestra IdwInterpolatorTask
- [ ] Criar `IdwInterpolatorTask.py`:
  - [ ] Estágio 4: IDW paralelo com joblib
  - [ ] Estágio 5: Mescla bandas em paralelo (ParalelStep)
  - [ ] Estágio 6: Montagem saída (mosaico ou separado via RasterLayerProcessing)
  - [ ] Estágio 7: Metadados JSON
  - [ ] Progresso via SignalManager (HUD + ProgressBar + Statistics)

### Fase 4 — Testes
- [ ] Testar LAS sem RGB (só altura Z)
- [ ] Testar LAS com RGB (modo mosaico)
- [ ] Testar "Separar Bandas = true"
- [ ] Testar RGB + Z (4 bandas)
- [ ] Testar botão "Calcular Pixel Ideal"
- [ ] Testar validação: mosaico sem R+G+B completo → erro
- [ ] Testar cancelamento durante execução
- [ ] Testar retomada automática de tiles
- [ ] Testar BIGTIFF=YES com arquivos grandes (>4GB)

### Fase 5 — Documentação
- [ ] Atualizar `docs/implementacoes/FERRAMENTAS_EXTRAIDAS_EST3.md` — marcar #5 como implementado
- [ ] Garantir Contrato 12: documentação atualizada

---

## 13. Referências

| Documento | Local |
|-----------|-------|
| Fonte EST3 | `docs/implementacoes/EST3.PY` |
| Ferramentas extraídas | `docs/implementacoes/FERRAMENTAS_EXTRAIDAS_EST3.md` |
| Skill criação tool | `docs/skills/SKILL_CREATE_TOOL.md` |
| Skill widgets | `docs/skills/SKILL_WIDGETS.md` |
| Skill utils | `docs/skills/SKILL_UTILS.md` |
| Contratos sistema | `docs/ia/agent.md` |
| LasCheckPlugin (ref) | `plugins/las_check/LasCheckPlugin.py` |
| PointBoundaryPlugin (ref) | `plugins/point_boundary/PointBoundaryPlugin.py` |
| LasUtil | `utils/LasUtil.py` |
| RasterLayerProcessing | `utils/raster/RasterLayerProcessing.py` |
| RasterLayerMetrics | `utils/raster/RasterLayerMetrics.py` |