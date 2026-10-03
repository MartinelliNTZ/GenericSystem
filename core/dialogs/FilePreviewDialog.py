# -*- coding: utf-8 -*-
"""
FilePreviewDialog — Diálogo de pré-visualização de arquivo
============================================================
Exibe abas horizontais customizadas no topo (HorizontalTab) e
um QStackedWidget que troca de conteúdo conforme a aba selecionada.

- Aba "Preview": PreviewPanel que auto-detecta o tipo do arquivo
- Aba "Propriedades": vazia (futuro)

Uso:
    FilePreviewDialog.exec_preview(
        file_path="c:/pasta/arquivo.txt",
        parent=self,
    )
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedWidget

from core.config.LogUtils import LogUtils
from core.dialogs.BaseDialog import BaseDialog
from core.enum.ToolKey import ToolKey
from resources.widgets.DialogPage import DialogPage
from resources.widgets.HorizontalTab import HorizontalTab
from resources.widgets.PreviewPanel import PreviewPanel
from utils.basic_extractor import BasicExtractor
from utils.JsonUtil import JsonUtil

_logger = LogUtils(tool=ToolKey.SYSTEM.value, class_name="FilePreviewDialog")


class FilePreviewDialog(BaseDialog):
    """
    Diálogo modal com HorizontalTab + QStackedWidget + PreviewPanel.

    Args:
        file_path: Caminho completo do arquivo a exibir.
        title: Título opcional da janela.
        parent: Widget pai.
    """

    def __init__(
        self,
        file_path: str,
        title: str = "Pré-Visualização do Arquivo",
        parent=None,
    ):
        self._file_path = file_path
        super().__init__(
            parent=parent,
            title=title,
            modal=True,
        )
        # Layout full-bleed (sem margins) para abas horizontais
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.resize(700, 500)

    def _build_ui(self):
        self.tab_bar = HorizontalTab(closable=False, parent=self)
        self.main_layout.addWidget(self.tab_bar)

        self._stack = QStackedWidget()
        self._stack.setObjectName("file_preview_stack")
        self.main_layout.addWidget(self._stack, 1)

    # ── Conteúdo das abas ───────────────────────────────────────
        self._add_tab("Preview", self._file_path)
        self._add_properties_tab()

        # Conecta sinal de troca de aba
        self.tab_bar.currentChanged.connect(self._on_tab_changed)

        # Ativa primeira aba
        if self.tab_bar.count() > 0:
            self.tab_bar.setCurrentIndex(0)
            QTimer.singleShot(0, lambda: self._on_tab_changed(0))

        # ── Botão fechar ────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(12, 8, 12, 8)
        btn_layout.addStretch()
        btn = QPushButton("Fechar")
        btn.clicked.connect(self.accept)
        btn_layout.addWidget(btn)
        self.main_layout.addLayout(btn_layout)

    def _add_tab(self, title: str, file_path: str | None) -> None:
        """Adiciona uma aba + sua DialogPage no stack."""
        tab_index = self.tab_bar.addTab("")
        self.tab_bar.setTabData(tab_index, title)
        if file_path is not None:
            self.tab_bar.setTabToolTip(tab_index, file_path)

        page = DialogPage(self)
        self._stack.addWidget(page)

        if file_path is not None:
            preview = PreviewPanel(fixed_size=None, parent=self)
            preview.setProperty("file_path", file_path)
            page.add_widget(preview, 1)

    def _add_properties_tab(self) -> None:
        """
        Adiciona aba 'Propriedades' com PropertyInfoWidget.

        Fluxo JSON:
            1. Cria JSON temporário via JsonUtil
            2. Enriquece o JSON com metadados via BasicExtractor.enrich_json
            3. Extrai os campos que precisa do dict retornado
            4. Exibe via PropertyInfoWidget.load_data()
            5. Remove o JSON temporário (cleanup)
        """
        from resources.widgets.PropertyInfoWidget import PropertyInfoWidget

        tab_index = self.tab_bar.addTab("")
        self.tab_bar.setTabData(tab_index, "Propriedades")

        page = DialogPage(self)
        self._stack.addWidget(page)

        self._prop_widget = PropertyInfoWidget(parent=self)
        page.add_widget(self._prop_widget, 1)

        # ── JSON Pipeline ───────────────────────────────────────
        json_path = JsonUtil.create_temp_json()
        enriched = BasicExtractor.enrich_json(json_path, self._file_path)
        if enriched:
            self._prop_widget.load_data(enriched)
            _logger.info(
                "Propriedades carregadas",
                code="PROP_LOADED",
                file=self._file_path,
                fields=list(enriched.keys()),
            )
        else:
            _logger.warning(
                "Arquivo não encontrado para propriedades",
                code="PROP_NO_FILE",
                file=self._file_path,
            )
        JsonUtil.cleanup_temp_json(json_path)

    def _on_tab_changed(self, index: int) -> None:
        """Atualiza a página visível quando a aba muda."""
        page = self._stack.widget(index)
        if page:
            self._stack.setCurrentWidget(page)

        if page:
            preview = page.findChild(PreviewPanel)
            if preview:
                path = preview.property("file_path")
                if path:
                    preview.show_preview(str(path))
                    preview.setProperty("file_path", None)
                    preview.setFocus()

    @staticmethod
    def exec_preview(
        file_path: str,
        title: str = "Pré-Visualização do Arquivo",
        parent=None,
    ) -> None:
        """
        Atalho para criar, executar e descartar o diálogo.

        Args:
            file_path: Caminho completo do arquivo.
            title: Título opcional da janela.
            parent: Widget pai.
        """
        _logger.info(
            "Abrindo preview",
            code="PREVIEW_OPEN",
            file=file_path,
            title=title,
        )
        dlg = FilePreviewDialog(file_path=file_path, title=title, parent=parent)
        dlg.exec()
        _logger.info(
            "Preview finalizado",
            code="PREVIEW_DONE",
            file=file_path,
        )