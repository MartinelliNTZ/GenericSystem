# -*- coding: utf-8 -*-
"""
resources/styles — Sistema de estilos e temas do Aetheris ToolBox
=================================================================

Estrutura:
    BaseTheme        : Classe base abstrata com TODAS as variáveis de tema
    DarkCharcoalTheme : Tema concreto (Dark Charcoal + Gold)
    ThemeManager     : Singleton que mantém o tema ativo
    BaseStyle        : Estilos globais Qt usando o tema
    AppStyles        : Herda BaseStyle + botões, badges, logs, menus

Uso exclusivo (fora de resources/styles/):
    from resources.styles.AppStyles import AppStyles
    stylesheet = AppStyles.global_stylesheet()
    button_qss = AppStyles.btn_secondary_style()

Nenhum módulo fora de resources/styles/ pode importar temas diretamente.
"""

from resources.styles.AnimationManager import AnimationManager
from resources.styles.AppStyles import AppStyles
from resources.styles.BaseStyle import BaseStyle
from resources.styles.BaseTheme import BaseTheme
from resources.styles.DarkCharcoalTheme import DarkCharcoalTheme
from resources.styles.ThemeManager import ThemeManager, theme_manager
