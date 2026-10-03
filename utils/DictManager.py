# -*- coding: utf-8 -*-
"""
DictManager — Catálogo centralizado de dicionários do sistema
===============================================================
Fornece dicionários padronizados para uso em widgets como GridCheckBox.

Cada entrada tem:
    label       → texto exibido
    description → tooltip/dica
    default     → valor padrão (True = checado, False = deschecado)

Cada categoria tem sua própria constante no topo do módulo.
O método `file_extensions()` mescla todas e retorna o dict completo.
"""

from __future__ import annotations

from typing import Any, Dict


# ── Backup ──
BAK_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".bak":   {"label": ".bak",   "description": "Arquivo de backup", "default": False},
    ".lock":  {"label": ".lock",  "description": "Arquivo de lock (dependências)", "default": False},
    ".old":   {"label": ".old",   "description": "Arquivo de versão anterior", "default": False},
    ".tmp":   {"label": ".tmp",   "description": "Arquivo temporário", "default": False},
}

# ── Config / Setup ──
CONFIG_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".cfg":   {"label": ".cfg",   "description": "Arquivo de configuração genérico", "default": True},
    ".env":   {"label": ".env",   "description": "Variáveis de ambiente", "default": True},
    ".ini":   {"label": ".ini",   "description": "Arquivo de configuração", "default": True},
    ".toml":  {"label": ".toml",  "description": "TOML (config moderno)", "default": True},
    ".yaml":  {"label": ".yaml",  "description": "YAML alternativo", "default": True},
    ".yml":   {"label": ".yml",   "description": "YAML (recursos, config)", "default": True},
}

# ── Documentos ──
DOCUMENT_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".csv":   {"label": ".csv",   "description": "Valores separados por vírgula", "default": True},
    ".doc":   {"label": ".doc",   "description": "Microsoft Word (antigo)", "default": True},
    ".docx":  {"label": ".docx",  "description": "Microsoft Word (moderno)", "default": True},
    ".html":  {"label": ".html",  "description": "HyperText Markup Language", "default": True},
    ".json":  {"label": ".json",  "description": "JavaScript Object Notation", "default": True},
    ".log":   {"label": ".log",   "description": "Arquivo de log", "default": True},
    ".md":    {"label": ".md",    "description": "Markdown", "default": True},
    ".pdf":   {"label": ".pdf",   "description": "Adobe Portable Document", "default": True},
    ".rtf":   {"label": ".rtf",   "description": "Rich Text Format", "default": True},
    ".txt":   {"label": ".txt",   "description": "Arquivo de texto puro", "default": True},
    ".xml":   {"label": ".xml",   "description": "eXtensible Markup Language", "default": True},
}

# ── Geoprocessamento ──
GEOPROCESSOR_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".dbf":    {"label": ".dbf",    "description": "Shapefile (atributos dBASE)", "default": True},
    ".dem":    {"label": ".dem",    "description": "Digital Elevation Model", "default": True},
    ".ecw":    {"label": ".ecw",    "description": "Enhanced Compressed Wavelet", "default": True},
    ".geojson":{"label": ".geojson","description": "GeoJSON", "default": True},
    ".gpkg":   {"label": ".gpkg",   "description": "GeoPackage", "default": True},
    ".grd":    {"label": ".grd",    "description": "Surfer Grid / DEM", "default": True},
    ".hdf":    {"label": ".hdf",    "description": "Hierarchical Data Format", "default": True},
    ".jp2":    {"label": ".jp2",    "description": "JPEG 2000", "default": True},
    ".las":    {"label": ".las",    "description": "LIDAR Point Cloud (ASPRS)", "default": True},
    ".laz":    {"label": ".laz",    "description": "LIDAR Point Cloud (comprimido)", "default": True},
    ".nc":     {"label": ".nc",     "description": "NetCDF", "default": True},
    ".prj":    {"label": ".prj",    "description": "Shapefile (projeção)", "default": True},
    ".qpj":    {"label": ".qpj",    "description": "Shapefile (projeção QGIS)", "default": True},
    ".shp":    {"label": ".shp",    "description": "Shapefile (geometria)", "default": True},
    ".shx":    {"label": ".shx",    "description": "Shapefile (índice)", "default": True},
    ".sid":    {"label": ".sid",    "description": "MrSID Image", "default": True},
    ".vrt":    {"label": ".vrt",    "description": "GDAL Virtual Raster", "default": True},
    "qmd":     {"label": ".qmd",     "description": "QGIS Project (Markdown)", "default": True},
    "cpg":     {"label": ".cpg",     "description": "Shapefile (codificação)", "default": True},
    "qix":     {"label": ".qix",     "description": "Shapefile (índice QGIS)", "default": True},
}

