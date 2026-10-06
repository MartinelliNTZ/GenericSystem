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
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, QRunnable, Signal

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from utils.FormatUtils import FormatUtils
from utils.ProjectStructureUtil import (
    DEFAULT_PROJECT_FOLDERS,
    DEFAULT_YEARS,
    DOCUMENT_YEARS_FOLDER,
    PROJECT_FOLDER_TEMPLATES,
    PROJECT_PREFIX,
    discover_projects,
    is_year_folder,
)


# Pastas/anos, prefixo e descoberta são definidos em utils/ProjectStructureUtil
# (compartilhados com o Banco de Dados — Contrato 7) e re-exportados no topo
# deste módulo para manter a API pública usada pelo ProjectStructurePlugin.

STATUS_CORRECT = "CORRETA"
STATUS_INCORRECT = "INCOERENTE"
STATUS_MISSING = "AUSENTE"

# Template completo criado (e validado) dentro de cada pasta de ano.
# ``None`` = folha (sem subpastas); ``dict`` = subpastas esperadas.
DOCUMENT_TEMPLATE: Dict[str, Any] = {
    "01_DADOS_OPERACIONAIS": {
        "COMBUSTIVEL": None,
        "DEFENSIVOS": {"ALGODAO": None, "MILHO": None, "SOJA": None},
        "FERTILIZANTES": {"ALGODAO": None, "MILHO": None, "SOJA": None},
        "PRODUTIVIDADE": None,
    },
    "02_ANALISES_SOLO": None,
    "03_NOTAS_FISCAIS": {
        "NF_ANIMAIS": {"FICHA_VACINACAO": None, "GTA_ANIMAL": None},
        "NF_COMBUSTIVEL": None,
        "NF_DEFENSIVOS": None,
        "NF_ENERGIA": None,
        "NF_FERTILIZANTE": {"CALCARIO": None, "KCL": None, "MAP": None},
        "NF_RACOES": None,
        "NF_SEMENTES": None,
    },
    "04_TICKETS_PESSAGEM_BALANCA": None,
    "05_ANEXOS_TREINAMENTOS": None,
}


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


@dataclass
class StructureNode:
    """Nó recursivo de uma estrutura esperada (template) de um projeto.

    ``subtree`` guarda a estrutura esperada DENTRO deste nó (usada para criar
    toda a árvore de uma vez quando o nó está ausente).
    """

    name: str
    path: Optional[Path]
    status: str
    subtree: Optional[Dict[str, Any]] = None
    children: List["StructureNode"] = field(default_factory=list)


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


def _list_subdirs(path: Path) -> List[Path]:
    """Lista as subpastas de ``path`` ordenadas por nome (vazio em falha)."""
    try:
        return sorted(
            [item for item in path.iterdir() if item.is_dir()],
            key=lambda item: item.name.lower(),
        )
    except (PermissionError, FileNotFoundError, OSError) as e:
        _logger().error(
            "Falha ao listar subpastas",
            code="PSM_LIST_ERR",
            error=str(e),
            path=str(path),
        )
        return []


@dataclass
class FileEntry:
    """Arquivo contido diretamente em uma pasta do projeto."""

    name: str
    path: Path
    size: int


def list_contents(folder: Path) -> tuple[List[Path], List[FileEntry]]:
    """Lista subpastas e arquivos diretos de ``folder``.

    Retorna ``(subpastas, arquivos)`` ordenados por nome. Em falha de leitura
    retorna duas listas vazias e registra o erro.
    """
    folder = Path(folder)
    dirs: List[Path] = []
    files: List[FileEntry] = []
    try:
        for item in folder.iterdir():
            try:
                if item.is_dir():
                    dirs.append(item)
                elif item.is_file():
                    files.append(
                        FileEntry(item.name, item, item.stat().st_size)
                    )
            except OSError:
                continue
    except (PermissionError, FileNotFoundError, OSError) as e:
        _logger().error(
            "Falha ao listar conteúdo da pasta",
            code="PSM_CONTENT_ERR",
            error=str(e),
            path=str(folder),
        )
        return [], []
    dirs.sort(key=lambda item: item.name.lower())
    files.sort(key=lambda entry: entry.name.lower())
    return dirs, files


def folder_has_items(path: Path) -> bool:
    """Indica se ``path`` contém ao menos um item (subpasta ou arquivo).

    Verificação leve (``os.scandir`` + primeiro item) usada para marcar na
    árvore quais pastas devem exibir o indicador de expansão antes de o
    conteúdo ser carregado sob demanda.
    """
    try:
        with os.scandir(path) as entries:
            return next(entries, None) is not None
    except (PermissionError, FileNotFoundError, OSError) as e:
        _logger().warning(
            "Falha ao verificar conteúdo da pasta",
            code="PSM_HAS_ITEMS_ERR",
            error=str(e),
            path=str(path),
        )
        return False


