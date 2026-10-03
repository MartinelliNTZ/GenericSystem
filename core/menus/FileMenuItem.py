# -*- coding: utf-8 -*-
"""
FileMenuItem — Aba "Arquivo" da barra de menus
================================================
Itens: Novo, Abrir, Salvar como, Abrir Recente, Sair

Responsabilidades:
    - Novo: Limpa o projeto atual e emite project_changed
    - Abrir: Abre diálogo para selecionar .mtl, carrega nas prefs, emite project_changed
    - Salvar como: Abre diálogo para criar novo .mtl, salva nas prefs, emite project_changed
    - Abrir Recente: Submenu com projetos recentes (active/inactive)
    - Sair: Fecha a aplicação

Uso:
    file_item = FileMenuItem()
    file_item.novo_clicked.connect(minha_funcao)
    file_item.abrir_clicked.connect(minha_funcao)
    file_item.salvar_como_clicked.connect(minha_funcao)
    file_item.recente_clicked.connect(minha_funcao)
    file_item.sair_clicked.connect(minha_funcao)
"""

from __future__ import annotations

from typing import Any, Dict, List

from PySide6.QtCore import Signal

from core.menus.BaseMenuItem import BaseMenuItem
from resources.widgets.RecentProjectsMenu import RecentProjectsMenu
from utils.RecentProjectsManager import RecentProjectsManager


class FileMenuItem(BaseMenuItem):
    """
    Menu "Arquivo" — ações de gerenciamento de projeto.

    Sinais:
        novo_clicked        — emitido quando o usuário clica em "Novo"
        abrir_clicked       — emitido quando o usuário clica em "Abrir"
        salvar_como_clicked — emitido quando o usuário clica em "Salvar como"
        recente_clicked     — emitido quando o usuário clica em um projeto recente (str path)
        sair_clicked        — emitido quando o usuário clica em "Sair"
    """

    novo_clicked = Signal()
    abrir_clicked = Signal()
    salvar_como_clicked = Signal()
    recente_clicked = Signal(str)
    sair_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Arquivo", parent)
        self._recent_manager = RecentProjectsManager()
        self._recent_menu = RecentProjectsMenu(self.parent())
        self._recent_menu.project_clicked.connect(self._on_recente)
        self._build_actions()

    # ── API pública ──────────────────────────────────────────────────

    def refresh_recentes(self) -> None:
        """
        Reconstrói o submenu de recentes lendo do disco.
        Usado na construção inicial do menu.
        """
        recents = self._recent_manager.get_validated()
        self._recent_menu.rebuild(recents)

    def rebuild_recentes_from_signal(self, recents: List[Dict[str, Any]]) -> None:
        """
        Reconstrói o submenu de recentes com dados recebidos via sinal (in-memory).
        Mais rápido que refresh_recentes() porque não lê do disco.

        Args:
            recents: Lista de dicts com chaves path, name, active
        """
        self._recent_menu.rebuild(recents)

    # ── Construção do menu ───────────────────────────────────────────

    def _build_actions(self):
        """Constrói a lista de ações do menu Arquivo."""
        self.add_action(
            text="Novo",
            callback=self._on_novo,
            data="novo",
        )
        self.add_action(
            text="Abrir",
            callback=self._on_abrir,
            data="abrir",
        )
        self.add_action(
            text="Salvar como",
            callback=self._on_salvar_como,
            data="salvar_como",
        )
        self.add_separator()
        # Submenu "Abrir Recente" — já populado no __init__
        self.refresh_recentes()
        self.add_submenu("Abrir Recente", self._recent_menu)
        self.add_separator()
        self.add_action(
            text="Sair",
            callback=self._on_sair,
            data="sair",
        )

    # ── Handlers ────────────────────────────────────────────────────

    def _on_novo(self):
        """Propaga o clique em Novo."""
        self.novo_clicked.emit()

    def _on_abrir(self):
        """Propaga o clique em Abrir."""
        self.abrir_clicked.emit()

    def _on_salvar_como(self):
        """Propaga o clique em Salvar como."""
        self.salvar_como_clicked.emit()

    def _on_recente(self, path: str):
        """Propaga o clique em um projeto recente."""
        self.recente_clicked.emit(path)

    def _on_sair(self):
        """Propaga o clique em Sair."""
        self.sair_clicked.emit()