# ── Tamanhos de Ícone ICO (ImageConverter) ──
ICO_SIZES: Dict[str, Dict[str, Any]] = {
    "16":   {"label": "16 pixels",   "description": "16x16", "default": True},
    "32":   {"label": "32 pixels",   "description": "32x32", "default": True},
    "48":   {"label": "48 pixels",   "description": "48x48", "default": True},
    "64":   {"label": "64 pixels",   "description": "64x64", "default": True},
    "128":  {"label": "128 pixels",  "description": "128x128", "default": True},
    "256":  {"label": "256 pixels",  "description": "256x256", "default": False},
}

# ── Formatos de Saída de Imagem (ImageConverter) ──
OUTPUT_IMAGE_FORMATS: Dict[str, Dict[str, Any]] = {
    "PNG":  {"label": "PNG",  "description": "Portable Network Graphics (lossless)", "ext": ".png",  "lossy": False, "supports_alpha": True,  "supports_ico_sizes": False},
    "JPEG": {"label": "JPEG", "description": "Joint Photographic Experts Group (lossy)", "ext": ".jpg",  "lossy": True,  "supports_alpha": False, "supports_ico_sizes": False},
    "BMP":  {"label": "BMP",  "description": "Bitmap Image (lossless)", "ext": ".bmp",  "lossy": False, "supports_alpha": False, "supports_ico_sizes": False},
    "GIF":  {"label": "GIF",  "description": "Graphics Interchange Format (palette)", "ext": ".gif",  "lossy": True,  "supports_alpha": True,  "supports_ico_sizes": False},
    "TIFF": {"label": "TIFF", "description": "Tagged Image File Format (lossless)", "ext": ".tif",  "lossy": False, "supports_alpha": True,  "supports_ico_sizes": False},
    "WEBP": {"label": "WEBP", "description": "WebP Image (lossy/lossless)", "ext": ".webp", "lossy": True,  "supports_alpha": True,  "supports_ico_sizes": False},
    "ICO":  {"label": "ICO",  "description": "Windows Icon (multi-size)", "ext": ".ico",  "lossy": False, "supports_alpha": True,  "supports_ico_sizes": True},
}

# ── Imagens / Raster ──
IMAGE_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".bmp":   {"label": ".bmp",   "description": "Bitmap Image", "default": True},
    ".gif":   {"label": ".gif",   "description": "Graphics Interchange Format", "default": True},
    ".ico":   {"label": ".ico",   "description": "Windows Icon", "default": False},
    ".jpeg":  {"label": ".jpeg",  "description": "JPEG Image (alternativo)", "default": True},
    ".jpg":   {"label": ".jpg",   "description": "JPEG Image", "default": True},
    ".png":   {"label": ".png",   "description": "Portable Network Graphics", "default": True},
    ".svg":   {"label": ".svg",   "description": "Scalable Vector Graphics", "default": True},
    ".tif":   {"label": ".tif",   "description": "Tagged Image File (GeoTIFF)", "default": True},
    ".tiff":  {"label": ".tiff",  "description": "Tagged Image File Format", "default": True},
}

# ── Keras / ML ──
KERAS_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".h5":    {"label": ".h5",    "description": "HDF5 (modelos Keras/TF)", "default": True},
    ".keras": {"label": ".keras", "description": "Keras modelo salvo", "default": True},
    ".onnx":  {"label": ".onnx",  "description": "Open Neural Network Exchange", "default": True},
    ".pt":    {"label": ".pt",    "description": "PyTorch model", "default": True},
    ".pth":   {"label": ".pth",   "description": "PyTorch model (alternativo)", "default": True},
}

# ── Programação ──
PROGRAMMING_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".bat":   {"label": ".bat",   "description": "Windows batch script", "default": True},
    ".cpp":   {"label": ".cpp",   "description": "C++ source", "default": False},
    ".css":   {"label": ".css",   "description": "Cascading Style Sheets", "default": True},
    ".h":     {"label": ".h",     "description": "C/C++ header", "default": False},
    ".js":    {"label": ".js",    "description": "JavaScript source", "default": True},
    ".ps1":   {"label": ".ps1",   "description": "PowerShell script", "default": True},
    ".py":    {"label": ".py",    "description": "Python source", "default": True},
    ".qss":   {"label": ".qss",   "description": "Qt Style Sheet", "default": True},
    ".ts":    {"label": ".ts",    "description": "TypeScript source", "default": True},
}

