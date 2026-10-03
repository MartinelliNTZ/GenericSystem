# -*- coding: utf-8 -*-
"""
ProjectUtil — Utilitário para gerenciar arquivos de projeto (.mtl)
===================================================================
Cria, lê e atualiza arquivos de projeto com extensão .mtl (estrutura JSON).

O arquivo .mtl contém:
    {
        "project_name": "MeuProjeto",
        "path": "C:/caminho/para/pasta",
        "created_at": "2026-05-14T20:30:00",
        "last_modified": "2026-05-14T20:30:00",
        "file_path": "C:/caminho/para/pasta/MeuProjeto.mtl"
    }

Uso:
    from utils.ProjectUtil import ProjectUtil
    info = ProjectUtil.create_project("C:/pasta", "MeuProjeto")
    info = ProjectUtil.update_last_modified("C:/pasta/MeuProjeto.mtl")
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ProjectUtil:
    """
    Métodos estáticos para gerenciar arquivos de projeto .mtl.
    """

    EXTENSION = ".mtl"

    # ── Templates de estrutura ──────────────────────────────────────

    @staticmethod
    def _default_structure(project_name: str, project_path: str) -> Dict[str, Any]:
        """
        Retorna a estrutura padrão de um arquivo .mtl.
        """
        now = datetime.now().isoformat()
        return {
            "project_name": project_name,
            "path": project_path,
            "created_at": now,
            "last_modified": now,
            "file_path": str(Path(project_path) / f"{project_name}{ProjectUtil.EXTENSION}"),
        }

    # ── Criar projeto ───────────────────────────────────────────────

    @staticmethod
    def create_project(
        folder_path: str,
        project_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um arquivo .mtl dentro de folder_path com o nome project_name.

        Args:
            folder_path: Caminho da pasta onde o .mtl será salvo.
            project_name: Nome do projeto (sem extensão).

        Returns:
            Dict com os dados salvos, ou None se falhar.
        """
        folder = Path(folder_path)
        if not folder.is_dir():
            return None

        structure = ProjectUtil._default_structure(project_name, str(folder.resolve()))
        file_path = folder / f"{project_name}{ProjectUtil.EXTENSION}"

        try:
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(structure, f, indent=2, ensure_ascii=False)
            structure["file_path"] = str(file_path.resolve())
            return structure
        except (OSError, PermissionError) as e:
            return None

    # ── Ler projeto ─────────────────────────────────────────────────

    @staticmethod
    def load_project(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Carrega um arquivo .mtl e retorna seu conteúdo como dict.

        Args:
            file_path: Caminho completo para o arquivo .mtl.

        Returns:
            Dict com os dados, ou None se falhar.
        """
        path = Path(file_path)
        if not path.is_file() or path.suffix != ProjectUtil.EXTENSION:
            return None

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, OSError) as e:
            return None

    # ── Atualizar last_modified ─────────────────────────────────────

    @staticmethod
    def update_last_modified(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Atualiza o campo last_modified de um arquivo .mtl com a data/hora atual.

        Args:
            file_path: Caminho completo para o arquivo .mtl.

        Returns:
            Dict atualizado, ou None se falhar.
        """
        data = ProjectUtil.load_project(file_path)
        if data is None:
            return None

        data["last_modified"] = datetime.now().isoformat()

        try:
            path = Path(file_path)
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return data
        except (OSError, PermissionError) as e:
            return None

    # ── Criar projeto com validação de substituição ─────────────────

    @staticmethod
    def create_project_safe(
        folder_path: str,
        project_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um arquivo .mtl, perguntando ao usuário se deseja substituir
        caso já exista um arquivo com o mesmo nome.

        A importação de MessageBox é feita internamente para evitar
        dependência circular.

        Args:
            folder_path: Caminho da pasta onde o .mtl será salvo.
            project_name: Nome do projeto (sem extensão).
            parent_widget: Widget pai para o diálogo (opcional).

        Returns:
            Dict com os dados salvos, ou None se o usuário cancelar ou falhar.
        """
        from pathlib import Path
        mtl_path = Path(folder_path) / f"{project_name}{ProjectUtil.EXTENSION}"

        if mtl_path.is_file():
            # Pergunta se deseja substituir
            from utils.MessageBox import MessageBox
            confirm = MessageBox.show_question(
                f"Já existe um projeto '{project_name}' nesta pasta.\n\n"
                f"Deseja sobrescrever?",
                title="Projeto Existente",
                buttons=MessageBox.YES_NO,
                default_button=MessageBox.NO,
            )
            if confirm != MessageBox.YES:
                return None

        return ProjectUtil.create_project(folder_path, project_name)

    # ── Obter root_folder do projeto ativo ──────────────────────────

    @staticmethod
    def get_root_folder() -> Optional[str]:
        """
        Retorna o root_folder do projeto ativo lendo das preferências do sistema.

        Returns:
            Caminho do root_folder, ou None se não houver projeto ativo.
        """
        try:
            from utils.Preferences import Preferences
            from core.enum.ToolKey import ToolKey
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            root = sys_prefs.get("root_folder", "")
            if root:
                return root
            return None
        except Exception:
            return None

    # ── Listar arquivos por extensões ──────────────────────────────

    @staticmethod
    def get_files_by_extensions(extensions: list[str]) -> dict[str, str]:
        """
        Varre a pasta do projeto ativo e retorna um dict com nome e caminho
        completo de todos os arquivos que possuem as extensões especificadas.

        Args:
            extensions: Lista de extensões (ex: [".las", ".laz"]).

        Returns:
            Dict no formato {nome_arquivo: caminho_completo}.
            Ex: {"nuvem.las": "C:/projeto/dados/nuvem.las"}
        """
        root = ProjectUtil.get_root_folder()
        if not root:
            return {}

        result: dict[str, str] = {}
        try:
            for dirpath, _, filenames in os.walk(root):
                for fname in filenames:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in extensions:
                        full_path = os.path.join(dirpath, fname)
                        result[fname] = full_path
        except (OSError, PermissionError) as e:
            return result

        return result

    # ── Atualizar campo específico ──────────────────────────────────

    @staticmethod
    def update_field(file_path: str, key: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        Atualiza um campo específico no arquivo .mtl e salva.

        Args:
            file_path: Caminho completo para o arquivo .mtl.
            key: Nome do campo a atualizar.
            value: Novo valor.

        Returns:
            Dict atualizado, ou None se falhar.
        """
        data = ProjectUtil.load_project(file_path)
        if data is None:
            return None

        data[key] = value
        data["last_modified"] = datetime.now().isoformat()

        try:
            path = Path(file_path)
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return data
        except (OSError, PermissionError) as e:
            return None