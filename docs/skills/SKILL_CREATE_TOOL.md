# Skill: Criação de Novas Ferramentas (Plugins)

Este guia descreve o processo padrão para criar e registrar uma nova ferramenta no **Aetheris ToolBox**, garantindo a integração com o sistema de logs, gerenciamento de sinais, carregamento dinâmico (Lazy Loading) e reutilização de widgets.

> ⚠️ **Antes de começar**, consulte:
> - `docs/skills/widgets_skill.md` — verifique se já existe um widget pronto para sua UI
> - `docs/ia/contracts.md` (Contrato 11) — regras sobre composição de widgets
> - `docs/skills/preferences_skill.md` — obrigatório implementar load/save_prefs
> - `docs/skills/log_utils_skill.md` — obrigatório logar eventos críticos

---

## 🛠 Passo 1: Definir a Identidade da Ferramenta

Toda ferramenta precisa de uma chave única no sistema. Adicione o nome da sua ferramenta ao Enum `ToolKey`.

**Arquivo:** `core/enum/ToolKey.py`
```python
class ToolKey(str, Enum):
    ...
    MINHA_FERRAMENTA = "MinhaFerramenta"
```

---

## 🏗 Passo 2: Implementar o Widget do Plugin

Crie um novo diretório em `plugins/` e implemente sua classe herdando de `BasePlugin`. Isso garante que sua ferramenta tenha acesso automático ao `self.logger` e participe do ciclo de vida de sinais (abertura/fechamento).

**Regras de UI (Contrato 11):**
1. **NUNCA** importe widgets brutos de `PySide6.QtWidgets` sem antes verificar em `resources/widgets/`.
2. Se o componente que você precisa é composto (ex: label + campo + botão), provavelmente já existe ou deve ser criado como widget único em `resources/widgets/`.
3. Consulte `docs/skills/widgets_skill.md` para ver a lista completa de widgets disponíveis.

**Arquivo:** `plugins/minha_ferramenta/main_widget.py`
```python
from core.model.BasePlugin import BasePlugin
from resources.widgets.GroupDiv import GroupDiv                          # ✅ container com título

class MinhaFerramentaWidget(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(
            tool_key="MinhaFerramenta",
            parent=parent,
            title="Minha Ferramenta",
            buttons_config={
                "executar": {
                    "text": "EXECUTAR",
                    "callback": self._on_executar,
                    "type": "primary",
                    "description": "Inicia o processamento",
                },
            },
        )
        # ⚠️ NÃO chame self._build_ui() nem self.load_prefs() aqui!
        # BasePlugin.__init__ já chama ambos automaticamente.
        self.logger.info("Ferramenta inicializada com sucesso!", code="TOOL_READY")

    def _build_ui(self):
        super()._build_ui()
        # NÃO crie ExecutionButtons manualmente — eles já estão no header do PluginPage
        # Acesse via self.page.buttons para habilitar/desabilitar
        grupo = GroupDiv("Configurações")
        # ... adicionar widgets do grupo
        self.main_layout.addWidget(grupo)

    def load_prefs(self):
        """Obrigatório — carrega preferências salvas."""
        pass

    def save_prefs(self):
        """Obrigatório — salva preferências."""
        pass

    def _on_executar(self):
        self.page.buttons.set_enabled("executar", False)
        # ... execução ...
        self.page.buttons.set_enabled("executar", True)
```

