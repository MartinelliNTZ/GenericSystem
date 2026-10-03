# Skill: Sistema de Projetos (.mtl)

Esta skill descreve o sistema de gerenciamento de projetos do Aetheris ToolBox, incluindo criação, abertura, salvamento, projetos recentes e exibição do status na AppBar.

## Visão Geral

O sistema de projetos usa arquivos `.mtl` (formato JSON) para armazenar metadados do projeto. Cada projeto contém:

```json
{
    "project_name": "MeuProjeto",
    "path": "C:/caminho/para/pasta",
    "created_at": "2026-05-14T20:30:00",
    "last_modified": "2026-05-14T20:30:00",
    "file_path": "C:/caminho/para/pasta/MeuProjeto.mtl"
}
```

## Componentes do Sistema

| Componente | Arquivo | Função |
|---|---|---|
| `ProjectUtil` | `utils/ProjectUtil.py` | Utilitário estático para criar, ler, atualizar arquivos .mtl |
| `SaveProjectPlugin` | `plugins/project_manager/SaveProjectPlugin.py` | Plugin INSTANT para salvar/criar projetos |
| `MenuManager` | `core/config/MenuManager.py` | Lógica de Novo, Abrir, Salvar como, Abrir Recente no menu Arquivo |
| `FileMenuItem` | `core/menus/FileMenuItem.py` | Aba "Arquivo" da barra de menus com ações de projeto |
| `RecentProjectsManager` | `utils/RecentProjectsManager.py` | Gerencia lista de projetos recentes |
| `AppBar` | `resources/widgets/app_bar.py` | Exibe status do projeto ativo na barra de título |
| `Preferences` | `utils/Preferences.py` | Persiste `current_project` e `root_folder` na seção `ToolKey.SYSTEM` |

## Fluxo de Dados

```
Usuário clica "Salvar como" (menu ou plugin)
    → ExplorerUtils.save_file() (diálogo nativo)
    → ProjectUtil.create_project_safe() (cria .mtl com validação)
    → Preferences.save_tool_prefs(ToolKey.SYSTEM, {current_project, root_folder})
    → SignalManager.instance().project_changed.emit()
    → MainWindow._update_appbar_project_status() (atualiza AppBar)
    → FileManager recarrega com nova raiz
```

## ProjectUtil — Utilitário de Projeto

`utils/ProjectUtil.py` fornece métodos estáticos:

### Criar projeto
```python
from utils.ProjectUtil import ProjectUtil

# Cria .mtl (sobrescreve sem perguntar)
result = ProjectUtil.create_project("C:/pasta", "MeuProjeto")

# Cria .mtl com validação (pergunta se já existe)
result = ProjectUtil.create_project_safe("C:/pasta", "MeuProjeto")
# Retorna dict com dados ou None se falhar/cancelar
```

### Ler projeto
```python
data = ProjectUtil.load_project("C:/pasta/MeuProjeto.mtl")
# Retorna dict ou None
```

### Atualizar
```python
# Atualiza last_modified para data/hora atual
result = ProjectUtil.update_last_modified("C:/pasta/MeuProjeto.mtl")

# Atualiza campo específico
result = ProjectUtil.update_field("C:/pasta/MeuProjeto.mtl", "project_name", "NovoNome")
```

### Utilitários
```python
# Obtém root_folder do projeto ativo (das preferências)
root = ProjectUtil.get_root_folder()

# Lista arquivos por extensões na pasta do projeto
files = ProjectUtil.get_files_by_extensions([".las", ".laz"])
# Retorna {nome_arquivo: caminho_completo}
```

## SaveProjectPlugin — Plugin Instantâneo

`plugins/project_manager/SaveProjectPlugin.py` é uma ferramenta do tipo **INSTANT** (não abre aba, executa ação imediata e se auto-destrói).

