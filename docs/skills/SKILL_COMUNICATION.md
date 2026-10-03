# Skill: Comunicação e Mensageria (MessageBox · SignalManager · Console · Progress · HUD · LogUtils)

Esta skill descreve as formas oficiais de comunicação no Aetheris ToolBox, quando usá-las e como elas se diferenciam:

- **MessageBox**: diálogo para interação direta com o usuário (erros, confirmações, inputs simples).
- **SignalManager**: canal exclusivo para comunicação entre *ferramentas* (plugins/core).
- **ConsolePlugin**: interface orientada ao usuário para mensagens, progresso e alertas.
- **ProgressBar (ui_main)**: barra de progresso central usada por todas as ferramentas.
- **HUDLoader**: indicador para operações longas; uso opcional quando apropriado.
- **LogUtils**: logging estruturado e diagnóstico para desenvolvedores.

## MessageBox — Interação com o usuário

Use sempre `utils.MessageBox` para qualquer diálogo com o usuário. Exemplos de uso:

- Erro/alerta: `MessageBox.show_error("Falha ao abrir arquivo", detail=traceback_text)`
- Confirmação: `if MessageBox.show_question("Deseja continuar?") == MessageBox.YES: ...`
- Informação: `MessageBox.show_info("Processo concluído")`
- Toast (não-bloqueante): `MessageBox.show_toast("Configurações salvas!")`
- Toast de erro: `MessageBox.show_toast("Falha ao processar", is_error=True)`

### Toast Notification (não-bloqueante)

O método `show_toast` substitui `show_info`/`show_error` quando a mensagem é temporária e não requer ação do usuário. A notificação aparece por ~2.5s na parte inferior da tela, faz fade out e se auto-destrói — sem travar a UI.

```python
from utils.MessageBox import MessageBox

# Sucesso — gradiente do tema (ACCENT)
MessageBox.show_toast("Configurações salvas com sucesso!")

# Erro — gradiente vermelho
MessageBox.show_toast("Falha ao processar", is_error=True)
```

**Diferenças entre os métodos:**

| Método | Bloqueante | Uso |
|--------|-----------|-----|
| `show_info` / `show_error` | ✅ Sim (QMessageBox.exec) | Mensagens que exigem atenção do usuário |
| `show_toast` | ❌ Não (QTimer + fade) | Feedbacks rápidos que não exigem ação |

Recomendações:
- Forneça `detail` ao exibir exceções (traceback) para permitir suporte/diagnóstico.
- Antes de mostrar um diálogo de erro, faça log via `self.logger.error(..., error=str(e))`.
- Nunca importe `QMessageBox` diretamente.
- Nunca importe `ToastNotification` diretamente — use `MessageBox.show_toast()`.

## SignalManager — Comunicação entre ferramentas

O `SignalManager` é o canal oficial para mensagens entre plugins e entre plugins ↔ core. Devido à sua abrangência, **não** use `SignalManager` para comunicação entre widgets internos do mesmo plugin — use sinais/slots locais.

### Catálogo completo de sinais (`SignalCatalog`)

