# 📋 Plano de Ação — CPUGovernor (Governador de CPU)

## 🎯 Objetivo

Implementar um sistema de governança de CPU que limite o número máximo de workers/threads que o software pode usar simultaneamente, evitando saturação total da CPU e garantindo headroom para outros processos do sistema.

**Cenário atual:** Com 32 CPUs físicas, `joblib.Parallel(n_jobs=-1)` e `os.cpu_count()` espalhados pelo código fazem o software consumir **100% da CPU**, causando contenção extrema.

**Solução:** `CpuGovernor` com constante editável `CPU_USAGE_LIMIT = 0.50` → max 16 workers (50% de 32).

---

## 🔍 Diagnóstico — Onde a CPU não é governada

| # | Arquivo | Linha | Código atual | Problema |
|---|---|---|---|---|
| 1 | `plugins/idw_interpolator/IdwInterpolatorTask.py` | 125 | `n_cpus = os.cpu_count() or 4` | Usa 100% das CPUs |
| 2 | `plugins/idw_interpolator/IdwInterpolatorTask.py` | 199 | `n_cpus = _os.cpu_count() or 4` | Usa 100% das CPUs |
| 3 | `plugins/idw_interpolator/IdwInterpolatorTask.py` | 260 | `Parallel(n_jobs=-1, ...)` | `-1` = joblib usa **TODAS** CPUs |
| 4 | `plugins/idw_interpolator/IdwInterpolatorTask.py` | 302 | `Parallel(n_jobs=-1, ...)` | `-1` = joblib usa **TODAS** CPUs |
| 5 | `plugins/tensorflow_classifier/tensor_utils/hardware_manager.py` | 47 | `cpu_count = os.cpu_count() or 4` | Usa 100% das CPUs para TF |
| 6 | `core/papeline/ParallelStep.py` | 52 | `max_workers = max_workers or len(steps)` | Sem limite de CPU |
| 7 | Em todo o código | — | `min(n_cpus, 8)` | Cap manual hardcoded (inconsistente) |

### Impacto

| Métrica | Sem CpuGovernor | Com CpuGovernor (50%) |
|---|---|---|
| Workers IDW | 32 | **16** |
| Workers Merge | 32 | **16** |
| Threads TF | 32 | **16** |
| ThreadPoolExecutor | ilimitado | **16** (teto) |
| CPU System Idle | ~0% | **~50%** |

---

## 🧱 Arquitetura Proposta

```
core/governor/
├── __init__.py                 — Adicionar export do CpuGovernor (sem import direto para evitar circular)
├── RamGovernor.py              ← (existente, sem alteração)
├── RamLimitPolicy.py           ← (existente, sem alteração)
├── ResourceGovernor.py         ← (existente, sem alteração)
└── CpuGovernor.py              ← ✨ NOVO
```

### Responsabilidades

| Classe | Responsabilidade |
|--------|-----------------|
| `CpuGovernor` | Centraliza o limite de CPU, expõe `max_workers()` e `n_jobs()`, tem constante editável `CPU_USAGE_LIMIT` |

---

## 📦 Componente Detalhado

### `CpuGovernor` — `core/governor/CpuGovernor.py`

```python
class CpuGovernor:
    """
    Governa o uso máximo de CPUs pelo software.

    Constante editável: CPU_USAGE_LIMIT define a fração dos CPUs totais
    que o software pode usar simultaneamente.

    Uso:
        from core.governor.CpuGovernor import CpuGovernor

        workers = CpuGovernor.max_workers()  # int(32 * 0.50) = 16
        n = CpuGovernor.n_jobs()             # mesmo valor, para joblib
    """

    CPU_USAGE_LIMIT: float = 0.50  # <<< EDITÁVEL: 0.0 a 1.0

    @classmethod
    def max_workers(cls) -> int:
        """Retorna o número máximo de workers permitido."""
        import os
        total = os.cpu_count() or 4
        return max(1, int(total * cls.CPU_USAGE_LIMIT))

    @classmethod
    def n_jobs(cls) -> int:
        """Retorna n_jobs para joblib.Parallel (evitar -1)."""
        return cls.max_workers()
```

### API Pública

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `CpuGovernor.max_workers()` | `int` | Workers máximos para ThreadPool/ProcessPool |
| `CpuGovernor.n_jobs()` | `int` | Workers para `joblib.Parallel(n_jobs=...)` |
| `CpuGovernor.CPU_USAGE_LIMIT` | `float` | Constante editável (ex: `0.50` = 50%) |

