# -*- coding: utf-8 -*-
"""
ProjectDatabaseBackup — Backup diário do Banco de Dados (.BancoDados)
====================================================================
Cria um arquivo ``<YYYYMMDDHHMMSS>.BancoDados.zip`` a partir da pasta
``<pasta-mãe>/.BancoDados``, no máximo uma vez por dia. Reutilizável por
mais de uma ferramenta (Contrato 7 — nenhum plugin importa outro).

Usa ``zipfile`` da stdlib (Contrato 8 — sem dependências externas).

Uso:
    from utils.ProjectDatabaseBackup import ProjectDatabaseBackup

    criado = ProjectDatabaseBackup.ensure_daily_backup(mother_folder)
"""

from __future__ import annotations

import glob
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ExplorerUtils import ExplorerUtils


class ProjectDatabaseBackup(BaseUtil):
    """Rotina de backup diário do Banco de Dados (ZIP)."""

    # Subpasta do banco de dados na raiz da pasta-mãe.
    DB_FOLDER = ".BancoDados"

    # Pasta de backup padrão (portátil — sem usuário embutido).
    DEFAULT_BACKUP_DIR = str(
        Path.home() / "Documents" / "Backups" / "VerraData"
    )

    @classmethod
    def ensure_daily_backup(
        cls,
        mother_folder: str,
        backup_dir: str = "",
        label: str = "BancoDados",
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> Optional[str]:
        """Cria ``<backup>/<YYYYMMDDHHMMSS>.<label>.zip`` a partir do banco.

        Args:
            mother_folder: Pasta-mãe que contém ``.BancoDados``.
            backup_dir: Pasta de destino (vazio = ``DEFAULT_BACKUP_DIR``).
            label: Rótulo do arquivo (``<label>.zip``).
            tool_key: Chave da ferramenta para logging (Contrato 26).

        Returns:
            Caminho do ZIP criado, ou ``None`` se já havia backup do dia,
            a origem não existe ou houve falha.
        """
        logger = cls._get_logger(tool_key, "ProjectDatabaseBackup")

        if not mother_folder:
            logger.info(
                "Pasta-mãe não informada — backup ignorado",
                code="PDB_BKP_NO_MOTHER",
            )
            return None

        source = Path(mother_folder) / cls.DB_FOLDER
        if not source.is_dir():
            logger.info(
                "Banco de dados inexistente — backup ignorado",
                code="PDB_BKP_NO_SOURCE",
                path=str(source),
            )
            return None

        dest_dir = Path(backup_dir) if backup_dir else Path(cls.DEFAULT_BACKUP_DIR)
        today = datetime.now().strftime("%Y%m%d")
        existing = glob.glob(str(dest_dir / f"{today}*.{label}.zip"))
        if existing:
            logger.info(
                "Backup do dia já existe — ignorado",
                code="PDB_BKP_SKIP",
                path=existing[0],
            )
            return None

        try:
            ExplorerUtils.ensure_directory(str(dest_dir), tool_key=tool_key)
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            target = dest_dir / f"{stamp}.{label}.zip"
            cls._zip_directory(source, target)
            logger.info(
                "Backup diário criado",
                code="PDB_BKP_OK",
                path=str(target),
            )
            return str(target)
        except (OSError, zipfile.BadZipFile) as e:
            logger.error(
                "Falha ao criar backup diário",
                code="PDB_BKP_ERR",
                error=str(e),
                path=str(source),
            )
            return None

    @staticmethod
    def _zip_directory(source: Path, target: Path) -> None:
        """Compacta ``source`` em ``target`` guardando caminhos relativos."""
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(source):
                for file_name in files:
                    full = Path(root) / file_name
                    rel = full.relative_to(source)
                    zf.write(full, arcname=str(Path(source.name) / rel))
