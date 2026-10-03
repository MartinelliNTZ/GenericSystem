# Fluxo do Sistema Compartilhado de Tiling LAS

## Visão Geral

O sistema de tiling LAS foi extraído do `IdwInterpolatorTask` para ser compartilhado entre múltiplas ferramentas. Ele consiste em três camadas:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Camada de Utilitários                       │
│                                                               │
│  utils/raster/LasTilerUtils.py                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ • calcular_tiles_por_densidade() — divide área em tiles │  │
│  │ • criar_pastas_bandas() — estrutura de pastas          │  │
│  │ • limpar_tiles() — cleanup de tiles temporários        │  │
│  │ • salvar_tile_tif() — salva GeoTIFF de tile            │  │
│  │ • mesclar_banda() — mescla tiles em banda completa     │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Camada de Pipeline                          │
│                                                               │
│  core/papeline/step/LasTilerStep.py  (BaseStep)               │
│  core/papeline/task/LasTilerTask.py  (BaseTask)               │
│                                                               │
│  PipelineRunner → LasTilerStep → LasTilerTask                 │
│                                                               │
│  Context IN:  file_path, target_bands, resol_m,               │
│               pontos_por_tile, overlap, crs_str               │
│                                                               │
│  Context OUT: tiles, grid_bounds, grid_width, grid_height,   │
│               transform, x_pts, y_pts, r/g/b/z_pts           │
│               tile_dirs, temp_dir                             │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
│ LasTilerPlugin│   │IdwInterpolator  │   │  (Futuros)    │
│ (standalone)  │   │Plugin (usa como │   │  Kriging,     │
│               │   │  etapa interna) │   │  NN, etc.     │
└──────────────┘   └──────────────────┘   └──────────────┘
```

---

## LasTilerUtils

Utilitário estático (herda de `BaseUtil`) com 5 métodos principais:

### `calcular_tiles_por_densidade()`

Divide a área da nuvem em tiles baseado em:

1. **Densidade de pontos**: Cada tile deve ter aproximadamente `pontos_por_chunk` pontos
2. **Limite de pixels** (`max_tile_pixels`): Cada tile não deve exceder N pixels para evitar OOM em `np.meshgrid`

O número final de tiles é o maior entre os dois critérios.

**Retorno**: `list[(x0, x1, y0, y1, row, col)]`

### `criar_pastas_bandas()`

Cria estrutura de diretórios:

```
base_dir/
├── r/
├── g/
├── b/
└── z/
```

**Retorno**: `dict[str, str]` mapeando banda → caminho completo.

### `limpar_tiles()`

Remove as subpastas de tiles recursivamente. Só executa se `eliminar=True`.

### `salvar_tile_tif()`

Salva um array numpy 2D como GeoTIFF de 1 banda com suporte a BIGTIFF.

### `mesclar_banda()`

Lê todos os tiles de uma banda e mescla em um GeoTIFF completo via `np.memmap`.

---

## LasTilerStep (BaseStep)

Step reutilizável que pode ser usado em qualquer pipeline:

```python
from core.papeline.step.LasTilerStep import LasTilerStep