> ⚠️ **Cuidado com signal chain ao restaurar paths:**  
> Widgets como `SimpleSelector` disparam callbacks automaticamente via `textChanged` quando `set_path()` é chamado.  
> **NUNCA** faça:
> ```python
> # ❌ ERRADO — callback será chamado DUAS VEZES
> self._selector.set_path(saved_path)
> self._selector.on_path_change(saved_path)  # redundante!
> 
> # ❌ ERRADO — carregar metadados sem setar o path visualmente
> self._carregar_las(file_path)  # path não aparece no QLineEdit!
> ```
> **Sempre** use `set_path()` para restaurar paths — o callback conectado via `on_path_change` será disparado automaticamente.
> 
> ⚠️ **Salve ambos os paths (file e folder) sempre:**  
> Se sua ferramenta tem modo "Arquivo"/"Pasta", salve AMBOS os paths no `save_prefs()`, não apenas o do modo atual:
> ```python
> def save_prefs(self):
>     # Salva o path do modo atual
>     if self._mode == "file":
>         self.preferences["file_path"] = self._current_path
>     elif self._mode == "folder":
>         self.preferences["folder_path"] = self._current_path
>     # Preserva o outro path que já estava salvo (não sobrescreve com vazio)
> ```
> Isso garante que ao alternar entre modos, o path do outro modo ainda esteja disponível.
```

---

## 📝 Passo 3: Registrar no ToolRegistry

Para que a ferramenta apareça na interface, ela deve ser registrada no `ToolRegistry`. É aqui que definimos onde ela será exibida e como o Python deve importá-la.

**Arquivo:** `core/config/ToolRegistry.py`
```python
# Dentro do dicionário _TOOLS:
ToolKey.MINHA_FERRAMENTA.value: Tool(
    name=ToolKey.MINHA_FERRAMENTA.value,
    title="Minha Nova Tool",
    widget_factory=_make_factory(
        "plugins.minha_ferramenta.main_widget", "MinhaFerramentaWidget"
    ),
    tooltip="Descrição curta que aparece no menu",
    tool_type=ToolType.RASTER,      # Define o ícone e grupo na AppBar
    category=CategoryTool.CENTRAL,  # CENTRAL (Abas) ou SIDE (Painel Lateral)
),
```

---

## 🎨 Passo 4: Ícones e Interface (Opcional)

1. **Ícone**: Adicione um arquivo `.ico` com o mesmo nome da ferramenta em `resources/icons/MinhaFerramenta.ico`. O `IconManager` o encontrará automaticamente.
2. **Menu**: O `MenuManager` lerá o `ToolType` definido no registro e adicionará o botão da ferramenta ao grupo correspondente na barra superior.

---

## 💬 Passo 5: Mensagens de Sucesso Padronizadas

O `BasePlugin` fornece **3 helpers** para mensagens de sucesso. Use-os no callback `_on_done()` da pipeline:

### `self.stats_message(n_arquivos, n_processed, ntype)`
Emite no Console o resumo de processamento com tempo decorrido do `ProcessStatisticsUtil`:
```
5 arquivo(s) processados | 38.705 pontos | em 4.2s.
```
```python
def _on_done(self, context):
    elapsed = self.statistics.end()
    self.stats_message(
        n_arquivos=5,
        n_processed=38705,
        ntype="pontos",
    )