# ── Planilhas ──
SPREADSHEET_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".xls":   {"label": ".xls",   "description": "Microsoft Excel (antigo)", "default": True},
    ".xlsx":  {"label": ".xlsx",  "description": "Microsoft Excel (moderno)", "default": True},
}

# ── Football — Top Clubs (World) ──────────────────────────────────────
TOP_CLUBS_WORLD: Dict[str, Dict[str, Any]] = {
    "real_madrid":       {"label": "Real Madrid",       "description": "Spain - La Liga",          "default": True},
    "barcelona":         {"label": "Barcelona",         "description": "Spain - La Liga",          "default": True},
    "atletico_madrid":   {"label": "Atletico Madrid",   "description": "Spain - La Liga",          "default": True},
    "man_city":          {"label": "Manchester City",   "description": "England - Premier League", "default": True},
    "man_united":        {"label": "Manchester United", "description": "England - Premier League", "default": True},
    "liverpool":         {"label": "Liverpool",         "description": "England - Premier League", "default": True},
    "chelsea":           {"label": "Chelsea",           "description": "England - Premier League", "default": True},
    "arsenal":           {"label": "Arsenal",           "description": "England - Premier League", "default": True},
    "tottenham":         {"label": "Tottenham",         "description": "England - Premier League", "default": True},
    "psg":               {"label": "PSG",               "description": "France - Ligue 1",         "default": True},
    "marseille":         {"label": "Marseille",         "description": "France - Ligue 1",         "default": True},
    "lyon":              {"label": "Lyon",              "description": "France - Ligue 1",         "default": True},
    "bayern_munich":     {"label": "Bayern Munich",     "description": "Germany - Bundesliga",     "default": True},
    "borussia_dortmund": {"label": "Borussia Dortmund", "description": "Germany - Bundesliga",     "default": True},
    "rb_leipzig":        {"label": "RB Leipzig",        "description": "Germany - Bundesliga",     "default": True},
    "juventus":          {"label": "Juventus",          "description": "Italy - Serie A",          "default": True},
    "inter_milan":       {"label": "Inter",             "description": "Italy - Serie A",          "default": True},
    "ac_milan":          {"label": "AC Milan",          "description": "Italy - Serie A",          "default": True},
    "napoli":            {"label": "Napoli",            "description": "Italy - Serie A",          "default": True},
    "roma":              {"label": "Roma",              "description": "Italy - Serie A",          "default": True},
    "ajax":              {"label": "Ajax",              "description": "Netherlands - Eredivisie", "default": True},
    "psv":               {"label": "PSV Eindhoven",     "description": "Netherlands - Eredivisie", "default": True},
    "feyenoord":         {"label": "Feyenoord",         "description": "Netherlands - Eredivisie", "default": True},
    "porto":             {"label": "Porto",             "description": "Portugal - Primeira Liga", "default": True},
    "benfica":           {"label": "Benfica",           "description": "Portugal - Primeira Liga", "default": True},
    "sporting":          {"label": "Sporting CP",       "description": "Portugal - Primeira Liga", "default": True},
    "celtic":            {"label": "Celtic",            "description": "Scotland - Premiership",   "default": True},
    "rangers":           {"label": "Rangers",           "description": "Scotland - Premiership",   "default": True},
    "al_hilal":          {"label": "Al Hilal",          "description": "Saudi Arabia - SPL",       "default": True},
    "al_nassr":          {"label": "Al Nassr",          "description": "Saudi Arabia - SPL",       "default": True},
    "al_ittihad":        {"label": "Al Ittihad",        "description": "Saudi Arabia - SPL",       "default": True},
    "boca_juniors":      {"label": "Boca Juniors",      "description": "Argentina - Liga Profesional", "default": True},
    "river_plate":       {"label": "River Plate",       "description": "Argentina - Liga Profesional", "default": True},
}

