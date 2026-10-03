# -*- coding: utf-8 -*-
"""
HomeTool — Página inicial do Aetheris ToolBox
===============================================
Widget exibido por padrão ao abrir o software.
Apresenta um resumo visual das ferramentas disponíveis
e boas-vindas ao usuário. Exibe partidas de futebol do dia
e dados climáticos lado a lado em painéis, após a conclusão
das pipelines de fetch.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy

from core.enum.ToolKey import ToolKey
from core.model.FootballModel import Fixture
from core.model.WeatherModel import WeatherData
from core.papeline import PipelineRunner
from core.papeline.step import FootballFetchStep
from core.papeline.step.WeatherFetchStep import WeatherFetchStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.FootballMatchWidget import FootballMatchWidget
from resources.widgets.grid.GridCardView import GridCardView
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.ListViewWidget import ListViewWidget
from resources.widgets.SeparatorWidget import SeparatorWidget
from resources.widgets.simple.SimpleLabel import SimpleLabel
from resources.widgets.simple.SimpleThemeButton import SimpleThemeButton
from utils.JsonUtil import JsonUtil


class HomePlugin(BasePlugin):
    """
    Página inicial do Aetheris ToolBox.
    Aberta por padrão ao iniciar o software.
    Executa pipelines de fetching de futebol e clima em background.

    Quando as pipelines terminam, exibe os dados lado a lado:
        - Esquerda: partidas de futebol do dia em GroupPainel com scroll
        - Direita:  dados climáticos em GroupPainel com GridCardView
    """

    def __init__(self, parent=None):
        self._runner = None
        self._matches_container = None
        self._scroll_list = None
        self._weather_runner = None
        self._weather_view = None
        super().__init__(tool_key=ToolKey.HOME.value, parent=parent)

    def _build_ui(self):
        # BasePlugin já cria PluginPage + self.main_layout (QVBoxLayout)
        super()._build_ui()

        # Ajusta margins, spacing e alinhamento para a Home
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(16)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === HEADER ===
        header = SimpleLabel("Aetheris ToolBox")
        header.setObjectName("header_title")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(header)

        subtitle = SimpleLabel("Bem-vindo! Selecione uma ferramenta nas abas acima.")
        subtitle.setObjectName("header_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(subtitle)

        # === SimpleThemeButton (demo do botão autossuficiente) ===
        self._theme_btn = SimpleThemeButton(
            "BOTÃO TEMÁTICO",
            min_width=200,
            min_height=38,
            shadow_enabled=True,
            border_radius=35,
        )
        self._theme_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(self._theme_btn)
        self.main_layout.addLayout(btn_layout)
        print(self._theme_btn.styleSheet()) 
        print(self._theme_btn.style().metaObject().className())# Debug: imprime stylesheet do botão

        # === SEPARATOR ===
        self.main_layout.addWidget(SeparatorWidget(orientation="horizontal"))

        # === SIDE BY SIDE: FOOTBALL | WEATHER ===
        self._side_layout = QHBoxLayout()
        self._side_layout.setSpacing(16)

        # --- Football panel (left) ---
        self._matches_container = GroupPainel("Partidas de Futebol — Hoje")
        self._scroll_list = ListViewWidget(spacing=6, scroll=True)
        self._matches_container.group_layout.addWidget(self._scroll_list)
        self._matches_container.setVisible(False)
        self._side_layout.addWidget(self._matches_container, stretch=2)

        # --- Weather panel (right) ---
        self._weather_panel = GroupPainel("Clima")
        self._weather_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # GridCardView será inserido dentro do group_layout do weather_panel
        self._weather_view = None
        self._weather_panel.setVisible(False)
        self._side_layout.addWidget(self._weather_panel, stretch=1)

        self.main_layout.addLayout(self._side_layout)

        # ── Placeholder ────────────────────────────────────────────
        self._placeholder = SimpleLabel(
            "Utilize as abas do Workspace para acessar\n"
            "as ferramentas disponíveis."
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #888890; font-size: 13px;")
        self.main_layout.addWidget(self._placeholder)

        # Espaçador
        self.main_layout.addStretch(1)

        # ── Start pipelines after UI is ready ─────────────────────
        QTimer.singleShot(500, self._start_football_pipeline)
        QTimer.singleShot(600, self._start_weather_pipeline)

    def _start_football_pipeline(self) -> None:
        """Executa a pipeline de fetch de futebol em background."""
        if self._runner is not None and self._runner.isRunning():
            self.logger.info(
                "Football pipeline já está em execução",
                code="HOME_FOOT_SKIP",
            )
            return

        self._runner = PipelineRunner(
            steps=[FootballFetchStep()],
            tool_key=ToolKey.FOOTBALL_FETCH.value,
        )
        self._runner.finished_ok.connect(self._on_football_done)
        self._runner.failed.connect(self._on_football_error)

        self.logger.info(
            "Iniciando pipeline de fetch de futebol",
            code="HOME_FOOT_START",
        )
        self._runner.start()

    def _on_football_done(self, context) -> None:
        """Callback when football pipeline completes successfully."""
        self.logger.info(
            "Pipeline de futebol concluída com sucesso",
            code="HOME_FOOT_DONE",
        )

        result = context.get_result("football_fetch")
        if not result:
            self.logger.warning(
                "Nenhum resultado na pipeline de futebol",
                code="HOME_FOOT_NO_RESULT",
            )
            return

        today_filtered_path = result.get("today_filtered")
        if not today_filtered_path:
            self.logger.warning(
                "Nenhum arquivo filtrado de hoje encontrado",
                code="HOME_FOOT_NO_FILE",
            )
            return

        self._load_matches(today_filtered_path)

    def _on_football_error(self, error_msg: str) -> None:
        """Callback when football pipeline fails."""
        self.logger.error(
            "Pipeline de futebol falhou",
            code="HOME_FOOT_ERR",
            error=error_msg,
        )

    # ── Weather pipeline ─────────────────────────────────────────────

    def _start_weather_pipeline(self) -> None:
        """Executa pipeline de clima em background."""
        if self._weather_runner is not None and self._weather_runner.isRunning():
            self.logger.info(
                "Weather pipeline já está em execução",
                code="HOME_WEATHER_SKIP",
            )
            return

        self._weather_runner = PipelineRunner(
            steps=[WeatherFetchStep()],
            tool_key=ToolKey.WEATHER_FETCH.value,
        )
        self._weather_runner.finished_ok.connect(self._on_weather_done)
        self._weather_runner.failed.connect(self._on_weather_error)

        self.logger.info(
            "Iniciando pipeline de fetch de clima",
            code="HOME_WEATHER_START",
        )
        self._weather_runner.start()

    def _on_weather_done(self, context) -> None:
        """Callback when weather pipeline completes successfully."""
        self.logger.info(
            "Pipeline de clima concluída com sucesso",
            code="HOME_WEATHER_DONE",
        )

        result = context.get_result("weather_fetch")
        if not result:
            self.logger.warning(
                "Nenhum resultado na pipeline de clima",
                code="HOME_WEATHER_NO_RESULT",
            )
            return

        weather_data = result.get("weather_data")
        if not weather_data:
            self.logger.warning(
                "Nenhum dado climático encontrado",
                code="HOME_WEATHER_NO_DATA",
            )
            return

        self._display_weather(weather_data)

    def _on_weather_error(self, error_msg: str) -> None:
        """Callback when weather pipeline fails."""
        self.logger.error(
            "Pipeline de clima falhou",
            code="HOME_WEATHER_ERR",
            error=error_msg,
        )
        # Exibe card de erro (GridCardView com title próprio) dentro do painel
        error_config = {
            "title": "⚠️ Clima indisponível",
            "items_per_row": 1,
            "cards": [
                {"labels": [
                    {"type": "simple", "text": "Não foi possível carregar os dados climáticos. Verifique sua conexão."},
                ]},
            ],
        }
        self._weather_view = GridCardView(error_config)
        self._weather_panel.group_layout.addWidget(self._weather_view)
        self._weather_panel.setVisible(True)

    def _display_weather(self, data: WeatherData) -> None:
        """Exibe dados climáticos usando GridCardView genérico dentro do weather panel."""
        config = self._build_weather_card_config(data)
        self._weather_view = GridCardView(config)
        self._weather_panel.group_layout.addWidget(self._weather_view)
        self._weather_panel.setVisible(True)

    @staticmethod
    def _build_weather_card_config(data: WeatherData) -> dict:
        """Constrói config do GridCardView a partir dos dados climáticos."""
        return {
            "title": f"{data.location}, {data.region}",
            "items_per_row": 4,
            "cards": [
                {"logo": data.weather_icon, "labels": [
                    {"type": "great_accent", "text": f"{data.temperature}°C"},
                    {"type": "simple", "text": data.weather_desc},
                ]},
                {"labels": [
                    {"type": "simple", "text": "🌅 Nascer"},
                    {"type": "great", "text": data.sunrise},
                ]},
                {"labels": [
                    {"type": "simple", "text": "🌇 Pôr"},
                    {"type": "great", "text": data.sunset},
                ]},
                {"labels": [
                    {"type": "simple_accent", "text": "Qualidade do Ar"},
                    {"type": "great_accent", "text": f"{data.air_index}"},
                ]},
                {"labels": [
                    {"type": "great", "text": f"{data.wind_speed} km/h"},
                    {"type": "simple", "text": f"Vento ({data.wind_dir})"},
                ]},
                {"labels": [
                    {"type": "great", "text": f"{data.humidity}%"},
                    {"type": "simple", "text": "Umidade"},
                ]},
                {"labels": [
                    {"type": "great", "text": f"{data.pressure} hPa"},
                    {"type": "simple", "text": "Pressão"},
                ]},
                {"labels": [
                    {"type": "great", "text": f"{data.precip} mm"},
                    {"type": "simple", "text": "Precipitação"},
                ]},
                {"labels": [
                    {"type": "great", "text": f"{data.cloudcover}%"},
                    {"type": "simple", "text": "Nuvens"},
                ]},
                {"labels": [
                    {"type": "great", "text": f"{data.uv_index}"},
                    {"type": "simple", "text": "UV Index"},
                ]},
                {"labels": [
                    {"type": "great", "text": f"{data.visibility} km"},
                    {"type": "simple", "text": "Visibilidade"},
                ]},
            ],
        }

    # ── Match loading ──────────────────────────────────────────────

    def _load_matches(self, json_path: str) -> None:
        """
        Lê o JSON filtrado, converte para lista de Fixture
        e preenche o ListViewWidget com FootballMatchWidgets.
        """
        try:
            data = JsonUtil.read_json(json_path, tool_key=self.tool_key)
            if not data:
                self.logger.warning(
                    "JSON vazio ou inválido", code="HOME_FOOT_EMPTY",
                )
                return

            fixtures_data = data.get("response", [])
            if not fixtures_data:
                self.logger.info(
                    "Nenhuma partida filtrada encontrada",
                    code="HOME_FOOT_NO_MATCHES",
                )
                return

            fixtures: list[Fixture] = []
            for item in fixtures_data:
                fixture = Fixture.from_api_response(item)
                fixtures.append(fixture)

            self.logger.info(
                "Partidas carregadas",
                code="HOME_FOOT_MATCHES",
                count=len(fixtures),
            )

            self._display_matches(fixtures)

        except Exception as e:
            self.logger.error(
                "Falha ao carregar partidas",
                code="HOME_FOOT_LOAD_ERR",
                error=str(e),
            )

    def _display_matches(self, fixtures: list[Fixture]) -> None:
        """Preenche o scroll list com widgets de partida."""
        if self._scroll_list:
            self._scroll_list.remove_all()

        for fixture in fixtures:
            widget = FootballMatchWidget(fixture)
            self._scroll_list.add_widget(widget)

        self._matches_container.setVisible(True)
        self._placeholder.setVisible(False)