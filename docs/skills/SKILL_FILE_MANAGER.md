# Skill: FileManager (Explorador de Arquivos Interno)

## Visão Geral

O `FileManagerPlugin` é uma ferramenta do tipo **SIDE** (painel lateral) que implementa um explorador de arquivos interno usando `QFileSystemModel` do Qt. Ele lê a `root_folder` das `sys_preferences` (definida pelo `SaveProjectPlugin`) e exibe o conteúdo daquela pasta em uma árvore, com suporte a operações básicas de gerenciamento de arquivos.

## Arquivos

| Arquivo | Descrição |
|---|---|
| `plugins/file_manager/FileManagerPlugin.py` | Plugin principal (herda `BasePlugin` com `sys_prefs=True`) |
| `resources/widgets/FileTreeWidget.py` | Widget reutilizável `QTreeView` + `QFileSystemModel` |

## Dependências

- Nenhuma externa. Usa `os`, `shutil`, `pathlib`, `subprocess` (stdlib) + `PySide6`.
- Não adiciona requirements novos.

## Como Usar no ToolRegistry

```python
ToolKey.FILE_MANAGER.value: Tool(
    name=ToolKey.FILE_MANAGER.value,
    title="Explorador",
    widget_factory=_make_factory(
        "plugins.file_manager.FileManagerPlugin",
        "FileManagerPlugin",
    ),
    tooltip="Explorador de arquivos interno do projeto",
    tool_type=ToolType.FOLDER,
    category=CategoryTool.SIDE,
    show_in_toolbar=True,
),
```

## API do FileTreeWidget

### Sinais

| Sinal | Assinatura | Descrição |
|---|---|---|
| `file_renamed` | `Signal(str, str)` | `(old_path, new_path)` |
| `file_deleted` | `Signal(str)` | `(path)` |
| `file_created` | `Signal(str)` | `(path)` |
| `file_moved` | `Signal(str, str)` | `(src, dst)` |
| `selection_changed` | `Signal(object)` | `(path \| None)` |

### Métodos Públicos

| Método | Retorno | Descrição |
|---|---|---|
| `set_root_path(path)` | `None` | Define diretório raiz da árvore |
| `refresh()` | `None` | Recarrega o modelo |
| `selected_path()` | `str \| None` | Caminho do primeiro item selecionado |
| `selected_paths()` | `list[str]` | Caminhos de todos itens selecionados |
| `selected_is_directory()` | `bool` | True se seleção for pasta |
| `delete_selected()` | `bool` | Exclui itens selecionados (com confirmação) |
| `rename_selected()` | `bool` | Renomeia item (apenas 1) |
| `create_text_file(directory)` | `bool` | Cria arquivo .txt vazio |
| `show_conflict_dialog(file_name)` | `tuple[str, bool]` | Diálogo de conflito (substituir/manter ambos/ignorar) |
| `resolve_name_conflict(dst_path)` (static) | `Path` | Adiciona sufixo numérico ao nome |

## Funcionalidades

### Context Menu (botão direito)
- **Renomear** (F2) — apenas com 1 item selecionado
- **Excluir** (Del) — com confirmação, suporta multi-seleção
- **Criar Arquivo de Texto** (Ctrl+N) — cria .txt na pasta selecionada
- **Atualizar** (F5) — recarrega árvore
- **Abrir Local no Explorer** — abre Windows Explorer na pasta/arquivo

### Drag & Drop
- **Drag externo**: arquivos podem ser arrastados para QGIS, Windows Explorer (emite `QMimeData` com `urls`)
- **Drop interno**: move arquivos entre pastas com `shutil.move()`
- **Conflito**: diálogo Substituir/Manter ambos/Ignorar quando arquivo já existe
- **Segurança**: não permite mover pasta para dentro de si mesma

### Integração com SaveProjectPlugin
- `FileManagerPlugin` conecta ao sinal `SignalManager.project_changed`
- Quando `SaveProjectPlugin` salva/cria projeto, o explorador recarrega automaticamente
- Lê `root_folder` das `sys_preferences` (chave definida pelo `SaveProjectPlugin`)

## Fluxo de Funcionamento

1. Usuário clica "Gerenciar Projeto" → define `root_folder` nas sys_preferences
2. `SaveProjectPlugin` emite `project_changed` via SignalManager
3. `FileManagerPlugin` (já aberto ou ao abrir) lê `root_folder` e exibe na árvore
4. Usuário pode renomear, excluir, criar arquivos, arrastar e soltar

## Contratos Respeitados

| Contrato | Como |
|---|---|
| **C1** — MessageBox | Todas confirmações usam `MessageBox.show_question` |
| **C2** — Exceções | Todo `except` tem `as e` |
| **C3** — Logger | Log Utils via BasePlugin |
| **C4** — Preferências | `self.sys_preferences` via BasePlugin |
| **C5** — ToolRegistry | Plugin registrado no `ToolRegistry._TOOLS` |
| **C6** — BasePlugin | Herda de BasePlugin |
| **C11** — Widgets | `FileTreeWidget` criado em `resources/widgets/` |
| **C12** — Docs | Esta skill + widgets_skill.md atualizados |