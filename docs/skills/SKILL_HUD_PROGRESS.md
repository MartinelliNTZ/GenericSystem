# Skill: HUD Loader e ProgressBar — Sistema de Progresso

Esta skill documenta como o **HUD Loader** (overlay visual) e a **ProgressBar** (barra inferior) funcionam em conjunto no Aetheris ToolBox, e como plugins/tasks devem emitir progresso corretamente.

---

## 📋 Visão Geral

O sistema de progresso é **centralizado na MainWindow** (`core/ui/ui_main.py`). Ela possui:

1. **`QProgressBar`** — barra fixa na parte inferior da janela (0–10000, formatada como %)
2. **`HudCircularRingsLoader`** — overlay animado no centro da tela

Ambos são controlados **exclusivamente via `SignalManager`**. Nenhum plugin deve criar sua própria barra ou loader.

---

## 🎯 Os 5 Cenários de Uso do HudCircularRingsLoader

O `HudCircularRingsLoader` (`core/ui/HudCircularRingsLoader.py`) possui **3 modos internos** que combinados com os **gatilhos automáticos da MainWindow** geram **5 cenários de uso** distintos:

### 📌 CENÁRIO 1 — Modo 1: Feedback Real Manual
**Quando usar:** O plugin/Task sabe exatamente o progresso e quer informar em tempo real.

```
Plugin conhece o progresso real
         │
         ├─ hud_show({"message": "Processando..."})
         │   → HUD entra em _mode=1 (manual)
         │
         ├─ hud_update({"message": "Etapa X", "progress": 35.0})
         │   → Plugin emite updates com progresso verdadeiro
         │
         └─ hud_hide()
             → Encerra
```

**Mecanismo interno:**
- `set_progress(value, message)` é chamado via `_on_hud_show` (no início) e `_on_hud_update` (durante execução)
- O progresso NÃO é calculado automaticamente — quem define é o plugin/Task
- O HUD exibe exatamente o valor recebido

**Atalho pela MainWindow:**
```python
# Plugin (Main Thread ou QThread)
SignalManager.instance().hud_update.emit({
    "message": "Baixando arquivo 5/10...",
    "progress": 50.0,
})
```

### 📌 CENÁRIO 2 — Modo 2: Temporizador (Timer)
**Quando usar:** O processo não tem feedback real de progresso, mas tem duração estimada conhecida. O HUD conta sozinho de 0% a 100% no tempo especificado.

```
Plugin não sabe o progresso real, mas sabe o tempo estimado
         │
         ├─ hud_show({"message": "Convertendo...", "timer": 10.0})
         │   → HUD entra em _mode=2 (timer)
         │   → _setup_stage(total_secs=10, num_stages=1)
         │   → _elapsed.start()
         │
         │   A cada 16ms (tick):
         │     elapsed_sec = _elapsed.elapsed() / 1000
         │     progress = (elapsed_sec / 10.0) * 100.0
         │     se elapsed_sec >= 10.0 → progress = 100.0
         │
         └─ hud_hide()
             → Encerra
```

**Mecanismo interno:**
- `start_timer(seconds, message)` configura `_mode=2`, `_num_stages=1`, `_secs_per_stage=seconds`
- O método `_update_auto_progress()` é chamado a cada 16ms pelo `_tick()`
- Calcula `progress = (elapsed_sec / secs_per_stage) * 100`
- Quando `elapsed_sec >= secs_per_stage`, trava em 100%
- A cada mudança, emite `hud_update` + `progress_update` automaticamente via `_emit_progress()`

### 📌 ETA — Display de Tempo (Decorrido, ETA, Restante)

O HUD Loader exibe automaticamente uma linha de tempo no topo do painel sempre que o plugin
fornece `"eta"` (segundos totais estimados) no dicionario do `hud_show` ou `hud_update`.

```
Decorrido: 00:00:25  |  ETA: 15:32  |  Restante: 00:14:35
```

**Separacao de responsabilidades:**

