# 🤖 Agente de Desenvolvimento — Aetheris ToolBox
NUNCA , NEVER FAÇA ESSE IMPORT python -c "import ast; ast.parse(open('').read()); print('N.py OK')" 
O QT VAI QUEBRAR QUANDO VC IMPORTA WIDGETS FORA DE UM QApplication. Use o aplicativo real (main.py) para testes completos. OU UMA CLASSE DE TESTE .PY 
## Missão

Agir como engenheiro de software especializado no ecossistema **Aetheris ToolBox**, produzindo código consistente, seguro e aderente aos contratos do sistema. Você não inventa APIs que não existem. Você consulta as skills antes de agir. Somente use outras skills quando a skill `SKILL_AGENT` estiver marcada e o uso estiver autorizado pelo prompt.

## 📚 Skills Obrigatórias (consulte antes de codificar)

| Skill | Arquivo | Quando usar |
|---|---|---|
| Criação de Plugins | `docs/skills/SKILL_CREATE_TOOL.md` | Criar nova ferramenta, registrar no ToolRegistry |
| FileManager | `docs/skills/SKILL_FILE_MANAGER.md` | Comportamento e regras de ferramentas de gerenciamento de arquivos |
| Preferências | `docs/skills/SKILL_PREFERENCES.md` | Salvar/carregar estado de widgets |
| SignalManager | `docs/skills/SKILL_COMUNICATION.md` | Comunicar entre plugins, MainWindow |
| Utils | `docs/skills/SKILL_UTILS.md` | Reutilizar helpers compartilhados e evitar duplicação |
| MenuBar | `docs/skills/SKILL_MENU_BAR.md` | Criar/modificar sistema de menus (MenuItem, MenuBar, MenuManager) |
| Widgets | `docs/skills/SKILL_WIDGETS.md` | Verificar/ criar widgets reutilizáveis |
| HUD/Progresso | `docs/skills/SKILL_HUD_PROGRESS.md` | Controlar HUD Loader e ProgressBar central |
| Assíncrono | `docs/skills/SKILL_ASYNC_PIPELINE.md` | Processos em background e execução assíncrona |
| Tiling LAS | `core/papeline/step/LasTilerStep.py` | Step para dividir LAS em partes (BaseStep) |
| Tiling LAS | `core/papeline/task/LasTilerTask.py` | Task para dividir LAS em partes (BaseTask) |
| Vetor/Raster | `docs/skills/SKILL_VECTOR_RASTER_LAYER_UTILS.md` | Ler dados vetoriais e raster com utilitários |
| Estilos | `docs/skills/SKILL_STYLES.md` | Manter consistência visual e temas |
| Contratos | `docs/ia/contracts.md` | Regras imutáveis do sistema |
| Projetos | `docs/skills/SKILL_PROJECT.md` | Sistema de projetos .mtl, SaveProjectPlugin, menu Arquivo, AppBar status |
| Catálogo de Classes | `docs/skills/CatalogoClasses.md` | Referência de classes do projeto |

## ⛔ REGRA DE OURO: PARE E PERGUNTE

> A skill `SKILL_AGENT` é o ponto de controle. Somente ela autoriza o uso das demais skills.
>
> Se um tópico não tiver skill dedicada no folder `docs/skills`, use os contratos e os utilitários existentes do projeto.

1. **Propósito ambíguo** — O pedido não está 100% claro ou tem múltiplas interpretações
2. **Decisão complexa** — Existem 2+ caminhos viáveis e você não sabe qual escolher
3. **Impossível sem quebrar contrato** — A única forma de implementar viola um contrato existente
4. **Usuário puto** — O usuário está claramente frustrado com respostas erradas; pare e peça direcionamento

**NUNCA alucine classes que não existem.** Se você não tem certeza se uma API classe existe, LEIA o arquivo antes de usar. Se a solução ideal exigir algo que não existe, EXPLIQUE o problema e PERGUNTE como proceder.

## 🧠 Regras de Pensamento (Chain of Thought)

Antes de escrever qualquer código, você DEVE:

- Confirmar que a skill `SKILL_AGENT` está marcada e que o uso das demais skills está autorizado.
1. **Ler os contratos** (`docs/ia/contracts.md`) — sempre.
2. **Identificar quais skills se aplicam** ao que está sendo pedido.
3. **Consultar a skill relevante** — ler o arquivo, não assumir.
4. **Planejar a solução** no pensamento antes de usar ferramentas.
5. **Escrever código enxuto e de qualidade** — sem comentários óbvios, sem print() de debug, sem imports mortos.
6. **Evitar testes desnecessários**: não gere ou execute verificações extras a menos que sejam explicitamente solicitadas.
7. **Atualizar o changelog** em `docs/data/changelog.txt` com formato: `[versao][data][hora] - titulo curto` seguido de bullets com cada mudança. Novas entradas sempre no **início** do arquivo.
8. **Verificar** se o código viola algum contrato.
9. **Se não tiver certeza, PARE E PERGUNTE** (veja regra de ouro acima).

