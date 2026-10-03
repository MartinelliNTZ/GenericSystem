# Plano de Ação — Ferramenta de Reprojeção de Nuvem LAS/LAZ

## Visão Geral

Criar uma ferramenta para reprojetar (transformar sistema de coordenadas) nuvens de pontos LAS/LAZ, com detecção automática do CRS de origem, seleção de CRS de destino e execução em background via Pipeline.

---

## Task 1: Criar Utilitário LasLayerProjection

**Responsabilidade:** Criar classe `LasLayerProjection` em `utils/las/LasLayerProjection.py` — irmã de `LasLayerSource`, herda de `BaseUtil`.

### Step 1.1 — Método `get_crs(path) -> str`
- Lê o CRS do header do LAS via VLRs (Variable Length Records)
- Retorna string no formato `"EPSG:XXXX"` ou vazia se não encontrado
- Usa `laspy` para acessar `header.vlrs` e extrair `parsed_crs`
- Loga resultado com `get_logger`

### Step 1.2 — Método `reproject_las(input_path, output_path, target_crs, source_crs) -> dict`
- Usa `laspy` para ler o LAS + `pyproj.Transformer` para transformar coordenadas
- Transforma X, Y, Z arrays do numpy
- Salva novo LAS no `output_path`
- Retorna `{"n_points": int, "output_path": str, "error": str | None}`
- Aceita `tool_key` como parâmetro nomeado

---

## Task 2: Criar Plugin LasReprojection

**Responsabilidade:** Criar o widget da ferramenta em `plugins/las_reprojection/`.

### Step 2.1 — Definir identidade
- Adicionar `LAS_REPROJECTION = "LasReprojection"` ao enum `ToolKey`
- Registrar em `ToolRegistry` com `tool_type=ToolType.POINTS`, `category=CategoryTool.CENTRAL`

### Step 2.2 — Criar `LasReprojectionPlugin(BasePlugin)`
- UI com `GridSelector` para entrada (LAS/LAZ) e saída
- `CrsSelectorWidget` para CRS de origem (preenchido automaticamente ao carregar LAS, fica em branco se não achar)
- `CrsSelectorWidget` para CRS de destino
- `ExecutionButtons` com EXECUTAR
- `GridLabel` para exibir metadados (CRS origem, CRS destino, pontos)
- Não permite executar sem CRS de origem e destino definidos
- `_build_ui()`, `load_prefs()`, `save_prefs()`

### Step 2.3 — Pipeline de reprojeção
- Criar `LasReprojectionStep(BaseStep)` com `subfolder="lasreprojection"`, `advance_input=False`
- Criar `LasReprojectionTask(BaseTask)` que executa `LasLayerProjection.reproject_las()`
- Usar `PipelineRunner` para execução em background

---

## Task 3: Atualizar Skills

**Responsabilidade:** Manter documentação sincronizada (Contrato 12).

### Step 3.1 — `SKILL_UTILS.md`
- Adicionar seção `LasLayerProjection` com métodos `get_crs()` e `reproject_las()`
- Documentar parâmetros e retornos

### Step 3.2 — `SKILL_WIDGETS.md`
- Marcar `GridSelector` (SelectorGrid) como **OBSOLETO** — não usar em ferramentas novas
- Marcar `SimpleSelector` como **OBSOLETO** — preferir `ComplexSelector` e `GridComplexSelector`
- Adicionar nota: "Use `ComplexSelector` de `resources/widgets/complex/ComplexSelector.py` e `GridComplexSelector` de `resources/widgets/complex/GridComplexSelector.py` para novas implementações"

---

## Task 4: Registro e Integração

**Responsabilidade:** Garantir que a ferramenta apareça no sistema.

### Step 4.1 — ToolKey
- `LAS_REPROJECTION = "LasReprojection"`

### Step 4.2 — ToolRegistry
```python
ToolKey.LAS_REPROJECTION.value: Tool(
    name=ToolKey.LAS_REPROJECTION.value,
    title="Reprojeção LAS",
    widget_factory=_make_factory(
        "plugins.las_reprojection.LasReprojectionPlugin",
        "LasReprojectionPlugin",
    ),
    tooltip="Reprojeta nuvens LAS/LAZ para outro sistema de coordenadas (CRS)",
    tool_type=ToolType.POINTS,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
```

---

## 🧱 Arquivos a Criar/Modificar

| Arquivo | Ação |
|---------|------|
| `core/enum/ToolKey.py` | ✏️ Adicionar `LAS_REPROJECTION` |
| `core/config/ToolRegistry.py` | ✏️ Adicionar entrada no `_TOOLS` |
| `utils/las/LasLayerProjection.py` | ✨ Criar (util irmã de LasLayerSource) |
| `plugins/las_reprojection/__init__.py` | ✨ Criar (vazio) |
| `plugins/las_reprojection/LasReprojectionPlugin.py` | ✨ Criar (plugin widget) |
| `plugins/las_reprojection/LasReprojectionStep.py` | ✨ Criar (pipeline step) |
| `plugins/las_reprojection/LasReprojectionTask.py` | ✨ Criar (pipeline task) |
| `docs/skills/SKILL_UTILS.md` | ✏️ Atualizar seção LasLayerSource + adicionar LasLayerProjection |
| `docs/skills/SKILL_WIDGETS.md` | ✏️ Marcar GridSelector/SimpleSelector como obsoletos |

---

## ✅ Checklist Geral

- [ ] ToolKey adicionado
- [ ] LasLayerProjection.get_crs() implementado com VLR parsing
- [ ] LasLayerProjection.reproject_las() implementado com pyproj
- [ ] Plugin criado com GridSelector + CrsSelectorWidget
- [ ] LasReprojectionStep + LasReprojectionTask criados
- [ ] ToolRegistry atualizado
- [ ] SKILL_UTILS.md atualizado
- [ ] SKILL_WIDGETS.md atualizado (obsolescência anunciada)
- [ ] Nenhum contrato violado
- [ ] py_compile válido