# 📋 Plano de Ação — Resource Governor (Governador de Recursos)

## 🎯 Objetivo

Implementar um sistema de governança de memória RAM para evitar que processos estourem a memória do computador, começando pelo `IdwInterpolatorPlugin` que atualmente crasha por OOM (Out Of Memory).

## 🧱 Arquitetura Proposta

```
core/governor/
├── __init__.py                 — Exporta ResourceGovernor, RamGovernor, RamLimitPolicy nao use init para importar pq fica propenso a circular import
├── RamLimitPolicy.py           — Estratégias de limite (90% global, 50% dedicado)
├── RamGovernor.py              — Monitoramento de RAM (psutil)
└── ResourceGovernor.py         — Orquestrador principal (consulta + decisão)
```

### Responsabilidades

| Classe | Responsabilidade |
|--------|-----------------|
| `RamGovernor` | Coleta dados de RAM do sistema, processo e tasks. Fornece snapshots. |
| `RamLimitPolicy` | Define a estratégia de limite (90% global ou 50% dedicado) e calcula se há folga. |
| `ResourceGovernor` | Orquestra decisões: "pode iniciar task?", "está no limite?". Ponto único de integração com o pipeline. |

---

## 📦 Componentes Detalhados

### 1. `RamGovernor` — Monitor de RAM

**Dependência:** `psutil` (já em `requirements.txt`)

```python
class RamGovernor:
    """Monitora RAM do sistema, do processo e das tasks."""

    def total_system_ram() -> int       # bytes — RAM física total
    def used_system_ram() -> int        # bytes — RAM usada (sistema todo)
    def available_system_ram() -> int   # bytes — RAM disponível (sistema todo)
    def process_ram() -> int            # bytes — RAM do processo atual
    def task_ram(task_id: str) -> int   # bytes — RAM de uma task específica (se rastreada)
    def snapshot() -> dict              # dicionário completo do estado atual
```

**Métodos auxiliares:**
- `percent_used() -> float` — % de RAM do sistema em uso
- `percent_process() -> float` — % de RAM do processo atual

> **Nota:** Para formatação legível de bytes (KB, MB, GB), usar `FormatUtils.format_size()` do `utils/FormatUtils.py` (Contrato 22). Não criar `format_bytes()` próprio.

### 2. `RamLimitPolicy` — Estratégias de Limite

```python
class RamLimitMode(Enum):
    GLOBAL_90 = "global_90"   # 90% do total, considerando todos os processos nao use 90 OU 50 pq se eu mudar esse valor no futuro vai perder legibilidade
    DEDICATED_50 = "dedicated_50"  # 50% do total, dedicado ao app

class RamLimitPolicy:
    mode: RamLimitMode
    custom_fraction: float | None = None  # permite override (ex: 0.75 para 75%)

    def max_allowed_ram() -> int       # bytes máximos permitidos
    def is_available(needed_bytes: int) -> bool  # cabe needed_bytes dentro do limite?
    def available_headroom() -> int    # bytes livres dentro do limite
    def utilization() -> float         # % de ocupação dentro do limite
```

**Regras de cálculo:**

- `GLOBAL_90`: `max_ram = total_ram * 0.90`
  - `headroom = max_ram - used_system_ram`
  - Se `headroom <= 0` → sem recursos, não executa

- `DEDICATED_50`: `max_ram = total_ram * 0.50`
  - `headroom = max_ram - process_ram`
  - Se `headroom <= 0` → sem recursos, não executa

### 3. `ResourceGovernor` — Orquestrador Principal

```python
class ResourceGovernor:
    """
    Ponto único de consulta para decisões baseadas em recursos.
    Plugins/pipelines consultam este governor ANTES de iniciar trabalho pesado.
    """

    def __init__(self, policy: RamLimitPolicy):
        self._ram = RamGovernor()
        self._policy = policy

    def can_execute(estimated_ram: int = 0) -> tuple[bool, str]
        # Retorna (True, "") se ok, ou (False, "motivo") se não pode

    def assert_can_execute(estimated_ram: int = 0) -> None
        # Levanta ResourceExceededError se não pode executar

    def snapshot() -> dict
        # Estado completo para logging/diagnóstico

    def recommended_tile_size(max_tile_points: int) -> int
        # Reduz tamanho do tile proporcionalmente à RAM disponível
        # Quanto menos headroom, menor o tile
```

