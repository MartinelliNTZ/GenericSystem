# -*- coding: utf-8 -*-
"""
RecentProjectsManager — Gerenciador de projetos recentes
=========================================================
Gerencia a lista de projetos recentes, salvando em arquivo próprio
(separado do preferences.json para evitar poluir ToolKey.SYSTEM).

A lista contém dicts com:
    {
        "path": "C:/projetos/MeuProjeto.mtl",
        "name": "MeuProjeto",
        "active": True        # False se o arquivo não existir mais
    }

Uso:
    manager = RecentProjectsManager()
    manager.add_recent("C:/projetos/MeuProjeto.mtl")
    manager.add_recent("C:/projetos/Outro.mtl")
    recents = manager.get_recents()       # lista de dicts
    validated = manager.get_validated()   # lista com active atualizado
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class RecentProjectsManager(BaseUtil):
    """
    Gerencia a lista de projetos recentes em arquivo próprio.
    """

    _MAX_RECENTS = 15
    _CONFIG_DIR: Path = Path(__file__).resolve().parent.parent / "config"
    _FILE_PATH: Path = _CONFIG_DIR / "recent_projects.json"

    def __init__(self, tool_key: str = ToolKey.UNTRACEABLE.value):
        self._tool_key = tool_key
        self._logger = self._get_logger(tool_key)

    # ── API pública ──────────────────────────────────────────────────

    def add_recent(self, project_path: str) -> None:
        """
        Adiciona um projeto à lista de recentes (ou move ao topo se já existe).

        Lê o arquivo .mtl para extrair last_modified e folder (path).

        Args:
            project_path: Caminho completo do arquivo .mtl
        """
        if not project_path:
            return

        recents = self._load()

        # Remove se já existe (para mover ao topo)
        recents = [r for r in recents if r.get("path") != project_path]

        # Adiciona no topo com dados enriquecidos
        project_name = Path(project_path).stem
        folder = os.path.dirname(project_path)
        last_modified = ""
        active = os.path.isfile(project_path)

        # Tenta ler last_modified do .mtl
        if active:
            try:
                from utils.ProjectUtil import ProjectUtil
                data = ProjectUtil.load_project(project_path, tool_key=self._tool_key)
                if data:
                    raw = data.get("last_modified", "")
                    if raw:
                        from utils.FormatUtils import FormatUtils
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(raw)
                            last_modified = FormatUtils.format_date(dt.timestamp(), tool_key=self._tool_key)
                        except Exception:
                            last_modified = raw[:10]  # fallback: só a data
            except Exception:
                pass

        recents.insert(0, {
            "path": project_path,
            "folder": folder,
            "name": project_name,
            "last_modified": last_modified,
            "active": active,
        })

        # Limita tamanho
        recents = recents[:self._MAX_RECENTS]

        self._save(recents)
        self._logger.info(
            "Projeto adicionado aos recentes",
            code="RECENT_ADD",
            path=project_path,
        )

    def get_recents(self) -> List[Dict[str, Any]]:
        """
        Retorna a lista de projetos recentes (sem validar existência).

        Returns:
            Lista de dicts com chaves: path, name, active
        """
        return self._load()

    def get_validated(self) -> List[Dict[str, Any]]:
        """
        Retorna a lista de projetos recentes com o campo 'active'
        atualizado conforme a existência do arquivo em disco.

        Returns:
            Lista de dicts com chaves: path, name, active
        """
        recents = self._load()
        for recent in recents:
            recent["active"] = os.path.isfile(recent.get("path", ""))
        return recents

    def remove_recent(self, project_path: str) -> None:
        """
        Remove um projeto específico da lista de recentes.

        Args:
            project_path: Caminho completo do arquivo .mtl
        """
        recents = self._load()
        recents = [r for r in recents if r.get("path") != project_path]
        self._save(recents)
        self._logger.info(
            "Projeto removido dos recentes",
            code="RECENT_REMOVE",
            path=project_path,
        )

    def clear_all(self) -> None:
        """Limpa toda a lista de projetos recentes."""
        self._save([])
        self._logger.info("Lista de recentes limpa", code="RECENT_CLEAR")

    # ── Persistência ─────────────────────────────────────────────────

    def _load(self) -> List[Dict[str, Any]]:
        """Carrega a lista de recentes do disco."""
        if not self._FILE_PATH.is_file():
            return []
        try:
            with self._FILE_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, OSError) as e:
            self._logger.error(
                "Erro ao carregar recentes",
                code="RECENT_LOAD_ERR",
                error=str(e),
            )
            return []

    def _save(self, recents: List[Dict[str, Any]]) -> None:
        """Persiste a lista de recentes no disco."""
        self._CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with self._FILE_PATH.open("w", encoding="utf-8") as f:
                json.dump(recents, f, indent=2, ensure_ascii=False)
        except (OSError, PermissionError) as e:
            self._logger.error(
                "Erro ao salvar recentes",
                code="RECENT_SAVE_ERR",
                error=str(e),
            )