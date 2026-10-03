# -*- coding: utf-8 -*-
"""
PointBoundaryTask — Task que gera limite (boundary) de nuvens de pontos
========================================================================
Executa em QThread dedicada o fluxo completo:
  1. Extração de pontos da fonte (LAS/LAZ ou vetor/CSV)
  2. Amostragem
  3. Loop iterativo do concave hull com detecção de escada
  4. Suavização
  5. Exportação GPKG final ( + intermediários opcional)
  6. JSON via botão no plugin (não automático)

ATENÇÃO: Emite progresso via SignalManager durante _run().
Os sinais Qt são thread-safe — funcionam de dentro da QThread.
"""

from __future__ import annotations

import json
import os

import numpy as np

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.BaseTask import BaseTask
from utils.BaseUtil import BaseUtil
from utils.las.LasLayerSource import LasLayerSource
from utils.vector.VectorLayerGeometry import VectorLayerGeometry
from utils.vector.VectorLayerSource import VectorLayerSource


class PointBoundaryTask(BaseTask):
    """
    Task que gera o limite (boundary) a partir de pontos.

    Args:
        file_path: Caminho do arquivo de entrada
        ratio_inicial: Ratio inicial do concave hull
        ratio_step: Decremento do ratio por iteração
        limiar_escada: % queda para detectar escada
        suavisacao: Buffer de suavização (m)
        n_amostras: Pontos para amostragem
        crs: CRS de saída
        output_dir: Diretório de saída
        tool_key: ToolKey para logging
        csv_x_field: Nome coluna X (CSV)
        csv_y_field: Nome coluna Y (CSV)
    """

    def __init__(
        self,
        file_path: str,
        ratio_inicial: float = 0.10,
        ratio_step: float = 0.01,
        limiar_escada: float = 12.0,
        suavisacao: float = 20.0,
        n_amostras: int = 100_000,
        crs: str = "EPSG:31982",
        output_dir: str = "",
        output_path: str = "",
        salvar_intermediarios: bool = False,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        csv_x_field: str = "x",
        csv_y_field: str = "y",
    ):
        basename = os.path.basename(file_path)
        super().__init__(description=f"Limite de pontos: {basename}")
        self._file_path = file_path
        self._ratio_inicial = ratio_inicial
        self._ratio_step = ratio_step
        self._limiar_escada = limiar_escada
        self._suavisacao = suavisacao
        self._n_amostras = n_amostras
        self._crs = crs
        self._output_dir = output_dir
        self._output_path = output_path
        self._salvar_intermediarios = salvar_intermediarios
        self._tool_key = tool_key
        self._csv_x_field = csv_x_field
        self._csv_y_field = csv_y_field

    def _run(self) -> bool:
        logger = BaseUtil._get_logger(self._tool_key, "PointBoundaryTask")
        signals = SignalManager.instance()

        # ── 1. Extração de pontos ────────────────────────────────────
        signals.hud_update.emit({
            "message": "Extraindo pontos da fonte...",
            "progress": 5.0,
        })
        signals.progress_update.emit(5.0)

        ext = os.path.splitext(self._file_path)[1].lower()

        try:
            if ext in (".las", ".laz"):
                x, y, metadata = LasLayerSource.extract_points(
                    self._file_path,
                    tool_key=self._tool_key,
                    sample=self._n_amostras,
                )
            elif ext in (".shp", ".gpkg", ".kml", ".geojson", ".csv"):
                x, y, metadata = VectorLayerSource.extract_point_coordinates(
                    self._file_path,
                    tool_key=self._tool_key,
                    sample=self._n_amostras,
                    csv_x_field=self._csv_x_field,
                    csv_y_field=self._csv_y_field,
                )
            else:
                raise ValueError(f"Extensão não suportada: {ext}")

            n_total = metadata["n_total"]
            n_extraidos = metadata["n_extraidos"]
            fonte = metadata.get("fonte", ext.lstrip("."))

            logger.info(
                "Pontos extraidos com sucesso",
                code="PB_EXTRACT_DONE",
                n_total=n_total,
                n_extraidos=n_extraidos,
                fonte=fonte,
            )

        except Exception as e:
            logger.error("Erro ao extrair pontos", code="PB_EXTRACT_ERR", error=str(e))
            raise

        # ── Determina CRS (hierarquia) ────────────────────────────────
        crs_efetivo = metadata.get("crs", "") or self._crs or "EPSG:4326"
        logger.info("CRS definido", code="PB_CRS", crs=crs_efetivo)

        if n_extraidos < 3:
            raise ValueError(
                f"Menos de 3 pontos extraídos ({n_extraidos}). "
                "São necessários ao menos 3 pontos para gerar um limite."
            )

        # ── Garante diretório de saída ────────────────────────────────
        output_dir = self._output_dir
        if not output_dir:
            output_dir = os.path.dirname(self._file_path)
        os.makedirs(output_dir, exist_ok=True)

        # ── 2. Loop iterativo do concave hull ────────────────────────
        signals.hud_update.emit({
            "message": "Gerando limite côncavo iterativo...",
            "progress": 30.0,
        })
        signals.progress_update.emit(30.0)

        ratio_atual = self._ratio_inicial
        areas: list[float] = []
        ratios: list[float] = []
        hulls: list = []
        gpkg_iteracoes: list[str] = []

        step_int = int(round(self._ratio_step * 1000))
        current_int = int(round(self._ratio_inicial * 1000))

        while current_int >= 0:
            ratio = current_int / 1000

            hull = VectorLayerGeometry.generate_concave_boundary(
                x, y, ratio=ratio, tool_key=self._tool_key,
            )

            area = hull.area
            areas.append(area)
            ratios.append(ratio)
            hulls.append(hull)

            # Salva GPKG da iteração (condicional)
            if self._salvar_intermediarios:
                gpkg_path = os.path.join(
                    output_dir, "intermediarios", f"boundary_r{ratio:.3f}.gpkg"
                )
                self._salvar_gpkg(hull, gpkg_path, crs_efetivo,
                                  f"boundary_r{ratio:.3f}")
                gpkg_iteracoes.append(gpkg_path)

            logger.debug(
                f"  ratio={ratio:.3f}: area={area:.4f} m2",
                code="PB_CONCAVE_ITER",
                ratio=ratio,
                area=round(area, 4),
            )

            current_int -= step_int
            if current_int < 0:
                break

        if len(areas) == 0:
            raise ValueError("Nenhum hull foi gerado.")

        # ── 3. Detecção de escada ────────────────────────────────────
        ratio_ideal, ratio_escada, encontrou_escada = \
            VectorLayerGeometry.detect_escada(
                areas, ratios,
                limiar=self._limiar_escada,
                tool_key=self._tool_key,
            )

        # Índice do ratio ideal
        idx_ideal = ratios.index(ratio_ideal)
        hull_final = hulls[idx_ideal]

        logger.info(
            "Escada detectada" if encontrou_escada else "Nenhuma escada",
            code="PB_ESCADA_RESULT",
            ratio_ideal=ratio_ideal,
            encontrou=encontrou_escada,
        )

        # ── 4. Suavização ────────────────────────────────────────────
        signals.hud_update.emit({
            "message": "Suavizando polígono...",
            "progress": 70.0,
        })
        signals.progress_update.emit(70.0)

        hull_suavizado = VectorLayerGeometry.smooth_polygon(
            hull_final,
            distance=self._suavisacao,
            tool_key=self._tool_key,
        )

        # ── 5. Exportação final ───────────────────────────────────────
        signals.hud_update.emit({
            "message": "Exportando resultados...",
            "progress": 90.0,
        })
        signals.progress_update.emit(90.0)

        # GPKG final suavizado
        gpkg_final = self._output_path or os.path.join(
            output_dir,
            f"boundary_r{ratio_ideal:.3f}_suavizado.gpkg"
        )
        self._salvar_gpkg(hull_suavizado, gpkg_final, crs_efetivo,
                          f"limite_r{ratio_ideal:.3f}_suavizado")

        # JSON de resultados
        resultados_iteracoes = [
            {
                "ratio": round(ratios[i], 3),
                "area_m2": round(areas[i], 4),
            }
            for i in range(len(areas))
        ]

        hull_summary = {
            "ratio_ideal": round(ratio_ideal, 3),
            "area_hull_m2": round(hull_final.area, 4),
            "area_suavizada_m2": round(hull_suavizado.area, 4),
            "encontrou_escada": encontrou_escada,
            "ratio_escada": round(ratio_escada, 3) if encontrou_escada else None,
            "n_pontos_usados": n_extraidos,
            "n_pontos_total": n_total,
            "fonte": fonte,
            "arquivo_origem": self._file_path,
            "crs": crs_efetivo,
            "gpkg_final": gpkg_final,
            "resultados_iteracoes": resultados_iteracoes,
        }

        signals.hud_update.emit({
            "message": "Limite gerado com sucesso!",
            "progress": 100.0,
        })
        signals.progress_update.emit(100.0)

        self.result = {
            "hull_result": hull_summary,
            "hull_summary": {
                "fonte": fonte,
                "n_pontos": f"{n_total:,}",
                "n_amostrados": f"{n_extraidos:,}",
                "ratio_ideal": f"{ratio_ideal:.3f}",
                "area_hull": f"{hull_final.area:.2f} m²",
                "area_suav": f"{hull_suavizado.area:.2f} m²",
                "escada": "Sim" if encontrou_escada else "Não",
                "crs_utilizado": crs_efetivo,
                "status": "Concluído",
            },
        }

        logger.info(
            "Limite gerado com sucesso",
            code="PB_DONE",
            ratio_ideal=ratio_ideal,
            area_hull=round(hull_final.area, 4),
            area_suavizada=round(hull_suavizado.area, 4),
            encontrou_escada=encontrou_escada,
            gpkg_final=gpkg_final,
        )

        return True

    @staticmethod
    def _salvar_gpkg(geometry, path: str, crs: str, name: str) -> None:
        """Salva geometria como GPKG."""
        import fiona
        from shapely.geometry import mapping

        schema = {"geometry": "Polygon", "properties": {"name": "str"}}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with fiona.open(path, "w", driver="GPKG", schema=schema, crs=crs) as dst:
            dst.write({
                "geometry": mapping(geometry),
                "properties": {"name": name},
            })