### Comportamento


---

## 🔧 Arquivos a Modificar — Detalhamento

### 1. ✨ CRIAR — `core/governor/CpuGovernor.py`

**Ação:** Criar o arquivo com a classe `CpuGovernor` conforme especificado acima.

---

### 2. ✏️ MODIFICAR — `core/governor/__init__.py`

**Ação:** Adicionar no docstring a referência para importe direto:
```python
#     from core.governor.CpuGovernor import CpuGovernor
```
(Não importar classes internamente no `__init__.py` para evitar circular imports.)

---

### 3. ✏️ MODIFICAR — `plugins/idw_interpolator/IdwInterpolatorTask.py`

#### 3a. Substituir `os.cpu_count()` em `_ajustar_tile_size()` (linhas 124-125)

**Antes:**
```python
        import os
        n_cpus = os.cpu_count() or 4
```

**Depois:**
```python
        from core.governor.CpuGovernor import CpuGovernor
        n_cpus = CpuGovernor.max_workers()
```

#### 3b. Substituir `_os.cpu_count()` em `_run()` (linha 199)

**Antes:**
```python
        n_cpus = _os.cpu_count() or 4
```

**Depois:**
```python
        from core.governor.CpuGovernor import CpuGovernor
        n_cpus = CpuGovernor.max_workers()
```

#### 3c. Substituir `Parallel(n_jobs=-1, ...)` no Estágio 4 (linha 260)

**Antes:**
```python
        results = Parallel(n_jobs=-1, verbose=0)(
```

**Depois:**
```python
        results = Parallel(n_jobs=CpuGovernor.n_jobs(), verbose=0)(
```

#### 3d. Substituir `Parallel(n_jobs=-1, ...)` no Estágio 5 (linha 302)

**Antes:**
```python
        Parallel(n_jobs=-1, verbose=0)(
```

**Depois:**
```python
        Parallel(n_jobs=CpuGovernor.n_jobs(), verbose=0)(
```

#### 3e. Adicionar import no topo do arquivo

```python
from core.governor.CpuGovernor import CpuGovernor
```

**Nota:** Import único no topo; remover o `import os` local na linha 124.

---

### 4. ✏️ MODIFICAR — `plugins/tensorflow_classifier/tensor_utils/hardware_manager.py`

**Antes (linha 47):**
```python
    cpu_count = os.cpu_count() or 4
```

**Depois:**
```python
    from core.governor.CpuGovernor import CpuGovernor
    cpu_count = CpuGovernor.max_workers()
```

---

### 5. ✏️ MODIFICAR — `core/papeline/ParallelStep.py`

**Em `ParallelTask.__init__()` (linha 52):**

**Antes:**
```python
        self._max_workers = max_workers or len(steps)
```

**Depois:**
```python
        from core.governor.CpuGovernor import CpuGovernor
        self._max_workers = min(
            max_workers or len(steps),
            CpuGovernor.max_workers(),
        )
```

---

### 6. ✏️ MODIFICAR — `core/papeline/PipelineRunner.py`

**Em `run()` (após criar o contexto, ~linha 87):**

Adicionar referência do CpuGovernor no contexto para steps/tasks que queiram consultar:

```python
        from core.governor.CpuGovernor import CpuGovernor
        ctx.set("_cpu_governor", CpuGovernor)
```

---

## 📊 Mapeamento Completo das Alterações

| Arquivo | Tipo | O quê muda |
|---|---|---|
| `core/governor/CpuGovernor.py` | ✨ NOVO | Classe `CpuGovernor` com `CPU_USAGE_LIMIT = 0.50` |
| `core/governor/__init__.py` | 📝 Documentação | Adicionar referência no docstring |
| `plugins/idw_interpolator/IdwInterpolatorTask.py` | 🔧 4 alterações | `os.cpu_count()` → `CpuGovernor.max_workers()`, 2× `n_jobs=-1` → `n_jobs=CpuGovernor.n_jobs()` |
| `plugins/tensorflow_classifier/tensor_utils/hardware_manager.py` | 🔧 1 alteração | `os.cpu_count()` → `CpuGovernor.max_workers()` |
| `core/papeline/ParallelStep.py` | 🔧 1 alteração | `max_workers` capped por `CpuGovernor.max_workers()` |
| `core/papeline/PipelineRunner.py` | 🔧 1 alteração | Injetar `CpuGovernor` no contexto |

---

