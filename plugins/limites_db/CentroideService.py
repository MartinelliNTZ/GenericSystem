# -*- coding: utf-8 -*-
"""
CentroideService — Centroides das feicoes e enriquecimento publico
==================================================================
Etapa de enriquecimento da Base de Limites: extrai o CENTROIDE de cada feicao
(talhao ou zona), consulta as duas APIs publicas e devolve as informacoes para
dentro do talhao de origem.

    API 1 — Altimetria  (``utils.AltimetriaApi`` / Open Topo Data) → ``ALTITUDE``
    API 2 — Localidade  (``utils.LocalidadeApi`` / IBGE)           → ``MUNICIPIO``,
                                                                     ``ESTADO``,
                                                                     ``PAIS``

O centroide carrega TODOS os atributos da feicao de origem. Os centroides sao
gravados SOMENTE na estrutura PRIVADA (``VERRA_DATA``) — completao em
``Consolidado`` e um arquivo por OS na pasta ``Centroides`` — e NUNCA na pasta
publica do projeto.

As consultas sao BEST-EFFORT: falha de rede deixa o campo vazio (o fluxo do
chamador continua) e o erro vai para o log.

Uso:
    from plugins.limites_db.CentroideService import CentroideService

    centroides = CentroideService.build(prepared, tool_key)
    centroides = CentroideService.enrich(centroides, tool_key, progress_cb)
    prepared = CentroideService.merge(prepared, centroides)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from core.enum.ToolKey import ToolKey
from utils.AltimetriaApi import AltimetriaApi
from utils.BaseUtil import BaseUtil
from utils.LocalidadeApi import LocalidadeApi
from utils.vector.VectorLayerGeometry import VectorLayerGeometry
from utils.vector.VectorLayerSource import VectorLayerSource

FIELD_MUNICIPIO = "MUNICIPIO"
FIELD_ESTADO = "ESTADO"
FIELD_PAIS = "PAIS"
FIELD_ALTITUDE = "ALTITUDE"

# Campos publicos obtidos pelas APIs (mesma ordem nos shapes e nos centroides).
PUBLIC_FIELDS: Tuple[str, ...] = (
    FIELD_MUNICIPIO,
    FIELD_ESTADO,
    FIELD_PAIS,
    FIELD_ALTITUDE,
)


def _counter(
    progress_cb: Optional[Callable[[int, int], None]],
    offset: int,
    total: int,
) -> Optional[Callable[[int, int], None]]:
    """Adapta o contador de um cliente de API para a contagem COMBINADA."""
    if progress_cb is None:
        return None
    return lambda done, size: progress_cb(offset + done, total)


class CentroideService(BaseUtil):
    """Centroides das feicoes + altimetria/localidade (APIs publicas)."""

    # ── Etapas ──────────────────────────────────────────────────────

    @classmethod
    def build(cls, gdf: Any, tool_key: str = ToolKey.UNTRACEABLE.value) -> Any:
        """Centroide de cada feicao, com TODOS os atributos da feicao de origem."""
        logger = cls._get_logger(tool_key, "CentroideService")
        centroides = VectorLayerGeometry.centroids(gdf, tool_key)
        logger.info(
            "Centroides montados",
            code="CEN_BUILD_DONE",
            n_centroides=len(centroides),
        )
        return centroides

    @classmethod
    def enrich(
        cls,
        centroides: Any,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> Any:
        """
        Consulta as duas APIs publicas e devolve os centroides enriquecidos.

        Args:
            centroides: GeoDataFrame de POINTs (saida de ``build``).
            tool_key: Chave da ferramenta para logging.
            progress_cb: Callback ``(processados, total)`` do TOTAL combinado
                das duas APIs (altimetria + localidade).

        Returns:
            GeoDataFrame novo com ``MUNICIPIO``, ``ESTADO``, ``PAIS`` e
            ``ALTITUDE`` preenchidos (vazio quando a consulta falha).
        """
        coords, positions = cls._valid_points(centroides)
        total = len(coords) * 2

        altitudes = AltimetriaApi.elevations(
            coords, tool_key, _counter(progress_cb, 0, total)
        )
        locations = LocalidadeApi.lookups(
            coords, tool_key, _counter(progress_cb, len(coords), total)
        )

        return cls._apply(centroides, positions, altitudes, locations)

    @classmethod
    def merge(cls, talhoes: Any, centroides: Any) -> Any:
        """Devolve os talhoes com os 4 campos publicos vindos dos centroides."""
        merged = talhoes.copy()
        for field in PUBLIC_FIELDS:
            merged[field] = centroides[field].to_numpy()
        return merged

    @classmethod
    def split(
        cls,
        centroides: Any,
        consolidated_path: str,
        os_paths: Dict[str, str],
        os_field: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> List[str]:
        """Grava o completao dos centroides e um arquivo por OS (base PRIVADA)."""
        logger = cls._get_logger(tool_key, "CentroideService")
        written: List[str] = []

        VectorLayerSource.write_geodataframe_atomic(
            centroides, consolidated_path, tool_key
        )
        written.append(str(consolidated_path))

        for os_key, group in centroides.groupby(os_field, sort=True):
            target = os_paths.get(str(os_key))
            if not target:
                continue
            VectorLayerSource.write_geodataframe_atomic(group, target, tool_key)
            written.append(str(target))

        logger.info(
            "Centroides gravados",
            code="CEN_WRITE_DONE",
            n_files=len(written),
            consolidated=consolidated_path,
        )
        return written

    @classmethod
    def summary(cls, centroides: Any) -> Dict[str, int]:
        """Contagem de centroides, de altitudes e de localidades preenchidas."""
        return {
            "n_centroides": int(len(centroides)),
            "n_altitude": int(centroides[FIELD_ALTITUDE].notna().sum()),
            "n_localidade": int(cls._filled(centroides[FIELD_MUNICIPIO])),
        }

    # ── Interno ─────────────────────────────────────────────────────

    @classmethod
    def _valid_points(cls, centroides: Any) -> Tuple[List[Tuple[float, float]], List[int]]:
        """Coordenadas ``(latitude, longitude)`` validas e as posicoes de origem."""
        coords: List[Tuple[float, float]] = []
        positions: List[int] = []

        for position, point in enumerate(centroides.geometry):
            if point is None or point.is_empty:
                continue
            coords.append((float(point.y), float(point.x)))
            positions.append(position)

        return coords, positions

    @classmethod
    def _apply(
        cls,
        centroides: Any,
        positions: List[int],
        altitudes: List[Optional[float]],
        locations: List[Dict[str, str]],
    ) -> Any:
        """Escreve os valores consultados nos centroides (posicao a posicao)."""
        enriched = centroides.copy()
        values: List[Optional[float]] = [None] * len(centroides)
        municipios = [""] * len(centroides)
        estados = [""] * len(centroides)
        paises = [""] * len(centroides)

        for offset, position in enumerate(positions):
            values[position] = altitudes[offset] if offset < len(altitudes) else None
            item = locations[offset] if offset < len(locations) else None
            if item:
                municipios[position] = item["municipio"]
                estados[position] = item["estado"]
                paises[position] = item["pais"]

        enriched[FIELD_ALTITUDE] = pd.Series(
            values, index=enriched.index, dtype="float64"
        )
        enriched[FIELD_MUNICIPIO] = municipios
        enriched[FIELD_ESTADO] = estados
        enriched[FIELD_PAIS] = paises
        return enriched

    @staticmethod
    def _filled(series: Any) -> int:
        """Quantidade de valores de texto preenchidos em uma coluna."""
        return int((series.astype(str).str.strip() != "").sum())

