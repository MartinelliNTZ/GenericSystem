# Plano de ação: integrar o Gerenciador de Estrutura como ferramenta

## Objetivo

Integrar o Gerenciador de Estrutura de Projetos, atualmente implementado em
`org.py`, ao Aetheris ToolBox como uma ferramenta registrada. A integração deve
reaproveitar a infraestrutura existente e deixar uma base de plugin clara para
ferramentas futuras, sem introduzir um segundo framework.

## Diretrizes

- Reutilizar `BasePlugin`, `ToolRegistry`, `ToolKey`, preferências, logging,
  sinais, widgets e utilitários que já existem no projeto.
- Separar o esqueleto reutilizável da lógica própria do Gerenciador de
  Estrutura, sem generalizar componentes antes de haver uma segunda necessidade
  concreta.
- Preservar os comportamentos úteis da ferramenta: descoberta e validação de
  projetos, indicadores de estrutura, estatísticas, filtro, atualização
  automática e ações sobre pastas.
- Escrever e formatar código novo conforme o estilo normal do projeto. A
  formatação atual de `org.py` não deve ser tratada como referência nem
  motivar uma reformatação ampla e não relacionada.
- Manter `org.py` intacto até a migração estar validada. O arquivo está
  atualmente não rastreado pelo Git.

## Fase 1 — Confirmar os contratos e os pontos de integração

1. Conferir as instruções atuais para criação de ferramentas e os contratos
   existentes no repositório.
2. Confirmar o comportamento de `BasePlugin`, incluindo a construção da página,
   persistência de preferências e tratamento do ciclo de vida.
3. Confirmar as opções de categoria e apresentação suportadas por
   `ToolRegistry` e `ToolKey`.
4. Consultar os widgets e utilitários existentes antes de criar componentes
   equivalentes.
5. Corrigir ou esclarecer a referência a `docs/ia/contracts.md` em
   `SKILL_AGENT.md`, caso o arquivo realmente não exista no projeto.

**Saída:** decisões de integração alinhadas aos contratos reais e aos padrões
atuais do código.

## Fase 2 — Definir a estrutura inicial do plugin

Criar um pacote para a ferramenta, por exemplo:

```text
plugins/
└── project_structure_manager/
    ├── __init__.py
    ├── ProjectStructurePlugin.py
    ├── ProjectStructureScanner.py
    └── FolderOperations.py
```

Responsabilidades:

- `ProjectStructurePlugin.py`: interface, árvore, filtros, cards e interação
  com o usuário; herda de `BasePlugin`.
- `ProjectStructureScanner.py`: descoberta de projetos, verificação das
  pastas esperadas e cálculo de estatísticas.
- `FolderOperations.py`: criação, renomeação e mesclagem de pastas, incluindo
  a identificação de conflitos.

Manter essa separação dentro do pacote da ferramenta na primeira versão.
Promover código a `utils/` ou `resources/widgets/` somente quando houver
reutilização comprovada ou quando o componente for genuinamente compartilhado.

## Fase 3 — Migrar a lógica de `org.py`

1. Inventariar as funções, estado e responsabilidades de
   `GerenciadorPastas`.
2. Migrar as regras de filesystem e estatísticas para os componentes de lógica
   da ferramenta, mantendo a interface fora dessas operações.
3. Adaptar a interface para ser uma página do workspace, não uma `QMainWindow`
   independente.
4. Remover da ferramenta a criação própria de `QApplication`, a janela
   principal autônoma e o `main()` que inicia um event loop separado.
5. Preservar atualização assíncrona e debounce do `QFileSystemWatcher`, sem
   acessar widgets Qt de dentro de workers.
6. Tratar erros de filesystem de forma explícita e apresentar resultados e
   falhas ao usuário pelos mecanismos padrão do aplicativo.

## Fase 4 — Configuração e preferências

1. Remover o caminho pessoal embutido em `PASTA_MAE_PADRAO`.
2. Permitir selecionar a pasta-mãe e usar uma opção inicial apropriada caso
   nenhuma preferência tenha sido salva.
3. Implementar `load_prefs()` e `save_prefs()` para persistir pelo menos a
   pasta-mãe escolhida.
4. Persistir estado adicional da árvore somente se isso for útil à experiência
   integrada e puder ser restaurado com segurança.
5. Manter as pastas padrão como configuração específica desta ferramenta, sem
   tratá-las como configuração global sem necessidade.

## Fase 5 — Registro da ferramenta

1. Adicionar uma chave dedicada em `core/enum/ToolKey.py`.
2. Registrar a factory do plugin em `core/config/ToolRegistry.py`.
3. Definir título, tooltip, tipo, categoria e visibilidade na toolbar conforme
   o uso esperado.
4. Confirmar que o plugin usa a mesma chave no registro e em
   `BasePlugin(tool_key=...)`.
5. Verificar que a importação continua lazy e não carrega a ferramenta no
   startup antes de ser aberta.

## Fase 6 — Validação funcional

Testar a ferramenta dentro da aplicação real, com diretórios temporários que
cubram:

- carregamento de projetos válidos e ordenação;
- pastas esperadas presentes, ausentes e incoerentes;
- filtragem e atualização da árvore;
- atualização automática após alterações no filesystem;
- criação e renomeação de pastas;
- mesclagem sem conflitos e com conflitos;
- erros de permissão ou caminhos removidos durante a operação;
- persistência e restauração de preferências;
- funcionamento da interface e dos workers sem travar a thread principal.

## Critérios de conclusão

- A ferramenta está registrada e abre no workspace do Aetheris ToolBox.
- As operações principais de `org.py` continuam disponíveis e são executadas
  com feedback claro.
- A ferramenta não cria uma aplicação ou janela principal paralela.
- As preferências relevantes são persistidas pelo mecanismo existente.
- A lógica de negócio está separada da interface em componentes locais ao
  plugin.
- Nenhuma abstração compartilhada é criada sem uma necessidade demonstrada.
- Os testes relevantes e a verificação de execução na aplicação passam.
- A documentação e o changelog são atualizados conforme os padrões vigentes do
  repositório.

## Fora do escopo inicial

- Reformatação completa de `org.py`.
- Reescrita visual sem relação com a integração.
- Criação de um framework genérico de ferramentas paralelo ao sistema atual.
- Extração prematura de todos os componentes para `utils/` ou
  `resources/widgets/`.
