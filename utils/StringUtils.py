# -*- coding: utf-8 -*-
"""
StringUtils — Catálogo de dicionários de extensões e utilitários de string
============================================================================
Fornece dicionários padronizados de extensões de arquivo para uso em
widgets como SimpleComboBox, GridCheckBox, etc.

Cada entrada tem:
    label       → texto exibido
    description → tooltip/dica

Uso:
    from utils.StringUtils import StringUtils
    ext_dict = StringUtils.LAS_EXTENSIONS
    combo = SimpleComboBox(items=ext_dict)
"""

from __future__ import annotations

from typing import Any, Dict


class StringUtils:
    """
    Dicionários de extensões de arquivo organizados por categoria.
    Cada dict tem formato {extensão: {"label": str, "description": str}}.
    """

    # ── LAS / LAZ ──────────────────────────────────────────────────
    LAS_EXTENSIONS: Dict[str, Dict[str, Any]] = {
        ".las": {"label": ".las", "description": "LAS Point Cloud (ASPRS)"},
        ".laz": {"label": ".laz", "description": "LAZ Point Cloud (comprimido)"},
    }

    # ── Vetores ────────────────────────────────────────────────────
    VECTOR_EXTENSIONS: Dict[str, Dict[str, Any]] = {
        ".shp":    {"label": ".shp",    "description": "Shapefile (geometria)"},
        ".gpkg":   {"label": ".gpkg",   "description": "GeoPackage"},
        ".geojson":{"label": ".geojson","description": "GeoJSON"},
        ".csv":    {"label": ".csv",    "description": "Valores separados por vírgula"},
        ".kml":    {"label": ".kml",    "description": "Keyhole Markup Language"},
    }

    # ── Raster ─────────────────────────────────────────────────────
    RASTER_EXTENSIONS: Dict[str, Dict[str, Any]] = {
        ".tif":  {"label": ".tif",  "description": "GeoTIFF"},
        ".tiff": {"label": ".tiff", "description": "Tagged Image File Format"},
        ".jp2":  {"label": ".jp2",  "description": "JPEG 2000"},
        ".dem":  {"label": ".dem",  "description": "Digital Elevation Model"},
        ".ecw":  {"label": ".ecw",  "description": "Enhanced Compressed Wavelet"},
        ".sid":  {"label": ".sid",  "description": "MrSID Image"},
        ".img":  {"label": ".img",  "description": "ERDAS IMAGINE"},
        ".vrt":  {"label": ".vrt",  "description": "GDAL Virtual Raster"},
    }

    # ── Documentos ─────────────────────────────────────────────────
    DOCUMENT_EXTENSIONS: Dict[str, Dict[str, Any]] = {
        ".pdf":  {"label": ".pdf",  "description": "Adobe Portable Document"},
        ".docx": {"label": ".docx", "description": "Microsoft Word (moderno)"},
        ".xlsx": {"label": ".xlsx", "description": "Microsoft Excel (moderno)"},
        ".txt":  {"label": ".txt",  "description": "Arquivo de texto puro"},
        ".md":   {"label": ".md",   "description": "Markdown"},
        ".json": {"label": ".json", "description": "JavaScript Object Notation"},
        ".xml":  {"label": ".xml",  "description": "eXtensible Markup Language"},
        ".html": {"label": ".html", "description": "HyperText Markup Language"},
        ".csv":  {"label": ".csv",  "description": "Valores separados por vírgula"},
    }

    @staticmethod
    def get_extensions_list(ext_dict: Dict[str, Dict[str, Any]]) -> list[str]:
        """
        Extrai apenas as extensões (chaves) de um dicionário de extensões.

        Args:
            ext_dict: Dict no formato {".ext": {"label": ..., "description": ...}}

        Returns:
            Lista de extensões, ex: [".las", ".laz"]
        """
        return list(ext_dict.keys())

    @staticmethod
    def get_extensions_filter(ext_dict: Dict[str, Dict[str, Any]]) -> str:
        """
        Gera um filtro de arquivo no formato usado por QFileDialog.

        Args:
            ext_dict: Dict no formato {".ext": {"label": ..., "description": ...}}

        Returns:
            String de filtro, ex: "LAS/LAZ (*.las *.laz)"
        """
        exts = StringUtils.get_extensions_list(ext_dict)
        patterns = " ".join(f"*{e}" for e in exts)
        return f"{patterns}"