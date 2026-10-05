# -*- coding: utf-8 -*-
"""
ProjectStructureScanner — Descoberta, validação e estatísticas de projetos
==========================================================================
Lógica pura (sem widgets) usada pelo ProjectStructurePlugin:

- Descoberta de projetos (pastas com prefixo "OS_") na pasta-mãe.
- Verificação das pastas esperadas (presentes, ausentes, incoerentes).
- Cálculo assíncrono de estatísticas (arquivos, subpastas, tamanho).

Os workers NÃO acessam widgets Qt: retornam apenas caminho + números + geração.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, QRunnable, Signal

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from utils.FormatUtils import FormatUtils


# Pastas esperadas na raiz de cada projeto (configuração local da ferramenta).
DEFAULT_PROJECT_FOLDERS: List[str] = [
    "01_Acessos_Plataforma_IA_AGLIBS",
    "02_Acompanhamento_de_Projeto_Reuniões",
    "03_ENVIO_DE_DOCUMENTOS",
    "04_ATIVIDADES_ATRIBUIDAS",
    "05_ASA",
    "06_CAR",
    "07_MATRICULA",
    "08_LIMITES",
    "09_HISTORICO_COBERTURA_SOLO",
    "10_VERRA",
    "11_AGROROBOTICA",
    "12_FOTOS_INICIO_PROJETO",
    "13_ZONAS_DE_MANEJO",
]

PROJECT_PREFIX = "OS_"

STATUS_CORRECT = "CORRETA"
STATUS_INCORRECT = "INCOERENTE"
STATUS_MISSING = "AUSENTE"


def _logger() -> LogUtils:
    return LogUtils(
        tool=ToolKey.PROJECT_STRUCTURE.value,
        class_name="ProjectStructureScanner",
    )


@dataclass
class FolderStatus:
    """Estado de uma pasta esperada (ou presente) dentro de um projeto."""

    name: str
    path: Optional[Path]
    status: str


@dataclass
class ProjectStructure:
    """Resultado da inspeção de um projeto."""

    name: str
    path: Path
    folders: List[FolderStatus] = field(default_factory=list)
    n_correct: int = 0
    n_incorrect: int = 0
    n_missing: int = 0


def discover_projects(mother: Path) -> List[Path]:
    """Retorna as pastas de projeto (prefixo OS_) ordenadas por nome."""
    logger = _logger()
    try:
        projects = [
            path
            for path in mother.iterdir()
            if path.is_dir() and path.name.upper().startswith(PROJECT_PREFIX)
        ]
    except (PermissionError, FileNotFoundError, OSError) as e:
        logger.error(
            "Falha ao ler a pasta-mãe",
            code="PSM_SCAN_ERR",
            error=str(e),
            path=str(mother),
        )
        return []
    projects.sort(key=lambda path: path.name.lower())
    return projects


def scan_project(project: Path, expected: List[str]) -> ProjectStructure:
    """Inspeciona um projeto: pastas presentes, incoerentes e ausentes."""
    result = ProjectStructure(name=project.name, path=project)
    try:
        existing = sorted(
            [path for path in project.iterdir() if path.is_dir()],
            key=lambda path: path.name.lower(),
        )
    except (PermissionError, FileNotFoundError, OSError) as e:
        _logger().error(
            "Falha ao ler projeto",
            code="PSM_PROJ_ERR",
            error=str(e),
            path=str(project),
        )
        existing = []

    existing_names = {path.name for path in existing}

    for folder in existing:
        if folder.name in expected:
            result.n_correct += 1
            result.folders.append(
                FolderStatus(folder.name, folder, STATUS_CORRECT)
            )
        else:
            result.n_incorrect += 1
            result.folders.append(
                FolderStatus(folder.name, folder, STATUS_INCORRECT)
            )

    for name in expected:
        if name not in existing_names:
            result.n_missing += 1
            result.folders.append(
                FolderStatus(name, project / name, STATUS_MISSING)
            )

    return result


def folder_statistics(path: Path) -> tuple[int, int, int]:
    """Retorna (n_arquivos, n_subpastas, tamanho_bytes) recursivamente."""
    n_files = 0
    n_dirs = 0
    total = 0
    try:
        for root, dirs, files in os.walk(path):
            n_dirs += len(dirs)
            n_files += len(files)
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    continue
    except OSError:
        pass
    return n_files, n_dirs, total


def format_count(value: int) -> str:
    """Formata contagem com separador de milhar ('.')."""
    return f"{value:,}".replace(",", ".")


def format_size(value: int) -> str:
    """Formata tamanho em bytes usando FormatUtils (Contrato 22)."""
    return FormatUtils.format_size(
        value, tool_key=ToolKey.PROJECT_STRUCTURE.value
    )


class _StatisticsSignals(QObject):
    """Sinais do worker de estatísticas.

    O último parâmetro (tamanho em bytes) usa ``object`` para suportar
    valores acima de 2^31 (pastas maiores que ~2 GB), evitando OverflowError.
    """

    finished = Signal(int, str, int, int, object)


class StatisticsWorker(QRunnable):
    """Calcula estatísticas de uma pasta em background (não toca em widgets)."""

    def __init__(self, generation: int, path: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.path = path
        self.signals = _StatisticsSignals()

    def run(self) -> None:
        """Executa o cálculo e emite o resultado."""
        try:
            n_files, n_dirs, size = folder_statistics(Path(self.path))
            self.signals.finished.emit(
                self.generation, self.path, n_files, n_dirs, size
            )
        except Exception as e:
            _logger().error(
                "Falha ao calcular estatísticas",
                code="PSM_STATS_ERR",
                error=str(e),
                path=self.path,
            )