## ✅ Checklist de Verificação de Contratos

| Contrato | Verificação |
|---|---|
| **C1** (Arquitetura) | `CpuGovernor` em `core/governor/` — pacote já existe para governança. ✅ |
| **C2** (Logger) | `CpuGovernor` não faz logging próprio (é utilitário puro). Quem chama loga. ✅ |
| **C3** (print) | Sem `print()`. ✅ |
| **C4** (Preferences) | `CpuGovernor` não usa Preferences. ✅ |
| **C5** (BasePlugin) | `CpuGovernor` não é plugin. ✅ |
| **C6** (closeEvent) | `CpuGovernor` não é plugin. ✅ |
| **C7** (Sinais) | `CpuGovernor` não acopla plugins. ✅ |
| **C8** (Dependências) | Sem novas dependências — usa apenas `os` (stdlib). ✅ |
| **C9** (Código morto) | Todas as classes têm uso definido. ✅ |
| **C10** (Categorias) | `CpuGovernor` não é tool. ✅ |
| **C11** (Widgets) | `CpuGovernor` não tem UI. ✅ |
| **C12** (Doc reflexiva) | Este plano documenta. ✅ |
| **C13** (ToolRegistry) | `CpuGovernor` não modifica tools. ✅ |
| **C14** (MenuManager) | `CpuGovernor` não mexe em menu. ✅ |
| **C15** (MenuCategory) | `CpuGovernor` não é tool. ✅ |
| **C16** (WorkspaceManager) | `CpuGovernor` não mexe em workspace. ✅ |
| **C17** (ExplorerUtils) | `CpuGovernor` não usa QFileDialog. ✅ |
| **C18** (ExecutionButtons) | `CpuGovernor` não tem UI. ✅ |
| **C19** (Estilos) | `CpuGovernor` não tem UI. ✅ |
| **C20** (Progress/HUD) | `CpuGovernor` não interage com HUD. ✅ |
| **C21** (JsonUtil) | `CpuGovernor` não cria JSONs. ✅ |
| **C22** (FormatUtils) | `CpuGovernor` não precisa formatar bytes. ✅ |
| **C23** (Utils compartilhados) | Cria em `core/governor/` — pacote já existente. ✅ |
| **C24** (SignalManager) | `CpuGovernor` não usa SignalManager. ✅ |
| **C25** (I/O vetorial/raster) | `CpuGovernor` não lê dados geoespaciais. ✅ |
| **C26** (ToolKey) | `CpuGovernor` não faz logging. ✅ |

### Conclusão: **Nenhum contrato precisa ser quebrado.**

---

## 📝 Checklist de Implementação

- [ ] Criar `core/governor/CpuGovernor.py` com classe `CpuGovernor` e constante `CPU_USAGE_LIMIT = 0.50`
- [ ] Atualizar `core/governor/__init__.py` (docstring com referência)
- [ ] Modificar `plugins/idw_interpolator/IdwInterpolatorTask.py` (4 alterações + import)
- [ ] Modificar `plugins/tensorflow_classifier/tensor_utils/hardware_manager.py` (1 alteração)
- [ ] Modificar `core/papeline/ParallelStep.py` (cap no `max_workers`)
- [ ] Modificar `core/papeline/PipelineRunner.py` (injetar no contexto)
- [ ] `py_compile` em todos os arquivos modificados
- [ ] Verificar que não há `os.cpu_count()` solto no código (além do `CpuGovernor.py`)

---

## 📊 Exemplo de Uso Final

```python
# Em qualquer lugar que precise limitar CPU:

from core.governor.CpuGovernor import CpuGovernor

# joblib
from joblib import Parallel, delayed
Parallel(n_jobs=CpuGovernor.n_jobs(), verbose=0)(...)

# ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=CpuGovernor.max_workers()) as executor:
    ...

# Onde antes usava os.cpu_count()
n_cpus = CpuGovernor.max_workers()

# Constante editável — para alterar o limite:
# CpuGovernor.CPU_USAGE_LIMIT = 0.75  # 75% dos CPUs
```

---

## 🧪 Teste de Verificação

```python
# Simulação: 32 CPUs → 16 workers
assert CpuGovernor.max_workers() == 16  # (em máquina com 32 CPUs)

# Mínimo de 1 worker
CpuGovernor.CPU_USAGE_LIMIT = 0.01
assert CpuGovernor.max_workers() >= 1

# Restaurar
CpuGovernor.CPU_USAGE_LIMIT = 0.50
```


