# -*- coding: utf-8 -*-
"""
ReportSource — Fonte dos dados do relatório (pasta e arquivos da OS)
===================================================================
Resolve a pasta física da OS, o caminho de cada base (``limites`` /
``zonas_manejo``) e monta o ``ReportContext`` com as SHAPES já convertidas em
GeoJSON.

É a ÚNICA classe do submódulo que conversa com o domínio do Acompanhamento de
OS (``OsTrackerService``) — os builders de painel recebem tudo pronto e não
conhecem disco, banco nem Qt.

Uso:
    from plugins.os_tracker.report.ReportSource import ReportSource

    context = ReportSource.context(mother, record, tool_key)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from core.enum.ToolKey import ToolKey
from plugins.os_tracker.OsTrackerService import OsTrackerService
from utils.BaseUtil import BaseUtil

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.ShapeGeoJsonReader import ShapeGeoJsonReader


class ReportSource(BaseUtil):
    """Resolve pasta/arquivos da OS e monta o contexto dos builders."""

    # Bases gravadas na OS que entram no relatório.
    ASSET_KEYS: Tuple[str, ...] = ("limites", "zonas_manejo")
    DATE_FORMAT = "%d/%m/%Y %H:%M"

    @classmethod
    def os_folder(
        cls,
        mother: Optional[Path],
        record: Optional[Dict[str, Any]],
    ) -> Optional[Path]:
        """Pasta física da OS (``None`` quando o registro não tem pasta)."""
        return OsTrackerService.project_folder(mother, record)

    @classmethod
    def asset_paths(
        cls,
        mother: Optional[Path],
        record: Optional[Dict[str, Any]],
    ) -> Dict[str, str]:
        """Caminho absoluto do vetor de cada base gravada na OS."""
        return {
            key: OsTrackerService.asset_file_path(mother, record, key)
            for key in cls.ASSET_KEYS
        }

    @classmethod
    def context(
        cls,
        mother: Optional[Path],
        record: Optional[Dict[str, Any]],
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> ReportContext:
        """Contexto do relatório: dados do registro + bases + shapes em GeoJSON."""
        paths = cls.asset_paths(mother, record)
        folder = cls.os_folder(mother, record)
        return ReportContext(
            record=dict(record or {}),
            mother=Path(mother) if mother else None,
            tool_key=tool_key,
            generated_at=datetime.now().strftime(cls.DATE_FORMAT),
            data_version=cls.data_version(record, tool_key),
            os_folder=str(folder) if folder is not None else "",
            asset_paths=paths,
            assets={
                key: OsTrackerService.asset_info(record, key)
                for key in cls.ASSET_KEYS
            },
            shapes={
                key: ShapeGeoJsonReader.read(path, key, tool_key)
                for key, path in paths.items()
            },
        )

    @classmethod
    def data_version(
        cls,
        record: Optional[Dict[str, Any]],
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> str:
        """Data da última atualização do registro (``—`` quando não houver)."""
        updated = str((record or {}).get("updated_at", "") or "")
        return OsTrackerService.format_when(updated, tool_key) or "—"
