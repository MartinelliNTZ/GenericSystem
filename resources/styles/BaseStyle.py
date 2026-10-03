# -*- coding: utf-8 -*-
"""
BaseStyle — Estilos globais base do sistema
=============================================
Usa o tema atual (`ct` = CurrentTheme do ThemeManager) para gerar
o stylesheet global do Qt que abrange todo o sistema.
Zero valores hardcoded — tudo centralizado no tema via tokens semânticos.
"""

from __future__ import annotations

import math

from PySide6.QtGui import QColor, QLinearGradient, QRadialGradient, QConicalGradient, QBrush, QPen
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from core.enum.GradientType import GradientType
from resources.styles.ThemeManager import theme_manager


class BaseStyle:
    """
    Classe base que gera o stylesheet global usando o tema ativo.
    Não instanciar — usar métodos de classe diretamente.
    """

    @classmethod
    def _gradient(cls, start: str, end: str) -> str:
        """Gera string qlineargradient top-left → bottom-right."""
        return (
            f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {start},stop:1 {end})"
        )

    # ────────────────────────────────────────────────────────────────
    # HELPERS PARA SOMBRA / GLOW PROGRAMÁTICO (QGraphicsDropShadowEffect)
    # ────────────────────────────────────────────────────────────────

    @classmethod
    def apply_drop_shadow(
        cls,
        widget: QWidget,
        blur: int,
        offset_x: int = 0,
        offset_y: int = 0,
        color_rgb: str = "#000000",
        alpha: int = 0,
    ) -> None:
        """
        Aplica um QGraphicsDropShadowEffect no widget usando valores
        numéricos discretos. Se blur == 0 ou alpha == 0, não aplica nada
        (efeito desligado).

        Args:
            widget: Widget alvo.
            blur: Raio de desfoque (px).
            offset_x: Deslocamento horizontal (px).
            offset_y: Deslocamento vertical (px).
            color_rgb: Cor base em hex (ex: "#000000").
            alpha: Canal alfa 0-255. 0 = invisível.
        """
        if blur <= 0 or alpha <= 0:
            return
        color = QColor(color_rgb)
        color.setAlpha(alpha)
        effect = QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(blur)
        effect.setOffset(offset_x, offset_y)
        effect.setColor(color)
        widget.setGraphicsEffect(effect)

    # ────────────────────────────────────────────────────────────────
    # HELPERS PARA GRADIENTE MULTI-STOP COM ÂNGULO
    # ────────────────────────────────────────────────────────────────

    @classmethod
    def _gradient_angle_to_points(cls, angle_deg: int) -> tuple[float, float, float, float]:
        """
        Converte um ângulo em graus para coordenadas (x1,y1,x2,y2)
        no espaço 0..1, simulando a direção do gradiente.

        Ângulos:
            0   → left → right   (x1:0,y1:0 → x2:1,y2:0)
            45  → top-left → bottom-right (padrão)
            90  → top → bottom   (x1:0,y1:0 → x2:0,y2:1)
            180 → right → left   (x1:1,y1:0 → x2:0,y2:0)
        """
        rad = math.radians(angle_deg)
        # Ponto central (0.5, 0.5), raio 0.5
        x1 = 0.5 - 0.5 * math.cos(rad)
        y1 = 0.5 - 0.5 * math.sin(rad)
        x2 = 0.5 + 0.5 * math.cos(rad)
        y2 = 0.5 + 0.5 * math.sin(rad)
        return (x1, y1, x2, y2)

    @classmethod
    def _gradient_qss_from_stops(
        cls,
        stops: tuple,
        angle_deg: int = 45,
        fallback_start: str = "",
        fallback_end: str = "",
        gradient_type: GradientType = GradientType.LINEAR,
        cx: float = 0.5,
        cy: float = 0.5,
        fx: float = 0.5,
        fy: float = 0.5,
        radius: float = 0.5,
    ) -> str:
        """
        Gera string QSS para gradiente a partir de stops, tipo e parâmetros.

        Tipos suportados:
            LINEAR  → qlineargradient(x1,y1,x2,y2, stop:...)
            RADIAL  → qradialgradient(cx,cy,radius,fx,fy, stop:...)

        ⚠ ATENÇÃO: CONICAL (qconicalgradient) NÃO é suportado em QSS.
        Qt Style Sheets aceita apenas qlineargradient e qradialgradient.
        Para gradiente cônico, use _build_conical_gradient() com QPainter
        em paintEvent customizado.

        Se a tupla de stops estiver vazia, usa o fallback de 2 cores
        (comportamento legado, sem mudança visual).

        Args:
            stops: Tupla de (pos_float, cor_hex_str), ordenada por posição.
            angle_deg: Ângulo do gradiente em graus (LINEAR) ou ângulo inicial (CONICAL).
            fallback_start: Cor inicial do fallback (ex: ACCENT_GRADIENT[0]).
            fallback_end: Cor final do fallback (ex: ACCENT_GRADIENT[1]).
            gradient_type: Tipo de gradiente (GradientType.LINEAR/RADIAL).
            cx: Centro X para RADIAL (0.0–1.0).
            cy: Centro Y para RADIAL (0.0–1.0).
            fx: Ponto focal X para RADIAL (0.0–1.0).
            fy: Ponto focal Y para RADIAL (0.0–1.0).
            radius: Raio para RADIAL (0.0–1.0).

        Returns:
            String QSS ``qlineargradient(...)`` ou ``qradialgradient(...)``.
            CONICAL não é suportado em QSS — use _build_conical_gradient().
        """
        if not stops:
            return cls._gradient(fallback_start, fallback_end)

        if gradient_type == GradientType.RADIAL:
            parts = [
                f"qradialgradient("
                f"cx:{cx:.3f},cy:{cy:.3f},"
                f"radius:{radius:.3f},"
                f"fx:{fx:.3f},fy:{fy:.3f}"
            ]
            for pos, color in stops:
                parts.append(f"stop:{pos} {color}")
            return ",".join(parts) + ")"

        elif gradient_type == GradientType.CONICAL:
            parts = [
                f"qconicalgradient("
                f"cx:{cx:.3f},cy:{cy:.3f},"
                f"angle:{angle_deg}"
            ]
            for pos, color in stops:
                parts.append(f"stop:{pos} {color}")
            return ",".join(parts) + ")"

        # LINEAR (padrão)
        x1, y1, x2, y2 = cls._gradient_angle_to_points(angle_deg)
        parts = [f"qlineargradient(x1:{x1:.3f},y1:{y1:.3f},x2:{x2:.3f},y2:{y2:.3f}"]
        for pos, color in stops:
            parts.append(f"stop:{pos} {color}")
        return ",".join(parts) + ")"

    @classmethod
    def _build_radial_gradient(
        cls,
        stops: tuple,
        cx: float = 0.5,
        cy: float = 0.5,
        fx: float = 0.5,
        fy: float = 0.5,
        radius: float = 0.5,
        rect_width: float = 100,
        rect_height: float = 100,
    ) -> QRadialGradient:
        """
        Constrói um QRadialGradient a partir de stops e parâmetros,
        para uso em paintEvent customizado (QPainter).

        Se stops estiver vazio, retorna um gradiente vazio (sem stops)
        — quem chamar deve tratar o fallback.

        Args:
            stops: Tupla de (pos_float, cor_hex_str).
            cx: Centro X (0.0–1.0, relativo à largura).
            cy: Centro Y (0.0–1.0, relativo à altura).
            fx: Ponto focal X (0.0–1.0).
            fy: Ponto focal Y (0.0–1.0).
            radius: Raio (0.0–1.0, relativo à diagonal).
            rect_width: Largura do retângulo alvo.
            rect_height: Altura do retângulo alvo.

        Returns:
            QRadialGradient configurado.
        """
        diag = math.sqrt(rect_width**2 + rect_height**2)
        grad = QRadialGradient(
            cx * rect_width, cy * rect_height,
            radius * diag,
            fx * rect_width, fy * rect_height,
        )
        for pos, color_hex in stops:
            grad.setColorAt(pos, QColor(color_hex))
        return grad

    @classmethod
    def _build_conical_gradient(
        cls,
        stops: tuple,
        cx: float = 0.5,
        cy: float = 0.5,
        angle_deg: float = 0.0,
        rect_width: float = 100,
        rect_height: float = 100,
    ) -> QConicalGradient:
        """
        Constrói um QConicalGradient a partir de stops e parâmetros,
        para uso em paintEvent customizado (QPainter).

        Se stops estiver vazio, retorna um gradiente vazio (sem stops)
        — quem chamar deve tratar o fallback.

        Args:
            stops: Tupla de (pos_float, cor_hex_str).
            cx: Centro X (0.0–1.0).
            cy: Centro Y (0.0–1.0).
            angle_deg: Ângulo inicial em graus.
            rect_width: Largura do retângulo alvo.
            rect_height: Altura do retângulo alvo.

        Returns:
            QConicalGradient configurado.
        """
        grad = QConicalGradient(cx * rect_width, cy * rect_height, angle_deg)
        for pos, color_hex in stops:
            grad.setColorAt(pos, QColor(color_hex))
        return grad

    @classmethod
    def _build_linear_gradient(
        cls,
        stops: tuple,
        angle_deg: int = 45,
        rect_width: float = 100,
        rect_height: float = 100,
    ) -> QLinearGradient:
        """
        Constrói um QLinearGradient a partir de stops e ângulo,
        para uso em paintEvent customizado (QPainter).

        Se stops estiver vazio, retorna um gradiente vazio (sem stops)
        — quem chamar deve tratar o fallback.

        Args:
            stops: Tupla de (pos_float, cor_hex_str).
            angle_deg: Ângulo em graus.
            rect_width: Largura do retângulo alvo (para calcular pontos reais).
            rect_height: Altura do retângulo alvo.

        Returns:
            QLinearGradient configurado.
        """
        x1, y1, x2, y2 = cls._gradient_angle_to_points(angle_deg)
        grad = QLinearGradient(x1 * rect_width, y1 * rect_height,
                               x2 * rect_width, y2 * rect_height)
        for pos, color_hex in stops:
            grad.setColorAt(pos, QColor(color_hex))
        return grad

    # ────────────────────────────────────────────────────────────────
    # HELPER PARA BORDA EM GRADIENTE ("efeito foil")
    # ────────────────────────────────────────────────────────────────

    @classmethod
    def _border_gradient_pen(
        cls,
        stops: tuple,
        width: float = 1.0,
        angle_deg: int = 45,
        rect_width: float = 100,
        rect_height: float = 100,
        fallback_color: str = "",
    ) -> QPen:
        """
        Retorna um QPen com QBrush(QLinearGradient) para desenhar borda
        em gradiente (efeito foil).

        Se stops estiver vazio, retorna uma caneta com cor sólida
        (fallback_color), sem gradiente.

        Args:
            stops: Tupla de (pos_float, cor_hex_str).
            width: Largura da borda.
            angle_deg: Ângulo do gradiente.
            rect_width: Largura do retângulo alvo.
            rect_height: Altura do retângulo alvo.
            fallback_color: Cor sólida de fallback (ex: BORDER_ACCENT).

        Returns:
            QPen configurado.
        """
        if not stops:
            return QPen(QColor(fallback_color), width)

        grad = cls._build_linear_gradient(stops, angle_deg, rect_width, rect_height)
        return QPen(QBrush(grad), width)

    @classmethod
    def global_stylesheet(cls) -> str:
        """Gera o QSS global completo usando o tema atual.
        Nenhuma unidade (px/%) é concatenada aqui — cada token do tema
        já carrega sua própria unidade. Ver convenção no topo de BlueTheme.
        """
        t = theme_manager.theme
        grad_panel = cls._gradient(*t.GRADIENT_PANEL)
        grad_tab = cls._gradient(*t.GRADIENT_TAB)
        grad_input = cls._gradient(*t.GRADIENT_INPUT)
        grad_btn = cls._gradient(*t.GRADIENT_BUTTON)
        return f"""
        QMainWindow, QWidget {{
            background-color: {t.SURFACE_1};
            color: {t.TEXT_MEDIUM};
            font-family: {t.FONT_FAMILY_DEFAULT};
            font-size: {t.FONT_SIZE_NORMAL};
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: {t.SURFACE_1};
            width: {t.SCROLLBAR_WIDTH};
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {t.SURFACE_4};
            border-radius: {t.BORDER_RADIUS_SCROLLBAR};
            min-height: {t.SCROLLBAR_MIN_HEIGHT};
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t.ACCENT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        /* ===== GROUP BOX ===== */
        QGroupBox {{
            background: {grad_panel};
            border: none;
            border-radius: {t.BORDER_RADIUS_CARD};
            margin-top: {t.GROUP_MARGIN_TOP};
            padding: {t.CARD_PADDING_V} {t.CARD_PADDING_H} {t.CARD_PADDING_H} {t.CARD_PADDING_H};
            font-weight: {t.FONT_WEIGHT_BOLD};
        }}
        QGroupBox::title {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            left: {t.GROUP_TITLE_LEFT};
            top: {t.GROUP_TITLE_TOP};
            padding: {t.GROUP_TITLE_PADDING};
            color: {t.ACCENT_TEXT};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.FONT_SIZE_SMALL};
            letter-spacing: {t.GROUP_TITLE_LETTER_SPACING};
            background: transparent;
        }}

        /* ===== LABEL ===== */
        QLabel {{
            background: transparent;
            color: {t.TEXT_MEDIUM};
        }}
        QLabel#header_title {{
            font-size: {t.FONT_SIZE_TITLE};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            color: {t.TEXT_HIGH};
            letter-spacing: {t.LETTER_SPACING_TITLE};
        }}
        QLabel#header_subtitle {{
            font-size: {t.FONT_SIZE_SMALL};
            color: {t.TEXT_LOW};
        }}
        QLabel#section_badge {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
            border-radius: {t.BORDER_RADIUS_BADGE};
            padding: {t.BADGE_PADDING_V} {t.BADGE_PADDING_H};
            font-size: {t.FONT_SIZE_TINY};
            font-weight: {t.FONT_WEIGHT_HEAVY};
            letter-spacing: {t.BADGE_LETTER_SPACING};
        }}

        /* ===== TITLE BAR ===== */
        QWidget#title_bar {{
            background-color: {t.TITLE_BAR};
            border-bottom: 1px solid {t.SURFACE_2};
        }}
        QLabel#window_title {{
            color: {t.TEXT_DISABLED};
            font-size: {t.WINDOW_TITLE_FONT_SIZE};
            font-weight: {t.FONT_WEIGHT_BOLD};
            letter-spacing: {t.WINDOW_TITLE_LETTER_SPACING};
        }}
        QPushButton#title_btn, QPushButton#title_btn_close {{
            background: transparent;
            color: {t.TEXT_DISABLED};
            border: none;
            border-radius: {t.BORDER_RADIUS_TITLE_BTN};
            min-width: {t.TITLE_BTN_WIDTH};
            max-width: {t.TITLE_BTN_WIDTH};
            min-height: {t.TITLE_BTN_HEIGHT};
            max-height: {t.TITLE_BTN_HEIGHT};
            font-size: {t.TITLE_BTN_FONT_SIZE};
        }}
        QPushButton#title_btn:hover {{
            background-color: {t.SURFACE_3};
            color: {t.TEXT_MEDIUM};
        }}
        QPushButton#title_btn_close:hover {{
            background-color: {t.COLOR_DANGER};
            color: {t.TEXT_ON_DANGER};
        }}

        /* ===== APPBAR TOOLBAR ===== */
        QWidget#appbar_toolbar {{
            background: transparent;
        }}
        QPushButton#toolbar_btn {{
            background-color: transparent;
            color: {t.TEXT_LOW};
            border: none;
            border-radius: {t.BORDER_RADIUS_TOOLBAR_BTN};
            padding: {t.TOOLBAR_BTN_PADDING_V} {t.TOOLBAR_BTN_PADDING_H};
            font-size: {t.FONT_SIZE_SMALL};
            font-weight: {t.FONT_WEIGHT_BOLD};
        }}
        QPushButton#toolbar_btn:hover {{
            background-color: {t.SURFACE_3};
            color: {t.ACCENT_TEXT};
        }}

        /* ===== SIDE PANEL (Workspace) ===== */
        QWidget#tool_side_panel {{
            background: {grad_panel};
        }}
        QPushButton#tool_selector_btn {{
            background: {grad_btn};
            color: {t.TEXT_DISABLED};
            border: none;
            border-radius: {t.BORDER_RADIUS_TOOL_SELECTOR};
            padding: {t.TOOL_SELECTOR_PADDING_V} {t.TOOL_SELECTOR_PADDING_H};
            font-size: {t.FONT_SIZE_TINY};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            letter-spacing: {t.TOOL_SELECTOR_LETTER_SPACING};
        }}
        QPushButton#tool_selector_btn:hover {{
            background: {t.SURFACE_2};
            color: {t.ACCENT_TEXT};
        }}
        QPushButton#tool_selector_btn:checked {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
        }}

        /* ===== CONSOLE TOOLBAR ===== */
        QWidget#console_toolbar {{
            background-color: {t.SURFACE_2};
            border-bottom: 1px solid {t.DIVIDER};
        }}
        /* ===== WORKSPACE TABS ===== */
        QTabBar#workspace_tabs {{
            background-color: {t.TITLE_BAR};
            border: none;
            padding: 0;
            font-size: {t.FONT_SIZE_SMALL};
        }}
        QTabBar::tab {{
            background: {grad_tab};
            color: {t.TEXT_LOW};
            border: none;
            padding: 0;
            margin: 0;
            font-weight: {t.FONT_WEIGHT_BOLD};
            font-size: {t.FONT_SIZE_SMALL};
        }}
        QTabBar::tab:hover {{
            background-color: {t.SURFACE_2};
            color: {t.TEXT_MEDIUM};
        }}
        QTabBar::tab:selected {{
            background-color: {t.SURFACE_1};
            color: {t.ACCENT_TEXT};
            border-bottom: 2px solid {t.ACCENT};
        }}

        QTabBar::close-button {{
            image: none;
            width: {t.TAB_CLOSE_BUTTON_SIZE};
            height: {t.TAB_CLOSE_BUTTON_SIZE};
            subcontrol-position: right;
            margin-right: 4px;
            opacity: 0;
        }}
        QTabBar::tab:hover > QTabBar::close-button,
        QTabBar::tab:selected > QTabBar::close-button {{
            opacity: 1;
        }}
        QTabBar::close-button:hover {{
            background-color: {t.COLOR_DANGER};
            border-radius: {t.CLOSE_BUTTON_BORDER_RADIUS};
        }}

        QWidget#workspace_tab {{
            background: transparent;
            border: none;
            padding: 0px;
        }}

        QWidget#vertical_tab {{
            background: transparent;
            border: none;
            padding: 0px;
        }}

        QFrame#workspace_separator, QFrame#separator {{
            background-color: {t.BORDER_DEFAULT};
            border: none;
        }}

        /* ===== SPLITTER ===== */
        QSplitter::handle {{
            background-color: {t.BORDER_DEFAULT};
        }}
        QSplitter::handle:hover {{
            background-color: {t.ACCENT};
        }}
        QSplitter#workspace_splitter::handle {{
            width: {t.SPLITTER_HANDLE_WIDTH};
        }}

        /* ===== LINE EDIT ===== */
        QLineEdit {{
            background: {grad_input};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT};
            padding: {t.INPUT_PADDING_V} {t.INPUT_PADDING_H};
            color: {t.TEXT_MEDIUM};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
        }}
        QLineEdit:focus {{
            background: {t.SURFACE_5};
        }}
        QLineEdit:disabled {{
            background: {t.SURFACE_3};
            color: {t.TEXT_DISABLED};
        }}

        /* ===== SPIN BOX ===== */
        QSpinBox, QDoubleSpinBox {{
            background: {grad_input};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT};
            padding: {t.SPINBOX_PADDING};
            color: {t.TEXT_MEDIUM};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            background: {t.SURFACE_5};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: {t.SPINBOX_BTN_WIDTH};
            background: {t.SURFACE_3};
            border-radius: {t.BORDER_RADIUS_SPINBOX_BTN};
            margin: {t.SPINBOX_BTN_MARGIN};
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: {t.ACCENT};
        }}

        /* ===== COMBO BOX ===== */
        QComboBox {{
            background: {grad_input};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT};
            padding: {t.COMBOBOX_PADDING};
            color: {t.TEXT_MEDIUM};
            min-width: {t.COMBOBOX_MIN_WIDTH};
        }}
        QComboBox:focus {{
            background: {t.SURFACE_5};
        }}
        QComboBox:disabled {{
            background: {t.SURFACE_3};
            color: {t.TEXT_DISABLED};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: {t.COMBOBOX_DROPDOWN_WIDTH};
            border-left: 1px solid {t.SURFACE_4};
            border-top-right-radius: {t.BORDER_RADIUS_INPUT};
            border-bottom-right-radius: {t.BORDER_RADIUS_INPUT};
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: {t.COMBOBOX_ARROW_SIZE} solid transparent;
            border-right: {t.COMBOBOX_ARROW_SIZE} solid transparent;
            border-top: 5px solid {t.TEXT_LOW};
        }}
        QComboBox QAbstractItemView {{
            background: {t.SURFACE_3};
            border: none;
            border-radius: {t.COMBOBOX_POPUP_BORDER_RADIUS};
            color: {t.TEXT_MEDIUM};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
            outline: none;
        }}

        /* ===== CHECK BOX ===== */
        QCheckBox {{
            spacing: {t.CHECKBOX_SPACING};
            background: transparent;
            color: {t.TEXT_MEDIUM};
        }}
        QCheckBox::indicator {{
            width: {t.CHECKBOX_SIZE};
            height: {t.CHECKBOX_SIZE};
            border-radius: {t.BORDER_RADIUS_CHECKBOX};
            background-color: {t.SURFACE_4};
        }}
        QCheckBox::indicator:checked {{
            background-color: {t.ACCENT};
        }}
        QCheckBox::indicator:hover {{
            background-color: {t.SURFACE_5};
        }}

        /* ===== TABLE ===== */
        QTableWidget {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_TABLE};
            gridline-color: {t.DIVIDER};
            color: {t.TEXT_MEDIUM};
        }}
        QTableWidget::item {{
            padding: {t.TABLE_ITEM_PADDING};
        }}
        QTableWidget::item:selected {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
        }}
        QHeaderView::section {{
            background-color: {t.SURFACE_3};
            color: {t.TEXT_LOW};
            padding: {t.HEADER_PADDING};
            border: none;
            border-bottom: 2px solid {t.ACCENT};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.HEADER_FONT_SIZE};
            letter-spacing: {t.HEADER_LETTER_SPACING};
        }}

        /* ===== TEXT BROWSER / TEXT EDIT ===== */
        QTextBrowser, QTextEdit {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_TABLE};
            color: {t.TEXT_MEDIUM};
            font-family: {t.FONT_FAMILY_MONO};
            font-size: {t.TEXT_EDIT_FONT_SIZE};
            padding: {t.TEXT_EDIT_PADDING};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
        }}

        /* ===== PROGRESS BAR ===== */
        QProgressBar {{
            border: none;
            border-radius: {t.BORDER_RADIUS_PROGRESS};
            background-color: {t.SURFACE_2};
            text-align: center;
            color: {t.TEXT_MEDIUM};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.FONT_SIZE_SMALL};
            height: {t.PROGRESS_BAR_HEIGHT};
        }}
        QProgressBar::chunk {{
            border-radius: {t.BORDER_RADIUS_PROGRESS};
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {t.ACCENT_GRADIENT[0]},
                stop:1 {t.ACCENT_GRADIENT[1]}
            );
        }}
        """
        """Gera o QSS global completo usando o tema atual. Sem hardcoded."""
        t = theme_manager.theme
        grad_panel = cls._gradient(*t.GRADIENT_PANEL)
        grad_tab = cls._gradient(*t.GRADIENT_TAB)
        grad_input = cls._gradient(*t.GRADIENT_INPUT)
        grad_btn = cls._gradient(*t.GRADIENT_BUTTON)
        return f"""
        QMainWindow, QWidget {{
            background-color: {t.SURFACE_1};
            color: {t.TEXT_MEDIUM};
            font-family: {t.FONT_FAMILY_DEFAULT};
            font-size: {t.FONT_SIZE_NORMAL}px;
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: {t.SURFACE_1};
            width: {t.SCROLLBAR_WIDTH}px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {t.SURFACE_4};
            border-radius: {t.BORDER_RADIUS_SCROLLBAR}px;
            min-height: {t.SCROLLBAR_MIN_HEIGHT}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t.ACCENT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        /* ===== GROUP BOX ===== */
        QGroupBox {{
            background: {grad_panel};
            border: none;
            border-radius: {t.BORDER_RADIUS_CARD}px;
            margin-top: {t.GROUP_MARGIN_TOP}px;
            padding: {t.CARD_PADDING_V}px {t.CARD_PADDING_H}px {t.CARD_PADDING_H}px {t.CARD_PADDING_H}px;
            font-weight: {t.FONT_WEIGHT_BOLD};
        }}
        QGroupBox::title {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            left: {t.GROUP_TITLE_LEFT}px;
            top: {t.GROUP_TITLE_TOP}px;
            padding: {t.GROUP_TITLE_PADDING};
            color: {t.ACCENT_TEXT};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.FONT_SIZE_SMALL}px;
            letter-spacing: {t.GROUP_TITLE_LETTER_SPACING};
            background: transparent;
        }}

        /* ===== LABEL ===== */
        QLabel {{
            background: transparent;
            color: {t.TEXT_MEDIUM};
        }}
        QLabel#header_title {{
            font-size: {t.FONT_SIZE_TITLE}px;
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            color: {t.TEXT_HIGH};
            letter-spacing: {t.LETTER_SPACING_TITLE};
        }}
        QLabel#header_subtitle {{
            font-size: {t.FONT_SIZE_SMALL}px;
            color: {t.TEXT_LOW};
        }}
        QLabel#section_badge {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
            border-radius: {t.BORDER_RADIUS_BADGE}px;
            padding: {t.BADGE_PADDING_V} {t.BADGE_PADDING_H};
            font-size: {t.FONT_SIZE_TINY}px;
            font-weight: {t.FONT_WEIGHT_HEAVY};
            letter-spacing: {t.BADGE_LETTER_SPACING};
        }}

        /* ===== TITLE BAR ===== */
        QWidget#title_bar {{
            background-color: {t.TITLE_BAR};
            border-bottom: 1px solid {t.SURFACE_2};
        }}
        QLabel#window_title {{
            color: {t.TEXT_DISABLED};
            font-size: {t.WINDOW_TITLE_FONT_SIZE}px;
            font-weight: {t.FONT_WEIGHT_BOLD};
            letter-spacing: {t.WINDOW_TITLE_LETTER_SPACING};
        }}
        QPushButton#title_btn, QPushButton#title_btn_close {{
            background: transparent;
            color: {t.TEXT_DISABLED};
            border: none;
            border-radius: {t.BORDER_RADIUS_TITLE_BTN}px;
            min-width: {t.TITLE_BTN_WIDTH}px;
            max-width: {t.TITLE_BTN_WIDTH}px;
            min-height: {t.TITLE_BTN_HEIGHT}px;
            max-height: {t.TITLE_BTN_HEIGHT}px;
            font-size: {t.TITLE_BTN_FONT_SIZE}px;
        }}
        QPushButton#title_btn:hover {{
            background-color: {t.SURFACE_3};
            color: {t.TEXT_MEDIUM};
        }}
        QPushButton#title_btn_close:hover {{
            background-color: {t.COLOR_DANGER};
            color: {t.TEXT_ON_DANGER};
        }}

        /* ===== APPBAR TOOLBAR ===== */
        QWidget#appbar_toolbar {{
            background: transparent;
        }}
        QPushButton#toolbar_btn {{
            background-color: transparent;
            color: {t.TEXT_LOW};
            border: none;
            border-radius: {t.BORDER_RADIUS_TOOLBAR_BTN}px;
            padding: {t.TOOLBAR_BTN_PADDING_V} {t.TOOLBAR_BTN_PADDING_H};
            font-size: {t.FONT_SIZE_SMALL}px;
            font-weight: {t.FONT_WEIGHT_BOLD};
        }}
        QPushButton#toolbar_btn:hover {{
            background-color: {t.SURFACE_3};
            color: {t.ACCENT_TEXT};
        }}

        /* ===== SIDE PANEL (Workspace) ===== */
        QWidget#tool_side_panel {{
            background: {grad_panel};
        }}
        QPushButton#tool_selector_btn {{
            background: {grad_btn};
            color: {t.TEXT_DISABLED};
            border: none;
            border-radius: {t.BORDER_RADIUS_TOOL_SELECTOR}px;
            padding: {t.TOOL_SELECTOR_PADDING_V} {t.TOOL_SELECTOR_PADDING_H};
            font-size: {t.FONT_SIZE_TINY}px;
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            letter-spacing: {t.TOOL_SELECTOR_LETTER_SPACING};
        }}
        QPushButton#tool_selector_btn:hover {{
            background: {t.SURFACE_2};
            color: {t.ACCENT_TEXT};
        }}
        QPushButton#tool_selector_btn:checked {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
        }}

        /* ===== CONSOLE TOOLBAR ===== */
        QWidget#console_toolbar {{
            background-color: {t.SURFACE_2};
            border-bottom: 1px solid {t.DIVIDER};
        }}
        /* ===== WORKSPACE TABS ===== */
        QTabBar#workspace_tabs {{
            background-color: {t.TITLE_BAR};
            border: none;
            padding: 0;
            font-size: {t.FONT_SIZE_SMALL}px;
        }}
        QTabBar::tab {{
            background: {grad_tab};
            color: {t.TEXT_LOW};
            border: none;
            padding: 0;
            margin: 0;
            font-weight: {t.FONT_WEIGHT_BOLD};
            font-size: {t.FONT_SIZE_SMALL}px;
        }}
        QTabBar::tab:hover {{
            background-color: {t.SURFACE_2};
            color: {t.TEXT_MEDIUM};
        }}
        QTabBar::tab:selected {{
            background-color: {t.SURFACE_1};
            color: {t.ACCENT_TEXT};
            border-bottom: 2px solid {t.ACCENT};
        }}

        QTabBar::close-button {{
            image: none;
            width: {t.TAB_CLOSE_BUTTON_SIZE}px;
            height: {t.TAB_CLOSE_BUTTON_SIZE}px;
            subcontrol-position: right;
            margin-right: 4px;
            opacity: 0;
        }}
        QTabBar::tab:hover > QTabBar::close-button,
        QTabBar::tab:selected > QTabBar::close-button {{
            opacity: 1;
        }}
        QTabBar::close-button:hover {{
            background-color: {t.COLOR_DANGER};
            border-radius: {t.CLOSE_BUTTON_BORDER_RADIUS}px;
        }}

        QWidget#workspace_tab {{
            background: transparent;
            border: none;
            padding: 0px;
        }}

        QWidget#vertical_tab {{
            background: transparent;
            border: none;
            padding: 0px;
        }}

        QFrame#workspace_separator, QFrame#separator {{
            background-color: {t.BORDER_DEFAULT};
            border: none;
        }}

        /* ===== SPLITTER ===== */
        QSplitter::handle {{
            background-color: {t.BORDER_DEFAULT};
        }}
        QSplitter::handle:hover {{
            background-color: {t.ACCENT};
        }}
        QSplitter#workspace_splitter::handle {{
            width: {t.SPLITTER_HANDLE_WIDTH}px;
        }}

        /* ===== LINE EDIT ===== */
        QLineEdit {{
            background: {grad_input};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT}px;
            padding: {t.INPUT_PADDING_V} {t.INPUT_PADDING_H};
            color: {t.TEXT_MEDIUM};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
        }}
        QLineEdit:focus {{
            background: {t.SURFACE_5};
        }}
        QLineEdit:disabled {{
            background: {t.SURFACE_3};
            color: {t.TEXT_DISABLED};
        }}

        /* ===== SPIN BOX ===== */
        QSpinBox, QDoubleSpinBox {{
            background: {grad_input};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT}px;
            padding: {t.SPINBOX_PADDING};
            color: {t.TEXT_MEDIUM};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            background: {t.SURFACE_5};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: {t.SPINBOX_BTN_WIDTH}px;
            background: {t.SURFACE_3};
            border-radius: {t.BORDER_RADIUS_SPINBOX_BTN}px;
            margin: {t.SPINBOX_BTN_MARGIN};
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: {t.ACCENT};
        }}

        /* ===== COMBO BOX ===== */
        QComboBox {{
            background: {grad_input};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT}px;
            padding: {t.COMBOBOX_PADDING};
            color: {t.TEXT_MEDIUM};
            min-width: {t.COMBOBOX_MIN_WIDTH}px;
        }}
        QComboBox:focus {{
            background: {t.SURFACE_5};
        }}
        QComboBox:disabled {{
            background: {t.SURFACE_3};
            color: {t.TEXT_DISABLED};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: {t.COMBOBOX_DROPDOWN_WIDTH}px;
            border-left: 1px solid {t.SURFACE_4};
            border-top-right-radius: {t.BORDER_RADIUS_INPUT}px;
            border-bottom-right-radius: {t.BORDER_RADIUS_INPUT}px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: {t.COMBOBOX_ARROW_SIZE} solid transparent;
            border-right: {t.COMBOBOX_ARROW_SIZE} solid transparent;
            border-top: 5px solid {t.TEXT_LOW};
        }}
        QComboBox QAbstractItemView {{
            background: {t.SURFACE_3};
            border: none;
            border-radius: {t.COMBOBOX_POPUP_BORDER_RADIUS}px;
            color: {t.TEXT_MEDIUM};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
            outline: none;
        }}

        /* ===== CHECK BOX ===== */
        QCheckBox {{
            spacing: {t.CHECKBOX_SPACING}px;
            background: transparent;
            color: {t.TEXT_MEDIUM};
        }}
        QCheckBox::indicator {{
            width: {t.CHECKBOX_SIZE}px;
            height: {t.CHECKBOX_SIZE}px;
            border-radius: {t.BORDER_RADIUS_CHECKBOX}px;
            background-color: {t.SURFACE_4};
        }}
        QCheckBox::indicator:checked {{
            background-color: {t.ACCENT};
        }}
        QCheckBox::indicator:hover {{
            background-color: {t.SURFACE_5};
        }}

        /* ===== TABLE ===== */
        QTableWidget {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_TABLE}px;
            gridline-color: {t.DIVIDER};
            color: {t.TEXT_MEDIUM};
        }}
        QTableWidget::item {{
            padding: {t.TABLE_ITEM_PADDING};
        }}
        QTableWidget::item:selected {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
        }}
        QHeaderView::section {{
            background-color: {t.SURFACE_3};
            color: {t.TEXT_LOW};
            padding: {t.HEADER_PADDING};
            border: none;
            border-bottom: 2px solid {t.ACCENT};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.HEADER_FONT_SIZE}px;
            letter-spacing: {t.HEADER_LETTER_SPACING};
        }}

        /* ===== TEXT BROWSER / TEXT EDIT ===== */
        QTextBrowser, QTextEdit {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_TABLE}px;
            color: {t.TEXT_MEDIUM};
            font-family: {t.FONT_FAMILY_MONO};
            font-size: {t.TEXT_EDIT_FONT_SIZE}px;
            padding: {t.TEXT_EDIT_PADDING};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
        }}

        /* ===== PROGRESS BAR ===== */
        QProgressBar {{
            border: none;
            border-radius: {t.BORDER_RADIUS_PROGRESS}px;
            background-color: {t.SURFACE_2};
            text-align: center;
            color: {t.TEXT_MEDIUM};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.FONT_SIZE_SMALL}px;
            height: {t.PROGRESS_BAR_HEIGHT}px;
        }}
        QProgressBar::chunk {{
            border-radius: {t.BORDER_RADIUS_PROGRESS}px;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {t.ACCENT_GRADIENT[0]},
                stop:1 {t.ACCENT_GRADIENT[1]}
            );
        }}
        """