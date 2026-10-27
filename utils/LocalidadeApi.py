# -*- coding: utf-8 -*-
"""
LocalidadeApi — Municipio, UF, regiao e pais de um ponto pela MALHA DO IBGE (OFFLINE)
=====================================================================================
API 2 do enriquecimento publico dos centroides da Base de Limites: devolve o
MUNICIPIO, a SIGLA da UF (2 letras), a REGIAO (Norte/Nordeste/Centro-Oeste/
Sudeste/Sul) e o PAIS de cada ponto (latitude/longitude).

Fonte LOCAL (sem rede — funciona OFFLINE):

    malha municipal do IBGE -> <BASE_DADOS>/PUBLICOS/IBGE_BR_Municipios_<ano>/
                               BR_Municipios_<ano>.shp

O caminho e resolvido por ``utils.PublicDataStructureUtil`` (a versao MAIS NOVA
da pasta e usada automaticamente) e os campos lidos do shape sao ``NM_MUN``
(municipio), ``SIGLA_UF`` (sigla da UF) e ``NM_REGIAO`` (regiao). O shape cobre
APENAS o Brasil: fora do territorio brasileiro o municipio, a UF, a regiao e o
pais saem VAZIOS; dentro dele o pais e sempre ``BRASIL``.

O trabalho pesado (celulas de 0,5°, leitura espacial por ``bbox``, point-in-
polygon e cache de sessao) fica no motor compartilhado ``utils.MalhaLookup`` —
aqui so ficam a MALHA e o formato de saida.

As consultas sao BEST-EFFORT: malha ausente/ilegivel nao interrompe o fluxo do
chamador — os campos ficam vazios e o erro vai para o log.

Uso:
    from utils.LocalidadeApi import LocalidadeApi

    LocalidadeApi.lookup(-48.3336, -10.1840)
    # {"municipio": "PALMAS", "estado": "TO", "regiao": "NORTE", "pais": "BRASIL"}

    LocalidadeApi.lookups([(-10.184, -48.3336), (-10.185, -48.3337)])
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.MalhaLookup import MalhaLookup
from utils.PublicDataStructureUtil import PublicDataStructureUtil

EMPTY: Dict[str, str] = {"municipio": "", "estado": "", "regiao": "", "pais": ""}


class LocalidadeApi(BaseUtil):
    """Municipio, UF (sigla), regiao e pais de um ponto pela malha do IBGE."""

    # Campos da malha municipal do IBGE (Malha Municipal Digital).
    FIELD_MUNICIPIO = "NM_MUN"
    FIELD_ESTADO = "SIGLA_UF"
    FIELD_REGIAO = "NM_REGIAO"
    FIELDS: Tuple[str, ...] = (FIELD_MUNICIPIO, FIELD_ESTADO, FIELD_REGIAO)

    PAIS_BRASIL = "BRASIL"
    SOURCE_LABEL = "malha municipal do IBGE"

    # ── API publica ─────────────────────────────────────────────────

    @classmethod
    def lookups(
        cls,
        points: Iterable[Tuple[float, float]],
        tool_key: str = ToolKey.UNTRACEABLE.value,
        progress_cb: Optional[Callable[[int, int, float], None]] = None,
    ) -> List[Dict[str, str]]:
        """
        Municipio/UF/regiao/pais de cada ponto, na MESMA ordem recebida.

        Args:
            points: Iteravel de ``(latitude, longitude)`` (EPSG:4326).
            tool_key: Chave da ferramenta para logging.
            progress_cb: Callback ``(processados, total, eta_segundos)``.

        Returns:
            Lista de dicionarios — vazios fora do Brasil ou quando a malha nao
            esta disponivel.
        """
        coords = list(points)
        if not coords:
            return []

        raw = MalhaLookup.lookups(
            cls._shape(tool_key),
            coords,
            cls.FIELDS,
            tool_key,
            progress_cb,
            cls.SOURCE_LABEL,
        )
        return [cls._to_item(item) for item in raw]

    @classmethod
    def lookup(
        cls,
        longitude: float,
        latitude: float,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, str]:
        """
        Municipio, UF (sigla), regiao e pais de UM ponto (EPSG:4326).

        Returns:
            ``{"municipio": ..., "estado": ..., "regiao": ..., "pais": ...}`` —
            vazio fora do Brasil ou quando a malha nao esta disponivel.
        """
        raw = MalhaLookup.lookup(
            cls._shape(tool_key),
            longitude,
            latitude,
            cls.FIELDS,
            tool_key,
            cls.SOURCE_LABEL,
        )
        return cls._to_item(raw)

    @classmethod
    def plan_seconds(cls, points: Iterable[Tuple[float, float]]) -> float:
        """Estimativa (segundos) da fase: 1 leitura espacial por celula."""
        return MalhaLookup.plan_seconds(
            PublicDataStructureUtil.municipios_shape(), points
        )

    @classmethod
    def shape_path(cls, tool_key: str = ToolKey.UNTRACEABLE.value) -> str:
        """Caminho da malha municipal em uso (``""`` quando nao encontrada)."""
        shape = cls._shape(tool_key)
        return str(shape) if shape is not None else ""

    # ── Interno ─────────────────────────────────────────────────────

    @staticmethod
    def _shape(tool_key: str) -> Any:
        """Shape da malha municipal resolvido pela BASE PUBLICA."""
        return PublicDataStructureUtil.municipios_shape(tool_key=tool_key)

    @classmethod
    def _to_item(cls, raw: Dict[str, str]) -> Dict[str, str]:
        """Converte os campos do shape no formato do projeto (pais so com municipio)."""
        municipio = raw.get(cls.FIELD_MUNICIPIO, "")
        if not municipio:
            return dict(EMPTY)

        return {
            "municipio": municipio,
            "estado": raw.get(cls.FIELD_ESTADO, ""),
            "regiao": raw.get(cls.FIELD_REGIAO, ""),
            "pais": cls.PAIS_BRASIL,
        }
