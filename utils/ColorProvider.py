# -*- coding: utf-8 -*-
"""
ColorProvider — Gerenciador de cores para visualizacao de logs
===============================================================
Fornece cores de fonte para:
- Niveis de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ToolKeys (cores unicas por ferramenta)
- Class names (cores unicas por nome de classe)

Uso:
    from utils.ColorProvider import ColorProvider

    # Cor do nivel
    ColorProvider.level_color("INFO")       # "#10B981"

    # Cor unica para uma tool
    ColorProvider.tool_color("Console")     # cor consistente sempre

    # Cor unica para uma classe
    ColorProvider.class_color("MainWindow") # cor consistente sempre
"""

from __future__ import annotations

from typing import Dict, List

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class ColorProvider(BaseUtil):
    """
    Provedor de cores via hash consistente.
    Para um mesmo nome (tool ou class), a cor e sempre a mesma.
    """

    # ── Cores fixas para niveis de log ──────────────────────────────
    LEVEL_COLORS: Dict[str, str] = {
        "DEBUG": "#9CA3AF",
        "INFO": "#10B981",
        "WARNING": "#F59E0B",
        "ERROR": "#DC2626",
        "CRITICAL": "#991B1B",
    }

    # ── Paletas de cores para tool keys ────────────────────────────
    # Cores vibrantes mas legiveis em fundo escuro
    _TOOL_PALETTE: List[str] = [
        "#F87171",  # vermelho suave
        "#60A5FA",  # azul claro
        "#34D399",  # verde menta
        "#FBBF24",  # amarelo
        "#A78BFA",  # violeta
        "#F472B6",  # rosa
        "#22D3EE",  # ciano
        "#FB923C",  # laranja
        "#E879F9",  # magenta
        "#4ADE80",  # verde lima
    ]

    # ── Paleta para class names ─────────────────────────────────────
    # Cores diferentes das tools para distinguir
    _CLASS_PALETTE: List[str] = [
        "#FDA4AF",  # rosa claro
        "#93C5FD",  # azul bebe
        "#6EE7B7",  # verde agua
        "#FCD34D",  # amarelo claro
        "#C4B5FD",  # lilas
        "#FDBA74",  # pessego
        "#67E8F9",  # ciano claro
        "#D8B4FE",  # violeta claro
        "#A7F3D0",  # verde claro
        "#FCA5A5",  # salmao
    ]

    # ── Paleta para pastas de estrutura de projeto ──────────────────
    # Cores distintas e legíveis em fundo escuro (>= DEFAULT_PROJECT_FOLDERS).
    _FOLDER_PALETTE: List[str] = [
        "#F87171",  # vermelho suave
        "#FB923C",  # laranja
        "#FBBF24",  # amarelo
        "#A3E635",  # lima
        "#4ADE80",  # verde
        "#34D399",  # esmeralda
        "#22D3EE",  # ciano
        "#60A5FA",  # azul
        "#818CF8",  # indigo
        "#A78BFA",  # violeta
        "#E879F9",  # magenta
        "#F472B6",  # rosa
        "#FCA5A5",  # salmao
        "#FCD34D",  # amarelo claro
    ]

    # ── Caches ──────────────────────────────────────────────────────
    _tool_cache: Dict[str, str] = {}
    _class_cache: Dict[str, str] = {}
    _folder_cache: Dict[str, str] = {}

    # ── API ─────────────────────────────────────────────────────────
    @staticmethod
    def rgba(
        hex_color: str,
        alpha: int,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Converte HEX + alpha para rgba().

        Args:
            hex_color: Cor hexadecimal (ex: "#a6784f").
            alpha: Valor alpha (0-255).
            tool_key: Chave da ferramenta para logging.

        Exemplo:
            rgba("#a6784f", 120) -> "rgba(166,120,79,120)"
        """
        logger = BaseUtil._get_logger(tool_key, "ColorProvider")
        clean_color = hex_color.lstrip("#")

        r = int(clean_color[0:2], 16)
        g = int(clean_color[2:4], 16)
        b = int(clean_color[4:6], 16)

        result = f"rgba({r},{g},{b},{alpha})"
        logger.debug("Cor convertida para rgba", code="RGBA_OK", hex=clean_color, alpha=alpha)
        return result

    @classmethod
    def level_color(
        cls,
        log_level: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna a cor hexadecimal para o nivel de log.

        Args:
            log_level: Nivel (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            tool_key: Chave da ferramenta para logging.
        """
        logger = cls._get_logger(tool_key)
        result = cls.LEVEL_COLORS.get(log_level.upper(), "#DCDCDC")
        logger.debug("Cor de nivel obtida", code="LEVEL_COLOR", log_level=log_level, color=result)
        return result

    @classmethod
    def tool_color(
        cls,
        tool_name: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna uma cor unica e consistente para uma tool.

        Args:
            tool_name: Nome da ferramenta (ex: "Console", "Home").
            tool_key: Chave da ferramenta para logging.
        """
        logger = cls._get_logger(tool_key)
        if not tool_name:
            logger.debug("Tool name vazio, retornando cor padrao", code="TOOL_COLOR_EMPTY")
            return "#DCDCDC"

        if tool_name not in cls._tool_cache:
            idx = cls._hash_name(tool_name, len(cls._TOOL_PALETTE))
            cls._tool_cache[tool_name] = cls._TOOL_PALETTE[idx]
            logger.debug("Nova cor de tool gerada", code="TOOL_COLOR_NEW", tool=tool_name, color=cls._tool_cache[tool_name])

        return cls._tool_cache[tool_name]

    @classmethod
    def class_color(
        cls,
        class_name: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna uma cor unica e consistente para uma classe.

        Args:
            class_name: Nome da classe (ex: "MainWindow", "ConsoleTool").
            tool_key: Chave da ferramenta para logging.
        """
        logger = cls._get_logger(tool_key)
        if not class_name:
            logger.debug("Class name vazio, retornando cor padrao", code="CLASS_COLOR_EMPTY")
            return "#DCDCDC"

        if class_name not in cls._class_cache:
            idx = cls._hash_name(class_name, len(cls._CLASS_PALETTE))
            cls._class_cache[class_name] = cls._CLASS_PALETTE[idx]
            logger.debug("Nova cor de classe gerada", code="CLASS_COLOR_NEW", cls=class_name, color=cls._class_cache[class_name])

        return cls._class_cache[class_name]

    @classmethod
    def folder_color(
        cls,
        folder_name: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Retorna uma cor unica e consistente para uma pasta de estrutura.

        As pastas padrao (``DEFAULT_PROJECT_FOLDERS``) recebem cores distintas
        pela posicao na lista; nomes fora do padrao usam hash consistente.

        Args:
            folder_name: Nome da pasta (ex: "05_ASA").
            tool_key: Chave da ferramenta para logging.
        """
        logger = cls._get_logger(tool_key)
        if not folder_name:
            logger.debug(
                "Nome de pasta vazio, retornando cor padrao",
                code="FOLDER_COLOR_EMPTY",
            )
            return "#DCDCDC"

        if folder_name not in cls._folder_cache:
            from utils.ProjectStructureUtil import DEFAULT_PROJECT_FOLDERS

            if folder_name in DEFAULT_PROJECT_FOLDERS:
                idx = DEFAULT_PROJECT_FOLDERS.index(folder_name)
            else:
                idx = cls._hash_name(folder_name, len(cls._FOLDER_PALETTE))
            idx %= len(cls._FOLDER_PALETTE)
            cls._folder_cache[folder_name] = cls._FOLDER_PALETTE[idx]
            logger.debug(
                "Nova cor de pasta gerada",
                code="FOLDER_COLOR_NEW",
                folder=folder_name,
                color=cls._folder_cache[folder_name],
            )

        return cls._folder_cache[folder_name]

    @staticmethod
    def shade(
        hex_color: str,
        factor: float,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Clareia uma cor HEX misturando com branco (factor 0..1).

        Usado para gerar tons mais claros conforme a profundidade na arvore.
        """
        logger = BaseUtil._get_logger(tool_key, "ColorProvider")
        clean = hex_color.lstrip("#")
        factor = max(0.0, min(1.0, factor))

        r = int(clean[0:2], 16)
        g = int(clean[2:4], 16)
        b = int(clean[4:6], 16)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)

        result = f"#{r:02X}{g:02X}{b:02X}"
        logger.debug(
            "Cor clareada gerada",
            code="SHADE_OK",
            base=clean,
            factor=factor,
            color=result,
        )
        return result

    @classmethod
    def text_primary(
        cls,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Cor padrao do texto primario (branco/cinza claro)."""
        _ = cls
        _ = tool_key
        return "#DCDCDC"

    # ── Metodos internos ────────────────────────────────────────────

    @staticmethod
    def _hash_name(name: str, palette_size: int) -> int:
        """
        Gera um indice hash unico para um nome.
        Usa soma dos ordinais + comprimento para distribuir bem.
        """
        if not name:
            return 0

        hash_val = sum(ord(c) for c in name) + len(name) * 7
        return hash_val % palette_size