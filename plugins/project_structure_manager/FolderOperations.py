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
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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


def _clear_readonly(path: Path) -> None:
    """Remove o atributo somente leitura de ``path`` (Windows)."""
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError as e:
        _logger().warning(
            f"Falha ao limpar atributo somente leitura: {path}",
            code="PSM_CHMOD_SKIP",
            error=str(e),
        )


def _remove_if_empty(
    path: Path, retries: int = 12, delay: float = 0.4
) -> bool:
    """Remove ``path`` se estiver vazia, com retries para locks transientes.

    No Windows, pastas sincronizadas (ex: OneDrive) ou pastas sendo enumeradas
    por ``os.scandir`` (worker de estatísticas) podem recusar a remoção
    momentaneamente ([WinError 5] Acesso negado). Limpa o atributo somente
    leitura e tenta novamente algumas vezes antes de desistir. Retorna True
    apenas se a pasta foi efetivamente removida.
    """
    last_error: Optional[OSError] = None
    for attempt in range(retries):
        try:
            if not path.is_dir() or any(path.iterdir()):
                return False
            os.rmdir(path)
            return True
        except PermissionError as e:
            last_error = e
            _clear_readonly(path)
            if attempt < retries - 1:
                time.sleep(delay)
        except OSError as e:
            _logger().warning(
                f"Nao foi possivel remover pasta vazia: {path}",
                code="PSM_RMDIR_SKIP",
                error=str(e),
            )
            return False
    _logger().warning(
        f"Pasta vazia permaneceu bloqueada (remocao falhou): {path}",
        code="PSM_RMDIR_SKIP",
        error=str(last_error),
    )
    return False


def _merge_recursive(
    source: Path, destination: Path, conflicts: List[str]
) -> None:
    """Mescla recursivamente ``source`` em ``destination``.

    Subpastas homônimas são mescladas recursivamente e removidas assim que
    ficam vazias, garantindo que a pasta de origem (nome incoerente) seja
    eliminada ao final da padronização.
    """
    destination.mkdir(parents=True, exist_ok=True)
    for item in list(source.iterdir()):
        target = destination / item.name
        if not target.exists():
            shutil.move(str(item), str(target))
        elif item.is_dir() and target.is_dir():
            _merge_recursive(item, target, conflicts)
            _remove_if_empty(item)
        else:
            conflicts.append(str(item))


def merge_folders(source: Path, destination: Path) -> List[str]:
    """Mescla ``source`` em ``destination`` e remove a origem se ficar vazia.

    Retorna a lista de conflitos (arquivos que já existiam no destino). Quando
    não há conflitos, a pasta de origem é eliminada por completo.
    """
    source = Path(source)
    destination = Path(destination)
    conflicts: List[str] = []
    try:
        _merge_recursive(source, destination, conflicts)
        _remove_if_empty(source)
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


def _launch(target: Path) -> None:
    """Abre ``target`` no shell do sistema e registra eventuais falhas."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(target))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except Exception as e:
        _logger().error(
            "Falha ao abrir caminho",
            code="PSM_OPEN_ERR",
            error=str(e),
            path=str(target),
        )


def open_in_explorer(path: Path) -> None:
    """Abre ``path`` (pasta) no gerenciador de arquivos do sistema."""
    _launch(Path(path))


def open_path(path: Path) -> None:
    """Abre ``path`` no programa padrão (arquivo) ou no explorer (pasta)."""
    _launch(Path(path))


class FolderOperationSignals(QObject):
    """Sinais de operações assíncronas de pasta."""

    success = Signal(str, str, str)
    error = Signal(str, str)


class FolderTaskSignals(QObject):
    """Sinais do worker genérico de operações de pasta."""

    success = Signal(str, str)   # (op, resultado como string)
    error = Signal(str, str)     # (op, mensagem de erro)


class FolderTaskWorker(QRunnable):
    """Executa uma operação de filesystem em background (não toca em widgets).

    A ``operation`` é um callable sem argumentos que realiza a criação/mesclagem
    e retorna um valor (convertido em string para o sinal de sucesso).
    """

    def __init__(self, op: str, operation: Callable[[], Any]) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.op = op
        self._operation = operation
        self.signals = FolderTaskSignals()

    def run(self) -> None:
        """Executa a operação e emite sucesso/erro."""
        try:
            value = self._operation()
            self.signals.success.emit(self.op, str(value))
        except Exception as e:
            _logger().error(
                f"Falha na operação de pasta '{self.op}'",
                code="PSM_TASK_ERR",
                error=str(e),
            )
            self.signals.error.emit(self.op, str(e))


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