| Componente | Responsabilidade |
|-----------|-----------------|
| **Plugin** | Calcula e emite `"eta"` (segundos totais estimados) via `hud_show["eta"]` |
| **MainWindow** | Extrai `"eta"` do dict e chama `self._hud.set_eta(valor)` |
| **HUD Loader** | Armazena o ETA, calcula elapsed/remaining/ETA clock com base no seu `QElapsedTimer`, e exibe formatado na tela |

**Exemplo de uso no plugin:**
```python
# No _on_executar do plugin
SignalManager.instance().hud_show.emit({
    "message": "Interpolacao IDW (500.000 pontos)...",
    "timer": total_estimate,      # Modo 2: auto-count 0% a 100%
    "eta": total_estimate,        # Exibe Decorrido | ETA | Restante
})
```

**Metodo auxiliar no BasePlugin:**
```python
# BasePlugin.get_eta_seconds() retorna o tempo estimado do ProcessStatisticsUtil
eta = self.get_eta_seconds()  # 300.0 (5 minutos)
```

> A linha de tempo usa fonte `Consolas 9` na cor `GOLD` (dourado do tema ativo)
> e e atualizada a cada tick (16ms) junto com o progresso.

### 📌 CENÁRIO 3 — Modo 3: Etapas (Stages)
**Quando usar:** O processo tem N etapas conhecidas com duração total estimada. Cada etapa avança o progresso em (100/N)% e o HUD espera confirmação externa para liberar a próxima etapa.

> 💡 **Dica:** O tempo total estimado pode ser obtido via `ProcessStatisticsUtil`:
> ```python
> # statistics.remaining_time → segundos restantes (baseado em histórico)
> # statistics.total_time → tempo total acumulado do histórico
> # fallback: 30s se não houver histórico
> total_estimate = max(
>     self.statistics.remaining_time,
>     self.statistics.total_time,
>     30.0,
> )
> ```
> Veja `utils/ProcessStatisticsUtil.py` para detalhes da API.

```
Plugin tem N etapas bem definidas
         │
         ├─ hud_show({"message": "Processando lote...", "stages": [200.0, 4]})
         │   → HUD entra em _mode=3 (staged)
         │   → _setup_stage(total=200, stages=4, stage_idx=0)
         │   → _pct_per_stage = 25%, _secs_per_stage = 50s
         │   → Progresso varia de 0% a 25% em 50s
         │
         │   Etapa 1 executando (0s → 50s):
         │     progress = 0% → 25% (automático)
         │     Quando atinge 25%, PARA e aguarda
         │
         ├─ hud_stage_done(0)  ← Plugin concluiu etapa 1
         │   → _on_stage_done(0)
         │   → next_stage = 1
         │   → _setup_stage(total=200, stages=4, stage_idx=1)
         │   → Progresso varia de 25% a 50% em 50s
         │
         ├─ hud_stage_done(1)  ← Plugin concluiu etapa 2
         │   → Progresso 25% → 50% → 75% em 50s
         │
         ├─ hud_stage_done(2)  ← Plugin concluiu etapa 3
         │   → Progresso 50% → 75% → 100% em 50s
         │
         └─ hud_stage_done(3)  ← Plugin concluiu etapa 4
             → next_stage(4) >= num_stages(4)
             → progress = 100% (direto, sem timer)
```

**Divisão do tempo total:**
- 200s totais, 4 stages → cada stage = 50s, cada stage = 25%
- 600s totais, 6 stages → cada stage = 100s, cada stage = 16.66%
- 100s totais, 4 stages → stage 1: 0-25% em 25s, stage 2: 25-50% em 25s, ...

**Mecanismo interno:**
- `start_staged(total_seconds, num_stages, message)` configura `_mode=3`
- `_setup_stage()` é chamado para cada stage, reiniciando `_elapsed`
- Dentro de cada stage, `_update_auto_progress()` calcula o progresso linear
- Quando `elapsed_sec >= secs_per_stage`, trava em `_stage_max_pct` e PARA (não avança)
- `_on_stage_done(stage_index)` libera o próximo stage
- Se `next_stage >= _num_stages`, vai direto para 100%

### 📌 CENÁRIO 4 — Gatilho Automático: execution_started
**Quando usar:** O plugin emite `execution_started` e a MainWindow automaticamente mostra o HUD em Modo 1 com 0%.

