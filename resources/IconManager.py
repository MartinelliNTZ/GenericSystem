# -*- coding: utf-8 -*-
"""
IconManager — Gerenciador central de ícones do Aetheris ToolBox
=================================================================
Fornece QIcons a partir de nomes de arquivo na pasta resources/icons/.
Como atualmente só existe Aetheris.ico, todas as ferramentas usam
esse mesmo ícone por enquanto.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtGui import QColor, QIcon, QImage, QPixmap


class IconManager:
    """
    Gerenciador central de ícones.

    Cada ferramenta tem seu ícone em resources/icons/ com o mesmo
    nome do ToolKey (ex: LogViewer.ico, Console.ico).
    Se o arquivo não existir, usa o ícone default.

    Uso:
        icon = IconManager.get_tool_icon("LogViewer")
        icon = IconManager.get("LogViewer.ico")
    """

    BASE_PATH = os.path.join(os.path.dirname(__file__), "icons")

    # ── Ícone default (fallback) ──────────────────────────────────────
    DEFAULT = "Aetheris2.ico"

    # ── Métodos ───────────────────────────────────────────────────────

    @classmethod
    def get_tool_icon(cls, tool_name: str) -> QIcon:
        """
        Retorna o QIcon de uma ferramenta pelo seu nome (ToolKey).
        O nome do arquivo é {tool_name}.ico em resources/icons/.
        Ex: get_tool_icon("LogViewer") → resources/icons/LogViewer.ico

        Se o arquivo não existir, retorna o ícone default.
        """
        filename = f"{tool_name}.ico"
        return cls.get(filename)

    @classmethod
    def get(cls, name: str) -> QIcon:
        """
        Retorna um QIcon a partir do nome do arquivo de ícone.
        Se o arquivo não existir, retorna o ícone default (nunca quebra).
        """
        path = cls.path(name)
        return QIcon(path)

    @classmethod
    def path(cls, name: str) -> str:
        """Retorna o caminho completo do arquivo de ícone."""
        full = os.path.join(cls.BASE_PATH, name)
        if os.path.isfile(full):
            return full
        # Fallback para o ícone default
        fallback = os.path.join(cls.BASE_PATH, cls.DEFAULT)
        return fallback if os.path.isfile(fallback) else ""

    @classmethod
    def default_icon(cls) -> QIcon:
        """Retorna o ícone default do sistema."""
        return cls.get(cls.DEFAULT)

    # ── Ícones nativos do sistema (shell) ────────────────────────────

    _system_icons: dict = {}
    _provider = None

    @classmethod
    def system_icon(cls, path: str, is_dir: bool = False) -> QIcon:
        """Retorna o ícone nativo do SO para um arquivo ou pasta.

        Usa ``QFileIconProvider`` (mesma origem dos ícones do Explorer).
        Mantém cache: um único ícone para pastas e um por extensão para
        arquivos, evitando consultas repetidas ao shell. Em falha, recorre
        aos ícones estáticos de ``resources/icons/``.
        """
        key = "dir" if is_dir else os.path.splitext(str(path))[1].lower()
        cached = cls._system_icons.get(key)
        if cached is not None:
            return cached
        icon = cls._build_system_icon(path, is_dir)
        cls._system_icons[key] = icon
        return icon

    @classmethod
    def _build_system_icon(cls, path: str, is_dir: bool) -> QIcon:
        """Cria o ícone nativo via shell (fallback estático em falha)."""
        try:
            from PySide6.QtCore import QFileInfo
            from PySide6.QtWidgets import QFileIconProvider

            if cls._provider is None:
                cls._provider = QFileIconProvider()
            if is_dir:
                icon_type = getattr(QFileIconProvider, "IconType", None)
                icon = cls._provider.icon(
                    icon_type.Folder if icon_type is not None
                    else QFileInfo(str(path))
                )
            else:
                icon = cls._provider.icon(QFileInfo(str(path)))
            if not icon.isNull():
                return icon
        except Exception as e:
            from core.config.LogUtils import LogUtils

            LogUtils(tool="System", class_name="IconManager").warning(
                f"Nao foi possivel obter icone do sistema: {path}",
                code="ICON_SYS_ERR",
                error=str(e),
            )
        return cls.get("folder.ico" if is_dir else "file1.ico")

    # ── Ícones de pasta coloridos (tint do ícone nativo) ─────────────

    _folder_icon_cache: dict = {}

    @classmethod
    def folder_icon(cls, color: str, size: int = 16) -> QIcon:
        """Ícone de pasta nativo tingido com ``color`` (sombreado preservado).

        Parte do ícone nativo de pasta e aplica um tint por luminância,
        mantendo o sombreado 3D. O resultado é cacheado por (cor, tamanho).
        """
        key = (str(color).lower(), int(size))
        cached = cls._folder_icon_cache.get(key)
        if cached is not None:
            return cached
        base = cls.system_icon("", is_dir=True)
        icon = cls.colorized(base, color, size)
        cls._folder_icon_cache[key] = icon
        return icon

    @classmethod
    def colorized(cls, icon: QIcon, color: str, size: int = 16) -> QIcon:
        """Retorna ``icon`` tingido com ``color`` no tamanho informado."""
        pixmap = icon.pixmap(int(size), int(size))
        if pixmap.isNull():
            return icon
        return QIcon(cls._tint(pixmap, color))

    @staticmethod
    def _tint(pixmap: QPixmap, color: str) -> QPixmap:
        """Tinge um pixmap: desatura por luminância e multiplica pela cor.

        Preserva o canal alpha, de modo que o sombreado 3D do ícone nativo
        continua visível apenas recolorido.
        """
        target = QColor(color)
        if not target.isValid():
            return pixmap
        image = pixmap.toImage().convertToFormat(
            QImage.Format.Format_ARGB32
        )
        cr, cg, cb = target.red(), target.green(), target.blue()
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = int(image.pixel(x, y))
                alpha = (pixel >> 24) & 0xFF
                if alpha == 0:
                    continue
                r = (pixel >> 16) & 0xFF
                g = (pixel >> 8) & 0xFF
                b = pixel & 0xFF
                lum = (299 * r + 587 * g + 114 * b) // 1000
                nr = (lum * cr) // 255
                ng = (lum * cg) // 255
                nb = (lum * cb) // 255
                image.setPixel(
                    x, y, (alpha << 24) | (nr << 16) | (ng << 8) | nb
                )
        return QPixmap.fromImage(image)
