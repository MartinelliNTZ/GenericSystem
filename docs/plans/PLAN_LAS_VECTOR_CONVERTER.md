# Plano: Ferramenta Conversor LAS ↔ Pontos Vetoriais

## 1. Visão Geral

Criar uma ferramenta bidirecional que converte **nuvens de pontos LAS/LAZ em vetores de pontos** (SHP, GPKG, GeoJSON, CSV) e **vetores de pontos em nuvens LAS/LAZ**.

A ferramenta opera em dois modos:
- **LAS → Vetor**: Lê arquivo(s) LAS/LAZ, extrai coordenadas X/Y/Z e atributos (RGB, intensidade, classificação), salva como camada vetorial de pontos.
- **Vetor → LAS**: Lê arquivo vetorial de pontos (SHP, GPKG, CSV, GeoJSON), extrai coordenadas e atributos, salva como LAS/LAZ.

Utiliza o sistema de **Task + Step** (`AsyncPipeline`) para execução em background sem travar a UI.

---

## 2. Arquivos a Criar/Modificar

### 2.1. Enum — `core/enum/ToolKey.py`
Adicionar:
```python
LAS_VECTOR_CONVERTER = "LasVectorConverter"
```

### 2.2. Step — `core/papeline/step/LasVectorConverterSteps.py`
Step único que detecta o sentido da conversão baseado na extensão de entrada:
- Se entrada for `.las`/`.laz` → converte para vetor
- Se entrada for `.shp`/`.gpkg`/`.csv`/`.geojson`/`.kml` → converte para LAS

**Atributos:**
| Atributo | Valor | Descrição |
|----------|-------|-----------|
| `subfolder` | `"lasvectorconverter"` | Pasta de saída |
| `_advance_input` | `True` | Step transforma dados |

**Parâmetros do construtor:**
| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `output_format` | `str` | `"gpkg"` | Formato vetorial de saída (gpkg, shp, geojson, csv) |
| `crs_str` | `str` | `"EPSG:31982"` | CRS para o LAS de saída |
| `advance_input` | `bool` | `True` | Se avança input_path |
| `input_path` | `str` | `""` | Path customizado (opcional) |

**Context produz:**
- `results["conversion_result"]`: Dict com resultados da conversão
- `results["n_input"]`: Nº de pontos/features de entrada
- `results["n_output"]`: Nº de pontos/features de saída
- `results["output_files"]`: Lista de arquivos gerados
- `results["direction"]`: `"las_to_vector"` ou `"vector_to_las"`

### 2.3. Task — `core/papeline/task/LasVectorConverterTask.py`
Task que executa a conversão pesada em background.
#nao esqueca de deixar generico e atualizar o input ao final para pode ser reaproveitado
**Parâmetros:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
input_path orbigatorio, padrao de task/step
faça no padrao 
 - deixe tudo pronto e padronizado para poder funcionan tanto com arquivo especidifco como no modo pasta, 
 leia o plugin @/plugins\las_black_filter\LasBlackFilterPlugin.py 
| `files` | `list[str]` | Arquivos de entrada |
| `output_dir` | `str` | Diretório de saída |
| `output_format` | `str` | Formato vetorial (gpkg, shp, geojson, csv) |
| `crs_str` | `str` | CRS para LAS de saída |

**Lógica interna:**
- Detecta direção pela extensão do primeiro arquivo
- **LAS → Vetor**: Usa `LasUtil.get_info()` + `laspy` para ler pontos, `geopandas`/`fiona` para salvar vetor
se tiver novas libs adicionar em requirements.txt
- **Vetor → LAS**: Usa `VectorLayerSource.extract_point_coordinates()` + `laspy` para criar LAS

**Resultado (`self.result`):**
```python
{
    "n_input": 1234,
    "n_output": 1234,
    "output_files": ["/path/to/output/file.gpkg"],
    "direction": "las_to_vector",
}
```

### 2.4. Plugin — `plugins/las_vector_converter/LasVectorConverterPlugin.py`
Widget principal da ferramenta, herda de `BasePlugin`.