| Sinal | Tipo | Descrição |
|-------|------|-----------|
| `tool_opened` | `Signal(str)` | Notificação de abertura de ferramenta |
| `tool_closed` | `Signal(str)` | Notificação de fechamento de ferramenta |
| `tool_focused` | `Signal(str)` | Notificação de foco em ferramenta |
| `app_startup` | `Signal()` | Aplicação iniciou |
| `app_shutdown` | `Signal()` | Aplicação encerrando |
| `console_message` | `Signal(str)` | Mensagem orientada ao usuário (ConsolePlugin) — texto seguro, HTML escapado |
| `console_html` | `Signal(str)` | Mensagem HTML formatada para o ConsolePlugin — NÃO escapa, aceita tags `<a>`, `<span>`, etc. |
| `progress_update` | `Signal(float)` | Progresso global (0.0–100.0) para a ProgressBar da `MainWindow` |
| `progress_reset` | `Signal()` | Reseta a barra de progresso para 0% |
| `project_changed` | `Signal()` | Projeto ativo foi salvo/criado |
| `recent_projects_changed` | `Signal(list)` | Lista de projetos recentes foi alterada: `list[dict]` com chaves path, name, active. Emitido após add_recent/remove_recent. FileMenuItem conecta-se a este sinal para atualizar o submenu "Abrir Recente" em tempo real. |
| `hud_show` | `Signal(dict)` | Exibe HUD Loader. Dict pode conter: `"message"`, `"timer"` (segundos, modo 2), `"stages"` (lista [segundos, num_etapas], modo 3). Aceita `"eta"` (segundos totais) para exibir tempo decorrido/restante. |
| `hud_update` | `Signal(dict)` | Atualiza HUD: `{"message": str, "progress": float}`. Aceita `"eta"` (float) para re-estimar ETA durante execução. |
| `hud_hide` | `Signal()` | Esconde HUD Loader |
| `hud_stage_done` | `Signal(int)` | Notifica que uma etapa externa foi concluída (modo 3): `stage_index` |
| `execution_started` | `Signal(str)` | Plugin iniciou execução: `tool_name` |
| `execution_finished` | `Signal(str)` | Plugin finalizou execução com sucesso: `tool_name` |
| `execution_cancelled` | `Signal(str)` | Plugin cancelou/falhou execução: `tool_name` |

### Ciclo de vida de execução (execution_*)

Quando um plugin inicia uma operação longa (ex: processamento em background), ele DEVE:

1. **Início**: emitir `execution_started(tool_name)` → MainWindow mostra HUD e reseta ProgressBar
2. **Durante**: emitir `progress_update(p)` e `hud_update({"message": m, "progress": p})` para manter ambos sincronizados
3. **Sucesso**: emitir `execution_finished(tool_name)` → MainWindow esconde HUD e marca 100%
4. **Falha/Cancelamento**: emitir `execution_cancelled(tool_name)` → MainWindow esconde HUD e reseta ProgressBar

Exemplo de fluxo completo:

```python
from core.manager.SignalManager import SignalManager

signals = SignalManager.instance()

# Início
signals.execution_started.emit("Meu Plugin")
signals.console_message.emit("[Meu Plugin] Iniciando...")
signals.hud_show.emit({"message": "Preparando..."})

# Durante o processamento
for i in range(total):
    pct = ((i + 1) / total) * 100.0
    signals.progress_update.emit(pct)
    signals.hud_update.emit({
        "message": f"Processando item {i+1}/{total}...",
        "progress": pct,
    })

# Sucesso
signals.execution_finished.emit("Meu Plugin")
signals.console_message.emit("[Meu Plugin] Concluído!")

# Falha
signals.execution_cancelled.emit("Meu Plugin")
signals.console_message.emit("[Meu Plugin] ERRO: ...")
```

### Método auxiliar para progresso combinado

Para evitar duplicação, crie um método helper no plugin:

```python
def _on_progress_both(self, progress: float):
    """Propaga progresso para ProgressBar e HUD simultaneamente."""
    SignalManager.instance().progress_update.emit(progress)
    SignalManager.instance().hud_update.emit({
        "message": f"Processando... {progress:.1f}%",
        "progress": progress,
    })
```

### Regras rápidas

- Use `SignalManager` para comunicação *inter-plugin* e para atualizar componentes centrais (Console, ProgressBar, HUD).
- Para lógica/fluxo interno ao plugin, prefira sinais locais ou chamadas diretas entre objetos.
- Sinais de ciclo de vida (`execution_*`) são processados pela `MainWindow` — não os emita manualmente para controle de HUD/ProgressBar.

## ConsolePlugin — Mensagens e alertas ao usuário

O `ConsolePlugin` é a face voltada ao usuário para mensagens de status, alertas e passos de processo. Mensagens aqui devem ser legíveis e focadas na experiência do usuário; evite dumps técnicos extensos — esses vão para o `LogUtils`.

Fluxo recomendado:
- Plugin emite `SignalManager.instance().console_message.emit("texto")` quando quiser notificar o usuário.
- Mensagens de progresso devem ser acompanhadas por `progress_update` quando aplicável.

