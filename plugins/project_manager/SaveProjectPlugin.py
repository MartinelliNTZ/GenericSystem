# -*- coding: utf-8 -*-
"""
SaveProjectPlugin — Ferramenta Instantânea para Salvar Projetos (.mtl)
========================================================================
Tipo: INSTANT — não abre aba, executa ação imediata.

Ao ser clicada:
1. Se current_project existe — atualiza last_modified (modo salvar)
2. Se não existe — abre diálogo nativo "Salvar como" com filtro .mtl
     (local + nome + extensão em UMA etapa)
     ProjectUtil.create_project_safe() cuida da validação de substituição
     Cria o .mtl com metadados
3. Salva o caminho do .mtl em preferences (ToolKey.SYSTEM / current_project)
"""

from __future__ import annotations

import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QLabel

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox
from utils.ProjectUtil import ProjectUtil


class SaveProjectPlugin(BasePlugin):
    """
    Ferramenta INSTANT: cria ou salva projetos .mtl.
    Usa o diálogo nativo "Salvar como" do Windows em uma única etapa.
    """

    _MTL_FILTER = "Projeto Aetheris (*.mtl)"

    def __init__(self, parent=None):
        # sys_prefs=True carrega self.sys_preferences (seção System)
        super().__init__(
            tool_key=ToolKey.SAVE_PROJECT.value,
            parent=parent,
            sys_prefs=True,
        )

        # Widget vazio (placeholder) — nunca será exibido como aba
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        placeholder = QLabel("")
        placeholder.setVisible(False)
        layout.addWidget(placeholder)

        # Carrega current_project do cache (já disponível via sys_preferences)
        self._load_prefs()

        # Executa o fluxo principal no próximo ciclo do event loop
        QTimer.singleShot(0, self._run_project_flow)

    def _load_prefs(self) -> None:
        """Carreva current_project e root_folder das preferências do sistema."""
        self._current_project = self.sys_preferences.get("current_project", None)
        self._current_root_folder = self.sys_preferences.get("root_folder", None)
        self.logger.info(
            "Prefs carregadas no init",
            code="PROJ_LOAD_INIT",
            current_project_raw=self._current_project,
            root_folder_raw=self._current_root_folder,
        )

    # ── Fluxo principal ────────────────────────────────────────────

    def _run_project_flow(self) -> None:
        """Executa o fluxo de criação/atualização de projeto."""
        try:
            # Recarrega do disco para pegar alterações externas
            from utils.Preferences import Preferences
            self.sys_preferences = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            self._current_project = self.sys_preferences.get("current_project", None)

            self.logger.info(
                "Verificando current_project",
                code="PROJ_CHECK",
                current_project_value=self._current_project,
                current_project_type=type(self._current_project).__name__,
                file_exists=(
                    os.path.isfile(self._current_project)
                    if self._current_project
                    else False
                ),
                cwd=os.getcwd(),
            )

            if self._current_project and os.path.isfile(self._current_project):
                self._handle_save_existing()
            else:
                if not self._current_project:
                    self.logger.info(
                        "current_project é None ou vazio — modo criar",
                        code="PROJ_MODE_CREATE_NONE",
                    )
                else:
                    self.logger.info(
                        "current_project não encontrado no disco — modo criar",
                        code="PROJ_MODE_CREATE_MISSING",
                        stored_path=self._current_project,
                    )
                self._handle_create_new()

        except Exception as e:
            self.logger.error(
                "Erro no fluxo do gerenciador de projetos",
                code="PROJ_FLOW_ERR",
                error=str(e),
            )
            MessageBox.show_error(
                "Erro ao gerenciar projeto",
                title="Gerenciador de Projetos",
                detail=str(e),
            )
        finally:
            self._self_destruct()

    # ── Modo "Salvar existente" ────────────────────────────────────

    def _handle_save_existing(self) -> None:
        """Atualiza o last_modified do projeto atual."""
        self.logger.info(
            "Modo salvar: atualizando last_modified",
            code="PROJ_SAVING",
            file_path=self._current_project,
        )
        result = ProjectUtil.update_last_modified(self._current_project)
        if result is not None:
            # Salva root_folder nas preferências do sistema
            from utils.Preferences import Preferences
            self.sys_preferences["root_folder"] = os.path.dirname(self._current_project)
            Preferences.save_tool_prefs(ToolKey.SYSTEM, self.sys_preferences)

            self.logger.info(
                "Projeto atualizado",
                code="PROJ_SAVE",
                file_path=self._current_project,
                project_name=result.get("project_name", ""),
                root_folder=self.sys_preferences["root_folder"],
            )
            SignalManager.instance().project_changed.emit()
            MessageBox.show_info(
                f"Projeto '{result.get('project_name', '')}' salvo com sucesso!",
                title="Projeto Salvo",
            )
        else:
            self.logger.warning(
                "Falha ao atualizar projeto existente",
                code="PROJ_SAVE_ERR",
                file_path=self._current_project,
            )
            self._handle_create_new()

    # ── Modo "Criar novo" ─────────────────────────────────────────

    def _handle_create_new(self) -> None:
        """
        Abre o diálogo nativo "Salvar como" com filtro .mtl.
        Tudo em UMA etapa: local + nome + extensão já inclusa.
        """
        self.logger.info(
            "Modo criar: abrindo diálogo salvar como",
            code="PROJ_CREATING",
        )

        # 1. Diálogo nativo do Windows — escolhe local e nome
        file_path = ExplorerUtils.save_file(
            title="Salvar projeto como",
            file_filter=self._MTL_FILTER,
            parent=self,
        )
        if not file_path:
            self.logger.info("Usuário cancelou a criação do projeto", code="PROJ_CANCEL")
            return

        # 2. Extrai pasta e nome do caminho completo
        folder = os.path.dirname(file_path)
        project_name = os.path.splitext(os.path.basename(file_path))[0]

        self.logger.info(
            "Usuário escolheu",
            code="PROJ_CHOOSED",
            folder=folder,
            project_name=project_name,
            full_path=file_path,
        )

        # 3. ProjectUtil cuida da validação — se já existe, pergunta
        result = ProjectUtil.create_project_safe(folder, project_name)
        if result is None:
            self.logger.error(
                "Falha ao criar arquivo de projeto",
                code="PROJ_CREATE_ERR",
                folder=folder,
                project_name=project_name,
            )
            MessageBox.show_error(
                f"Falha ao criar projeto '{project_name}' em:\n{folder}",
                title="Erro ao Criar Projeto",
            )
            return

        # 4. Salva current_project e root_folder nas preferências do sistema
        from utils.Preferences import Preferences
        self.sys_preferences["current_project"] = result["file_path"]
        self.sys_preferences["root_folder"] = folder
        Preferences.save_tool_prefs(ToolKey.SYSTEM, self.sys_preferences)
        self._current_project = result["file_path"]
        self._current_root_folder = folder

        self.logger.info(
            "Projeto criado com sucesso",
            code="PROJ_CREATED",
            file_path=result["file_path"],
            project_name=project_name,
            saved_in_prefs=True,
        )
        SignalManager.instance().project_changed.emit()
        MessageBox.show_info(
            f"Projeto '{project_name}' criado com sucesso!\n\n"
            f"Localização: {result['file_path']}",
            title="Projeto Criado",
        )

    # ── Auto-destruição ─────────────────────────────────────────────

    def _self_destruct(self) -> None:
        """Remove o widget do workspace e chama deleteLater."""
        self.logger.info("Finalizando SaveProjectPlugin", code="PROJ_DONE")
        self.deleteLater()

    def load_prefs(self) -> None:
        """Carreva preferências."""
        pass

    def save_prefs(self) -> None:
        """Não há preferências específicas da tool para persistir."""
        pass