def scan_document_years(envio: Path) -> List[StructureNode]:
    """Inspeciona as pastas de ano dentro de ``03_ENVIO_DE_DOCUMENTOS``.

    Pastas que não são anos são marcadas como incoerentes. Anos ausentes NÃO
    são reportados (nem toda OS usa todos os anos), validamos apenas os anos
    que já existem em disco.
    """
    nodes: List[StructureNode] = []
    for path in _list_subdirs(envio):
        if not is_year_folder(path.name):
            nodes.append(StructureNode(path.name, path, STATUS_INCORRECT))
            continue
        nodes.append(
            StructureNode(
                path.name,
                path,
                STATUS_CORRECT,
                subtree=DOCUMENT_TEMPLATE,
                children=scan_template(path, DOCUMENT_TEMPLATE),
            )
        )
    return nodes


def scan_project_trees(
    structure: ProjectStructure,
) -> Dict[str, List[StructureNode]]:
    """Valida as subpastas das pastas de topo que possuem template.

    Retorna um mapa ``caminho da pasta de topo -> nós validados`` apenas para
    as pastas de ``PROJECT_FOLDER_TEMPLATES`` presentes em disco.
    """
    trees: Dict[str, List[StructureNode]] = {}
    for folder in structure.folders:
        template = PROJECT_FOLDER_TEMPLATES.get(folder.name)
        if not template or folder.path is None:
            continue
        if folder.status == STATUS_MISSING:
            continue
        trees[str(folder.path)] = scan_template(folder.path, template)
    return trees


def scan_project_full(
    project: Path,
) -> tuple[
    ProjectStructure,
    Dict[str, List[StructureNode]],
    Dict[str, List[StructureNode]],
]:
    """Inspeciona um projeto por completo.

    Retorna a estrutura das pastas esperadas, as pastas de ano do
    ``03_ENVIO_DE_DOCUMENTOS`` e as subárvores de template das pastas de topo
    (ex: ``14_RELATORIO``), todas mapeadas por caminho.
    """
    structure = scan_project(project, DEFAULT_PROJECT_FOLDERS)
    years: Dict[str, List[StructureNode]] = {}
    for folder in structure.folders:
        if (
            folder.name == DOCUMENT_YEARS_FOLDER
            and folder.path is not None
            and folder.status != STATUS_MISSING
        ):
            years[str(folder.path)] = scan_document_years(folder.path)
    return structure, years, scan_project_trees(structure)


def project_status_counts(
    structure: ProjectStructure,
    years: Dict[str, List[StructureNode]],
    trees: Dict[str, List[StructureNode]],
) -> Dict[str, int]:
    """Conta os status (correta/incoerente/ausente) de um projeto.

    Soma as pastas de topo do projeto e todos os nós das subárvores de ano e
    de template de pastas de topo.
    """
    totals = {"correct": 0, "incorrect": 0, "missing": 0}

    def _bump(status: str) -> None:
        if status == STATUS_CORRECT:
            totals["correct"] += 1
        elif status == STATUS_INCORRECT:
            totals["incorrect"] += 1
        else:
            totals["missing"] += 1

    def _walk(nodes: List[StructureNode]) -> None:
        for node in nodes:
            _bump(node.status)
            _walk(node.children)

    for folder in structure.folders:
        _bump(folder.status)
    for year_nodes in years.values():
        _walk(year_nodes)
    for tree_nodes in trees.values():
        _walk(tree_nodes)
    return totals


def scan_template(root: Path, template: Dict[str, Any]) -> List[StructureNode]:
    """Compara as subpastas de ``root`` com ``template`` recursivamente.

    Presente e esperado → CORRETA (recursivo); ausente → AUSENTE; presente e
    não esperado → INCOERENTE.
    """
    existing = {path.name: path for path in _list_subdirs(root)}
    nodes: List[StructureNode] = []
    for name, subtree in template.items():
        path = existing.pop(name, None)
        if path is None:
            nodes.append(
                StructureNode(name, root / name, STATUS_MISSING, subtree=subtree)
            )
            continue
        children = scan_template(path, subtree) if subtree else []
        nodes.append(
            StructureNode(
                name, path, STATUS_CORRECT, subtree=subtree, children=children
            )
        )
    for name, path in existing.items():
        nodes.append(StructureNode(name, path, STATUS_INCORRECT))
    return nodes


