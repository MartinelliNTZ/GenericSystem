# -*- coding: utf-8 -*-
"""
FolderOperations — Criação, renomeação e mesclagem de pastas
============================================================
Operações de filesystem usadas pela ferramenta, isoladas da interface.
Inclui worker de renomeação para não bloquear a thread da UI.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import QObject, QRunnable, Signal

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from plugins.project_structure_manager.ProjectStructureScanner import (
    DOCUMENT_TEMPLATE,
)


def _logger() -> LogUtils:
    return LogUtils(
        tool=ToolKey.PROJECT_STRUCTURE.value, class_name="FolderOperations"
    )


def create_folder(project: Path, name: str) -> Path:
    """Cria a pasta ``name`` dentro de ``project``. Levanta OSError em falha."""
    destination = Path(project) / name
    destination.mkdir()
    _logger().info(f"Pasta criada: {destination}")
    return destination


def create_template(root: Path, template: Dict[str, Any]) -> Path:
    """Cria recursivamente o template de pastas dentro de ``root``.

    Pastas já existentes são preservadas (idempotente). Levanta OSError em
    falha de filesystem.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for name, subtree in template.items():
        child = root / name
        child.mkdir(exist_ok=True)
        if subtree:
            create_template(child, subtree)
    return root


def create_document_year(envio: Path, year: int) -> Path:
    """Cria a pasta do ``year`` com o template completo de documentos."""
    year_path = Path(envio) / str(year)
    create_template(year_path, DOCUMENT_TEMPLATE)
    _logger().info(f"Pasta de ano criada: {year_path}")
    return year_path


def destination_exists(origin: Path, new_name: str) -> bool:
    """Indica se já existe destino para a renomeação."""
    return (Path(origin).parent / new_name).exists()


def rename_folder(origin: Path, new_name: str) -> Path:
    """Renomeia ``origin`` para ``new_name``. Levanta OSError em falha."""
    origin = Path(origin)
    destination = origin.parent / new_name
    origin.rename(destination)
    _logger().info(f"Pasta renomeada: {origin} -> {destination}")
    return destination


def _merge_recursive(
    source: Path, destination: Path, conflicts: List[str]
) -> None:
    """Mescla recursivamente ``source`` em ``destination``."""
    destination.mkdir(parents=True, exist_ok=True)
    for item in list(source.iterdir()):
        target = destination / item.name
        if not target.exists():
            shutil.move(str(item), str(target))
        elif item.is_dir() and target.is_dir():
            _merge_recursive(item, target, conflicts)
        else:
            conflicts.append(str(item))


def merge_folders(source: Path, destination: Path) -> List[str]:
    """Mescla ``source`` em ``destination``. Retorna a lista de conflitos."""
    source = Path(source)
    destination = Path(destination)
    conflicts: List[str] = []
    try:
        _merge_recursive(source, destination, conflicts)
        try:
            if not any(source.iterdir()):
                source.rmdir()
        except OSError:
            pass
        _logger().info(
            f"Mesclagem concluída: {source} -> {destination} "
            f"({len(conflicts)} conflito(s))"
        )
    except Exception as e:
        _logger().error(
            "Falha na mesclagem",
            code="PSM_MERGE_ERR",
            error=str(e),
            source=str(source),
            destination=str(destination),
        )
        raise
    return conflicts


def open_in_explorer(path: Path) -> None:
    """Abre ``path`` no gerenciador de arquivos do sistema."""
    target = Path(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(target))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except Exception as e:
        _logger().error(
            "Falha ao abrir no explorer",
            code="PSM_OPEN_ERR",
            error=str(e),
            path=str(target),
        )


class FolderOperationSignals(QObject):
    """Sinais de operações assíncronas de pasta."""

    success = Signal(str, str, str)
    error = Signal(str, str)


class RenameFolderWorker(QRunnable):
    """Renomeia uma pasta em background (não toca em widgets)."""

    def __init__(self, origin: Path, new_name: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.origin = Path(origin)
        self.new_name = new_name
        self.signals = FolderOperationSignals()

    def run(self) -> None:
        """Executa a renomeação e emite sucesso/erro."""
        try:
            destination = rename_folder(self.origin, self.new_name)
            self.signals.success.emit(
                "rename", str(self.origin), str(destination)
            )
        except Exception as e:
            _logger().error(
                "Falha ao renomear pasta",
                code="PSM_RENAME_ERR",
                error=str(e),
                path=str(self.origin),
            )
            self.signals.error.emit("rename", str(e))