## ProgressBar (ui_main) — barra de progresso central

A `MainWindow` expõe uma única ProgressBar para sinalizar progresso global. **Regra obrigatória:**

Nenhuma ferramenta deve criar sua própria `QProgressBar` ou similar internamente — use `SignalManager.instance().progress_update.emit(valor)` para atualizar a barra central.

Use 0.0–100.0 como intervalo. A responsabilidade de transformar um avanço em percentuais (quando aplicável) fica a cargo da ferramenta que emite os sinais.

Para resetar a barra para 0%, emita `SignalManager.instance().progress_reset.emit()`.

## HUDLoader — Indicador para operações longas (3 modos + ETA)

O `HUDLoader` é um indicador visual para operações demoradas e pode exibir status mais detalhado que a ProgressBar. Possui 3 modos de funcionamento:

### Modo 1 — Feedback Real
Use `set_progress(percentual, mensagem)` quando o processo fornece feedback de progresso.
```python
self._hud.set_progress(50.0, "Processando etapa 3...")
```

### Modo 2 — Temporizador
Use `start_timer(segundos)` para processos sem feedback. A loader vai de 0% a 100% no tempo especificado.
```python
# Via SignalManager (recomendado para plugins):
SignalManager.instance().hud_show.emit({
    "message": "Convertendo documento...",
    "timer": 10.0,  # 10 segundos ate 100%
})

# Direto no HUD loader:
self._hud.start_timer(10.0, "Convertendo...")
```

### Modo 3 — Etapas (N stages)
Use `start_staged(segundos_totais, num_stages)` para processos com etapas conhecidas. Divide tempo e porcentagem igualmente:

- **Ex: 100s, 4 stages** → cada stage = 25% em 25s
- **Ex: 600s, 6 stages** → cada stage = 16.66% em 100s
- **Ex: 200s, 4 stages** → stage 1: 0-25% em 50s, stage 2: 25.01-50% em 50s, stage 3: 50.01-75% em 50s, stage 4: 75.01-100% em 50s

A loader avanca suavemente (0.01% a cada `tempo_stage / (pct_stage * 100)` segundos). Quando chega no limite do stage, PARA e aguarda `hud_stage_done`. O sinal `hud_stage_done(stage_index)` libera o proximo stage.

```python
# Inicio: 200s totais, 4 etapas
SignalManager.instance().hud_show.emit({
    "message": "Processando lote...",
    "stages": [200.0, 4],  # (total_seconds, num_stages)
})

# Quando uma etapa externa for concluida:
SignalManager.instance().hud_stage_done.emit(0)  # stage 0 concluido -> pula para 25%
SignalManager.instance().hud_stage_done.emit(1)  # stage 1 concluido -> pula para 50%
SignalManager.instance().hud_stage_done.emit(2)  # stage 2 concluido -> pula para 75%
SignalManager.instance().hud_stage_done.emit(3)  # stage 3 concluido -> pula para 100%
```

**Comportamento detalhado:**
- A cada tick (16ms), calcula `(elapsed / secs_per_stage) * pct_per_stage` para saber quanto % avancou dentro do stage atual
- Quando atinge `stage_target_progress`, a progressao para automaticamente
- `hud_stage_done(N)` libera o stage `(N+1)` e reinicia o timer
- Se o ultimo stage for liberado, vai direto para 100%

**Regras:**
- Usar `SignalManager` (sinais `hud_show`, `hud_update`, `hud_hide`) para controlar o HUD a partir de workers.
- Preferir HUD para operações que bloqueiam/ocupam muito tempo ou exigem indicação destacada ao usuário.
- O dicionário do `hud_update` aceita a chave `"progress"` (float, 0.0–100.0) para sincronizar o percentual com a ProgressBar.
- O dicionário do `hud_show` e `hud_update` aceita `"eta"` (float, segundos totais) para exibir "Decorrido | ETA (horario) | Restante" no topo do HUD.
- Não existe proibição estrita similar à ProgressBar, mas prefira reutilizar `HUDLoader` central quando disponível em vez de criar implementações locais.

