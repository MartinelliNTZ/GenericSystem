# Ferramentas Extraídas do Sistema EST3

> **Fonte:** `docs/implementacoes/EST3.PY`
> **Propósito original:** Script completo para ler LAS, gerar estatísticas JSON e mosaico RGB GeoTIFF com pipeline em 5 estágios.
> **Plugins existentes:** 3 (LasCheckPlugin, LasBlackFilterPlugin, PointBoundaryPlugin)
> **Potenciais novos plugins:** 9

---

## ✅ JÁ IMPLEMENTADOS (3)

### 1. LasCheckPlugin — Verificação de Qualidade LAS
**Arquivo:** `plugins/las_check/LasCheckPlugin.py`
**Step:** `core/papeline/step/LasCheckStep.py`
**Task:** `core/papeline/task/LasCheckTask.py`

Executa 8 checks de qualidade em arquivos LAS/LAZ:

| Check | Descrição | Status |
|-------|-----------|--------|
| `point_count` | Contagem total de pontos (>0, alerta se <1000) | pass/warning/fail |
| `bbox` | Valida bounding box (dimensões X, Y, Z) | pass/fail |
| `rgb` | Presença de bandas RGB | pass/warning |
| `classification` | Códigos de classificação LAS (0–255) | pass/warning/fail |
| `zero_coords` | Pontos com X=Y=Z=0 | pass/warning/fail |
| `duplicates` | Duplicatas XY (amostragem de 50k pontos) | pass/warning/fail |
| `density` | Densidade planar (pts/m²) | pass/warning |
| `intensity` | Range de intensidade (0–65535) | pass/warning/fail |

**UI:** SelectorGrid (entrada), GridCheckBox (seleção de checks), ExecutionButtons, GridLabel (resultados).
**Pipeline:** PipelineRunner + LasCheckStep (inline na QThread).
**Extraído de:** Funções `_check_*` e leitura `laspy.read()` no EST3 estagio inicial.

---

### 2. LasBlackFilterPlugin — Filtro de Pontos Pretos LAS
**Arquivo:** `plugins/las_black_filter/LasBlackFilterPlugin.py`
**Step:** `core/papeline/step/LasBlackFilterStep.py`
**Task:** `core/papeline/task/LasBlackFilterTask.py`

Remove pontos onde R, G e B estão todos abaixo de um limiar configurável (0–255).

**Funcionalidades:**
- Parâmetro `limiar` (0 = preto puro, >0 para remover pontos muito escuros)
- Opção de salvar pontos pretos removidos em arquivo separado (`_pretos.las`)
- Gera LAS filtrado com sufixo `_filtrado.las/.laz`
- Pipeline com 4 stages: Leitura → Filtragem → Salvar Filtrado → Salvar Pretos
- Progresso e HUD integrados

**Extraído de:** Função `_filtrar_pontos_pretos()` no EST3 (v5).

---

### 3. PointBoundaryPlugin — Geração de Limite de Pontos
**Arquivo:** `plugins/point_boundary/PointBoundaryPlugin.py`
**Step:** `plugins/point_boundary/PointBoundaryStep.py`
**Task:** `plugins/point_boundary/PointBoundaryTask.py`

Gera o limite (boundary) de nuvens de pontos a partir de múltiplas fontes com validação iterativa via concave hull e detecção automática de "escada".

**Fontes suportadas:** LAS/LAZ, SHP, GPKG, KML, CSV, GeoJSON

**Funcionalidades:**
- Amostragem configurável (default 100k pontos)
- Gera concave hull com ratio decrescente (default 0.10 passo 0.01)
- Detecta "escada" quando queda de área > limiar configurável (default 12%)
- Suaviza o polígono com buffer duplo configurável (default 20m)
- Salva GPKGs de cada iteração para validação visual
- Exporta JSON com resultados de cada iteração
- CRS hierárquico: fonte → configurado → EPSG:4326
- HUD + ProgressBar + Statistics integrados

