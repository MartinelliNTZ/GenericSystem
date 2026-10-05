# TODO — Integração do Gerenciador de Estrutura de Projetos

Rastreamento da execução do `plano de acao.md` (integração do `org.py` como
ferramenta registrada no Aetheris ToolBox).

## Fase 1 — Contratos e pontos de integração

- [x] Confirmar instruções de criação de ferramenta (`SKILL_CREATE_TOOL.md`) e contratos (`SKILL_PLUGIN_CONTRACT.md`).
- [x] Confirmar comportamento de `BasePlugin` (página, prefs, ciclo de vida).
- [x] Confirmar opções de `CategoryTool`, `ToolType`, `MenuCategory`.
- [x] Consultar widgets/utilitários existentes antes de criar equivalentes.
- [x] Esclarecer referência a `docs/ia/contracts.md` — o arquivo não existe; os contratos vivem em `docs/skills/SKILL_PLUGIN_CONTRACT.md`.

## Fase 2 — Estrutura inicial do plugin

- [x] Criar pacote `plugins/project_structure_manager/`.
- [x] `ProjectStructureScanner.py` — descoberta de projetos, verificação de pastas esperadas, estatísticas.
- [x] `FolderOperations.py` — criação, renomeação e mesclagem de pastas + conflitos.
- [x] `ProjectStructurePlugin.py` — interface (herda de `BasePlugin`).
- [x] Criar widget reutilizável `resources/widgets/grid/GridTree.py` (Contrato 11).
- [x] Criar widget reutilizável `resources/widgets/simple/SimpleMenuButton.py` (Contrato 11).

## Fase 3 — Migração da lógica de `org.py`

- [x] Inventariar funções/estado de `GerenciadorPastas`.
- [x] Migrar regras de filesystem e estatísticas para os componentes de lógica.
- [x] Adaptar a interface para página do workspace (não `QMainWindow`).
- [x] Remover `QApplication`/janela principal/`main()` próprios.
- [x] Preservar atualização assíncrona + debounce do `QFileSystemWatcher` (sem tocar widgets em workers).
- [x] Tratar erros de filesystem explicitamente e reportar pelos mecanismos padrão.

## Fase 4 — Configuração e preferências

- [x] Remover caminho pessoal embutido (`PASTA_MAE_PADRAO`).
- [x] Permitir selecionar a pasta-mãe (com padrão seguro quando não salvo).
- [x] Implementar `load_prefs()` / `save_prefs()` (pasta-mãe).
- [x] Manter pastas padrão como configuração local da ferramenta.

## Fase 5 — Registro da ferramenta

- [x] Adicionar `ToolKey.PROJECT_STRUCTURE`.
- [x] Registrar factory em `ToolRegistry`.
- [x] Definir título, tooltip, tipo, categoria e visibilidade na toolbar.
- [x] Garantir mesma chave no registro e em `BasePlugin(tool_key=...)`.
- [x] Garantir import lazy (factory por caminho de módulo).

## Fase 6 — Validação

- [x] Verificação sintática (`py_compile`) dos arquivos criados/alterados.
- [x] Conferir que não há `QMessageBox`/`QFileDialog` diretos, imports mortos ou `except` sem log.

## Documentação

- [x] Atualizar `docs/skills/SKILL_WIDGETS.md` (novos widgets).
- [x] Atualizar `docs/data/changelog.txt`.