def folder_statistics(path: Path) -> tuple[int, int, int]:
    """Retorna (n_arquivos, n_subpastas, tamanho_bytes) recursivamente.

    Usa ``os.scandir`` para aproveitar o cache de metadados do sistema de
    arquivos (evita ``Path.stat()`` redundante de ``os.walk``).
    """
    n_files = 0
    n_dirs = 0
    total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            n_dirs += 1
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            n_files += 1
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
        except OSError:
            continue
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


@dataclass
class ScanResult:
    """Resultado completo de uma varredura da pasta-mãe (dados puros)."""

    projects: List[ProjectStructure] = field(default_factory=list)
    years: Dict[str, List[StructureNode]] = field(default_factory=dict)
    trees: Dict[str, List[StructureNode]] = field(default_factory=dict)
    trees: Dict[str, List[StructureNode]] = field(default_factory=dict)


class _ScanSignals(QObject):
    """Sinais do worker de varredura."""

    progress = Signal(int, int, int)   # (generation, feitos, total)
    finished = Signal(int, object)   # (generation, ScanResult)
    failed = Signal(int, str)        # (generation, mensagem)


class ScanWorker(QRunnable):
    """Varre a pasta-mãe em background (não toca em widgets).

    Descobre os projetos, inspeciona a estrutura de cada um e coleta as pastas
    de ano do ``03_ENVIO_DE_DOCUMENTOS``. Emite progresso por projeto para
    alimentar a barra central (Contrato 20).
    """

    def __init__(self, generation: int, mother: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.mother = mother
        self.signals = _ScanSignals()
        self._cancelled = False

    def cancel(self) -> None:
        """Solicita o cancelamento cooperativo da varredura."""
        self._cancelled = True

    def run(self) -> None:
        """Executa a varredura e emite o resultado."""
        try:
            projects = discover_projects(
                Path(self.mother), tool_key=ToolKey.PROJECT_STRUCTURE.value
            )
            total = max(len(projects), 1)
            result = ScanResult()
            self.signals.progress.emit(self.generation, 0, total)
            for index, project in enumerate(projects, start=1):
                if self._cancelled:
                    return
                structure, years, trees = scan_project_full(project)
                result.projects.append(structure)
                result.years.update(years)
                result.trees.update(trees)
                self.signals.progress.emit(self.generation, index, total)
            if self._cancelled:
                return
            self.signals.finished.emit(self.generation, result)
        except Exception as e:
            _logger().error(
                "Falha na varredura em background",
                code="PSM_SCAN_WORKER_ERR",
                error=str(e),
                path=self.mother,
            )
            self.signals.failed.emit(self.generation, str(e))


@dataclass
class ProjectScanResult:
    """Resultado da varredura de um único projeto (refresh incremental)."""

    path: str
    structure: ProjectStructure
    years: Dict[str, List[StructureNode]] = field(default_factory=dict)
    trees: Dict[str, List[StructureNode]] = field(default_factory=dict)


class _ProjectScanSignals(QObject):
    """Sinais do worker de varredura de um projeto."""

    finished = Signal(int, object)   # (generation, ProjectScanResult)
    failed = Signal(int, str)        # (generation, mensagem)


class ProjectScanWorker(QRunnable):
    """Re-escaneia um único projeto em background (não toca em widgets)."""

    def __init__(self, generation: int, project: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.project = project
        self.signals = _ProjectScanSignals()

    def run(self) -> None:
        """Executa a varredura do projeto e emite o resultado."""
        try:
            structure, years, trees = scan_project_full(Path(self.project))
            self.signals.finished.emit(
                self.generation,
                ProjectScanResult(self.project, structure, years, trees),
            )
        except Exception as e:
            _logger().error(
                f"Falha ao re-escanear projeto: {self.project}",
                code="PSM_PROJ_SCAN_ERR",
                error=str(e),
            )
            self.signals.failed.emit(self.generation, str(e))


class _FolderContentSignals(QObject):
    """Sinais do worker de listagem de conteúdo de pasta."""

    finished = Signal(int, str, object, object)   # (geração, pasta, dirs, files)


class FolderContentWorker(QRunnable):
    """Lista subpastas e arquivos de uma pasta (não toca em widgets)."""

    def __init__(self, generation: int, path: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.path = path
        self.signals = _FolderContentSignals()

    def run(self) -> None:
        """Lista o conteúdo da pasta e emite o resultado."""
        try:
            dirs, files = list_contents(Path(self.path))
            self.signals.finished.emit(
                self.generation, self.path, dirs, files
            )
        except Exception as e:
            _logger().error(
                f"Falha ao listar conteúdo: {self.path}",
                code="PSM_CONTENT_WORKER_ERR",
                error=str(e),
            )
