# 🛠 Prompt Genérico: Criar Plano de Ação para Nova Ferramenta

## Objetivo

Analise a ferramenta descrita abaixo e monte um **plano de ação detalhado** .MD em docs/plans para implementá-la no **Aetheris ToolBox**, seguindo todas as skills, contratos e padrões do sistema.

O plano de ação deve ser claro, completo e executável. Após validado, a implementação será realizada seguindo cada passo do plano.

---

## 📚 Documentação Obrigatória (Consulte ANTES de planejar)

| Documento | Caminho | Finalidade |
|-----------|---------|------------|
| Skill Criação de Plugins | `@/docs/skills/create_tool_skill.md` | Processo completo de criar e registrar uma ferramenta |
| Contratos do Sistema | `@/docs/ia/contracts.md` | Regras imutáveis (obrigatório ler SEMPRE) |
| Agent Guidelines | `@/docs/ia/agent.md` | Diretrizes do agente de desenvolvimento |
| Skill Widgets | `@/docs/skills/widgets_skill.md` | Catálogo de widgets reutilizáveis (verificar antes de criar UI) |
| Skill Utils | `@/docs/skills/utils_skill.md` | Utilitários compartilhados (ExplorerUtils, MessageBox, JsonUtil, etc.) |
| Skill Signal/Comunicação | `@/docs/skills/signal_communication_skill.md` | SignalManager, ProgressBar, HUD, Console, LogUtils, MessageBox |

---

## 📋 Perguntas que o Plano Deve Responder

1. **Qual ToolKey adicionar ao Enum?** (arquivo `core/enum/ToolKey.py`)
2. **Quais widgets podem ser reutilizados?** (consultar `@/docs/skills/widgets_skill.md`)
3. **Quais widgets existentes podem ser modificados para atender a nova demanda?**
4. **Quais widgets NOVOS precisam ser criados em `resources/widgets/`?**
5. **Qual a estrutura da UI?** (seguindo Contrato 18: Título → Separator → ExecutionButtons → conteúdo)
6. **Quais bibliotecas novas serão necessárias?** (atualizar `requirements.txt`)
7. **Quais classes `utils/` serão utilizadas?** (ExplorerUtils, MessageBox, JsonUtil, FormatUtils, etc.)
8. **Quais dados serão salvos nas preferências do usuário?** (`load_prefs()` / `save_prefs()`)
9. **Como será o registro no ToolRegistry?** (`core/config/ToolRegistry.py` — factory, category, tool_type)
10. **Quais sinais do SignalManager serão usados?** (progress, console, HUD, ciclo de vida)
11. **Qual o fluxo de comunicação entre componentes?** (SignalManager para comunicação inter-plugin)
12. **Quais logs obrigatórios inserir?** (inicialização, início/fim de processo, erros)

---

## 🏗 Estrutura do Plano de Ação

O plano deve ser organizado nos seguintes blocos:

### 1. 📁 Arquivos a Criar
Listar todos os novos arquivos que serão criados e seus propósitos.

### 2. 🔧 Arquivos a Modificar
Listar todos os arquivos existentes que serão alterados e o que muda em cada um.

### 3. 🧱 Estrutura da UI
Descrever a interface do plugin usando a skill de widgets, seguindo:
- `PluginPage` como container base (via `BasePlugin._build_ui()`)
- `ExecutionButtons` para botões de ação (Contrato 18)
- `GroupPainel` / `GridGroupPainel` para agrupar controles
- Widgets específicos do catálogo (`SimpleSelector`, `GridCheckBox`, `GridDoubleSpinBox`, etc.)

### 4. 🔄 Fluxo de Execução
Descrever o pipeline completo desde a interação do usuário até o resultado final:
- Inputs que o usuário fornece
- Processamento (com progresso via SignalManager)
- Outputs gerados
- Mensagens de log e console

### 5. ⚡ Sinais e Comunicação
- `execution_started`, `execution_finished`, `execution_cancelled` — ciclo de vida
- `progress_update` — barra de progresso central
- `hud_show` / `hud_update` / `hud_hide` — HUDLoader
- `console_message` — mensagens no ConsolePlugin
- `self.logger.info/error/warning` — logs estruturados

### 6. 💾 Preferências
Quais configurações do usuário serão persistidas via `load_prefs()` / `save_prefs()`.

### 7. ✅ Checklist de Verificação
Checklist completo baseado no `create_tool_skill.md`:
- [ ] ToolKey adicionado ao Enum
- [ ] Widget herda de `BasePlugin`
- [ ] Implementa `load_prefs()` e `save_prefs()`
- [ ] Registrado no `ToolRegistry` com factory e categoria correta
- [ ] Widgets reutilizáveis consultados (Contrato 11)
- [ ] ExecutionButtons usado para botões de ação (Contrato 18)
- [ ] SignalManager para comunicação (não `QProgressBar` local)
- [ ] Logs obrigatórios inseridos
- [ ] Contratos respeitados (sem `QMessageBox`, sem `QFileDialog`, sem `except:` sem log)
- [ ] Dependências adicionadas ao `requirements.txt`
- [ ] Atualização de documentação se necessário (Contrato 12)

---

## 🎯 Funcionalidades da Ferramenta

*(AQUI VOCÊ DESCREVE AS FUNCIONALIDADES DA NOVA FERRAMENTA)*

- Funcionalidade 1
- Funcionalidade 2
- ...

---

## 📤 Outputs Esperados

*(AQUI VOCÊ LISTA OS OUTPUTS QUE A FERRAMENTA DEVE PRODUZIR)*

- Output 1
- Output 2
- ...

---

## 📥 Inputs Necessários

*(AQUI VOCÊ LISTA OS INPUTS QUE O USUÁRIO DEVE FORNECER)*

- Input 1
- Input 2
- ...

---

## 💡 Observações Adicionais

*(AQUI VOCÊ PODE ADICIONAR INFORMAÇÕES EXTRAS RELEVANTES)*

- Observação 1
- Observação 2
- ...

---

> ⚠️ **Importante:** Gere o plano de ação APENAS após consultar todos os documentos listados. O plano deve ser detalhado o suficiente para ser executado passo a passo sem necessidade de releitura dos documentos de referência.