**Flags de segurança:**
- `self._warnings: int` — contador de warnings consecutivos
- Se > 3 warnings consecutivos → força pausa/cancelamento

---

## 🔌 Integração com o Pipeline

### 4. Modificações no `AsyncPipelineEngine`

No método `_run_loop`, antes de criar uma task:

```python
# ANTES de step.create_task()
if not self._governor.can_execute()[0]:
    self._finish_error("Memória insuficiente")
    return
```

O `ResourceGovernor` será injetado opcionalmente no construtor:

```python
class AsyncPipelineEngine:
    def __init__(self, ..., governor: ResourceGovernor | None = None):
        self._governor = governor or ResourceGovernor.default()
```

### 5. Modificações no `PipelineRunner`

Propagar o `governor` para a engine.

### 6. Modificações no `BaseTask.run()`

Durante a execução, a task pode checar periodicamente:
```python
if self._governor and not self._governor.can_execute()[0]:
    self.cancel()
    return False
```

---

## 🧪 Integração com IdwInterpolatorPlugin

### 7. Onde o RAM estoura

Analisando o fluxo:
1. `IdwInterpolatorStep` cria `IdwInterpolatorTask`
2. A task carrega a nuvem LAS inteira na memória (`laspy.read`)
3. Processa tiles, mas se o LAS é muito grande, o tile individual + dados acumulados estoura

### 8. Ações concretas

| O quê | Onde | Como |
|-------|------|------|
| Calcular RAM estimada | `IdwInterpolatorStep.create_task()` | `estimated = n_pontos * bytes_por_ponto * n_bandas` |
| Consultar governor | `IdwInterpolatorPlugin._on_executar()` | Antes de criar o runner |
| Ajustar tile dinamicamente | `IdwInterpolatorStep.create_task()` | `max_tile = governor.recommended_tile_size(pontos_por_tile)` |
| Logar diagnóstico | `RamGovernor.snapshot()` | Antes e durante a execução |

---

## ⚠️ Requisitos Realistas vs. Não Realistas

### ✅ Realizável

| Requisito | Complexidade |
|-----------|-------------|
| Monitorar RAM total do sistema via `psutil` | Baixa |
| Monitorar RAM do processo atual | Baixa |
| Bloquear execução se RAM insuficiente | Média |
| Reduzir tile size dinamicamente baseado em RAM disponível | Média |
| Logging estruturado de warnings de memória | Baixa |
| HUD com indicador de memória (via SignalManager) | Média | 
| Estratégia configurável (90% global vs 50% dedicado) | Baixa |

### ❌ NÃO Realizável / Não Recomendado

| Requisito | Motivo |
|-----------|--------|
| Matar processos do sistema para liberar RAM | Perigoso, imprevisível, viola segurança |
| Limitar RAM por thread Python | Python não suporta `setrlimit` por thread de forma confiável no Windows |
| Prever RAM exata de uma task | Depende de implementação interna (laspy, numpy, rasterio) — estimativa, nunca valor exato |
| Swap automático para disco | Complexidade altíssima, risco de corromper dados |
| Garbage collection forçado | `gc.collect()` não garante liberação; pode piorar performance |
| Impedir totalmente OOM | Sempre há risco se o SO não cooperar ou se houver leak em biblioteca C |

---

## 📁 Estrutura de Arquivos

```
core/governor/
├── __init__.py                        — exports
├── RamLimitPolicy.py                  — RamLimitMode enum + RamLimitPolicy
├── RamGovernor.py                     — monitoramento psutil
└── ResourceGovernor.py               — orquestrador + ResourceExceededError
```

---

## ✅ Análise de Quebra de Contratos

### Nenhum contrato existente é quebrado