**Parâmetros (GridDoubleSpinBox):**
| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `ratio_inicial` | 0.10 | Ratio inicial do concave hull |
| `ratio_step` | 0.01 | Decremento do ratio por iteração |
| `limiar_escada` | 12.0% | Queda de área que dispara detecção de escada |
| `suavisacao` | 20 m | Buffer de suavização pós-hull |
| `n_amostras` | 100.000 | Pontos usados para o hull |

**Métodos utilitários adicionados:**
- `LasUtil.extract_points()` — extração de coordenadas de LAS/LAZ
- `VectorLayerSource.extract_point_coordinates()` — extração de coordenadas de vetores + CSV
- `VectorLayerGeometry.generate_concave_boundary()` — geração do concave hull
- `VectorLayerGeometry.smooth_polygon()` — suavização via buffer duplo
- `VectorLayerGeometry.detect_escada()` — detecção de escada em sequência de áreas

**Extraído de:** Bloco `# ── VALIDACAO CONCAVE HULL` (linhas ~260–350) no EST3.

---

## 📋 POTENCIAIS NOVAS FERRAMENTAS (9)

### 4. LasStatisticsPlugin — Estatísticas Completas do LAS
**Função alvo:** Geração do JSON de estatísticas (`estatisticas_las.json`).

**Descrição:**
- Extrai bounding box (X, Y, Z min/max)
- Altimetria (Z min/max)
- Estatísticas RGB (min/max de cada banda)
- Conversão automática 16-bit → 8-bit
- Densidade de pontos (bbox e polígono suavizado)
- Cálculo do **pixel ideal** baseado na densidade real:
  > `espacamento = 1 / sqrt(densidade_real)`
  > `pixel_ideal = max(espacamento * 0.75, 0.01)`
- Exporta JSON formatado

**Código fonte EST3:** Bloco `# ── DENSIDADE E PIXEL IDEAL` e `# ── JSON`.

---

### 5. IdwInterpolatorPlugin — Interpolação IDW para Grid (✅ IMPLEMENTADO)
**Arquivo:** `plugins/idw_interpolator/IdwInterpolatorPlugin.py`
**Step:** `plugins/idw_interpolator/IdwInterpolatorStep.py`
**Task:** `plugins/idw_interpolator/IdwInterpolatorTask.py`
**Utils:** `utils/raster/InterpolatorUtils.py`

Interpola nuvem LAS/LAZ em grid regular via IDW (Inverse Distance Weighting).

**Funcionalidades:**
- **GridCheckBox** para selecionar bandas alvo: R, G, B, Altura (Z) — checkboxes individuais
- **GridCheckBox** "Separar Bandas?" (default false) — bandas individuais ou mosaico RGB/RGBZ
- **Botão "Calcular Pixel Ideal"** — calcula `1/sqrt(densidade)` e carrega no GridDoubleSpinBox
- **GridDoubleSpinBox** com parâmetros: resolução (cm), fator conversão, k, power, raio_max, overlap, pontos_por_tile
- **ExecutionButtons** padronizado: PIXEL IDEAL, EXECUTAR, CANCELAR
- PipelineRunner + IdwInterpolatorStep + IdwInterpolatorTask em background
- Processamento paralelo via `joblib.Parallel` com tiles
- Retomada automática (pula tiles já processados)
- Tiles salvos em pasta temporária (`ExplorerUtils.get_plugin_config_dir`)
- Mescla de bandas em paralelo (bandas independentes)
- Montagem final via `RasterLayerProcessing.compose_multiband_raster()`
- Metadados JSON com parâmetros, grid, tiles e arquivos gerados
- Progresso via HUD + ProgressBar + Console
- `load_prefs()` / `save_prefs()` completos

**Métodos adicionados ao LasUtil:**
- `extract_point_arrays()` — extrai arrays (x, y, z, r, g, b) conforme bandas
- `calcular_pixel_ideal()` — cálculo do pixel ideal por densidade

**Utils criados:**
- `InterpolatorUtils.idw_tile_para_disco()` — implementação principal IDW
- `InterpolatorUtils.calcular_tiles_por_densidade()` — gradeamento por pontos/tile
- `InterpolatorUtils.mesclar_banda()` — merge de tiles via memmap
- `InterpolatorUtils.salvar_tile_tif()` — escrita GeoTIFF com BIGTIFF=YES