runner = PipelineRunner(
    steps=[
        LasTilerStep(),        # 1. Divide nuvem em tiles
        MeuStepDeProcessamento(), # 2. Processa cada tile
        MeuStepDeMerge(),      # 3. Mescla resultados
    ],
    context={...}
)
```

**Contexto de entrada**:

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `file_path` | `str` | Caminho do arquivo LAS/LAZ |
| `target_bands` | `dict` | Bandas a incluir `{"r": bool, "g": bool, "b": bool, "z": bool}` |
| `resol_m` | `float` | Resolução em metros |
| `pontos_por_tile` | `int` | Número alvo de pontos por tile |
| `overlap` | `float` | Overlap entre tiles (para bounds) |
| `crs_str` | `str` | CRS (ex: "EPSG:31982") |

**Contexto de saída** (via `on_success`):

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `tiles` | `list` | Lista de `(x0, x1, y0, y1, row, col)` |
| `grid_bounds` | `tuple` | `(min_x_g, max_x_g, min_y_g, max_y_g)` |
| `grid_width` | `int` | Largura do grid em pixels |
| `grid_height` | `int` | Altura do grid em pixels |
| `transform` | `Affine` | Transform rasterio do grid global |
| `n_pontos` | `int` | Total de pontos no LAS |
| `x_pts`, `y_pts` | `np.ndarray` | Coordenadas dos pontos |
| `r_pts`, `g_pts`, `b_pts`, `z_pts` | `np.ndarray` ou `None` | Arrays das bandas |
| `tile_dirs` | `dict` ou `None` | Pastas criadas (se `output_dir` definido) |
| `temp_dir` | `str` ou `None` | Diretório temporário de tiles |

---

## LasTilerTask (BaseTask)

Task que executa o tiling em background:

1. **Leitura do LAS** via `LasUtil.extract_point_arrays()`
2. **Cálculo do grid global**: min/max X, Y, dimensões, transform
3. **Divisão em tiles** via `LasTilerUtils.calcular_tiles_por_densidade()` com ajuste via `ResourceGovernor`
4. **Criação de pastas** (opcional, se `output_dir` definido)
5. **Resultado**: dict com todos os arrays e metadados

**Proteções de RAM**:
- `estimated_ram`: `n_pontos * 32 bytes`
- `_ajustar_tile_size()`: usa `ResourceGovernor.recommended_tile_size()` para reduzir tamanho dos tiles se RAM insuficiente
- `_check_during_execution()` entre estágios

---

## LasTilerPlugin

Plugin standalone que expõe o tiling como ferramenta independente:

**UI**:
- GridSelector: entrada LAS/LAZ + pasta de saída
- GridCheckBox: bandas R, G, B, Z + "Eliminar Tiles Temporários"
- GridDoubleSpinBox: pontos_por_tile, overlap
- ExecutionButtons: EXECUTAR, CANCELAR
- GridLabel: resultados (N Tiles, Pontos, Grid, Saída, Status)

**Fluxo**:
1. Usuário seleciona LAS → `_on_input_path_changed()` → `_carregar_las()`
2. Usuário clica EXECUTAR → `_on_executar()` → validações → cria `PipelineRunner` com `LasTilerStep`
3. Pipeline executa em background → `_on_done()` exibe resultados
4. Usuário pode clicar CANCELAR → `_on_cancelar()` → `runner.cancel()`

---

## Refatoração do IdwInterpolatorTask

O `IdwInterpolatorTask` foi refatorado para usar:

| Funcionalidade | Antes (duplicado) | Depois (compartilhado) |
|----------------|-------------------|------------------------|
| Cálculo de tiles | `InterpolatorUtils.calcular_tiles_por_densidade()` | `LasTilerUtils.calcular_tiles_por_densidade()` |
| Criação de pastas | `for banda in ... os.makedirs(...)` | `LasTilerUtils.criar_pastas_bandas()` |
| Limpeza de tiles | `for sub in ... shutil.rmtree(...)` | `LasTilerUtils.limpar_tiles()` |

Os métodos específicos do IDW (RAM estimation, logging, merge) permanecem no `IdwInterpolatorTask`.

---

## Contratos Seguidos

| Contrato | Descrição |
|:--------:|-----------|
| 11 | Widgets reutilizáveis (GridCheckBox, GridDoubleSpinBox, etc.) |
| 18 | ExecutionButtons padronizado |
| 20 | SignalManager para progresso/console |
| 23 | Utilitários compartilhados — lógica extraída para `utils/raster/LasTilerUtils.py` |
| 24 | SignalManager apenas para comunicação entre componentes |
| 25 | I/O via utils especializados (`utils.raster.LasTilerUtils`) |
| 26 | ToolKey no lugar de strings soltas |

## Como Adicionar uma Nova Ferramenta que Usa Tiling

1. **Use o step existente**: inclua `LasTilerStep` na sua pipeline
2. **Acesse os resultados**: o contexto conterá `tiles`, arrays, grid, etc.
3. **Processe cada tile**: itere sobre `tiles` e use os bounds para processar
4. **Mescle se necessário**: use `LasTilerUtils.mesclar_banda()` ou `LasTilerUtils.salvar_tile_tif()`
5. **Limpe**: use `LasTilerUtils.limpar_tiles()` se criou pastas temporárias

```python
# Exemplo de pipeline híbrida
step1 = LasTilerStep()
step2 = MeuStepCustomizado()  # step que processa cada tile
runner = PipelineRunner(
    steps=[step1, step2],
    context={
        "file_path": "nuvem.las",
        "target_bands": {"r": True, "g": True, "b": True, "z": False},
        "resol_m": 0.01,
        "pontos_por_tile": 10_000_000,
        "overlap": 3.0,
        "crs_str": "EPSG:31982",
    }
)