# ── Football — Top Clubs (Brazil) ─────────────────────────────────────
TOP_CLUBS_BRAZIL: Dict[str, Dict[str, Any]] = {
    "flamengo":          {"label": "Flamengo",          "description": "Brazil - Serie A", "default": True},
    "palmeiras":         {"label": "Palmeiras",         "description": "Brazil - Serie A", "default": True},
    "corinthians":       {"label": "Corinthians",       "description": "Brazil - Serie A", "default": True},
    "sao_paulo":         {"label": "Sao Paulo",         "description": "Brazil - Serie A", "default": True},
    "santos":            {"label": "Santos",            "description": "Brazil - Serie A", "default": True},
    "gremio":            {"label": "Gremio",            "description": "Brazil - Serie A", "default": True},
    "internacional":     {"label": "Internacional",     "description": "Brazil - Serie A", "default": True},
    "cruzeiro":          {"label": "Cruzeiro",          "description": "Brazil - Serie A", "default": True},
    "atletico_mineiro":  {"label": "Atletico Mineiro",  "description": "Brazil - Serie A", "default": True},
    "fluminense":        {"label": "Fluminense",        "description": "Brazil - Serie A", "default": True},
    "vasco":             {"label": "Vasco",             "description": "Brazil - Serie A", "default": True},
    "botafogo":          {"label": "Botafogo",          "description": "Brazil - Serie A", "default": True},
}

# ── Football — Top National Teams ─────────────────────────────────────
TOP_NATIONAL_TEAMS: Dict[str, Dict[str, Any]] = {
    "brazil":            {"label": "Brazil",            "description": "CONMEBOL", "default": True},
    "argentina":         {"label": "Argentina",         "description": "CONMEBOL", "default": True},
    "germany":           {"label": "Germany",           "description": "UEFA",    "default": True},
    "france":            {"label": "France",            "description": "UEFA",    "default": True},
    "spain":             {"label": "Spain",             "description": "UEFA",    "default": True},
    "england":           {"label": "England",           "description": "UEFA",    "default": True},
    "portugal":          {"label": "Portugal",          "description": "UEFA",    "default": True},
    "italy":             {"label": "Italy",             "description": "UEFA",    "default": True},
    "netherlands":       {"label": "Netherlands",       "description": "UEFA",    "default": True},
    "belgium":           {"label": "Belgium",           "description": "UEFA",    "default": True},
}

# ── Football — Top Competitions (long list) ───────────────────────────
TOP_COMPETITIONS: Dict[str, Dict[str, Any]] = {
    "world_cup":                 {"label": "World Cup",                 "description": "FIFA",            "default": True},
    "champions_league":          {"label": "UEFA Champions League",     "description": "UEFA",            "default": True},
    "europa_league":             {"label": "UEFA Europa League",        "description": "UEFA",            "default": True},
    "conference_league":         {"label": "UEFA Europa Conference League", "description": "UEFA",        "default": True},
    "libertadores":              {"label": "Copa Libertadores",         "description": "CONMEBOL",        "default": True},
    "sudamericana":              {"label": "Copa Sudamericana",         "description": "CONMEBOL",        "default": True},
    "premier_league":            {"label": "Premier League",            "description": "England",         "default": True},
    "la_liga":                   {"label": "La Liga",                   "description": "Spain",           "default": True},
    "serie_a_italy":             {"label": "Serie A",                   "description": "Italy",           "default": True},
    "bundesliga":                {"label": "Bundesliga",                "description": "Germany",         "default": True},
    "ligue_1":                   {"label": "Ligue 1",                   "description": "France",          "default": True},
    "brasileirao":               {"label": "Brasileirao",               "description": "Brazil - Serie A","default": True},
    "copa_do_brasil":            {"label": "Copa do Brasil",            "description": "Brazil",          "default": True},
    "primeira_liga":             {"label": "Primeira Liga",             "description": "Portugal",        "default": True},
    "eredivisie":                {"label": "Eredivisie",                "description": "Netherlands",     "default": True},
    "copa_america":              {"label": "Copa America",              "description": "CONMEBOL",        "default": True},
    "euro_championship":         {"label": "Euro Championship",         "description": "UEFA",            "default": True},
    "afc_champions_league":      {"label": "AFC Champions League",      "description": "AFC",             "default": True},
}

# ── Football — Filtered Competitions (only these are used for filtering) ──
TOP_COMPETITIONS_FILTER: Dict[str, Dict[str, Any]] = {
    "world_cup":            {"label": "World Cup",            "description": "FIFA",     "default": True},
    "libertadores":         {"label": "Copa Libertadores",    "description": "CONMEBOL", "default": True},
    "copa_america":         {"label": "Copa America",         "description": "CONMEBOL", "default": True},
    "copa_america_pt":      {"label": "Copa América",         "description": "CONMEBOL", "default": True},
}