**Contratos seguidos:**
- Contrato 11: widgets reutilizáveis (GridCheckBox, GridDoubleSpinBox, etc.)
- Contrato 18: ExecutionButtons padronizado
- Contrato 20: SignalManager para progresso/console
- Contrato 25: LasUtil para leitura LAS, não importa laspy/rasterio diretamente

**Plano:** `docs/plans/PLAN_IDW_INTERPOLATOR.md`

---

### 6. TiledRasterGeneratorPlugin — Geração de Mosaico Tileado
**Função alvo:** Divisão da área em tiles com ~PONTOS_POR_CHUNK pontos cada.

**Descrição:**
- Divide a área em grade N×M baseada na densidade de pontos
- Cada tile ~10M pontos para balancear memória vs performance
- Tile salvo individualmente em pastas separadas (R, G, B)
- Suporte a overlap (3m) para evitar artefatos de borda
- Retomada automática: se os 3 tiles (R,G,B) existem, pula

**Parâmetros:**
| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `PONTOS_POR_CHUNK` | 10.000.000 | Pontos alvo por tile |
| `CHUNK_OVERLAP_M` | 3.0 m | Overlap entre tiles vizinhos |

**Código fonte EST3:** Função `_calcular_tiles_por_densidade()` e ESTAGIO 1.

---

### 7. TileMosaicMergePlugin — Mesclagem de Tiles em Bandas
**Função alvo:** Merge de tiles individuais em bandas completas (R, G, B).

**Descrição:**
- Lê todos os tiles de uma pasta (R/, G/, B/)
- Calcula posição de cada tile no grid global via `rowcol()`
- Usa `np.memmap` em disco para evitar RAM insuficiente
- Escrita chunked (2048 linhas por vez) com compressão LZW
- BIGTIFF=YES para arquivos >4GB
- Gera `banda_R.tif`, `banda_G.tif`, `banda_B.tif`

**Código fonte EST3:** Função `_mesclar_banda()` e ESTAGIO 2.

---

### 8. RgbMosaicAssemblerPlugin — Montagem de Mosaico RGB
**Função alvo:** Combinação de bandas R, G, B em mosaico RGB 3-bandas.

**Descrição:**
- Lê as 3 bandas isoladas (`banda_R/G/B.tif`)
- Escreve em único GeoTIFF de 3 bandas
- Compressão LZW, tiled (512×512)
- Mantém photometric=RGB
- Chunked processing (2048 linhas)

**Saída:** `mosaico_rgb.tif`

**Código fonte EST3:** ESTAGIO 3.

---

### 9. RasterPolygonClipperPlugin — Recorte de Raster por Polígono
**Função alvo:** Recorte preciso de raster utilizando polígono GPKG.

**Descrição:**
- Usa `rasterio.mask.mask()` com polígono de recorte
- nodata = 255 (max uint8) para distinguir de preto real (0)
- Mantém photometric=RGB
- Crop automático para bounds do polígono
- BIGTIFF=YES, compressão LZW

**Saída:** `mosaico_rgb_recortado.tif`

**Código fonte EST3:** ESTAGIO 4.

---

### 10. AlphaBandGeneratorPlugin — Geração de Banda Alpha
**Função alvo:** Criação de máscara de transparência a partir do polígono.

**Descrição:**
- **Correção v3:** Alpha calculada pela máscara do polígono, NÃO pelo valor RGB
- Usa `geometry_mask()` do rasterio
- 255 = dentro do polígono (opaco), 0 = fora (transparente)
- Gera RGBA final (4 bandas)
- Compressão LZW, tiled, BIGTIFF=YES

**Saída:** `mosaico_rgba_final.tif`

**Código fonte EST3:** ESTAGIO 5.

---

### 11. OverviewGeneratorPlugin — Geração de Pirâmides (Overviews)
**Função alvo:** Criação de overviews para visualização eficiente.

**Descrição:**
- Usa GDAL `BuildOverviews()` com método "AVERAGE"
- Níveis configuráveis: [2, 4, 8, 16, 32, 64]
- Compressão DEFLATE para overviews
- Fallback para `gdaladdo` via CLI se GDAL não disponível

