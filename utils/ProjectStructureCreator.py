# -*- coding: utf-8 -*-
"""
ProjectStructureCreator — Criação física das pastas/arquivos base dos projetos
==============================================================================
Camada COMPARTILHADA (``utils/`` — Contrato 7) que materializa em disco a
estrutura descrita por ``utils.ProjectStructureUtil``. Como vive em ``utils``,
pode ser usada por qualquer ferramenta (Gerenciador de Estrutura e Acompanhamento
de OS) SEM importar um plugin a partir de outro.

- ``create_base_file``      — cria/copia um ARQUIVO BASE (``str`` | ``BaseFile``).
- ``create_template``       — cria recursivamente uma subárvore (pastas + arquivos).
- ``create_project_folder`` — cria UMA pasta padrão + seu template de subpastas.
- ``create_project_folders``— cria VÁRIAS pastas padrão selecionadas (checklist),
  com as subpastas de cada uma, EXCETO os anos do ``03_ENVIO_DE_DOCUMENTOS``.
- ``create_document_year``  — cria a pasta de um ano com o template de documentos.

Uso:
    from utils.ProjectStructureCreator import ProjectStructureCreator

    ProjectStructureCreator.create_project_folders(project, ["05_ASA", "06_CAR"])
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureUtil import (
    BaseFile,
    DOCUMENT_TEMPLATE,
    DOCUMENT_YEARS_FOLDER,
    PROJECT_FOLDER_TEMPLATES,
    ProjectStructureUtil,
    file_spec,
    is_file_node,
)


class ProjectStructureCreator(BaseUtil):
    """Materializa a estrutura de pastas/arquivos base definida na fonte única."""

    _TOOL = ToolKey.PROJECT_STRUCTURE.value

    @classmethod
    def create_folder(
        cls, project: Path, name: str, tool_key: str = _TOOL
    ) -> Path:
        """Cria a pasta ``name`` dentro de ``project``. Levanta OSError em falha."""
        destination = Path(project) / name
        destination.mkdir()
        cls._get_logger(tool_key, "ProjectStructureCreator").info(
            f"Pasta criada: {destination}", code="PSC_FOLDER_OK"
        )
        return destination

    @classmethod
    def create_base_file(
        cls, destination: Path, spec: BaseFile, tool_key: str = _TOOL
    ) -> Path:
        """Cria/copia um ARQUIVO BASE conforme ``spec`` dentro do projeto.

        Copia de ``ProjectStructureUtil.BASE_FILES_DIR`` quando ``spec.source`` é
        informado; caso contrário grava ``spec.content``. Levanta OSError em falha.
        """
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not spec.overwrite:
            return destination
        if spec.source:
            shutil.copy2(
                ProjectStructureUtil.BASE_FILES_DIR / spec.source, destination
            )
        else:
            destination.write_text(spec.content, encoding="utf-8")
        cls._get_logger(tool_key, "ProjectStructureCreator").info(
            f"Arquivo base criado: {destination}", code="PSC_FILE_OK"
        )
        return destination

    @classmethod
    def create_template(
        cls, root: Path, template: Dict[str, Any], tool_key: str = _TOOL
    ) -> Path:
        """Cria recursivamente o template (pastas e arquivos base) dentro de ``root``.

        Pastas já existentes são preservadas (idempotente). Nós de arquivo
        (``str`` ou ``BaseFile``) materializam o arquivo correspondente. Levanta
        OSError em falha de filesystem.
        """
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        for name, node in template.items():
            child = root / name
            if is_file_node(node):
                cls.create_base_file(child, file_spec(node), tool_key=tool_key)
                continue
            child.mkdir(exist_ok=True)
            if isinstance(node, dict):
                cls.create_template(child, node, tool_key=tool_key)
        return root

    @classmethod
    def create_project_folder(
        cls,
        project: Path,
        name: str,
        template: Optional[Dict[str, Any]] = None,
        tool_key: str = _TOOL,
    ) -> Path:
        """Cria a pasta padrão ``name`` e, se houver, o template de subpastas.

        Levanta OSError em falha de filesystem.
        """
        destination = cls.create_folder(project, name, tool_key=tool_key)
        if template:
            cls.create_template(destination, template, tool_key=tool_key)
        return destination

    @classmethod
    def create_project_folders(
        cls, project: Path, names: Iterable[str], tool_key: str = _TOOL
    ) -> int:
        """Cria VÁRIAS pastas padrão selecionadas (checklist) dentro de ``project``.

        Cria cada pasta com as suas subpastas de template, EXCETO a pasta
        especial de ANOS (``DOCUMENT_YEARS_FOLDER``), que é criada vazia (sem os
        anos). Idempotente — pastas já existentes são preservadas. Retorna o
        número de pastas de topo efetivamente criadas.
        """
        project = Path(project)
        project.mkdir(parents=True, exist_ok=True)
        created = 0
        for name in names:
            target = project / name
            if name == DOCUMENT_YEARS_FOLDER:
                if not target.exists():
                    target.mkdir(parents=True, exist_ok=True)
                    created += 1
                continue
            template = PROJECT_FOLDER_TEMPLATES.get(name, {})
            existed = target.exists()
            cls.create_template(target, template, tool_key=tool_key)
            if not existed:
                created += 1
        return created

    @classmethod
    def create_document_year(
        cls, envio: Path, year: int, tool_key: str = _TOOL
    ) -> Path:
        """Cria a pasta do ``year`` com o template completo de documentos."""
        year_path = Path(envio) / str(year)
        cls.create_template(year_path, DOCUMENT_TEMPLATE, tool_key=tool_key)
        cls._get_logger(tool_key, "ProjectStructureCreator").info(
            f"Pasta de ano criada: {year_path}", code="PSC_YEAR_OK"
        )
        return year_path
