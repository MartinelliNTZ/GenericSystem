# 🔧 Fix: Migração ExecutionContext API — `get()`/`set()` → `get_result()`/`set_result()`

## 📋 Contexto

O `ExecutionContext` foi refatorado para usar **atributos diretos** em vez de `get()`/`set()` dict-style.  
A nova API:

```python
# ✅ NOVO (atributos diretos)
context.input_path = "/path"
context.output_path = "/output"
context.tool_key = "my_tool"
context.files = ["file.las"]

# ✅ NOVO (resultados)
context.set_result("check_results", {...})
data = context.get_result("check_results", {})

# ❌ VELHO (não existe mais)
context.get("file_path")       # AttributeError!
context.set("key", value)      # AttributeError!
context.get("check_results")   # AttributeError!
```
#
## 🔴 Problema

Vários plugins ainda usavam a API antiga `context.get()` e `context.set()`, causando:

```
AttributeError: 'ExecutionContext' object has no attribute 'get'
```

O `PipelineRunner` também foi alterado para aceitar kwargs diretos (`input_path=`, `output_path=`, `tool_key=`) em vez de `context={...}` com chaves arbitrárias.

## 📁 Arquivos Modificados

### 1. `core/papeline/step/LasCheckStep.py`
- **Adicionado** parâmetro `checks_enabled` no construtor (Contrato 28)
- `run_inline()` agora lê de `self._checks_enabled` em vez de `context.results.get("checks_enabled")`

### 2. `plugins/las_check/LasCheckPlugin.py`
- **`_on_done()`**: `context.get("check_results")` → `context.get_result("check_results")`
- **`_on_done()`**: `context.get("summary")` → `context.get_result("summary")`
- **`_on_executar()`**: `context={"file_path": ..., "checks_enabled": ...}` → kwargs diretos + `LasCheckStep(checks_enabled=...)`

### 3. `plugins/point_boundary/PointBoundaryStep.py`
- **Adicionado** `__init__` com todos os parâmetros (Contrato 28)
- **`should_run()`**: `context.get("file_path")` → `context.input_path`
- **`create_task()`**: todos os `context.get()` → parâmetros do construtor
- **`on_success()`**: `context.set()` → `context.set_result()`
- **Adicionado** `import os`

### 4. `plugins/point_boundary/PointBoundaryPlugin.py`
- **`_on_done()`**: `context.get("hull_result")` → `context.get_result("hull_result")`
- **`_on_done()`**: `context.get("hull_summary")` → `context.get_result("hull_summary")`
- **`_on_executar()`**: `context={...}` com 12 chaves → kwargs diretos + `PointBoundaryStep(...)` com parâmetros

### 5. `plugins/las_tiler/LasTilerPlugin.py`
- **`_on_done()`**: `context.get("split_result")` → `context.get_result("split_result")`
- **`_on_executar()`**: `context={"file_path": ..., "output_dir": ..., "pontos_por_parte": ...}` → kwargs diretos + `LasTilerStep(points_per_part=...)`

### 6. `plugins/idw_interpolator/IdwInterpolatorPlugin.py`
- **`_on_done()`**: `context.get("idw_result")` → `context.get_result("idw_result")`

## ✅ Plugins Verificados (sem `context.get()`)

| Plugin | Status |
|--------|--------|
| `LasCheckPlugin` | ✅ Corrigido e testado (logs confirmam execução OK) |
| `LasBlackFilterPlugin` | ✅ Já usava `context.results` (correto) |
| `LasTilerPlugin` | ✅ Corrigido |
| `PointBoundaryPlugin` | ✅ Corrigido |
| `IdwInterpolatorPlugin` | ✅ `_on_done` corrigido (ainda precisa refatorar `context={}` no `_on_executar`) |
| `DoclingPlugin` | ⚠️ Ainda usa `context.get()` — precisa de correção similar |

## 📐 Padrão de Correção (Contratos 27-31)

Para cada plugin, o padrão de correção foi:

1. **PipelineRunner**: usar kwargs diretos em vez de `context={}`
   ```python
   # ANTES (quebrado)
   runner = PipelineRunner(steps=[step], context={"file_path": path, "tool_key": key}, parent=self)
   
   # DEPOIS (correto)
   runner = PipelineRunner(steps=[step], input_path=path, tool_key=key, parent=self)
   ```

2. **Step**: parâmetros exclusivos vão no construtor (Contrato 28)
   ```python
   # ANTES (quebrado)
   step = LasCheckStep()  # checks_enabled via context.results
   
   # DEPOIS (correto)
   step = LasCheckStep(checks_enabled=checks_enabled)
   ```

3. **Callback `_on_done`**: usar `context.get_result()` em vez de `context.get()`
   ```python
   # ANTES (quebrado)
   results = context.get("check_results", {})
   
   # DEPOIS (correto)
   results = context.get_result("check_results", {})
   ```

## 🔗 Referências

- Plano de padronização: `docs/plans/PLAN_PADRONIZACAO_EXECUTION_CONTEXT.md`
- Contratos do sistema: `docs/skills/SKILL_PLUGIN_CONTRACT.md` (Contratos 27-31)
- Skill de pipeline assíncrona: `docs/skills/SKILL_ASYNC_PIPELINE.md`