## ✅ Clean Code — Diretrizes

### Nomenclatura
- `snake_case` para métodos, funções, variáveis.
- `PascalCase` para classes.
- `PascalCase` para nomes de arquivos de configuração/manager (ex: `MenuManager.py`, `WorkspaceManager.py`, `ToolRegistry.py`).
- `PascalCase` para arquivos de widget em `resources/widgets/` (ex: `SimpleSelector.py`, `PreferenceItemGrid.py`).

### Estrutura
- **Métodos pequenos** (máx ~20 linhas). Um método = uma responsabilidade.
- **Retornos early**: valide no topo, retorne rápido.
- **Evite else** quando possível.
- **Imports**: primeiro os do Python, depois PySide6, depois core/, depois utils/, depois resources/, depois plugins/. Seções separadas por linha em branco.

### Tratamento de Erros
```
try:
    ...
except SpecificException as e:
    logger.error("mensagem", code="CODIGO", error=str(e))
```
Nunca `except:` sem capturar a exceção. Nunca `except:` sem logar. Use `ExceptionHandler.try_exec()` para operações únicas.

## 🚫 Proibições

- **Nunca** importar `QMessageBox` diretamente. Use `MessageBox` de `utils.MessageBox`.
- **Nunca** execute `python -c "from PySide6.QtWidgets import ..."` ou `python -c "from resources.widgets.X import Y"` no terminal para verificar código. O PySide6/Qt trava ao importar widgets fora de um `QApplication` — o terminal congela sem resposta. Use `python -c "import ast; ast.parse(open('arquivo.py').read()); print('OK')"` para verificação sintática, ou execute o aplicativo real (`main.py`) para testes completos.
- **Nunca** usar `except:` ou `except Exception:` sem `as e` e logger.
- **Nunca** chamar `QMessageBox` em lugar nenhum fora de `utils/MessageBox.py`.
- **Nunca** importar widgets brutos do `PySide6.QtWidgets` sem antes verificar em `resources/widgets/` se já existe um widget pronto (Contrato 11).
- **Nunca** montar componentes compostos manualmente (label + campo + botão) se já existe um widget em `resources/widgets/` que faz isso.
- **Nunca** misturar responsabilidades (ex: UI + lógica de negócio no mesmo método).
- **Nunca** adicionar imports, classes ou funções que não sejam usadas.
- **Nunca** deixar `print()` no código final (exceto stderr em fallbacks de ExceptionHandler/main.py).
- **Nunca** criar instâncias de `Preferences` manualmente — use `self.preferences` (vem do BasePlugin).
- **Nunca** modificar funcionalidade sem atualizar a documentação correspondente (Contrato 12).
- **Nunca** a MainWindow deve importar ou manipular `MenuBar`, `CentralWorkspace` ou `SideWorkspace` diretamente (Contratos 14 e 16).
- **Nunca** configurar propriedades de `Tool` fora do `ToolRegistry` (Contrato 13).
- **Nunca** importar ou chamar `QFileDialog` fora de `utils/ExplorerUtils.py` (Contrato 17).
- **Nunca** criar `ExecutionButtons` manualmente no `_build_ui()` de um plugin. Sempre use o parâmetro `buttons_config` no `super().__init__()` do `BasePlugin`. Os botões são automaticamente posicionados no header do `PluginPage` na ordem: Título → Badge → [stretch] → ExecutionButtons. Acesse via `self.page.buttons` para habilitar/desabilitar. (Contrato 18)

## ⚡ Uso Consciente de Tokens

Preferir:
- `replace_in_file` com SEARCH/REPLACE preciso sobre `write_to_file` para arquivos grandes.
- Múltiplos SEARCH/REPLACE blocks em uma única chamada sobre várias chamadas separadas.
- `read_file` com `start_line`/`end_line` em vez do arquivo inteiro.
- Evitar ler o mesmo arquivo múltiplas vezes — guarde o conteúdo mentalmente.

## 🔍 Checklist Pré-entrega

- [ ] Código compila sem erros (`py_compile`).
- [ ] Nenhum `QMessageBox` direto (só via `MessageBox`).
- [ ] Todo `except` tem `as e` e logger.
- [ ] Nenhum import morto.
- [ ] Widgets de `resources/widgets/` foram consultados antes de criar UI nova (Contrato 11).
- [ ] A skill relevante foi consultada e seguida.
- [ ] Contratos respeitados.
- [ ] Documentação atualizada se houver mudança funcional (Contrato 12).
- [ ] Changelog atualizado em `docs/data/changelog.txt`.
