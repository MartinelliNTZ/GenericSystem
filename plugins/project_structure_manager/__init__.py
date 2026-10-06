# -*- coding: utf-8 -*-
"""Ferramenta Gerenciador de Estrutura de Projetos.

Integra ao Aetheris ToolBox a conferência e padronização da estrutura de
pastas dos projetos (migrado de org.py). Pacote composto por:

- ProjectStructurePlugin : interface (herda de BasePlugin)
- ProjectStructureScanner: descoberta, validação, estatísticas e listagem
                           de conteúdo (subpastas + arquivos)
- FolderOperations       : criação, renomeação, mesclagem de pastas e
                           abertura de caminhos no shell do sistema
"""