```python
# Plugin (Main Thread)
SignalManager.instance().execution_started.emit(self.tool_key)
```

**O que acontece na MainWindow:**
```python
def _on_execution_started(self, tool_name: str):
    self._hud.set_progress(0.0, f"Iniciando {tool_name}...")  # Modo 1
    self._hud.show_loader()
    self._on_progress_reset()
```

**Quando usar este cenário:** O plugin quer que o HUD apareça automaticamente ao iniciar, mas vai fornecer progresso real via `hud_update` durante a execução (Cenário 1 combinado).

### 📌 CENÁRIO 5 — Gatilho Automático: execution_finished / execution_cancelled
**Quando usar:** O plugin finaliza (sucesso ou erro) e a MainWindow automaticamente esconde o HUD.

```python
# Sucesso
SignalManager.instance().execution_finished.emit(self.tool_key)
# Falha
SignalManager.instance().execution_cancelled.emit(self.tool_key)
```

**O que acontece na MainWindow:**
```python
def _on_execution_finished(self, tool_name: str):
    self._hud.hide_loader()  # _mode = 1, self.hide()
    self._on_progress_reset()

def _on_execution_cancelled(self, tool_name: str):
    self._hud.hide_loader()  # _mode = 1, self.hide()
    self._on_progress_reset()
```

**Importante:** `hide_loader()` reseta `_mode` para 1 (manual) e esconde o widget. Na próxima exibição, o HUD começa do zero.

---

### 🔀 Tabela Comparativa dos Cenários

| Cenário | Modo Interno | Sinal de Disparo | Quem calcula o % | Ideal para |
|---------|-------------|-------------------|-------------------|------------|
| 1 - Feedback Real | `_mode=1` | `hud_show` + `hud_update` | Plugin/Task (real) | Operações com progresso mensurável |
| 2 - Temporizador | `_mode=2` | `hud_show({"timer": sec})` | HUD (automático) | Operações sem feedback, tempo conhecido |
| 3 - Etapas | `_mode=3` | `hud_show({"stages": [s, n]})` + `hud_stage_done` | HUD (automático por etapa) | Processos multi-etapa |
| 4 - Auto Início | `_mode=1` | `execution_started` | MainWindow (setup) | Inicialização automática |
| 5 - Auto Fim | — | `execution_finished`/`execution_cancelled` | MainWindow (teardown) | Finalização automática |

```
Plugin / Task                          MainWindow
      │                                     │
      ├─ execution_started ───────────────► │  ← mostra HUD + reseta ProgressBar
      │                                     │
      ├─ hud_update + progress_update ────► │  ← durante processamento
      │                                     │
      ├─ execution_finished ──────────────► │  ← sucesso: esconde HUD + reseta
      └─ execution_cancelled ────────────► │  ← falha: esconde HUD + reseta
```

---

## 🔌 Conexões na MainWindow (`core/ui/ui_main.py`)

```python
# ── ProgressBar ──────────────────────────────────────────────
self.progress = QProgressBar()
self.progress.setMinimum(0)
self.progress.setMaximum(10000)
self.progress.setValue(0)
self.progress.setFormat(" %p% - aguardando... ")
self.progress.setFixedHeight(20)

SignalManager.instance().progress_update.connect(self._on_progress_update)
SignalManager.instance().progress_reset.connect(self._on_progress_reset)

# ── HUD Loader (overlay) ────────────────────────────────────
self._hud = HudCircularRingsLoader(self)
self._hud.setGeometry(self.rect())

SignalManager.instance().hud_show.connect(self._on_hud_show)
SignalManager.instance().hud_update.connect(self._on_hud_update)
SignalManager.instance().hud_hide.connect(self._on_hud_hide)

# ── Ciclo de vida de execução ───────────────────────────────
SignalManager.instance().execution_started.connect(self._on_execution_started)
SignalManager.instance().execution_finished.connect(self._on_execution_finished)
SignalManager.instance().execution_cancelled.connect(self._on_execution_cancelled)
```

### Handlers da MainWindow