**Código fonte EST3:** Bloco `# ── OVERVIEWS` no final da geração do mosaico.

---

### 12. LasCleanExporterPlugin — Exportação de LAS Limpo
**Função alvo:** Salvar LAS filtrado (sem pontos pretos) preservando estrutura.

**Descrição:**
- Após aplicar filtro de pontos pretos, salva LAS completo sem os pontos removidos
- Preserva todas as dimensões e campos do LAS original (classificação, intensidade, etc.)
- Nome automático: `{original}_limpo.las`
- Registra no JSON quantos pontos foram removidos

**Código fonte EST3:** Bloco `# [V5] Salva LAS limpo se houve remocao`.

---

## 🔗 RELAÇÃO ENTRE FERRAMENTAS

```
LAS Original
    │
    ├──► [1] LasCheckPlugin          → Diagnóstico da nuvem
    ├──► [4] LasStatisticsPlugin      → Estatísticas + pixel ideal
    │
    ├──► [2] LasBlackFilterPlugin     → Remove pontos pretos
    │       └──► [12] LasCleanExporterPlugin → Salva LAS limpo
    │
    ├──► [3] PointBoundaryPlugin      → Polígono de recorte (GPKG)
    │
    └──► [5] IdwInterpolatorPlugin    → Grid RGB interpolado
            │
            ├──► [6] TiledRasterGeneratorPlugin → Tiles individuais
            │       └──► [7] TileMosaicMergePlugin → Bandas completas
            │               └──► [8] RgbMosaicAssemblerPlugin → mosaico_rgb.tif
            │                       └──► [9] RasterPolygonClipperPlugin → recortado
            │                               └──► [10] AlphaBandGeneratorPlugin → RGBA final
            │                                       └──► [11] OverviewGeneratorPlugin → pirâmides
            │
            └──► JSON de estatísticas (integrado)
```

## 📐 ARQUITETURA DE PLUGIN — PADRÃO

Cada ferramenta deve seguir o padrão já estabelecido:

| Componente | Exemplo | Obrigatório |
|------------|---------|-------------|
| `plugins/{nome}/` | `plugins/las_check/` | Sim |
| `Plugin` | `LasCheckPlugin` (herda `BasePlugin`) | Sim |
| `Step` | `LasCheckStep` (herda `BaseStep`) | Sim |
| `Task` (opcional) | `LasCheckTask` (herda `BaseTask`) | Se processamento pesado |
| `__init__.py` | Vazio | Sim |

**Ciclo de vida do plugin:**
1. `_build_ui()` → Constrói widgets (SelectorGrid, ExecutionButtons, GridLabel, etc.)
2. `load_prefs()` → Restaura última config do usuário
3. Usuário seleciona arquivo → `_carregar_las()`
4. Usuário clica EXECUTAR → `PipelineRunner` + `Step` em background
5. `_on_done()` / `_on_error()` → Atualiza UI
6. `save_prefs()` → Salva config ao fechar

## 🔧 CORREÇÕES EXTRAÍDAS DO EST3 APLICÁVEIS AOS PLUGINS

| ID | Correção | Descrição | Plugin Afetado |
|----|----------|-----------|----------------|
| V1 | Posição de tiles | Usar `rowcol(transform, left, top)` em vez de `src.window(*src.bounds)` | TileMosaicMergePlugin |
| V2 | nodata=255 | Usar nodata=255 (max uint8) em vez de 0 para não confundir com preto real | RasterPolygonClipperPlugin |
| V3 | Alpha por polígono | Calcular alpha pela máscara do polígono, não pelo valor RGB | AlphaBandGeneratorPlugin |
| V4 | Pastas separadas | Tiles R/, G/, B/ separados em vez de sufixo no nome | TiledRasterGeneratorPlugin |
| V5 | BIGTIFF=YES | Todas as escritas GTiff com BIGTIFF="YES" para >4GB | Todos que geram GeoTIFF |
| V5 | Filtro preto | Remover pontos R=G=B=0 antes da interpolação | LasBlackFilterPlugin |

---

> **Documentação gerada em:** 23/06/2026
> **Baseada no código:** EST3.PY v5 — arquitetura por estágios com retomada automática