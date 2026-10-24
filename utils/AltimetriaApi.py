# -*- coding: utf-8 -*-
"""
AltimetriaApi — Altimetria (elevacao) de pontos pela API publica Open Topo Data
===============================================================================
API 1 do enriquecimento publico dos centroides da Base de Limites: devolve a
ELEVACAO do terreno de cada ponto (latitude/longitude).

    https://api.opentopodata.org/v1/srtm90m

O servidor publico do Open Topo Data NAO exige chave e aplica tres limites,
respeitados por esta classe:

    - no maximo 100 pontos por requisicao (``MAX_LOCATIONS``);
    - no maximo 1 chamada por segundo (intervalo de ``MIN_INTERVAL_S``);
    - no maximo 1000 chamadas por dia.

As consultas sao BEST-EFFORT: falhas de rede nao interrompem o fluxo do
chamador — o lote fica com ``None`` e o erro vai para o log.

Uso:
    from utils.AltimetriaApi import AltimetriaApi

    altitudes = AltimetriaApi.elevations([(-10.184, -48.3336)])
    # [456.0]
"""

from __future__ import annotations

import time
from typing import Any, Callable, Iterable, List, Optional, Tuple

import requests

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class AltimetriaApi(BaseUtil):
    """Altimetria de pontos (lat/lon) pela API publica do Open Topo Data."""

    ENDPOINT = "https://api.opentopodata.org/v1/srtm90m"
    MAX_LOCATIONS = 100
    MIN_INTERVAL_S = 1.05
    TIMEOUT_S = 30
    RETRIES = 2

    _last_call_s = 0.0

    # ── API publica ─────────────────────────────────────────────────

    @classmethod
    def elevations(
        cls,
        points: Iterable[Tuple[float, float]],
        tool_key: str = ToolKey.UNTRACEABLE.value,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> List[Optional[float]]:
        """
        Elevacao (metros) de cada ponto, na MESMA ordem recebida.

        Args:
            points: Iteravel de ``(latitude, longitude)`` em EPSG:4326.
            tool_key: Chave da ferramenta para logging.
            progress_cb: Callback ``(processados, total)`` opcional.

        Returns:
            Lista de elevacoes — ``None`` quando a API nao cobre o ponto
            ou quando a consulta falha.
        """
        logger = cls._get_logger(tool_key, "AltimetriaApi")
        coords = list(points)
        if not coords:
            return []

        logger.info(
            "Consultando altimetria (Open Topo Data)",
            code="ALT_API_START",
            n_points=len(coords),
            dataset=cls.ENDPOINT.rsplit("/", 1)[-1],
        )

        values: List[Optional[float]] = []
        batches = [
            coords[index : index + cls.MAX_LOCATIONS]
            for index in range(0, len(coords), cls.MAX_LOCATIONS)
        ]

        for number, batch in enumerate(batches, start=1):
            values.extend(cls._batch(batch, logger, number, len(batches)))
            if progress_cb:
                progress_cb(len(values), len(coords))

        logger.info(
            "Altimetria concluida",
            code="ALT_API_DONE",
            n_points=len(coords),
            n_elevations=sum(1 for value in values if value is not None),
            n_batches=len(batches),
        )
        return values

    # ── Interno ─────────────────────────────────────────────────────

    @classmethod
    def _batch(
        cls,
        batch: List[Tuple[float, float]],
        logger: Any,
        number: int,
        total: int,
    ) -> List[Optional[float]]:
        """Consulta um lote de ate ``MAX_LOCATIONS`` pontos (com retentativas)."""
        locations = "|".join(
            f"{float(lat):.6f},{float(lon):.6f}" for lat, lon in batch
        )

        for attempt in range(1, cls.RETRIES + 2):
            cls._throttle()
            try:
                response = requests.post(
                    cls.ENDPOINT,
                    data={"locations": locations},
                    timeout=cls.TIMEOUT_S,
                )
                response.raise_for_status()
                payload = response.json() or {}
                if payload.get("status") != "OK":
                    raise ValueError(
                        f"status {payload.get('status')}: {payload.get('error')}"
                    )

                results = payload.get("results") or []
                return [cls._to_float(item.get("elevation")) for item in results]
            except (requests.RequestException, ValueError) as e:
                logger.warning(
                    "Falha no lote de altimetria",
                    code="ALT_API_RETRY",
                    batch=f"{number}/{total}",
                    attempt=attempt,
                    error=str(e),
                )

        logger.error(
            "Lote de altimetria descartado",
            code="ALT_API_ERR",
            batch=f"{number}/{total}",
            n_points=len(batch),
        )
        return [None] * len(batch)

    @classmethod
    def _throttle(cls) -> None:
        """Mantem o intervalo minimo entre chamadas (1 chamada por segundo)."""
        wait = cls.MIN_INTERVAL_S - (time.monotonic() - cls._last_call_s)
        if wait > 0:
            time.sleep(wait)
        cls._last_call_s = time.monotonic()

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        """Converte a elevacao devolvida pela API (``None`` fora do dataset)."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return round(float(value), 2)