# ── Texto editável (abre como bloco de notas) ─────────────────────────
TEXT_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".bat":   {"label": ".bat",   "description": "Windows batch script", "default": True},
    ".cfg":   {"label": ".cfg",   "description": "Arquivo de configuração genérico", "default": True},
    ".cpp":   {"label": ".cpp",   "description": "C++ source", "default": True},
    ".css":   {"label": ".css",   "description": "Cascading Style Sheets", "default": True},
    ".csv":   {"label": ".csv",   "description": "Valores separados por vírgula", "default": True},
    ".env":   {"label": ".env",   "description": "Variáveis de ambiente", "default": True},
    ".h":     {"label": ".h",     "description": "C/C++ header", "default": True},
    ".html":  {"label": ".html",  "description": "HyperText Markup Language", "default": True},
    ".ini":   {"label": ".ini",   "description": "Arquivo de configuração", "default": True},
    ".js":    {"label": ".js",    "description": "JavaScript source", "default": True},
    ".json":  {"label": ".json",  "description": "JavaScript Object Notation", "default": True},
    ".log":   {"label": ".log",   "description": "Arquivo de log", "default": True},
    ".md":    {"label": ".md",    "description": "Markdown", "default": True},
    ".ps1":   {"label": ".ps1",   "description": "PowerShell script", "default": True},
    ".py":    {"label": ".py",    "description": "Python source", "default": True},
    ".qss":   {"label": ".qss",   "description": "Qt Style Sheet", "default": True},
    ".rtf":   {"label": ".rtf",   "description": "Rich Text Format", "default": True},
    ".toml":  {"label": ".toml",  "description": "TOML (config moderno)", "default": True},
    ".ts":    {"label": ".ts",    "description": "TypeScript source", "default": True},
    ".txt":   {"label": ".txt",   "description": "Arquivo de texto puro", "default": True},
    ".xml":   {"label": ".xml",   "description": "eXtensible Markup Language", "default": True},
    ".yaml":  {"label": ".yaml",  "description": "YAML alternativo", "default": True},
    ".yml":   {"label": ".yml",   "description": "YAML (recursos, config)", "default": True},
}


class DictManager:
    """
    Métodos estáticos que retornam dicionários padronizados.

    As constantes de módulo (ex: DOCUMENT_EXTENSIONS) podem ser usadas
    individualmente; o método `file_extensions()` mescla todas.
    """

    @staticmethod
    def file_extensions() -> Dict[str, Dict[str, Any]]:
        """
        Retorna o catálogo completo de extensões mesclando todas
        as constantes de categoria.

        Retorna:
            { ".ext": { "label": "...", "description": "...", "default": bool } }
        """
        return {
            **BAK_EXTENSIONS,
            **CONFIG_EXTENSIONS,
            **DOCUMENT_EXTENSIONS,
            **GEOPROCESSOR_EXTENSIONS,
            **IMAGE_EXTENSIONS,
            **KERAS_EXTENSIONS,
            **PROGRAMMING_EXTENSIONS,
            **SPREADSHEET_EXTENSIONS,
        }

    # ── Football Dictionaries ──────────────────────────────────────

    @staticmethod
    def football_clubs_world() -> Dict[str, Dict[str, Any]]:
        """Top clubs from around the world (non-Brazil)."""
        return TOP_CLUBS_WORLD

    @staticmethod
    def football_clubs_brazil() -> Dict[str, Dict[str, Any]]:
        """Top clubs from Brazil."""
        return TOP_CLUBS_BRAZIL

    @staticmethod
    def football_national_teams() -> Dict[str, Dict[str, Any]]:
        """Top national teams."""
        return TOP_NATIONAL_TEAMS

    @staticmethod
    def football_competitions() -> Dict[str, Dict[str, Any]]:
        """Top competitions / leagues."""
        return TOP_COMPETITIONS

    @staticmethod
    def football_competitions_filter() -> Dict[str, Dict[str, Any]]:
        """Filtered competition list (only these are used for filtering by default)."""
        return TOP_COMPETITIONS_FILTER

    @staticmethod
    def football_filter_labels() -> list[str]:
        """Returns the display labels for filter matching using the FILTER competition list."""
        result: list[str] = []
        for d in (TOP_CLUBS_WORLD, TOP_CLUBS_BRAZIL, TOP_NATIONAL_TEAMS):
            for entry in d.values():
                result.append(entry["label"])
        # Use the short filter list for competitions, not the full list
        for entry in TOP_COMPETITIONS_FILTER.values():
            result.append(entry["label"])
        return result