```

### `self.output_message(output_path, label="Pasta de Saída")`
Emite no Console um **link clicável** (HTML) que abre o caminho no Windows Explorer:
```
Resultado disponível em: 📂 Pasta de Saída  ← link clicável
```
**Sempre passe o diretório, não o arquivo:**
```python
self.output_message(os.path.dirname(output_path), label="Pasta de Saída")
```

### `self.success_message(output_path, label, summary, n_input, n_output, n_arquivos)`
Combina ambos + `execution_finished` + `MessageBox.show_info`:
```python
self.success_message(
    output_path=output_dir,
    label="Pasta de Saída",
    summary="Processamento concluído!",
    n_output=38705,
    n_arquivos=5,
)
```

### 📝 Regras de Log e Console

**Logs (LogUtils / self.logger):**
- Use **f-string de uma linha** — sem dict com code/data excessivo
- Preferência: `self.logger.info(f"Executando: {path}")` em vez de dict com code
- Erros ainda usam `self.logger.error(f"Falha: {e}")` com `code=` e `error=str(e)`

**Console (SignalManager.console_message):**
- **NÃO** emita o nome da ferramenta no início da mensagem — o ConsolePlugin já mostra de quem é
- Mensagens limpas e diretas:
  ```python
  SignalManager.instance().console_message.emit(f"Processando: {arquivo}")
  SignalManager.instance().console_message.emit(f"Concluido: {n} pontos")
  SignalManager.instance().console_message.emit(f"ERRO: {mensagem}")
  ```

---

> 💡 **Consulte também:** `docs/skills/SKILL_HUD_PROGRESS.md` para entender como emitir progresso (HUD + ProgressBar) durante a execução de operações longas em background.

## ✅ Checklist de Verificação
- [ ] A chave em `ToolKey` é idêntica ao `tool_key` passado no `super().__init__`.
- [ ] O caminho do módulo no `_make_factory` usa pontos (ex: `plugins.pasta.arquivo`).
- [ ] A categoria `CategoryTool` está correta (ferramentas de análise costumam ser `CENTRAL`).
- [ ] Se a ferramenta for `BOTH`, ela será registrada no `SideWorkspace` mas poderá ser movida.
- [ ] **Widgets reutilizáveis**: consultei `docs/skills/widgets_skill.md` antes de criar UI? (Contrato 11)
- [ ] **Preferências**: A ferramenta implementa `load_prefs()` e `save_prefs()` para persistir dados do usuário? (Obrigatório)
- [ ] 🛑 **Logs Obrigatórios**: A ferramenta deve registrar logs em pontos críticos (inicialização, início/fim de processos, capturas de erro). Ferramentas sem log não serão aceitas no core.
- [ ] **Mensagens de sucesso**: use `self.stats_message()` + `self.output_message()` ou `self.success_message()` para feedback padronizado ao usuário.
- [ ] **Documentação**: se criei um widget novo, atualizei `docs/skills/widgets_skill.md`? (Contrato 12)

---

## ⚡ Ferramentas INSTANT (Ação Imediata)

Ferramentas do tipo `INSTANT` não abrem abas no workspace. Elas executam uma ação imediata (abrir diálogo, processar algo, etc.) e se auto-destroem.

### Quando usar

- Operações que não precisam de UI persistente (ex: criar projeto, exportar, salvar snapshot).
- Ações que abrem diálogos modais e depois encerram.

### Como criar

1. **CategoryTool**: já existe `CategoryTool.INSTANT = "instant"`.
2. **Widget**: herde de `BasePlugin`, use `QTimer.singleShot(0, self._run)` para executar a ação após o `__init__`.
3. **Auto-destruição**: chame `self.deleteLater()` ao final.

```python
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QLabel

class MinhaInstantTool(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(tool_key="MinhaInstant", parent=parent)
        # Placeholder invisível
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        placeholder = QLabel("")
        placeholder.setVisible(False)
        layout.addWidget(placeholder)
        # Executa no próximo ciclo do event loop
        QTimer.singleShot(0, self._run)

    def _run(self) -> None:
        try:
            # ... ação principal ...
            pass
        except Exception as e:
            self.logger.error("Erro", code="INSTANT_ERR", error=str(e))
        finally:
            self.deleteLater()

    def load_prefs(self): pass
    def save_prefs(self): pass
```

### Registro no ToolRegistry

```python
ToolKey.MINHA_INSTANT.value: Tool(
    name=ToolKey.MINHA_INSTANT.value,
    title="Minha Ação Instantânea",
    widget_factory=_make_factory(
        "plugins.minha_instant.MinhaInstantPlugin",
        "MinhaInstantPlugin",
    ),
    tooltip="Descrição curta",
    tool_type=ToolType.FOLDER,
    category=CategoryTool.INSTANT,
    show_in_toolbar=True,
),
```

### Comportamento no WorkspaceManager

- Ferramentas `INSTANT` **não** são registradas em `CentralWorkspace` nem `SideWorkspace`.
- Quando o usuário clica no botão da toolbar, o `WorkspaceManager.open_tool()` acessa `tool.widget` (lazy loading), o que instancia o plugin, executa a ação e o widget se auto-destrói.
- Nenhuma aba é criada. Nenhum estado é mantido.

### Requisitos

- [ ] **QTimer.singleShot**: use para adiar a execução para depois do `__init__`.
- [ ] **self.deleteLater()**: chame no `finally` para garantir limpeza.
- [ ] **Logger**: registre início, fim e erros.
- [ ] **MessageBox**: use para feedback ao usuário.