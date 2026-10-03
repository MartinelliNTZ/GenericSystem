analise @/EST3.PY e a  partir dele monte um plano de acao para para implementar 1 nova ferramentas
filtro de pontos las
 
quais widgets podem ser reutilizados?
quais widgets podem ser modifificados atender novas demandas?
quais widgets novos podem ser criados
quais bibliotecas novas serao necessarias? (requirements.txt)
Quais classes utils serao ultilizadas na demanda?
Quais dados serao salvos nas preferencias do usuario?
@/docs\skills\widgets_skill.md
 @/docs\skills\utils_skill.md 
 @/docs\skills\signal_communication_skill.md 
 @/docs\skills\create_tool_skill.md 
 @/docs\ia\contracts.md 
 @/docs\ia\agent.md 

FUNCIONALIDADES DA FERRAMENTA:
- FILTRA PONTOS PRETOS EM UMA NUVEM DE PONTOS LAS OU LAZ
- NAO ALTERA O ARQUIVO ORIGINAL, APENAS CRIA UM NOVO ARQUIVO COM OS PONTOS FILTRADOS
- PERMITE SALVAR OS PONTOS PRETOS FILTRADOS EM UM NOVO ARQUIVO LAS OU LAZ (CHECKBOX)
- PERMITE SELECIONAR O NOME DO NOVO ARQUIVO 


- EXIBE O PROGRESSO DO FILTRO DE PONTOS PRETOS (PROGRES BAR DA UIMAIN)
- EXIBE HUDLOADER DURANTE O PROCESSAMENTO DO FILTRO DE PONTOS PRETOS
- EXIBE MENSAGEMS DE LOG E MENSAGEM DE PROGRESSO NO @/plugins\console\ConsolePlugin.py 

OUTPUTS
- NOVO ARQUIVO LAS OU LAZ FILTRADO
- ARQUIVO LAS/LAZ COM OS PONTOS PRETOS FILTRADOS (OPCIONAL)
- MENSAGEMS DE PROGRESSO E LOG NO CONSOLE + MODAL FINAL EXIBINDO SUCESSO E NUMERO DE PONTOS FILTRADOS