**UI Structure (Contrato 18 — Título → ExecutionButtons → conteúdo):**
```
┌─ PluginPage ──────────────────────────────────┐
│ [Badge: PRONTA]                                │
│ ┌─ ExecutionButtons ─────────────────────────┐ │
│ │ [USAR ORIGEM]              [EXECUTAR]      │ │
│ └────────────────────────────────────────────┘ │
│ ┌─ GroupPainel "Entrada" ────────────────────┐ │
│ │ SimpleSelector (Arquivo/Pasta)             │ │
│ │   mode_selector: {"file", "folder"}        │ │
│ │ GridLabel (info do arquivo)   
    SimpleSelector (pasta/arquivo) (pode ser uma pasta caso no modo pasta)             │ │
│ └────────────────────────────────────────────┘ │
│ ┌─ GroupPainel "Configurações" ──────────────┐ │
│ │ GridRadio:                                  │ │
│ │   "las_to_vector": "LAS/LAZ → Vetor"       │ │
│ │   "vector_to_las": "Vetor → LAS/LAZ"       │ │
│ │ SimpleComboBox: "Formato Saída"            │ │
│ │   (gpkg, shp, geojson, csv) — só p/ LAS→V │ │
│ │ GridDoubleSpinBox: "CRS" (EPSG)            │ │
│ └────────────────────────────────────────────┘ │

desnecessario painel de saida, coloque ele junto com o painel de entrada

```

**Widgets utilizados (todos de `resources/widgets/`):**
- `SimpleSelector` — seleção de entrada/saída com mode_selector
- `GridLabel` — info do arquivo carregado
- `GridRadio` — direção da conversão
- `SimpleComboBox` — formato de saída
- `GridDoubleSpinBox` — CRS
- `ExecutionButtons` — USAR ORIGEM + EXECUTAR
- `GroupPainel` — containers
- `PluginPage` — container base (via BasePlugin)

**Fluxo de execução:**
1. Usuário seleciona arquivo/pasta de entrada
2. Plugin detecta extensão e pré-seleciona direção
3. Usuário configura parâmetros
4. Clica EXECUTAR
5. Cria `PipelineRunner` com `LasVectorConverterStep`
6. Pipeline executa em background
7. Callback `_on_done` exibe resultados via `MessageBox`

**Preferências (`load_prefs` / `save_prefs`):**
- `mode`: "file" | "folder"
- `file_path`: path do arquivo
- `folder_path`: path da pasta
- `direction`: "las_to_vector" | "vector_to_las"
- `output_format`: "gpkg" | "shp" | "geojson" | "csv"
- `crs`: código EPSG
- `output_path`: path de saída
use as classes 
@/utils/ProcessStatisticsUtil.py @/plugins\BasePlugin.py 
leia a skill  da loader para passar o  tempo correto para a loader o paramtro e numero de pontos, caso no modo pasta passa a quantidade total de ponto e cada arquivo é 1 step 
### 2.5. Registro — `core/config/ToolRegistry.py`
Adicionar entrada no `_TOOLS`:
```python
ToolKey.LAS_VECTOR_CONVERTER.value: Tool(
    name=ToolKey.LAS_VECTOR_CONVERTER.value,
    title="Conversor LAS ↔ Pontos",
    widget_factory=_make_factory(
        "plugins.las_vector_converter.LasVectorConverterPlugin",
        "LasVectorConverterPlugin",
    ),
    tooltip="Converte nuvens LAS/LAZ para vetores de pontos (SHP, GPKG, CSV) e vice-versa",
    tool_type=ToolType.VECTOR,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
```

### 2.6. Step/Task `__init__.py` — Atualizar exports
- `core/papeline/step/__init__.py`: adicionar `LasVectorConverterStep`
- `core/papeline/task/__init__.py`: adicionar `LasVectorConverterTask`

---

## 3. Dependências

Nenhuma nova dependência externa. O sistema já possui:
- `laspy` — leitura/escrita LAS/LAZ
- `geopandas` — leitura/escrita vetores
- `numpy` — manipulação de arrays
- `VectorLayerSource` — extração de coordenadas de vetores
- `LasUtil` — metadados de LAS

---

## 4. Contratos Respeitados

