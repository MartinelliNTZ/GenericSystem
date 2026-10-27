# -*- coding: utf-8 -*-
"""
BiomaApi — Bioma de um ponto pela MALHA DE BIOMAS do IBGE (OFFLINE)
===================================================================
API 3 do enriquecimento publico dos centroides da Base de Limites: devolve o
BIOMA de cada ponto (latitude/longitude).

Fonte LOCAL (sem rede — funciona OFFLINE):

    malha de biomas do IBGE -> <BASE_DADOS>/PUBLICOS/IBGE_BIOMAS/
                               lml_bioma_e250k_v<AAAAMMDD>_A.shp

O caminho e resolvido por ``utils.PublicDataStructureUtil`` (a versao MAIS NOVA
do shape e usada automaticamente) e o campo lido e ``NM_BIOMA`` — normalizado
como os demais textos do projeto (MAIUSCULAS, sem acento, espacos → ``_``):
``Amazônia`` → ``AMAZONIA``, ``Mata Atlântica`` → ``MATA_ATLANTICA``.

O trabalho pesado (celulas de 0,5°, leitura espacial por ``bbox``, point-in-
polygon e cache de sessao) fica no motor compartilhado ``utils.MalhaLookup`` —
aqui so ficam a MALHA e o formato de saida.

As consultas sao BEST-EFFORT: malha ausente/ilegivel nao interrompe o fluxo do
chamador — o campo fica vazio e o erro vai para o log.

Uso:
    from utils.BiomaApi import BiomaApi

    BiomaApi.lookup(-48.3336, -10.1840)
    # {"bioma": "CERRADO"}

    BiomaApi.lookups([(-10.184, -48.3336), (-10.185, -48.3337)])
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.MalhaLookup import MalhaLookup
from utils.PublicDataStructureUtil import PublicDataStructureUtil

EMPTY: Dict[str, str] = {"bioma": ""}


class BiomaApi(BaseUtil):
    """Bioma de um ponto pela malha de biomas do IBGE."""

    # Campo da malha de biomas do IBGE (Biomas e Sistema Costeiro-Marinho).
    FIELD_BIOMA = "NM_BIOMA"
    FIELDS: Tuple[str, ...] = (FIELD_BIOMA,)

    SOURCE_LABEL = "malha de biomas do IBGE"

    # ── API publica ─────────────────────────────────────────────────

    @classmethod
    def lookups(
        cls,
        points: Iterable[Tuple[float, float]],
        tool_key: str = ToolKey.UNTRACEABLE.value,
        progress_cb: Optional[Callable[[int, int, float], None]] = None,
    ) -> List[Dict[str, str]]:
        """
        Bioma de cada ponto, na MESMA ordem recebida.

        Args:
            points: Iteravel de ``(latitude, longitude)`` (EPSG:4326).
            tool_key: Chave da ferramenta para logging.
            progress_cb: Callback ``(processados, total, eta_segundos)``.

        Returns:
            Lista de dicionarios — vazios fora dos biomas mapeados ou quando a
            malha nao esta disponivel.
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
        Bioma de UM ponto (EPSG:4326).

        Returns:
            ``{"bioma": ...}`` — vazio fora dos biomas mapeados ou quando a
            malha nao esta disponivel.
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
        return MalhaLookup.plan_seconds(PublicDataStructureUtil.biomas_shape(), points)

    @classmethod
    def shape_path(cls, tool_key: str = ToolKey.UNTRACEABLE.value) -> str:
        """Caminho da malha de biomas em uso (``""`` quando nao encontrada)."""
        shape = cls._shape(tool_key)
        return str(shape) if shape is not None else ""

    # ── Interno ─────────────────────────────────────────────────────

    @staticmethod
    def _shape(tool_key: str) -> Any:
        """Shape da malha de biomas resolvido pela BASE PUBLICA."""
        return PublicDataStructureUtil.biomas_shape(tool_key=tool_key)

    @classmethod
    def _to_item(cls, raw: Dict[str, str]) -> Dict[str, str]:
        """Converte o campo do shape no formato do projeto."""
        return {"bioma": raw.get(cls.FIELD_BIOMA, "")}