## LogUtils — Logs estruturados para desenvolvedores

`LogUtils` é a fonte primária de diagnóstico e deve ser usado para:

- Registrar exceções e contexto (`logger.error("msg", code="COD", error=str(e))`).
- Registrar variáveis, estados e entradas/saídas críticas.

### 📝 Regras de Log

**Prefira f-string de uma linha** em vez de dict com code/data excessivo:
```python
# ✅ RECOMENDADO — f-string simples de uma linha
self.logger.info(f"Executando: {path}")
self.logger.info(f"OK: {n} pontos salvos em {output}")
self.logger.warning(f"CRS nao detectado: {path}")

# ✅ Erros usam code + error (obrigatório)
self.logger.error(f"Falha ao processar {path}", code="PROC_ERR", error=str(e))
self.logger.critical(f"Pipeline falhou: {msg}", code="PIPE_FAIL", error=msg)

# ⚠️ ACEITÁVEL — quando muitos dados estruturados são necessários
self.logger.info(f"LAS carregado: {path}", code="LAS_OK", points=n, crs=crs)

# ❌ EVITE — dict com code/data excessivo para logs simples
self.logger.info("Iniciando processamento", code="START", path=p, modo=m, ...)
```

**Regras:**
- Logs de início/fim/diagnóstico simples: **f-string de uma linha, sem code**
- Logs de erro: **f-string + code + error=str(e)** (obrigatório)
- Logs com muitos dados estruturados: **f-string + code + kwargs específicos**
- `print()` só para testes locais — remova antes do commit

### 📝 Regras de Console (console_message)

**NÃO** emita o nome da ferramenta no início da mensagem — o ConsolePlugin já mostra o tooltip de origem. Mensagens devem ser limpas e diretas:

```python
# ✅ RECOMENDADO — sem prefixo [NomeDaFerramenta]
SignalManager.instance().console_message.emit("Processando arquivo...")
SignalManager.instance().console_message.emit("5 arquivos processados em 4.2s")
SignalManager.instance().console_message.emit("ERRO: formato inválido")
SignalManager.instance().console_message.emit("Concluído com 3 falhas!")

# ❌ EVITE — prefixo [Ferramenta] redundante
SignalManager.instance().console_message.emit("[MinhaFerramenta] Iniciando...")
```

### Assinatura dos métodos (referência)

Todos os métodos de log (`debug`, `info`, `warning`, `error`, `critical`) seguem o mesmo padrão:

```python
def info(self, msg: str, *, code: str | None = None, **data: Any) -> None:
```

**Importante:** O `*` na assinatura significa que `code` e `**data` são **keyword-only** — ou seja, devem ser passados **sempre como argumentos nomeados**. Apenas `self` e `msg` são posicionais.

### ✅ Forma RECOMENDADA — f-strings + keyword args

**f-strings sao RECOMENDADAS** para interpolar variaveis na mensagem.

> **Nota:** f-string nao e proibida — printf-style (`%d`, `%s`) SIM e proibido.
> Use f-string quando a mensagem tiver variaveis; string simples quando for estatica.
> Nunca passe variaveis como argumentos posicionais extras — o `LogUtils` **nao aceita** `*args`.

Exemplos:

```python
# ✅ Certo: f-string + keyword-only code + keyword-only data
self._logger.info(f"LAS lido: {n_pontos} pontos", code="IDW_TASK_LAS_READ")
self._logger.info(f"Grid: {width}x{height} px", code="IDW_TASK_GRID")
self._logger.info(f"IDW OK: {n_ok}, Pulado: {n_pulado}", code="IDW_TASK_IDW_DONE")

# ✅ Certo: dados extras via **data
self._logger.info(
    "Metadados LAS obtidos",
    code="LAS_INFO",
    path=path,
    point_count=point_count,
    has_rgb=has_rgb,
)

# ✅ Certo: logger.error com code e error
self._logger.error("Erro ao carregar LAS", code="IDW_LAS_LOAD_ERR", error=str(e))
```

