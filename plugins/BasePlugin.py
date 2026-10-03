# -*- coding: utf-8 -*-
"""
BasePlugin — Classe base para todos os plugins do Aetheris ToolBox
====================================================================
Centraliza:
- Logger automático (via LogUtils) — self.logger
- Preferências carregadas do disco — self.preferences
- Métodos load_prefs() / save_prefs() — override nos filhos
- Emissão de tool_opened e tool_closed via SignalManager
- _build_ui() chamado automaticamente no __init__
- load_prefs() chamado automaticamente no __init__
- prompt_force_projection() — fluxo de projeção forçada reaproveitável

Uso:
    from core.model.BasePlugin import BasePlugin

    class ConsoleTool(BasePlugin):
        def __init__(self, parent=None):
            super().__init__(tool_key="Console", parent=parent)

        def _build_ui(self):
            super()._build_ui()
            self.main_layout.addWidget(...)

        def load_prefs(self):
            texto = self.preferences.get("texto", "")

        def save_prefs(self):
            self.preferences["texto"] = self._edit.text()
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from resources.widgets.PluginPage import PluginPage
from utils.Preferences import Preferences
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil


class BasePlugin(QWidget):
    """
    Classe base para todos os plugins (ferramentas) do sistema.

    Ao ser instanciada:
        - Cria PluginPage com título opcional (self.page, self.main_layout)
        - Chama self._build_ui() — override no filho com super()
        - Chama self.load_prefs() — override no filho opcional
        - Emite SignalManager.tool_opened(tool_key, self)

    Atributos:
        self.logger          : LogUtils
        self.preferences     : Dict[str, Any]
        self.sys_preferences : Dict[str, Any] | None
        self.tool_key        : str
        self.statistics      : ProcessStatisticsUtil — monitor de tempo/ETA
        self.main_layout     : QVBoxLayout — layout do PluginPage para addWidget
    """

    def __init__(
        self,
        *,
        tool_key: str,
        parent: QWidget | None = None,
        sys_prefs: bool = False,
        title: str | None = None,
        show_project_path: bool = False,
        buttons_config: dict | None = None,
    ) -> None:
        self._show_project_path = show_project_path
        self._buttons_config = buttons_config
        super().__init__(parent)
        self.tool_key = tool_key
        self._title = title

        self.preferences: Dict[str,
                               Any] = Preferences.load_tool_prefs(tool_key)
        self.sys_preferences: Dict[str, Any] | None = None
        if sys_prefs:
            self.sys_preferences = Preferences.load_tool_prefs(ToolKey.SYSTEM)

        self.logger = LogUtils(
            tool=tool_key, class_name=self.__class__.__name__)

        self.statistics = ProcessStatisticsUtil(tool_key=tool_key)

        self._build_ui()
        self.load_prefs()

        SignalManager.instance().tool_opened.emit(tool_key)

    def _build_ui(self) -> None:
        """
        Constrói a UI base do plugin.

        Cria um QVBoxLayout externo (margins 0) com um PluginPage inside.
        self.main_layout = PluginPage.main_layout (margins 18,10,18,10 / spacing 8).

        Os filhos DEVEM chamar super()._build_ui() antes de adicionar
        widgets em self.main_layout.
        """
        # Layout externo sem margins para ancorar a PluginPage
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.page = PluginPage(self, title=self._title, buttons_config=self._buttons_config)
        self.main_layout = self.page.main_layout
        outer.addWidget(self.page)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.logger.info(
            "Ferramenta sendo fechada — persistindo preferências",
            code="TOOL_CLOSE_SAVE",
            tool_key=self.tool_key,
        )
        self.save_prefs()
        self.force_save_prefs()
        self.logger.info(
            "Preferências persistidas ao fechar",
            code="TOOL_CLOSE_DONE",
            tool_key=self.tool_key,
        )
        SignalManager.instance().tool_closed.emit(self.tool_key)
        super().closeEvent(event)

    def force_save_prefs(self, toolkey=None) -> None:
        """
        Força a persistência imediata das preferências atuais.
        
        ATENÇÃO: Salva no tool_key ou no toolkey passado.
        Se o plugin usa sys_prefs=True, as system preferences (tema, etc.)
        NÃO são salvas aqui. Use:
            Preferences.save_tool_prefs(ToolKey.SYSTEM, self.sys_preferences)
        """
        if toolkey is None:
            toolkey = self.tool_key
        self.logger.info(
            "Forçando salvamento de preferências",
            code="TOOL_FORCE_SAVE",
            tool_key=self.tool_key,
        )
        Preferences.save_tool_prefs(self.tool_key, self.preferences)
        self.logger.info(
            "Preferências forçadas a salvar",
            code="TOOL_FORCE_SAVE_DONE",
            tool_key=toolkey,
        )

    # ── ETA utility ─────────────────────────────────────────────────

    def get_eta_seconds(self) -> float:
        """
        Retorna o tempo total estimado em segundos baseado no historico
        do ProcessStatisticsUtil.

        O plugin deve chamar self.statistics.start() antes para que o ETA
        seja calculado corretamente.

        Returns:
            Segundos totais estimados (min 30s se nao houver historico).
        """
        if hasattr(self, 'statistics') and self.statistics is not None:
            eta = self.statistics.remaining_time
            if eta > 0:
                return eta
            # Fallback se statistics foi iniciado mas nao tem historico
            if self.statistics.usages == 0:
                return 30.0
        return 30.0

    # ══════════════════════════════════════════════════════════════════
    # Output Message — link clicável para pasta de saída
    # ══════════════════════════════════════════════════════════════════

    def output_message(
        self,
        output_path: str,
        label: str = "Pasta de Saída",
        message: str ="Resultado disponível em: ",
    ) -> None:
        """
        Emite console_html com link clicável para a pasta de saída
        no Windows Explorer.

        Uso no callback de sucesso:
            self.output_message(output_dir)

        Args:
            output_path: Caminho da pasta/arquivo de saída.
            label: Texto do link (padrão: "Pasta de Saída").
        """
        from utils.ExplorerUtils import ExplorerUtils

        link_html = ExplorerUtils.format_explorer_link(
            output_path, label=label, tool_key=self.tool_key
        )

        if link_html:
            SignalManager.instance().console_html.emit(
                f"{message} 📂 {link_html}"
            )
        else:
            SignalManager.instance().console_message.emit(
                f"{message} {output_path}"
            )

        self.logger.info(
            "output_message emitido",
            code="OUTPUT_MSG",
            output_path=output_path,
            label=label,
        )

    # ══════════════════════════════════════════════════════════════════
    # Stats Message — N arquivos processados em X segundos
    # ══════════════════════════════════════════════════════════════════

    def stats_message(
        self,
        n_arquivos: int = 0,
        n_processed: int = 0,
        ntype: str = "itens",
    ) -> None:
        """
        Emite console_message com resumo de processamento:
            "N arquivos processados (X pts) em Y.Ys"

        Usa self.statistics para obter o tempo decorrido.
        Deve ser chamado APÓS self.statistics.end().

        Uso no callback de sucesso:
            elapsed = self.statistics.end()
            self.stats_message(n_arquivos=5, n_processed=38705, ntype="pontos")

        Args:
            n_arquivos: Número de arquivos processados.
            n_processed: Quantidade total processada (pontos, feições, etc.).
            ntype: Nome do tipo processado (ex: "pontos", "feições").
        """
        elapsed = self.statistics._last_elapsed
        elapsed_str = f"{elapsed:.1f}s" if elapsed else "—"

        parts = []
        if n_arquivos:
            parts.append(f"{n_arquivos} arquivo(s) processados")
        if n_processed:
            parts.append(f"{n_processed:,} {ntype}")
        parts.append(f"em {elapsed_str}")

        msg = f"{' | '.join(parts)}."
        SignalManager.instance().console_message.emit(msg)

        self.logger.info(
            "stats_message emitido",
            code="STATS_MSG",
            n_arquivos=n_arquivos,
            n_processed=n_processed,
            ntype=ntype,
            elapsed_s=round(elapsed, 1),
        )

    # ══════════════════════════════════════════════════════════════════
    # Success Message — combina stats + output (legado, simplificado)
    # ══════════════════════════════════════════════════════════════════

    def success_message(
        self,
        output_path: str,
        label: str = "Pasta de Saída",
        summary: str = "Operação concluída com sucesso!",
        n_input: int = 0,
        n_output: int = 0,
        n_arquivos: int = 0,
    ) -> None:
        """
        Emite mensagem de sucesso padronizada combinando stats_message
        + output_message + execution_finished + MessageBox.

        Args:
            output_path: Caminho da pasta/arquivo de saída.
            label: Texto do link (padrão: "Pasta de Saída").
            summary: Texto resumo da operação.
            n_input: Quantidade de entrada.
            n_output: Quantidade de saída.
            n_arquivos: Número de arquivos gerados.
        """
        SignalManager.instance().execution_finished.emit(self.tool_key)

        # Stats
        self.stats_message(
            n_arquivos=n_arquivos,
            n_processed=n_output,
            ntype="itens" if not n_output else "pontos" if n_output > 0 else "itens",
        )

        # Output link
        self.output_message(output_path=output_path, label=label)

        # Log + MessageBox
        msg = f"{summary}\n\n"
        if n_input:
            msg += f"Entrada: {n_input:,}\n"
        if n_output:
            msg += f"Saída: {n_output:,}\n"
        if n_arquivos:
            msg += f"Arquivos gerados: {n_arquivos}\n"
        if output_path:
            msg += f"\nPasta:\n{output_path}"

        self.logger.info(
            "success_message emitido",
            code="SUCCESS_MSG",
            output_path=output_path,
            n_input=n_input,
            n_output=n_output,
            n_arquivos=n_arquivos,
        )

    # ══════════════════════════════════════════════════════════════════
    # las_projection — Obtém / força projeção de um arquivo LAS
    # ══════════════════════════════════════════════════════════════════

    def las_projection(
        self,
        las_path: str,
    ) -> Optional[str]:
        """
        Obtém a projeção de um arquivo LAS. Se não detectada, pergunta
        ao usuário se deseja forçar uma projeção (cria .mdata).

        Fluxo:
        1. Tenta detectar CRS automaticamente via LasLayerProjection.get_crs()
        2. Se detectou → retorna "EPSG:XXXX"
        3. Se NÃO detectou → MessageBox perguntando se quer forçar:
            - Sim → abre CrsSearchDialog → salva .mdata → retorna "EPSG:XXXX"
            - Não → retorna None

        Args:
            las_path: Caminho completo do arquivo .las/.laz.

        Returns:
            String "EPSG:XXXX" se há projeção (detectada ou forçada),
            None se não há projeção e o usuário recusou forçar.

        Uso nos plugins:
            crs = self.las_projection(path)
            if crs:
                # tem projeção
            else:
                # sem projeção
        """
        from utils.MessageBox import MessageBox
        from utils.las.LasLayerProjection import LasLayerProjection

        # ── 1. Tenta detectar automaticamente ───────────────────────
        crs = LasLayerProjection.get_crs(las_path, tool_key=self.tool_key)
        if crs:
            self.logger.info(
                "Projeção detectada automaticamente",
                code="LAS_PROJ_AUTO",
                path=las_path,
                crs=crs,
            )
            return crs

        # ── 2. Não detectou — pergunta ao usuário ───────────────────
        self.logger.warning(
            "Projeção não detectada — consultando usuário",
            code="LAS_PROJ_NOT_FOUND",
            path=las_path,
        )

        resposta = MessageBox.show_question(
            (
                "Não foi possível detectar a projeção do arquivo:\n"
                f"{las_path}\n\n"
                "Deseja forçar uma projeção no arquivo?\n\n"
                "Isso criará um arquivo .mdata com a definição de projeção, "
                "mas não modificará o arquivo LAS original."
            ),
            title="Projeção não detectada",
            buttons=MessageBox.YES_NO,
            default_button=MessageBox.YES,
        )

        if resposta != MessageBox.YES:
            self.logger.info(
                "Usuário recusou forçar projeção",
                code="LAS_PROJ_DECLINED",
                path=las_path,
            )
            return None

        # ── 3. Abre CrsSearchDialog para escolher CRS ───────────────
        from resources.widgets.crs.CrsSearchDialog import CrsSearchDialog

        dialog = CrsSearchDialog(parent=self)
        if not dialog.exec():
            self.logger.info(
                "Usuário cancelou a seleção de CRS",
                code="LAS_PROJ_CANCELED",
                path=las_path,
            )
            return None

        epsg_escolhido = dialog.selected_epsg
        if not epsg_escolhido:
            self.logger.warning(
                "Nenhum EPSG selecionado no diálogo",
                code="LAS_PROJ_NO_EPSG",
                path=las_path,
            )
            return None

        # ── 4. Salva .mdata ─────────────────────────────────────────
        salvo = LasLayerProjection.save_mdata(
            las_path=las_path,
            epsg_code=epsg_escolhido,
            tool_key=self.tool_key,
        )

        if salvo:
            self.logger.info(
                "Projeção forçada salva em .mdata",
                code="LAS_PROJ_SAVED",
                path=las_path,
                epsg=epsg_escolhido,
            )
            SignalManager.instance().console_message.emit(
                f"Projeção forçada: {epsg_escolhido} → {las_path}"
            )
        else:
            self.logger.error(
                "Falha ao salvar .mdata para projeção forçada",
                code="LAS_PROJ_SAVE_ERR",
                path=las_path,
                epsg=epsg_escolhido,
            )

        return epsg_escolhido

    # ── Preferences (override nos filhos) ────────────────────────────

    def load_prefs(self) -> None:
        """Carrega preferências e aplica nos widgets. Override no filho."""
        pass

    def save_prefs(self) -> None:
        """
        Lê widgets e atualiza self.preferences.
        O closeEvent persiste automaticamente com save_tool_prefs.
        """
        pass