### Fluxo:
1. Carrega `current_project` das preferências do sistema
2. Se existe e arquivo está no disco → `_handle_save_existing()` (atualiza last_modified)
3. Se não existe → `_handle_create_new()` (abre diálogo "Salvar como")
4. Emite `project_changed` e exibe MessageBox de confirmação
5. Chama `_self_destruct()` (remove o widget)

### Registro no ToolRegistry:
```python
Tool(
    key=ToolKey.SAVE_PROJECT,
    name="Salvar Projeto",
    tool_type=ToolType.PROJECT,
    plugin_class=SaveProjectPlugin,
    show_in_toolbar=True,
    show_in_menu=True,
)
```

## MenuManager — Lógica de Projeto no Menu Arquivo

O `MenuManager` em `core/config/MenuManager.py` gerencia as ações de projeto do menu Arquivo:

### Novo Projeto (`_on_novo`)
```python
# Zera current_project e root_folder nas preferências
Preferences.save_tool_prefs(ToolKey.SYSTEM, {
    "current_project": "",
    "root_folder": "",
})
SignalManager.instance().project_changed.emit()
```

### Abrir Projeto (`_on_abrir`)
```python
# 1. Diálogo nativo para selecionar .mtl
file_path = ExplorerUtils.open_file(title="Abrir projeto", file_filter="Projeto Aetheris (*.mtl)")

# 2. Valida com ProjectUtil.load_project()
project_data = ProjectUtil.load_project(file_path)

# 3. Salva nas preferências
sys_prefs["current_project"] = file_path
sys_prefs["root_folder"] = os.path.dirname(file_path)
Preferences.save_tool_prefs(ToolKey.SYSTEM, sys_prefs)

# 4. Atualiza last_modified
ProjectUtil.update_last_modified(file_path)

# 5. Adiciona aos recentes
self._recent_manager.add_recent(file_path)

# 6. Emite sinais
SignalManager.instance().recent_projects_changed.emit(self._recent_manager.get_validated())
SignalManager.instance().project_changed.emit()
```

### Salvar como (`_on_salvar_como`)
```python
# 1. Diálogo nativo "Salvar como"
file_path = ExplorerUtils.save_file(title="Salvar projeto como", file_filter="Projeto Aetheris (*.mtl)")

# 2. ProjectUtil.create_project_safe() (valida substituição)
result = ProjectUtil.create_project_safe(folder, project_name)

# 3. Salva nas preferências + recentes + emite sinais
Preferences.save_tool_prefs(ToolKey.SYSTEM, {current_project, root_folder})
self._recent_manager.add_recent(result["file_path"])
SignalManager.instance().recent_projects_changed.emit(...)
SignalManager.instance().project_changed.emit()
```

### Abrir Recente (`_on_recente_abrir`)
```python
# 1. Valida se arquivo existe (os.path.isfile)
# 2. Carrega com ProjectUtil.load_project()
# 3. Salva nas preferências
# 4. Atualiza last_modified
# 5. Move ao topo dos recentes (add_recent)
# 6. Emite sinais
```

## FileMenuItem — Aba "Arquivo" da MenuBar

`core/menus/FileMenuItem.py` constrói o menu Arquivo com:

```
Arquivo
├── Novo              → novo_clicked Signal
├── Abrir             → abrir_clicked Signal
├── Salvar como       → salvar_como_clicked Signal
├── ─────────
├── Abrir Recente     → submenu RecentProjectsMenu
│   ├── Projeto1.mtl  (active)
│   ├── Projeto2.mtl  (active)
│   └── Projeto3.mtl  (inactive — cinza)
├── ─────────
└── Sair              → sair_clicked Signal
```

### Sinais emitidos:
- `novo_clicked` → `MenuManager._on_novo()`
- `abrir_clicked` → `MenuManager._on_abrir()`
- `salvar_como_clicked` → `MenuManager._on_salvar_como()`
- `recente_clicked(str path)` → `MenuManager._on_recente_abrir(path)`
- `sair_clicked` → `MenuManager._on_sair()`

