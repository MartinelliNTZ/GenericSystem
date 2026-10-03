# -*- coding: utf-8 -*-
"""
MessageBox — Gerenciador centralizado de diálogos para o usuário
==================================================================
Centraliza todas as chamadas a QMessageBox, garantindo:
  - Interface consistente em toda a aplicação
  - Nenhum código acessa QMessageBox diretamente
  - Títulos, ícones e textos padronizados
  - Fácil manutenção e customização global

Uso:
    from utils.MessageBox import MessageBox

    # Erro
    MessageBox.show_error("Falha ao carregar arquivo")
    MessageBox.show_error("Falha ao conectar", title="Erro de Rede",
                          detail="Detalhes técnicos...")

    # Informação
    MessageBox.show_info("Operação concluída com sucesso")

    # Aviso
    MessageBox.show_warning("Espaço em disco baixo")

    # Pergunta (retorna True/False)
    if MessageBox.show_question("Deseja salvar as alterações?"):
        ...

    # Pergunta com botões personalizados
    resultado = MessageBox.show_question(
        "O que deseja fazer?",
        title="Salvar?",
        buttons=MessageBox.YES_NO_CANCEL,
    )
    # resultado: QMessageBox.StandardButton.Yes, .No, .Cancel
"""

from __future__ import annotations

import sys
from typing import Any, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from core.config.LogUtils import LogUtils


class MessageBox:
    """
    Classe estática para exibição de diálogos ao usuário.

    Todos os métodos aceitam os seguintes parâmetros nomeados opcionais:
        title      : str   — Título da janela (padrão varia por método)
        detail     : str   — Texto detalhado (seção "Mostrar Detalhes")
        icon       : QMessageBox.Icon — Ícone (padrão varia por método)
        parent     : QWidget — Widget pai (padrão: janela ativa)
        buttons    : QMessageBox.StandardButtons — Botões (padrão: OK)
        default_btn: QMessageBox.StandardButton — Botão padrão (foco)
    """

    # ── Atalhos para botões comuns ──────────────────────────────────
    OK = QMessageBox.StandardButton.Ok
    YES = QMessageBox.StandardButton.Yes
    NO = QMessageBox.StandardButton.No
    CANCEL = QMessageBox.StandardButton.Cancel
    YES_NO = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    YES_NO_CANCEL = (
        QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No
        | QMessageBox.StandardButton.Cancel
    )
    OK_CANCEL = QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel

    # ── Títulos padrão ─────────────────────────────────────────────
    DEFAULT_TITLE_INFO = "Informação"
    DEFAULT_TITLE_WARNING = "Aviso"
    DEFAULT_TITLE_ERROR = "Erro"
    DEFAULT_TITLE_CRITICAL = "Erro Crítico"
    DEFAULT_TITLE_QUESTION = "Confirmação"

    # ═════════════════════════════════════════════════════════════════
    # API Pública
    # ═════════════════════════════════════════════════════════════════

    @staticmethod
    def show_info(
        text: str,
        *,
        title: str = DEFAULT_TITLE_INFO,
        detail: str = "",
        parent: Any = None,
    ) -> None:
        """
        Exibe uma mensagem informativa.

        Parâmetros:
            text  : Mensagem principal a ser exibida
            title : Título da janela (opcional, padrão: "Informação")
            detail: Texto detalhado colapsável (opcional)
            parent: Widget pai (opcional, padrão: janela ativa)
        """
        _show(
            text=text,
            title=title,
            detail=detail,
            icon=QMessageBox.Icon.Information,
            parent=parent,
            buttons=QMessageBox.StandardButton.Ok,
        )

    @staticmethod
    def show_warning(
        text: str,
        *,
        title: str = DEFAULT_TITLE_WARNING,
        detail: str = "",
        parent: Any = None,
    ) -> None:
        """
        Exibe uma mensagem de aviso.

        Parâmetros:
            text  : Mensagem principal
            title : Título da janela (opcional, padrão: "Aviso")
            detail: Texto detalhado colapsável (opcional)
            parent: Widget pai (opcional)
        """
        _show(
            text=text,
            title=title,
            detail=detail,
            icon=QMessageBox.Icon.Warning,
            parent=parent,
            buttons=QMessageBox.StandardButton.Ok,
        )

    @staticmethod
    def show_error(
        text: str,
        *,
        title: str = DEFAULT_TITLE_ERROR,
        detail: str = "",
        parent: Any = None,
    ) -> None:
        """
        Exibe uma mensagem de erro.

        Parâmetros:
            text  : Mensagem principal
            title : Título da janela (opcional, padrão: "Erro")
            detail: Texto detalhado colapsável (opcional)
            parent: Widget pai (opcional)
        """
        _show(
            text=text,
            title=title,
            detail=detail,
            icon=QMessageBox.Icon.Critical,
            parent=parent,
            buttons=QMessageBox.StandardButton.Ok,
        )

    @staticmethod
    def show_critical(
        text: str,
        *,
        title: str = DEFAULT_TITLE_CRITICAL,
        detail: str = "",
        parent: Any = None,
    ) -> None:
        """
        Exibe uma mensagem de erro crítico.

        Parâmetros:
            text  : Mensagem principal
            title : Título da janela (opcional, padrão: "Erro Crítico")
            detail: Texto detalhado colapsável (opcional)
            parent: Widget pai (opcional)
        """
        _show(
            text=text,
            title=title,
            detail=detail,
            icon=QMessageBox.Icon.Critical,
            parent=parent,
            buttons=QMessageBox.StandardButton.Ok,
        )

    @staticmethod
    def show_question(
        text: str,
        *,
        title: str = DEFAULT_TITLE_QUESTION,
        detail: str = "",
        parent: Any = None,
        buttons: QMessageBox.StandardButtons = YES_NO,
        default_button: QMessageBox.StandardButton = YES,
    ) -> QMessageBox.StandardButton:
        """
        Exibe uma pergunta ao usuário.

        Parâmetros:
            text           : Mensagem da pergunta
            title          : Título da janela (opcional, padrão: "Confirmação")
            detail         : Texto detalhado colapsável (opcional)
            parent         : Widget pai (opcional)
            buttons        : Botões exibidos (padrão: Yes | No)
            default_button : Botão com foco padrão (padrão: Yes)

        Retorna:
            QMessageBox.StandardButton pressionado pelo usuário.
            Ex: QMessageBox.StandardButton.Yes, .No, .Cancel
        """
        return _show(
            text=text,
            title=title,
            detail=detail,
            icon=QMessageBox.Icon.Question,
            parent=parent,
            buttons=buttons,
            default_button=default_button,
        )

    # ═════════════════════════════════════════════════════════════════
    # Toast Notification (não-bloqueante)
    # ═════════════════════════════════════════════════════════════════

    @staticmethod
    def show_toast(
        text: str,
        *,
        is_error: bool = False,
        parent: Any = None,
    ) -> None:
        """
        Exibe uma notificação toast temporária (não-bloqueante).
        A mensagem aparece por ~2.5s, faz fade out e se auto-destrói,
        sem travar a UI.

        O import do ToastNotification é lazy para evitar dependência
        circular e garantir que o widget só seja carregado quando usado.

        Args:
            text: Mensagem a exibir.
            is_error: True para estilo vermelho (erro), False para padrão.
            parent: Widget pai (opcional — usa janela ativa se omitido).
        """
        from resources.widgets.ToastNotification import ToastNotification
        ToastNotification.show(text, is_error=is_error, parent=parent)

    # ═════════════════════════════════════════════════════════════════
    # Método genérico (para uso interno ou casos avançados)
    # ═════════════════════════════════════════════════════════════════

    @staticmethod
    def show(
        text: str,
        *,
        title: str = "",
        detail: str = "",
        icon: QMessageBox.Icon = QMessageBox.Icon.NoIcon,
        parent: Any = None,
        buttons: QMessageBox.StandardButtons = QMessageBox.StandardButton.Ok,
        default_button: Optional[QMessageBox.StandardButton] = None,
    ) -> QMessageBox.StandardButton:
        """
        Método genérico para exibir qualquer tipo de mensagem.

        Parâmetros:
            text           : Mensagem principal
            title          : Título da janela
            detail         : Texto detalhado colapsável
            icon           : Ícone (QMessageBox.Icon)
            parent         : Widget pai
            buttons        : Botões exibidos
            default_button : Botão com foco padrão

        Retorna:
            QMessageBox.StandardButton pressionado pelo usuário.
        """
        return _show(
            text=text,
            title=title,
            detail=detail,
            icon=icon,
            parent=parent,
            buttons=buttons,
            default_button=default_button,
        )


