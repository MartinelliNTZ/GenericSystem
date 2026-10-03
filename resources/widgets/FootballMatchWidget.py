# -*- coding: utf-8 -*-
"""
FootballMatchWidget — Card de partida de futebol
==================================================
Exibe informações de uma partida: data/hora (Brasília),
campeonato, times com logo, placar, status e local.

Uso:
    from core.model.FootballModel import Fixture
    from resources.widgets.FootballMatchWidget import FootballMatchWidget

    widget = FootballMatchWidget(fixture)
    scrollable_list.add_widget(widget)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import (
    QLabel, QFrame, QHBoxLayout, QVBoxLayout, QSizePolicy,
)

from core.model.FootballModel import Fixture
from resources.styles.AppStyles import AppStyles
from resources.styles.BaseStyle import BaseStyle
from utils.FormatUtils import FormatUtils


class FootballMatchWidget(QFrame):
    """
    Card individual de partida.

    Layout:
        Linha 1: data+ hora BR (esq) | campeonato + rodada (dir)
        Linha 2: [time casa logo + nome] [placar] [time fora logo + nome]
        Linha 3: status (long) | estádio, cidade
    """

    _LOGO_SIZE = 36

    def __init__(self, fixture: Fixture, parent=None):
        super().__init__(parent)
        self._fixture = fixture
        self._setup_ui()
        self._populate()

    # ── UI setup ───────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        current_theme = AppStyles.current_theme
        radius = current_theme.BORDER_RADIUS_CARD

        self.setObjectName("football_match_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

        self.setStyleSheet(
            f"QFrame#football_match_card {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  border: 1px solid {current_theme.BORDER_DEFAULT};"
            f"  border-radius: {radius}px;"
            f"}}"
        )

        # ── Sombra igual ao GridCardView ──────────────────────────
        BaseStyle.apply_drop_shadow(
            self,
            blur=current_theme.SHADOW_BLUR_MD,
            offset_x=0,
            offset_y=current_theme.SHADOW_OFFSET_Y_MD,
            color_rgb=current_theme.SHADOW_COLOR_RGB,
            alpha=current_theme.SHADOW_COLOR_ALPHA,
        )

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 8, 12, 8)
        self._main_layout.setSpacing(6)

        # Row 1: Date + League
        self._header_layout = QHBoxLayout()
        self._header_layout.setSpacing(0)

        self._date_label = QLabel()
        self._date_label.setObjectName("match_date")
        self._date_label.setStyleSheet(
            f"color: {current_theme.TEXT_LOW}; font-size: 11px;"
        )

        self._league_label = QLabel()
        self._league_label.setObjectName("match_league")
        self._league_label.setStyleSheet(
            f"color: {current_theme.TEXT_LOW}; font-size: 11px;"
        )
        self._league_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._header_layout.addWidget(self._date_label)
        self._header_layout.addStretch(1)
        self._header_layout.addWidget(self._league_label)
        self._main_layout.addLayout(self._header_layout)

        # Row 2: Teams + Score
        self._teams_layout = QHBoxLayout()
        self._teams_layout.setSpacing(12)

        # Home team (logo + name + goals)
        self._home_layout = QVBoxLayout()
        self._home_layout.setSpacing(2)
        self._home_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._home_logo = QLabel()
        self._home_logo.setFixedSize(self._LOGO_SIZE, self._LOGO_SIZE)
        self._home_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._home_logo.setStyleSheet("background: transparent;")

        self._home_name = QLabel()
        self._home_name.setObjectName("team_name")
        self._home_name.setStyleSheet(
            f"color: {current_theme.TEXT_HIGH}; font-size: 13px; font-weight: bold;"
        )
        self._home_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._home_goals = QLabel()
        self._home_goals.setObjectName("team_goals")
        self._home_goals.setStyleSheet(
            f"color: {current_theme.ACCENT}; font-size: 18px; font-weight: bold;"
        )
        self._home_goals.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self._home_layout.addWidget(self._home_logo)
        self._home_layout.addWidget(self._home_name)
        self._home_layout.addWidget(self._home_goals)

        # Score separator
        self._score_label = QLabel()
        self._score_label.setObjectName("match_score")
        self._score_label.setStyleSheet(
            f"color: {current_theme.ACCENT}; font-size: 22px; font-weight: bold;"
        )
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._score_label.setFixedWidth(40)

        # Away team (logo + name + goals)
        self._away_layout = QVBoxLayout()
        self._away_layout.setSpacing(2)
        self._away_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._away_logo = QLabel()
        self._away_logo.setFixedSize(self._LOGO_SIZE, self._LOGO_SIZE)
        self._away_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._away_logo.setStyleSheet("background: transparent;")

        self._away_name = QLabel()
        self._away_name.setObjectName("team_name")
        self._away_name.setStyleSheet(
            f"color: {current_theme.TEXT_HIGH}; font-size: 13px; font-weight: bold;"
        )
        self._away_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._away_goals = QLabel()
        self._away_goals.setObjectName("team_goals")
        self._away_goals.setStyleSheet(
            f"color: {current_theme.ACCENT}; font-size: 18px; font-weight: bold;"
        )
        self._away_goals.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self._away_layout.addWidget(self._away_logo)
        self._away_layout.addWidget(self._away_name)
        self._away_layout.addWidget(self._away_goals)

        self._teams_layout.addLayout(self._home_layout)
        self._teams_layout.addWidget(self._score_label)
        self._teams_layout.addLayout(self._away_layout)
        self._main_layout.addLayout(self._teams_layout)

        # Row 3: Status + Venue
        self._footer_layout = QHBoxLayout()
        self._footer_layout.setSpacing(0)

        self._status_label = QLabel()
        self._status_label.setObjectName("match_status")
        self._status_label.setStyleSheet(
            f"color: {current_theme.TEXT_LOW}; font-size: 11px;"
        )

        self._venue_label = QLabel()
        self._venue_label.setObjectName("match_venue")
        self._venue_label.setStyleSheet(
            f"color: {current_theme.TEXT_LOW}; font-size: 11px;"
        )
        self._venue_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self._footer_layout.addWidget(self._status_label)
        self._footer_layout.addStretch(1)
        self._footer_layout.addWidget(self._venue_label)
        self._main_layout.addLayout(self._footer_layout)

    # ── Hover ──────────────────────────────────────────────────────

    def enterEvent(self, event: QEnterEvent) -> None:
        """Ao entrar, destaca a borda com accent e ilumina o fundo."""
        current_theme = AppStyles.current_theme
        radius = current_theme.BORDER_RADIUS_CARD
        self.setStyleSheet(
            f"QFrame#football_match_card {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  border: 1px solid {current_theme.BORDER_ACCENT};"
            f"  border-radius: {radius}px;"
            f"}}"
        )
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Ao sair, restaura a borda e fundo padrão."""
        current_theme = AppStyles.current_theme
        radius = current_theme.BORDER_RADIUS_CARD
        self.setStyleSheet(
            f"QFrame#football_match_card {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  border: 1px solid {current_theme.BORDER_DEFAULT};"
            f"  border-radius: {radius}px;"
            f"}}"
        )
        super().leaveEvent(event)

    # ── Populate data ──────────────────────────────────────────────

    def _populate(self) -> None:
        current_theme = AppStyles.current_theme
        fixture = self._fixture

        # Date/time Brasília
        brasilia = FormatUtils.format_brasilia_date(fixture.date)
        self._date_label.setText(brasilia)

        # League
        league_text = fixture.league.name
        if fixture.league.round:
            league_text += f" — {fixture.league.round}"
        self._league_label.setText(league_text)

        # Teams
        self._home_name.setText(fixture.home_team.name)
        self._away_name.setText(fixture.away_team.name)
        self._load_logo_placeholder(self._home_logo)
        self._load_logo_placeholder(self._away_logo)

        # Score / VS
        has_fulltime = fixture.score.fulltime_home is not None
        has_penalty = fixture.score.penalty_home is not None
        has_result = has_fulltime or has_penalty

        if has_result:
            if has_fulltime and has_penalty:
                home_text = f"{fixture.score.fulltime_home}({fixture.score.penalty_home})"
                away_text = f"{fixture.score.fulltime_away}({fixture.score.penalty_away})"
            elif has_fulltime:
                home_text = str(fixture.score.fulltime_home)
                away_text = str(fixture.score.fulltime_away)
            else:
                home_text = str(fixture.score.penalty_home)
                away_text = str(fixture.score.penalty_away)

            self._home_goals.setText(home_text)
            self._away_goals.setText(away_text)
            self._home_goals.setVisible(True)
            self._away_goals.setVisible(True)
            self._score_label.setText("×")
        else:
            self._home_goals.setVisible(False)
            self._away_goals.setVisible(False)
            self._score_label.setText("VS")

        # Status
        status_text = fixture.status_long or fixture.status or ""
        if "Finished" in status_text:
            self._status_label.setStyleSheet(
                f"color: {current_theme.TEXT_DISABLED}; font-size: 11px;"
            )
        elif fixture.status in {"LIVE", "1H", "2H", "HT", "ET"}:
            self._status_label.setStyleSheet(
                f"color: {current_theme.COLOR_SUCCESS}; font-size: 11px; font-weight: bold;"
            )
        elif fixture.status == "PEN":
            self._status_label.setStyleSheet(
                f"color: {current_theme.ACCENT}; font-size: 11px; font-weight: bold;"
            )
        else:
            self._status_label.setStyleSheet(
                f"color: {current_theme.TEXT_LOW}; font-size: 11px;"
            )
        self._status_label.setText(status_text)

        # Venue
        venue_parts = []
        if fixture.venue:
            venue_parts.append(fixture.venue)
        if fixture.city:
            venue_parts.append(fixture.city)
        text = " — ".join(venue_parts) if venue_parts else ""
        self._venue_label.setText(text)

    # ── Logo placeholder ───────────────────────────────────────────

    @staticmethod
    def _load_logo_placeholder(label: QLabel) -> None:
        """Marca o espaço do logo com um placeholder visual."""
        current_theme = AppStyles.current_theme
        label.setText("")
        label.setStyleSheet(
            f"background-color: {current_theme.SURFACE_4}; "
            f"border-radius: 18px; "
            f"border: 1px solid {current_theme.BORDER_DEFAULT};"
        )

    # ── Properties ─────────────────────────────────────────────────

    @property
    def fixture(self) -> Fixture:
        """Retorna a fixture associada a este widget."""
        return self._fixture