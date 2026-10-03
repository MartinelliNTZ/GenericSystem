# -*- coding: utf-8 -*-
"""
VectorLayerSource — I/O de camadas vetoriais (Shapefile, GeoPackage, CSV)
==========================================================================
Classe estatica unica para leitura de dados vetoriais.
Usa geopandas para .shp/.gpkg e csv.DictReader para .csv.

Responsabilidades:
    - Carregar, salvar, validar, clonar camadas vetoriais
    - I/O de arquivos (Shapefile, GeoPackage, CSV)
    - Validacao de camadas com regras padronizadas
    - Exportacao para GPKG temporario
    - Gerenciamento de conflitos de nomes

Uso:
    from utils.vector.VectorLayerSource import VectorLayerSource
    data = VectorLayerSource.read("dados.shp", tool_key=ToolKey.MEU_PLUGIN.value)
    saved = VectorLayerSource.save_vector_layer(layer, save_to_folder=True, ...)
"""

from __future__ import annotations

import csv
import os
from typing import Any, List, Optional, Tuple

import numpy as np

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class VectorLayerSource(BaseUtil):
    """
    Metodos estaticos para I/O de camadas vetoriais.
    Converte tipos numpy para tipos nativos Python automaticamente.
    Nao transforma geometrias — use VectorLayerGeometry para isso.
    """

    _SUPPORTED_EXTENSIONS = frozenset({".shp", ".gpkg", ".csv", ".kml", ".geojson"})

    # ── API Publica — Leitura ────────────────────────────────────────

    @staticmethod
    def read(path: str, tool_key: str = ToolKey.UNTRACEABLE.value) -> List[dict]:
        """
        Le um arquivo vetorial e retorna lista de dicionarios.

        Args:
            path: Caminho do arquivo (.shp, .gpkg, .csv).
            tool_key: Chave da ferramenta para logging.

        Returns:
            Lista de dicts com os dados. Cada dict = uma linha/feature.
            Vazio se arquivo invalido ou vazio.

        Raises:
            ValueError: Se extensao nao suportada.
            FileNotFoundError: Se arquivo nao existe.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("Lendo arquivo vetorial", code="VECTOR_READ_START", path=path)

        if not os.path.exists(path):
            logger.error("Arquivo nao encontrado", code="VECTOR_NOT_FOUND", path=path)
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

        ext = os.path.splitext(path)[1].lower()
        if ext not in VectorLayerSource._SUPPORTED_EXTENSIONS:
            logger.error(
                "Extensao nao suportada",
                code="VECTOR_UNSUPPORTED_EXT",
                path=path,
                extension=ext,
                supported=list(VectorLayerSource._SUPPORTED_EXTENSIONS),
            )
            raise ValueError(
                f"Extensao '{ext}' nao suportada. "
                f"Use: {', '.join(VectorLayerSource._SUPPORTED_EXTENSIONS)}"
            )

        try:
            if ext == ".csv":
                data = VectorLayerSource._read_csv(path)
            else:
                data = VectorLayerSource._read_geo(path)

            logger.info(
                "Arquivo lido com sucesso",
                code="VECTOR_READ_DONE",
                path=path,
                record_count=len(data),
            )
            return data

        except Exception as e:
            logger.error("Falha ao ler arquivo vetorial", code="VECTOR_READ_ERR", path=path, error=str(e))
            raise

    @staticmethod
    def get_driver_name(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna o nome do driver/formato baseado na extensao.

        Args:
            path: Caminho do arquivo.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Nome legivel do formato: "ESRI Shapefile", "GeoPackage", "CSV", ou "Desconhecido".
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        ext = os.path.splitext(path)[1].lower()
        drivers = {
            ".shp": "ESRI Shapefile",
            ".gpkg": "GeoPackage",
            ".csv": "CSV",
            ".kml": "KML",
            ".geojson": "GeoJSON",
        }
        result = drivers.get(ext, "Desconhecido")
        logger.debug("Driver obtido", code="VECTOR_DRIVER", path=path, driver=result)
        return result

    # ── API Publica — Salvamento ─────────────────────────────────────

    @staticmethod
    def save_vector_layer(
        layer: Any,
        save_to_folder: bool = True,
        output_path: Optional[str] = None,
        output_name: Optional[str] = None,
        decision: str = "rename",
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Salva camada (memoria ou disco).
        decision: "rename" ou "overwrite".

        Args:
            layer: QgsVectorLayer
            save_to_folder: Salvar em pasta
            output_path: Caminho de saida
            output_name: Nome de saida
            decision: "rename" ou "overwrite"
            external_tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "VectorLayerSource")
        logger.info("save_vector_layer chamado — stub", code="VECTOR_SAVE_STUB")
        return None

    @staticmethod
    def save_layer_to_path(
        layer: Any,
        output_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        decision: str = "rename",
    ) -> Optional[str]:
        """
        Salva e retorna caminho efetivo.

        Args:
            layer: QgsVectorLayer
            output_path: Caminho de saida
            tool_key: Chave da ferramenta para logging
            decision: "rename" ou "overwrite"

        Returns:
            Caminho efetivo ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("save_layer_to_path chamado — stub", code="VECTOR_SAVE_STUB")
        return output_path

    @staticmethod
    def save_and_load_layer(
        layer: Any,
        output_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        decision: str = "rename",
    ) -> Any:
        """
        Salva e retorna camada carregada.

        Args:
            layer: QgsVectorLayer
            output_path: Caminho de saida
            tool_key: Chave da ferramenta para logging
            decision: "rename" ou "overwrite"

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("save_and_load_layer chamado — stub", code="VECTOR_SAVE_STUB")
        return None

    # ── API Publica — Carregamento ───────────────────────────────────

    @staticmethod
    def load_existing_vector_layer(
        file_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Carrega camada de arquivo existente.

        Args:
            file_path: Caminho do arquivo
            tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("load_existing_vector_layer chamado — stub", code="VECTOR_LOAD_STUB")
        return None

    # ── API Publica — Utilitarios ────────────────────────────────────

    @staticmethod
    def get_layer_file_size(
        layer: Any,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> int:
        """
        Tamanho do datasource em bytes.

        Args:
            layer: QgsVectorLayer
            tool_key: Chave da ferramenta para logging

        Returns:
            Tamanho em bytes.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("get_layer_file_size chamado — stub", code="VECTOR_UTIL_STUB")
        return 0

    @staticmethod
    def get_extension(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Extensao normalizada do caminho.

        Args:
            path: Caminho do arquivo
            tool_key: Chave da ferramenta para logging

        Returns:
            Extensao em lowercase.
        """
        return os.path.splitext(path)[1].lower()

    @staticmethod
    def export_temp_layer(
        layer: Any,
        prefix: str = "temp",
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[str]:
        """
        Exporta para GPKG temporario.

        Args:
            layer: QgsVectorLayer
            prefix: Prefixo do nome
            external_tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do GPKG temporario ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "VectorLayerSource")
        logger.info("export_temp_layer chamado — stub", code="VECTOR_UTIL_STUB")
        return None

    @staticmethod
    def delete_shapefile_set(
        base_path: str,
        retries: int = 3,
        delay: float = 0.5,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Remove conjunto de arquivos SHP.

        Args:
            base_path: Caminho base do shapefile
            retries: Tentativas de remocao
            delay: Delay entre tentativas
            tool_key: Chave da ferramenta para logging

        Returns:
            True se removido com sucesso.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("delete_shapefile_set chamado — stub", code="VECTOR_UTIL_STUB")
        return False

    @staticmethod
    def generate_incremental_path(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Gera caminho incremental (arquivo_1, _2, ...).

        Args:
            path: Caminho base
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho incremental.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("generate_incremental_path chamado — stub", code="VECTOR_UTIL_STUB")
        return path

    # ── API Publica — Validacao ──────────────────────────────────────

    @staticmethod
    def validate_layer(
        layer: Any,
        expected_geometry: Any = None,
        require_editable: bool = False,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Tuple[bool, str]:
        """
        Valida camada com regras padronizadas.

        Args:
            layer: QgsVectorLayer
            expected_geometry: QgsWkbTypes esperado (opcional)
            require_editable: Exige modo de edicao
            tool_key: Chave da ferramenta para logging

        Returns:
            (valido, mensagem).
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("validate_layer chamado — stub", code="VECTOR_VALIDATE_STUB")
        return (False, "Nao implementado")

    # ── Leitura Interna ──────────────────────────────────────────────

    @staticmethod
    def _read_csv(path: str) -> List[dict]:
        """Le CSV usando csv.DictReader."""
        data: List[dict] = []
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned = {k.strip(): v.strip() if v else "" for k, v in row.items()}
                data.append(cleaned)
        return data

    @staticmethod
    def _read_geo(path: str) -> List[dict]:
        """Le Shapefile ou GeoPackage usando geopandas."""
        import geopandas as gpd
        import numpy as np

        gdf = gpd.read_file(path)

        # Remove coluna geometry
        if "geometry" in gdf.columns:
            gdf = gdf.drop(columns=["geometry"])

        # Converte tipos numpy para tipos nativos
        rows: List[dict] = []
        for _, row in gdf.iterrows():
            d = {}
            for col in gdf.columns:
                val = row[col]
                if isinstance(val, (np.integer,)):
                    d[col] = str(int(val))
                elif isinstance(val, (np.floating,)):
                    d[col] = str(float(val))
                elif isinstance(val, (np.bool_,)):
                    d[col] = str(bool(val))
                elif val is None or (isinstance(val, float) and np.isnan(val)):
                    d[col] = ""
                else:
                    d[col] = str(val)
            rows.append(d)

        return rows

    # ══════════════════════════════════════════════════════════════════
    # API — Extração de Coordenadas (PointBoundaryPlugin)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def extract_point_coordinates(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        sample: int = 0,
        csv_x_field: str = "x",
        csv_y_field: str = "y",
    ) -> tuple[np.ndarray, np.ndarray, dict]:
        """
        Extrai coordenadas (x, y) de arquivos vetoriais de pontos.

        Suporta: .shp, .gpkg, .kml, .geojson, .csv

        Para CSV: usa csv_x_field e csv_y_field para identificar colunas.
        Para KML/GeoJSON/SHP/GPKG: extrai geometrias Point e MultiPoint.

        Args:
            path: Caminho do arquivo.
            tool_key: ToolKey para logging.
            sample: Se > 0, amostragem uniforme.
            csv_x_field: Nome da coluna X (CSV).
            csv_y_field: Nome da coluna Y (CSV).

        Returns:
            (x_array, y_array, metadata) onde metadata contém:
                - n_total: total de pontos
                - n_extraidos: pontos extraídos (após amostragem)
                - crs: CRS em formato string (se disponível)
                - fonte: "shp", "gpkg", "kml", "geojson" ou "csv"
                - fields: lista de nomes de campos (atributos)
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("Extraindo coordenadas de vetor", code="VECTOR_EXTRACT_COORDS", path=path)

        ext = os.path.splitext(path)[1].lower()
        if ext not in VectorLayerSource._SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Extensão '{ext}' não suportada. "
                f"Use: {', '.join(VectorLayerSource._SUPPORTED_EXTENSIONS)}"
            )

        if ext == ".csv":
            return VectorLayerSource._extract_csv_coords(
                path, tool_key, sample, csv_x_field, csv_y_field
            )
        else:
            return VectorLayerSource._extract_geo_coords(
                path, tool_key, sample
            )

    @staticmethod
    def _extract_csv_coords(
        path: str,
        tool_key: str,
        sample: int,
        x_field: str,
        y_field: str,
    ) -> tuple[np.ndarray, np.ndarray, dict]:
        """Extrai coordenadas de CSV."""
        import pandas as pd

        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        df = pd.read_csv(path)

        if x_field not in df.columns or y_field not in df.columns:
            raise ValueError(
                f"Colunas X='{x_field}' ou Y='{y_field}' não encontradas no CSV. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        x = df[x_field].values.astype(np.float64)
        y = df[y_field].values.astype(np.float64)

        n_total = len(x)
        fields = list(df.columns)

        # Remove pontos com NaN
        mask_valido = ~(np.isnan(x) | np.isnan(y))
        x = x[mask_valido]
        y = y[mask_valido]
        n_validos = len(x)

        if n_validos == 0:
            raise ValueError("Nenhum ponto válido encontrado no CSV (todos NaN).")

        # Amostragem
        if sample > 0 and n_validos > sample:
            step = max(1, n_validos // sample)
            x = x[::step]
            y = y[::step]
            n_extraidos = len(x)
        else:
            n_extraidos = n_validos

        metadata = {
            "n_total": n_total,
            "n_extraidos": n_extraidos,
            "crs": "",
            "fonte": "csv",
            "fields": fields,
        }

        logger.info(
            "Coordenadas extraidas do CSV",
            code="VECTOR_CSV_EXTRACT_DONE",
            n_total=n_total,
            n_validos=n_validos,
            n_extraidos=n_extraidos,
            x_field=x_field,
            y_field=y_field,
        )
        return x, y, metadata

    @staticmethod
    def _extract_geo_coords(
        path: str,
        tool_key: str,
        sample: int,
    ) -> tuple[np.ndarray, np.ndarray, dict]:
        """Extrai coordenadas de Shapefile/GPKG/KML/GeoJSON usando geopandas."""
        import geopandas as gpd
        from shapely.geometry import Point, MultiPoint

        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        gdf = gpd.read_file(path)

        if gdf.empty:
            raise ValueError(f"Arquivo vazio: {path}")

        crs = ""
        if gdf.crs is not None:
            crs = str(gdf.crs)

        fields = list(gdf.columns)
        n_total = len(gdf)

        # Extrai coordenadas de Point e MultiPoint
        xs: list[float] = []
        ys: list[float] = []

        for geom in gdf.geometry:
            if geom is None:
                continue
            if geom.geom_type == "Point":
                xs.append(float(geom.x))
                ys.append(float(geom.y))
            elif geom.geom_type == "MultiPoint":
                for pt in geom.geoms:
                    xs.append(float(pt.x))
                    ys.append(float(pt.y))
            else:
                logger.warning(
                    "Geometria ignorada (nao e Point/MultiPoint)",
                    code="VECTOR_SKIP_NON_POINT",
                    geom_type=geom.geom_type,
                )

        if len(xs) == 0:
            raise ValueError(
                "Nenhuma geometria Point ou MultiPoint encontrada no arquivo."
            )

        x = np.array(xs, dtype=np.float64)
        y = np.array(ys, dtype=np.float64)
        n_extraidos_raw = len(x)

        # Amostragem
        if sample > 0 and n_extraidos_raw > sample:
            step = max(1, n_extraidos_raw // sample)
            x = x[::step]
            y = y[::step]
            n_extraidos = len(x)
        else:
            n_extraidos = n_extraidos_raw

        metadata = {
            "n_total": n_total,
            "n_extraidos": n_extraidos,
            "crs": crs,
            "fonte": os.path.splitext(path)[1].lower().lstrip("."),
            "fields": fields,
        }

        logger.info(
            "Coordenadas extraidas de vetor",
            code="VECTOR_GEO_EXTRACT_DONE",
            n_features=n_total,
            n_points_raw=n_extraidos_raw,
            n_extraidos=n_extraidos,
            crs=crs or "N/A",
        )
        return x, y, metadata