### Atualização em tempo real:
O `recent_projects_changed` signal reconstrói o submenu de recentes sem ler do disco:
```python
SignalManager.instance().recent_projects_changed.connect(
    self._file_item.rebuild_recentes_from_signal
)
```

## AppBar — Status do Projeto

A `AppBar` em `resources/widgets/app_bar.py` exibe o projeto ativo ao lado do título da janela.

### Formato de exibição:
- **Com projeto ativo:** `Aetheris ToolBox  -  [project_name] - C:/caminho/para/pasta`
- **Sem projeto:** `Aetheris ToolBox  -  [Não salvo]`

### Métodos:
```python
# Define status com nome e caminho
appbar.set_project_status("MeuProjeto", "C:/pasta/MeuProjeto.mtl")

# Limpa status (exibe [Não salvo])
appbar.clear_project_status()
```

### Atualização automática:
A `MainWindow` conecta-se ao sinal `project_changed` e atualiza a AppBar:
```python
SignalManager.instance().project_changed.connect(self._update_appbar_project_status)
```

O método `_update_appbar_project_status()` lê `current_project` das preferências do sistema, carrega o `.mtl` com `ProjectUtil.load_project()` e chama `appbar.set_project_status()` ou `appbar.clear_project_status()`.

Na inicialização, o status é carregado em `_open_home_on_startup()`:
```python
self._update_appbar_project_status()
```

## Sinal project_changed

O sinal `project_changed` (definido em `SignalCatalog`) é o ponto central de notificação. **Sempre que o projeto ativo mudar**, emita este sinal.

### Quem emite:
- `SaveProjectPlugin._handle_save_existing()` — após salvar
- `SaveProjectPlugin._handle_create_new()` — após criar
- `MenuManager._on_novo()` — após limpar
- `MenuManager._on_abrir()` — após abrir
- `MenuManager._on_salvar_como()` — após salvar como
- `MenuManager._on_recente_abrir()` — após abrir recente

### Quem escuta:
- `MainWindow._update_appbar_project_status()` — atualiza AppBar
- `FileManager` (via WorkspaceManager) — recarrega árvore de arquivos

## Sinal recent_projects_changed

O sinal `recent_projects_changed` (definido em `SignalCatalog`) atualiza o submenu "Abrir Recente" em tempo real.

### Payload:
```python
# Lista de dicts
[
    {"path": "C:/proj/Proj1.mtl", "name": "Proj1", "active": True},
    {"path": "C:/proj/Proj2.mtl", "name": "Proj2", "active": False},  # arquivo não existe mais
]
```

### Quem emite:
- `MenuManager._on_abrir()` — após abrir
- `MenuManager._on_salvar_como()` — após salvar como
- `MenuManager._on_recente_abrir()` — após abrir recente

### Quem escuta:
- `FileMenuItem.rebuild_recentes_from_signal()` — reconstrói submenu

## Regras e Boas Práticas

1. **Sempre use `ExplorerUtils`** para diálogos de arquivo — nunca `QFileDialog` diretamente (Contrato 17).
2. **Sempre use `ProjectUtil`** para manipular arquivos .mtl — não crie JSON manualmente.
3. **Sempre emita `project_changed`** após qualquer alteração no projeto ativo.
4. **Sempre emita `recent_projects_changed`** após adicionar/remover recentes.
5. **Use `RecentProjectsManager`** para gerenciar a lista de recentes — não manipule o JSON diretamente.
6. **O `SaveProjectPlugin` é INSTANT** — não cria aba, executa e se auto-destrói.
7. **A lógica de projeto no menu Arquivo** vive no `MenuManager`, não no `FileMenuItem`.
8. **O status visual do projeto** na AppBar é atualizado via `project_changed` — não atualize manualmente.
9. **Ao criar novo projeto**, sempre zere `current_project` e `root_folder` nas preferências.
10. **Ao abrir/salvar**, sempre atualize `last_modified` via `ProjectUtil.update_last_modified()`.