```python
def _on_execution_started(self, tool_name: str):
    """Início de execução: mostra HUD e reseta progresso."""
    self._hud.set_progress(0.0, f"Iniciando {tool_name}...")
    self._hud.show_loader()
    self._on_progress_reset()

def _on_execution_finished(self, tool_name: str):
    """Fim de execução: esconde HUD e reseta progress para 0%."""
    self._hud.hide_loader()
    self._on_progress_reset()

def _on_execution_cancelled(self, tool_name: str):
    """Cancelamento: esconde HUD e reseta progresso."""
    self._hud.hide_loader()
    self._on_progress_reset()

def _on_progress_update(self, value: float):
    scaled = int(round(value * 100.0))
    self.progress.setValue(scaled)
    if value <= 0:
        self.progress.setFormat(" %p% - aguardando... ")
    elif value >= 100:
        self.progress.setFormat(" 100% - concluído! ")
    else:
        self.progress.setFormat(f" {value:.2f}% - executando... ")

def _on_hud_show(self, data: dict):
    msg = data.get("message", "Processando...")
    timer = data.get("timer", None)       # Modo 2: segundos
    stages = data.get("stages", None)     # Modo 3: (segundos, num_etapas)
    eta = data.get("eta", None)           # ETA em segundos totais
    if timer is not None:
        self._hud.start_timer(float(timer), msg)
    elif stages is not None and isinstance(stages, (list, tuple)) and len(stages) == 2:
        self._hud.start_staged(float(stages[0]), int(stages[1]), msg)
    else:
        self._hud.set_progress(0.0, msg)  # Modo 1
    if eta is not None:
        self._hud.set_eta(float(eta))
    self._hud.show_loader()

def _on_hud_update(self, data: dict):
    msg = data.get("message", "")
    progress = data.get("progress", None)
    eta = data.get("eta", None)           # ETA em segundos (atualizacao)
    if progress is not None:
        self._hud.progress = max(0.0, min(100.0, float(progress)))
    if msg:
        self._hud.message = msg
    if eta is not None:
        self._hud.set_eta(float(eta))
    if progress is not None or msg or eta is not None:
        self._hud.update()
```

---

## 📡 Fluxo de Progresso em Background (QThread)

Quando uma **Task** (herdando de `BaseTask`) executa em **QThread** (via `PipelineRunner`), ela DEVE emitir progresso usando `SignalManager.instance()` — os **sinais Qt são thread-safe**:

```python
# core/papeline/task/MinhaTask.py
from core.manager.SignalManager import SignalManager

class MinhaTask(BaseTask):
    def _run(self) -> bool:
        signals = SignalManager.instance()

        # Etapa 1 (0% → 30%)
        signals.hud_update.emit({"message": "Etapa 1...", "progress": 10.0})
        signals.progress_update.emit(10.0)
        # ... lógica pesada ...

        # Etapa 2 (30% → 70%)
        signals.hud_update.emit({"message": "Etapa 2...", "progress": 50.0})
        signals.progress_update.emit(50.0)
        # ... lógica pesada ...

        # Final (100%)
        self.result = {...}
        return True
```

### Progresso combinado (HUD + ProgressBar)

Para manter HUD e ProgressBar sincronizados, **sempre emita ambos**:

```python
progresso = 50.0
mensagem = "Processando..."

signals.hud_update.emit({"message": mensagem, "progress": progresso})
signals.progress_update.emit(progresso)
```

---

## 🎯 Fluxo Completo (Plugin + PipelineRunner + Task)