### ❌ Forma ERRADA — printf-style (`%d`, `%s`) com argumentos posicionais

NUNCA use formatação estilo `%d`/`%s` com argumentos posicionais — o `LogUtils` **não aceita** `*args` posicionais além de `msg`:

```python
# ❌ ERRADO! "takes 2 positional arguments but 3 were given"
self._logger.info("LAS lido: %d pontos", n_pontos, code="IDW_TASK_LAS_READ")
self._logger.info("Grid: %dx%d px", width, height, code="IDW_TASK_GRID")
self._logger.info("IDW OK: %d, Pulado: %d", n_ok, n_pulado, code="IDW_TASK_IDW_DONE")
```

Isso causa o erro:
```
LogUtils.info() takes 2 positional arguments but 3 positional arguments
(and 1 keyword-only argument) were given
```

### ⚠️ Atenção: código legado

Se encontrar chamadas como as abaixo no código, **corrija-as imediatamente** trocando para f-strings:

| ❌ Errado (printf positional) | ✅ Correto (f-string) |
|---|---|
| `logger.info("LAS lido: %d pontos", n)` | `logger.info(f"LAS lido: {n} pontos")` |
| `logger.info("Grid: %dx%d px", w, h, code="GRID")` | `logger.info(f"Grid: {w}x{h} px", code="GRID")` |
| `logger.info("OK: %d, Pul: %d", ok, pul, code="DONE")` | `logger.info(f"OK: {ok}, Pul: {pul}", code="DONE")` |

### Exemplo mínimo

```python
try:
    resultado = self._processar(dados)
except Exception as e:
    self.logger.error("Falha no processamento", code="PROC_ERR", error=str(e))
    SignalManager.instance().console_message.emit("Erro ao processar arquivo")
    MessageBox.show_error("Erro durante o processamento", detail=traceback.format_exc())
```

### Resumo de regras para LogUtils

| Regra | Descrição |
|---|---|
| **Mensagem** | Use f-string (`f"..."`) para interpolar variáveis na `msg` |
| **Código** | Use `code="MEU_CODIGO"` como argumento nomeado |
| **Dados extras** | Passe via `**data` como argumentos nomeados (`path=x, n=y`) |
| **Posicionais** | Apenas `self` e `msg` — NUNCA passe valores posicionais extras |
| **printf-style** | ❌ Proibido: `%d`, `%s`, `%f` com argumentos separados |
| **Erro** | Sempre `logger.error("msg", code="COD", error=str(e))` — nunca `except:` sem `as e` |

## Uso de `print()`

`print()` não é proibido, mas deve ser evitado. Permissões:

- Permitido apenas para testes locais rápidos (por exemplo, testar saídas do `LogUtils`) e scripts temporários.
- Nunca deixe `print()` em código final ou em commits destinados à base principal.

> 💡 **Consulte também:** `docs/skills/SKILL_HUD_PROGRESS.md` para o fluxo completo de integração entre HUD Loader, ProgressBar e execução em QThread (PipelineRunner + Tasks).

## Regras Resumidas (Golden Rules)

- **MessageBox**: sempre `utils.MessageBox` para diálogo com usuário.
- **SignalManager**: exclusivo para comunicação entre ferramentas e atualização de componentes centrais.
- **ConsolePlugin**: mensagens legíveis para o usuário; use `console_message`.
- **ProgressBar (ui_main)**: única barra oficial; atualize com `progress_update` — nunca crie barras locais.
- **HUDLoader**: use para operações longas; controle via sinais HUD quando disponível. Passe `"eta"` (segundos) no `hud_show` para exibir "Decorrido | ETA | Restante" no topo.
- **Ciclo de vida**: use `execution_started`/`execution_finished`/`execution_cancelled` para iniciar/parar indicadores visuais.
- **Progresso combinado**: propague progresso para ProgressBar **e** HUD simultaneamente via `_on_progress_both()`.
- **LogUtils**: registro estruturado e diagnóstico; erros sempre com `as e` e `logger.error(..., error=str(e))`.
- **print()**: só para testes locais; remova antes de commitar.