| Contrato | Como |
|----------|------|
| C1 — MessageBox | Usa `MessageBox` de `utils.MessageBox` |
| C2 — Exceções | Todo `except` tem `as e` + logger |
| C3 — Logger | Usa `self.logger` (via BasePlugin) |
| C4 — Preferências | Usa `self.preferences` (via BasePlugin) |
| C5 — ToolRegistry | Registro via `_TOOLS` dict |
| C6 — BasePlugin | Herda de `BasePlugin`, implementa `load_prefs()` e `save_prefs()` |
| C7 — SignalManager | Comunicação via `SignalManager` (progress, console, HUD) |
| C9 — Código Morto | Sem imports mortos |
| C10 — Categorias | `CategoryTool.CENTRAL` |
| C11 — Widgets | Todos os widgets de `resources/widgets/` |
| C13 — ToolRegistry | Configuração centralizada |
| C18 — UI Padrão | Título → ExecutionButtons → conteúdo |
| C20 — Progress/HUD | Usa `SignalManager` para progresso e HUD |
| C25 — I/O Vetorial | Usa `VectorLayerSource` para ler vetores |
| C26 — ToolKey | Usa `ToolKey.LAS_VECTOR_CONVERTER.value` |

---

## 5. Estrutura de Diretórios

```
plugins/las_vector_converter/
├── __init__.py
└── LasVectorConverterPlugin.py

core/papeline/step/LasVectorConverterSteps.py
core/papeline/task/LasVectorConverterTask.py
```

---

## 6. Observações e Ressalvas

### 6.1. Sentido da Conversão
- O step detecta automaticamente o sentido pela extensão do primeiro arquivo.
  vamos fazer 2 steps e 2tasks para cada sentido vector--las e las--vector isso sera melhora para reaproveitar futuramente
- Se misturar LAS e vetor na mesma pasta (modo folder), o comportamento é indefinido — o step usa a extensão do primeiro arquivo como referência.
- **Sugestão**: validar no plugin que todos os arquivos na pasta têm a mesma extensão antes de executar.

### 6.2. Atributos na Conversão
- **LAS → Vetor**: Exporta X, Y, Z, intensidade, classificação, return number, RGB (se disponível) como campos do vetor.
- **Vetor → LAS**: Usa X, Y, Z dos campos ou geometria. Se o vetor tiver campos RGB (R, G, B), Intensity, Classification, estes são preservados no LAS.
- **CSV**: Requer colunas X, Y (configuráveis). Z é opcional (default 0).

### 6.3. CRS
- **LAS → Vetor**: O CRS é lido do header LAS (VLR) se disponível. Se não, usa o CRS configurado no plugin.
- **Vetor → LAS**: O CRS é lido do arquivo vetorial (se disponível) ou usa o configurado. O CRS é escrito como VLR no LAS.

### 6.4. Performance
- Para arquivos LAS muito grandes (>50M pontos), a conversão pode consumir muita RAM.
- opção de usar o lastiler para quebrar o las em pedação de x pontos
- O `ResourceGovernor` (integrado no `PipelineRunner`) gerencia automaticamente o uso de memória.
- Para modo folder, o processamento é sequencial (1 arquivo por vez).

### 6.5. Formato CSV
- CSV de saída (LAS → CSV) usa `,` como delimitador e `utf-8-sig` encoding.
- CSV de entrada (CSV → LAS) espera `,` como delimitador. Colunas X/Y configuráveis via `GridFieldMapping` (futuro).

### 6.6. Limitações
- Não suporta LAS 1.4 com formatos de ponto > 6 (waveform, etc.) — apenas pontos com RGB e intensidade.
- Não suporta MultiPoint em vetores de entrada — apenas Point.
- Arquivos LAS sem coordenadas válidas (todos os pontos em 0,0,0) geram vetor vazio.

---

## 7. Checklist de Implementação

- [ ] `ToolKey.LAS_VECTOR_CONVERTER` adicionado
- [ ] `LasVectorConverterTask` criado em `core/papeline/task/`
- [ ] `LasVectorConverterStep` criado em `core/papeline/step/`
- [ ] Step registrado em `core/papeline/step/__init__.py`
- [ ] Task registrada em `core/papeline/task/__init__.py`
- [ ] Plugin `LasVectorConverterPlugin` criado em `plugins/las_vector_converter/`
- [ ] Plugin registrado em `core/config/ToolRegistry.py`
- [ ] `load_prefs()` e `save_prefs()` implementados
- [ ] PipelineRunner com HUD + ProgressBar + Console
- [ ] Tratamento de erros com logger + MessageBox
- [ ] Documentação atualizada (esta skill)