| Contrato | Análise |
|----------|---------|
| **C1** (QMessageBox) | ResourceGovernor não usa QMessageBox. Plugin usa `MessageBox`. ✅ |
| **C2** (Tratamento exceções) | Todo except captura `as e` e loga. ✅ |
| **C3** (Logger) | Usa `self.logger` do BasePlugin ou LogUtils. ✅ |
| **C4** (Preferences) | Não instancia Preferences manualmente. ✅ |
| **C5** (ToolRegistry) | Governor não registra tools. ✅ |
| **C6** (Estrutura Plugin) | Governor não é plugin. ✅ |
| **C7** (Sinais) | Governor não acopla plugins. Comunicação via SignalManager se necessário. ✅ |
| **C8** (Dependências) | `psutil` já está em requirements.txt. Nenhuma nova dependência. ✅ |
| **C9** (Código morto) | Todas as classes têm uso definido. ✅ |
| **C10** (Categorias) | Governor não é tool. ✅ |
| **C11** (Widgets) | Governor não tem UI. ✅ |
| **C12** (Doc reflexiva) | Este plano já documenta. Skill `SKILL_ASYNC_PIPELINE.md` será atualizada. ✅ |
| **C13** (ToolRegistry) | Governor não modifica tools. ✅ |
| **C14** (MenuManager) | Governor não mexe em menu. ✅ |
| **C15** (MenuCategory) | Governor não é tool. ✅ |
| **C16** (WorkspaceManager) | Governor não mexe em workspace. ✅ |
| **C17** (ExplorerUtils) | Governor não usa QFileDialog. ✅ |
| **C18** (ExecutionButtons) | Governor não tem UI. ✅ |
| **C19** (Estilos) | Governor não tem UI. ✅ |
| **C20** (Progress/HUD) | Governor usa SignalManager para HUD se necessário. ✅ |
| **C21** (JsonUtil) | Governor não cria JSONs temporários. ✅ |
| **C22** (FormatUtils) | **Correção no plano**: `RamGovernor` NÃO terá `format_bytes()` próprio. Usará `FormatUtils.format_size()`. ✅ |
| **C23** (Utils compartilhados) | Governor segue o padrão — cria novo pacote em `core/pipeline/governor/`. ✅ |
| **C24** (SignalManager) | Governor só usa SignalManager para eventos de sistema (progresso, HUD). ✅ |
| **C25** (I/O vetorial/raster) | Governor não lê dados geoespaciais. ✅ |
| **C26** (ToolKey) | Governor não usa ToolKey (não faz logging próprio — delega ao plugin). ✅ |ERRADO GOVERNOR USA LOGGING SIM INCLUSIVE DEVE USAR COM TOOLKEY  SYSTEM

### Conclusão: **Nenhum contrato precisa ser quebrado.**

O plano foi ajustado para remover `format_bytes()` próprio (violava o Contrato 22 — `FormatUtils.format_size()` já existe). Demais contratos são respeitados integralmente.

---

## 📝 Checklist de Implementação

- [ ] Criar `core/governor/` com `__init__.py`
- [ ] Implementar `RamGovernor` (monitoramento psutil, sem `format_bytes` — usar `FormatUtils.format_size()`)
- [ ] Implementar `RamLimitPolicy` (estratégias 90% global / 50% dedicado)
- [ ] Implementar `ResourceGovernor` (orquestrador + `can_execute`, `recommended_tile_size`)
- [ ] Criar `ResourceExceededError` custom exception
- [ ] Adicionar `snapshot()` para logging diagnóstico
- [ ] Integration: injetar `ResourceGovernor` no `AsyncPipelineEngine`
- [ ] Integration: injetar `ResourceGovernor` no `PipelineRunner`
- [ ] Integration: `BaseTask.run()` checar periodicamente
- [ ] Integration: `IdwInterpolatorStep.create_task()` estimar RAM e ajustar tile
- [ ] Integration: `IdwInterpolatorPlugin._on_executar()` consultar governor antes
- [ ] Logging estruturado em todos os pontos (Contrato 2)
- [ ] Atualizar `docs/skills/SKILL_ASYNC_PIPELINE.md` com novo componente
- [ ] Testar com LAS grande que estourava RAM

---

## 📊 Exemplo de Uso Final

```python
# No plugin
from core.governor import ResourceGovernor, RamLimitPolicy, RamLimitMode

policy = RamLimitPolicy(mode=RamLimitMode.GLOBAL_90)
governor = ResourceGovernor(policy)

# Antes de executar
can, reason = governor.can_execute(estimated_ram=8_000_000_000)  # 8GB estimado
if not can:
    MessageBox.show_error(reason)
    return

# Tamanho de tile ajustado
safe_tile_size = governor.recommended_tile_size(original_tile_size)

# Criar runner com governor
runner = PipelineRunner(steps=[...], context={...}, governor=governor, parent=self)

# Durante execução, logs automáticos
# RamGovernor: RAM 68% | Processo: 2.4GB | Headroom: 12.8GB | Tile ajustado: 5M pts