# ═══════════════════════════════════════════════════════════════════════
# Função interna de exibição
# ═══════════════════════════════════════════════════════════════════════

def _show(
    text: str,
    title: str,
    detail: str,
    icon: QMessageBox.Icon,
    parent: Any = None,
    buttons: QMessageBox.StandardButtons = QMessageBox.StandardButton.Ok,
    default_button: Optional[QMessageBox.StandardButton] = None,
) -> QMessageBox.StandardButton:
    """
    Constrói e exibe o QMessageBox de forma segura.

    Regras:
      1. Obtém o parent automaticamente se não fornecido
      2. Cria QApplication se não existir (fallback para antes do startup)
      3. Usa QMessageBox.exec() — bloqueante mas seguro
      4. Retorna o botão pressionado
    """
    # ── Garante QApplication ──────────────────────────────────────
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # ── Parent automático ─────────────────────────────────────────
    if parent is None:
        parent = _find_active_window()

    # ── Constrói a mensagem ───────────────────────────────────────
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(str(text))
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(buttons)

    if detail:
        msg_box.setDetailedText(str(detail))

    if default_button is not None:
        msg_box.setDefaultButton(default_button)

    # ── Exibe (bloqueante) ────────────────────────────────────────
    pressed = msg_box.exec()

    # Converte o resultado para StandardButton (compatível PySide6)
    return QMessageBox.StandardButton(pressed)


def _get_logger():
    """Retorna um LogUtils para uso interno do MessageBox."""
    return LogUtils(tool="System", class_name="MessageBox")


def _find_active_window() -> Any:
    """
    Tenta encontrar a janela principal ativa para usar como parent.

    Percorre os topLevelWidgets da QApplication e retorna o primeiro
    que esteja visível e tenha título.
    """
    app = QApplication.instance()
    if app is None:
        return None

    try:
        for widget in app.topLevelWidgets():
            if widget.isVisible() and widget.windowTitle():
                return widget
    except Exception as e:
        _get_logger().error("Falha ao buscar janela ativa", code="FIND_WIN_ERR", error=str(e))

    return None