```
┌─────────────────────────────────────────────────────────────────────┐
│ PLUGIN (Main Thread)                                                │
│                                                                     │
│  1. _on_executar()                                                  │
│     ├─ signals.execution_started.emit(tool_name)  ← MainWindow      │
│     │                                          mostra HUD + reseta  │
│     ├─ signals.hud_show.emit({"message": "..."}) ← Modo 1           │
│     └─ runner.start() ─────────────────────────────────────────┐    │
│                                                                 │    │
│  2. _on_done(context)  ← finished_ok da pipeline               │    │
│     ├─ signals.execution_finished.emit(tool_name)               │    │
│     └─ MessageBox.show_info("Concluído!")                      │    │
│                                                                 │    │
│  3. _on_runner_finished()  ← finished da pipeline              │    │
│     ├─ hud_hide.emit()                                         │    │
│     ├─ progress_update.emit(0)                                 │    │
│     └─ restaura botões                                        │    │
└─────────────────────────────────────────────────────────────────┘    │
                                                                       │
┌─────────────────────────────────────────────────────────────────────┐ │
│ PIPELINERUNNER (QThread)                                           │ │
│                                                                     │ │
│  runner.run()                                                       │ │
│    ├─ Cria ExecutionContext                                         │ │
│    ├─ Cria AsyncPipelineEngine(steps, context)                      │ │
│    ├─ engine.start_non_blocking() ──────────────────────────────┐   │ │
│    │                                                            │   │ │
│    └─ while engine.is_running: msleep(50) ← mantém thread viva  │   │ │
└─────────────────────────────────────────────────────────────────┤   │ │
                                                                   │   │ │
┌─────────────────────────────────────────────────────────────────┐│   │ │
│ TASK (dentro da QThread)                                        ││   │ │
│                                                                  ││   │ │
│  _run()                                                          ││   │ │
│    ├─ signals.hud_update(5%) + progress_update(5%)              ││   │ │
│    │   ← "Lendo arquivo..."                                     ││   │ │
│    ├─ laspy.read()                                              ││   │ │
│    ├─ signals.hud_update(50%) + progress_update(50%)            ││   │ │
│    │   ← "Filtrando pontos..."                                  ││   │ │
│    ├─ processamento                                             ││   │ │
│    ├─ signals.hud_update(75%) + progress_update(75%)            ││   │ │
│    │   ← "Salvando resultado..."                                ││   │ │
│    ├─ write()                                                   ││   │ │
│    └─ return True                                               ││   │ │
└─────────────────────────────────────────────────────────────────┘│   │ │
                                                                   │   │ │
  SignalManager.instance() (thread-safe) ◄─────────────────────────┘   │ │
    ├─ hud_update ──► MainWindow._on_hud_update (Main Thread)          │ │
    ├─ progress_update ──► MainWindow._on_progress_update              │ │
    └─ sinais são postos na fila de eventos da Main Thread ────────────┘ │
                                                                         │
  PipelineRunner terminou ◄──────────────────────────────────────────────┘
    ├─ finished_ok.emit(context) ──► Plugin._on_done (Main Thread)
    └─ finished.emit() ──► Plugin._on_runner_finished (Main Thread)
```

---

## 📌 Regras Obrigatórias

| Regra | Descrição |
|-------|-----------|
| **Sinais Qt são thread-safe** | `SignalManager.instance().hud_update.emit(...)` funciona de dentro de qualquer QThread |
| **Sempre emita progress_update com hud_update** | Para manter a ProgressBar sincronizada com o HUD |
| **execution_started/finished** | Controlam mostrar/esconder o HUD automaticamente |
| **Nunca crie QProgressBar no plugin** | Use sempre `progress_update` (Contrato 20) |
| **Task não sabe da UI** | Task só emite sinais — não importa widgets, não chama MessageBox |
| **Plugin gerencia o ciclo** | Plugin chama `hud_show` antes do runner, `hud_hide` no `_on_runner_finished` |
| **ETA opcional** | Passe `"eta"` (segundos totais) no `hud_show` para exibir "Decorrido | ETA | Restante" no topo do HUD |

---

## 🔍 Checklist ao implementar progresso

- [ ] Task importa `SignalManager` e emite `hud_update` + `progress_update` durante `_run()`
- [ ] Plugin emite `execution_started` antes de iniciar o runner
- [ ] Plugin emite `execution_finished` no callback de sucesso
- [ ] Plugin emite `hud_hide` + `progress_update(0)` no `_on_runner_finished`
- [ ] Nenhum `QProgressBar` ou `QLabel` de progresso foi criado no plugin
- [ ] A Task não importa `QWidget`, `MessageBox` ou qualquer classe de UI
- [ ] Plugin emite `"eta"` (segundos totais) no `hud_show` para exibir Decorrido/ETA/Restante