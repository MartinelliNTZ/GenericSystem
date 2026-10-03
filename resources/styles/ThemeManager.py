# -*- coding: utf-8 -*-
"""
ThemeManager — Gerenciador central de temas
=============================================
Mantém a instância única do tema atual.
Qualquer módulo do sistema importa `ct` (current_theme) deste manager
para acessar cores, fontes, dimensões e espaçamentos centralizados.

Uso:
    from resources.styles.ThemeManager import ct
    bg = ct.BG_DARK
    btn_h = ct.BUTTON_HEIGHT

────── COMO ADICIONAR UM NOVO TEMA ────────────────────────────────
1. Crie um arquivo .py em resources/styles/ (ex: MeuTema.py)
   com uma classe que herde de BaseTheme e sobrescreva todos os tokens.

2. Importe a classe neste arquivo e registre o tema no dicionário
   THEMES abaixo, adicionando uma entrada no formato:
       "meu_tema": {
           "module":      "resources.styles.MeuTema",
           "class":       MeuTema,
           "label":       "Meu Tema",
           "description": "Descrição visual do tema",
           "author":      "Seu Nome (opcional)",
           "version":     "1.0.0 (opcional)",
       }

3. Altere CURRENT_THEME_KEY para a chave do novo tema
   (ex: CURRENT_THEME_KEY = "meu_tema").
────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme


THEMES: dict[str, dict] = {
    "blue_theme": {
        "module":      "resources.styles.BlueTheme",
        "label":       "Blue Theme",
        "description": "Tema inspirado no design: "
                       "https://dribbble.com/shots/23707627-Modern-Dashboard-UI-Design. "
                       "Fundo azul-escuro profundo, cards em glassmorphism sutil, "
                       "acento azul elétrico vibrante e texto branco suave.",
    },
    "dark_charcoal": {
        "module":      "resources.styles.DarkCharcoalTheme",
        "label":       "Dark Charcoal",
        "description": "Tema escuro minimalista com detalhes em dourado. "
                       "Profundidade via sombras, fundo preto-azulado e "
                       "acento dourado elegante.",
    },
    "emerald_teal": {
        "module":      "resources.styles.EmeraldTealTheme",
        "label":       "Emerald Teal",
        "description": "Tema escuro esmeralda-teal com gradiente vertical "
                       "3-stop, bordas pill (35px) e sombra 3D preta. "
                       "Inspirado no design de botão gradiente verde.",
    },
    "gold_premium": {
        "module":      "resources.styles.GoldPremiumTheme",
        "label":       "Gold Premium",
        "description": "Tema premium dourado com gradientes multi-stop (5 stops, "
                       "reflexo metálico a 20°), foil borders em gradiente, "
                       "glow estruturado, sombras numéricas discretas, fonte "
                       "display serifada e badge outline habilitado. Demonstra "
                       "todos os novos tokens de estilo premium.",
        "author":      "Aetheris ToolBox",
        "version":     "1.0.0",
    },
    "neon_accent": {
        "module":      "resources.styles.NeonAccentTheme",
        "label":       "Neon Accent",
        "description": "Tema com destaque neon, utilizando cores vibrantes e "
                       "efeitos de brilho para um visual moderno e impactante.",
    },
    "pearl_white": {
        "module":      "resources.styles.PearlWhiteTheme",
        "label":       "Pearl White",
        "description": "Tema claro pérola com detalhes em dourado. "
                       "Oposto do Dark Charcoal: fundos branco/pérola, "
                       "texto escuro e acentos dourados elegantes.",
    },
    "zero_graus": {
        "module":      "resources.styles.ZeroGrausTheme",
        "label":       "Zero Graus",
        "description": "Tema cristalino Ice Glass. Tons azulados profundos, "
                       "brilho frio mbar-azulado e superfícies que "
                       "simulam gelo translúcido.",
    },
}

# ═══════════════════════════════════════════════════════════════════
# TEMA ATIVO — lido dinamicamente das system preferences
# ═══════════════════════════════════════════════════════════════════
# O valor salvo em System > "theme" no preferences.json tem prioridade.
# Se não existir, usa "dark_charcoal" como padrão.
# ═══════════════════════════════════════════════════════════════════

_DEFAULT_THEME_KEY: str = "dark_charcoal"
__CURRENT_THEME_KEY: str | None = None


def _get_current_theme_key() -> str:
    """
    Retorna a chave do tema ativo, lendo de System > "theme"
    nas preferências do sistema.
    """
    global __CURRENT_THEME_KEY
    if __CURRENT_THEME_KEY is not None:
        return __CURRENT_THEME_KEY
    try:
        from utils.Preferences import Preferences
        from core.enum.ToolKey import ToolKey
        sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
        __CURRENT_THEME_KEY = sys_prefs.get("theme", _DEFAULT_THEME_KEY)
    except Exception:
        __CURRENT_THEME_KEY = _DEFAULT_THEME_KEY
    return __CURRENT_THEME_KEY


class ThemeManager:
    """
    Gerenciador singleton de tema.
    Para alternar o tema, mude `CURRENT_THEME_KEY` para a chave
    desejada em THEMES e reinicie (ou recarregue) a UI.
    """

    _instance: ThemeManager | None = None

    def __new__(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._theme = cls._build_theme()
        return cls._instance

    # ── API pública ──────────────────────────────────────────────

    @property
    def theme(self) -> BaseTheme:
        """Retorna a instância do tema atual."""
        return self._theme

    @property
    def current_key(self) -> str:
        """Chave do tema ativo no momento (lida das preferências)."""
        return _get_current_theme_key()

    @property
    def current_info(self) -> dict:
        """Metadados completos do tema ativo."""
        key = _get_current_theme_key()
        return THEMES[key]

    @classmethod
    def available_themes(cls) -> dict[str, dict]:
        """Retorna o dicionário completo de temas registrados (apenas metadados)."""
        return {key: dict(meta) for key, meta in THEMES.items()}

    @staticmethod
    def _load_theme_class(module_path: str) -> type[BaseTheme]:
        """
        Importa dinamicamente o módulo do tema e retorna sua classe.
        Isso evita importar todos os temas no startup — só carrega o necessário.
        """
        mod_name = module_path.replace("/", ".").replace("\\", ".")
        mod = __import__(mod_name, fromlist=["_trash"])
        # Procura a única classe que herda de BaseTheme no módulo
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseTheme) and attr is not BaseTheme:
                return attr
        raise ImportError(
            f"[ThemeManager] Nenhuma subclasse de BaseTheme encontrada "
            f"em '{module_path}'"
        )

    def reload_theme(self) -> None:
        """Recria a instância do tema a partir da chave nas preferências."""
        global __CURRENT_THEME_KEY
        __CURRENT_THEME_KEY = None  # força releitura
        self._theme = self._build_theme()

    # ── Internos ─────────────────────────────────────────────────

    @staticmethod
    def _build_theme() -> BaseTheme:
        """Constrói e retorna a instância do tema apontado pelas preferências."""
        key = _get_current_theme_key()
        entry = THEMES.get(key)
        if entry is None:
            raise KeyError(
                f"[ThemeManager] Chave de tema '{key}' "
                f"não encontrada em THEMES. "
                f"Disponíveis: {list(THEMES.keys())}"
            )
        theme_class = ThemeManager._load_theme_class(entry["module"])
        return theme_class()


# ── Singleton pré-instanciado para importação direta ──────────────
# Uso: from resources.styles.ThemeManager import theme_manager
theme_manager = ThemeManager()
"Instância singleton da thememanager."
