# Plano: Dois Side Workspaces (Esquerda + Direita)

## Objetivo
Criar um sistema de 2 workspaces laterais: um fixo à esquerda (FileManager) e um fixo à direita (Console). Ferramentas BOTH podem ser movidas entre os dois lados.

## Arquivos a modificar

1. **`core/enum/CategoryTool.py`** — Adicionar `LEFT_SIDE` e `RIGHT_SIDE`
2. **`core/ui/SideWorkspace.py`** — Aceitar parâmetro `side` (`left`/`right`) para posicionar abas no lado correto
3. **`core/config/WorkspaceManager.py`** — Substituir 1 side por 2 sides (left + right) no QSplitter
4. **`core/config/ToolRegistry.py`** — Atualizar categorias: FileManager→LEFT_SIDE, Console→RIGHT_SIDE, BOTH→pode ir para ambos
5. **`docs/ia/agent.md` / `docs/skills/SKILL_PLUGIN_CONTRACT.md`** — Atualizar documentação se necessário

## Passos

- [ ] 1. Modificar CategoryTool com LEFT_SIDE e RIGHT_SIDE
- [ ] 2. Modificar SideWorkspace para aceitar `side` parameter
- [ ] 3. Modificar WorkspaceManager para 3-panel splitter
- [ ] 4. Modificar ToolRegistry com novas categorias
- [ ] 5. Atualizar contratos/documentação
- [ ] 6. Testar compilação