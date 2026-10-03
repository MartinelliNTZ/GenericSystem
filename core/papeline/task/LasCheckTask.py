# -*- coding: utf-8 -*-
"""
LasCheckTask — Task que executa checks de qualidade em nuvens LAS/LAZ
======================================================================
Executa uma bateria de verificações configuráveis via parametros e
retorna resultados consolidados em self.result.

Checks implementados (8):
  1. Contagem de Pontos (point_count)
  2. Bounding Box (bbox)
  3. Bandas RGB (rgb)
  4. Classificação (classification)
  5. Coordenadas Zero (zero_coords)
  6. Duplicatas XY (duplicates)
  7. Densidade / Gaps (density)
  8. Intensidade (intensity)

ATENÇÃO: Emite progresso via SignalManager durante _run().
Os sinais Qt são thread-safe — funcionam de dentro da QThread.
"""

from __future__ import annotations

import os

import laspy
import numpy as np

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from utils.BaseUtil import BaseUtil
from ..BaseTask import BaseTask


class LasCheckTask(BaseTask):
    """
    Task que executa checks de qualidade em um arquivo LAS/LAZ.

    Args:
        file_path: Caminho do arquivo LAS/LAZ de entrada
        checks_enabled: Dict com chaves dos checks habilitados (True/False)
        tool_key: ToolKey para logging

    Result produz (dict):
        check_results: dict[str, dict] — resultado de cada check
        summary: dict — consolidado (pass, warning, fail, total)
        file_path: str — caminho do arquivo processado
    """

    # Nomes amigáveis dos checks
    _CHECK_DISPLAY: dict[str, str] = {
        "point_count": "Contagem de Pontos",
        "bbox": "Bounding Box",
        "rgb": "Bandas RGB",
        "classification": "Classificação",
        "zero_coords": "Coordenadas Zero",
        "duplicates": "Duplicatas XY",
        "density": "Densidade / Gaps",
        "intensity": "Intensidade",
    }

    def __init__(
        self,
        file_path: str,
        checks_enabled: dict[str, bool] | None = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ):
        super().__init__(
            description=f"Checks de qualidade: {os.path.basename(file_path)}"
        )
        self._file_path = file_path
        self._checks_enabled = checks_enabled or {}
        self._tool_key = tool_key

    def _run(self) -> bool:
        """
        Executa todos os checks em background thread emitindo progresso.

        8 etapas (stages) sincronizadas com o HUD Modo 3:
          Cada check é uma etapa (0% → 100%)
        """
        logger = BaseUtil._get_logger(self._tool_key, "LasCheckTask")
        signals = SignalManager.instance()

        # ── Tenta abrir o arquivo (suporta .las e .laz) ──────────────
        signals.hud_update.emit({
            "message": "Abrindo arquivo LAS/LAZ...",
            "progress": 2.0,
        })
        signals.progress_update.emit(2.0)

        try:
            las = laspy.read(self._file_path)
        except Exception as e:
            error_msg = str(e)
            # Verifica se é problema de backend LAZ
            if "No LazBackend selected" in error_msg or "cannot decompress" in error_msg:
                self.result = {
                    "check_results": {},
                    "summary": {"pass": 0, "warning": 0, "fail": 0, "total": 0, "error": True},
                    "file_path": self._file_path,
                    "error_type": "laz_backend",
                    "error": (
                        "Formato LAZ detectado, mas o backend de compressão "
                        "não está instalado.\n\n"
                        "Solução: Instale o backend LAZ com:\n"
                        "  pip install lazrs\n\n"
                        "Ou converta o arquivo para LAS usando a opção "
                        "'USAR ORIGEM' no plugin Filtro Pontos Pretos."
                    ),
                }
                logger.error(
                    "Backend LAZ não encontrado",
                    code="LASCHECK_LAZ_BACKEND",
                    path=self._file_path,
                )
                return False
            raise

        n_total = len(las.points)
        logger.info(
            "LAS aberto para checks",
            code="LASCHECK_OPEN",
            path=self._file_path,
            points=n_total,
        )

        # ── Ordem dos checks ──────────────────────────────────────────
        check_order = [
            "point_count", "bbox", "rgb", "classification",
            "zero_coords", "duplicates", "density", "intensity",
        ]
        check_methods = {
            "point_count": self._check_point_count,
            "bbox": self._check_bbox,
            "rgb": self._check_rgb,
            "classification": self._check_classification,
            "zero_coords": self._check_zero_coords,
            "duplicates": self._check_duplicates,
            "density": self._check_density,
            "intensity": self._check_intensity,
        }

        results: dict[str, dict] = {}
        n_checks = len(check_order)
        enabled_count = 0

        for idx, check_name in enumerate(check_order):
            # Verifica cancelamento
            if self.is_cancelled:
                logger.warning("Check cancelado pelo usuário", code="LASCHECK_CANCELLED")
                return False

            enabled = self._checks_enabled.get(check_name, True)
            if not enabled:
                results[check_name] = {
                    "status": "skipped",
                    "message": "Check desabilitado",
                    "detail": "",
                    "suggestion": "",
                }
                continue

            enabled_count += 1
            progress = ((idx + 1) / n_checks) * 100.0
            signals.progress_update.emit(progress)

            display = self._CHECK_DISPLAY.get(check_name, check_name)
            signals.hud_update.emit({
                "message": f"Verificando: {display}...",
                "progress": progress,
            })
            signals.hud_stage_done.emit(idx)

            method = check_methods[check_name]
            try:
                result = method(las, n_total)
                results[check_name] = result

                logger.info(
                    f"Check '{display}' → {result['status']}",
                    code="LASCHECK_CHECK_DONE",
                    check=check_name,
                    status=result["status"],
                )
            except Exception as e:
                logger.error(
                    f"Erro no check '{display}'",
                    code="LASCHECK_CHECK_ERR",
                    check=check_name,
                    error=str(e),
                )
                results[check_name] = {
                    "status": "fail",
                    "message": f"Erro ao verificar: {str(e)}",
                    "detail": "",
                    "suggestion": "Verifique a integridade do arquivo.",
                }

        signals.progress_update.emit(100.0)

        # ── Consolida ─────────────────────────────────────────────────
        pass_count = sum(1 for r in results.values() if r.get("status") == "pass")
        warn_count = sum(1 for r in results.values() if r.get("status") == "warning")
        fail_count = sum(1 for r in results.values() if r.get("status") == "fail")

        self.result = {
            "check_results": results,
            "summary": {
                "pass": pass_count,
                "warning": warn_count,
                "fail": fail_count,
                "total": enabled_count,
                "error": False,
            },
            "file_path": self._file_path,
            "error_type": None,
            "error": None,
        }

        logger.info(
            "Checks concluídos",
            code="LASCHECK_DONE",
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
        )
        return True

    # ══════════════════════════════════════════════════════════════════
    # Checks individuais (static methods)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _check_point_count(las: laspy.LasData, n_total: int) -> dict:
        if n_total == 0:
            return {
                "status": "fail",
                "message": "Nenhum ponto encontrado",
                "detail": "0",
                "suggestion": "Verifique se o arquivo contém dados.",
            }
        elif n_total < 1000:
            return {
                "status": "warning",
                "message": f"Apenas {n_total:,} pontos (nuvem pequena)",
                "detail": str(n_total),
                "suggestion": "Considere unir com outras nuvens.",
            }
        return {
            "status": "pass",
            "message": f"{n_total:,} pontos",
            "detail": str(n_total),
            "suggestion": "",
        }

    @staticmethod
    def _check_bbox(las: laspy.LasData, n_total: int) -> dict:
        x, y, z = las.x, las.y, las.z
        x_min, x_max = float(np.min(x)), float(np.max(x))
        y_min, y_max = float(np.min(y)), float(np.max(y))
        z_min, z_max = float(np.min(z)), float(np.max(z))

        issues = []
        if x_min >= x_max: issues.append("X")
        if y_min >= y_max: issues.append("Y")
        if z_min >= z_max: issues.append("Z")

        bbox_str = f"X[{x_min:.1f}, {x_max:.1f}] Y[{y_min:.1f}, {y_max:.1f}] Z[{z_min:.1f}, {z_max:.1f}]"

        if issues:
            return {
                "status": "fail",
                "message": f"BBox inválida nos eixos: {', '.join(issues)}",
                "detail": bbox_str,
                "suggestion": "Verifique o sistema de coordenadas.",
            }
        return {
            "status": "pass",
            "message": bbox_str,
            "detail": bbox_str,
            "suggestion": "",
        }

    @staticmethod
    def _check_rgb(las: laspy.LasData, n_total: int) -> dict:
        has = hasattr(las, "red") and hasattr(las, "green") and hasattr(las, "blue")
        if not has:
            return {
                "status": "warning",
                "message": "LAS não possui bandas RGB",
                "detail": "",
                "suggestion": "Sem informação de cor RGB disponível.",
            }
        return {"status": "pass", "message": "RGB presente", "detail": "", "suggestion": ""}

    @staticmethod
    def _check_classification(las: laspy.LasData, n_total: int) -> dict:
        if not hasattr(las, "classification"):
            return {
                "status": "warning",
                "message": "Sem campo de classificação",
                "detail": "",
                "suggestion": "Execute classificador antes de usar.",
            }
        classes = np.unique(las.classification)
        invalid = classes[(classes < 0) | (classes > 255)]
        if len(invalid) > 0:
            return {
                "status": "fail",
                "message": f"Códigos inválidos: {invalid.tolist()}",
                "detail": str(invalid.tolist()),
                "suggestion": "Reclassifique a nuvem.",
            }
        valid = sorted(classes[classes > 0].tolist())
        return {"status": "pass", "message": f"Códigos: {valid}", "detail": str(valid), "suggestion": ""}

    @staticmethod
    def _check_zero_coords(las: laspy.LasData, n_total: int) -> dict:
        mask = (las.x == 0) & (las.y == 0) & (las.z == 0)
        n_zero = int(np.sum(mask))
        pct = (n_zero / n_total * 100) if n_total > 0 else 0
        if pct >= 1.0:
            return {
                "status": "fail",
                "message": f"{n_zero:,} pontos ({pct:.3f}%) com X=Y=Z=0",
                "detail": f"{n_zero} ({pct:.3f}%)",
                "suggestion": "Remova pontos com coordenadas zero.",
            }
        elif pct > 0:
            return {
                "status": "warning",
                "message": f"{n_zero:,} pontos ({pct:.3f}%) com X=Y=Z=0",
                "detail": f"{n_zero} ({pct:.3f}%)",
                "suggestion": "Considere filtrar pontos inválidos.",
            }
        return {"status": "pass", "message": "Sem pontos com coordenadas zero", "detail": "0", "suggestion": ""}

    @staticmethod
    def _check_duplicates(las: laspy.LasData, n_total: int) -> dict:
        sample = min(n_total, 50000)
        if n_total > sample:
            rng = np.random.default_rng()
            idx = rng.choice(n_total, sample, replace=False)
        else:
            idx = slice(None)
        coords = np.column_stack((las.x[idx], las.y[idx]))
        _, counts = np.unique(coords, axis=0, return_counts=True)
        dup = int(np.sum(counts > 1))
        pct = (dup / sample * 100) if sample > 0 else 0
        if pct > 0.1:
            return {
                "status": "fail",
                "message": f"{dup:,} duplicatas ({pct:.3f}%)",
                "detail": f"{dup} ({pct:.3f}%)",
                "suggestion": "Execute filtro de duplicatas.",
            }
        elif dup > 0:
            return {
                "status": "warning",
                "message": f"{dup:,} duplicatas ({pct:.3f}%)",
                "detail": f"{dup} ({pct:.3f}%)",
                "suggestion": "",
            }
        return {"status": "pass", "message": "Sem duplicatas detectadas", "detail": "0", "suggestion": ""}

    @staticmethod
    def _check_density(las: laspy.LasData, n_total: int) -> dict:
        x_min, x_max = float(np.min(las.x)), float(np.max(las.x))
        y_min, y_max = float(np.min(las.y)), float(np.max(las.y))
        area = (x_max - x_min) * (y_max - y_min)
        if area <= 0:
            return {
                "status": "warning",
                "message": "Área planar zero",
                "detail": "",
                "suggestion": "Pontos sem extensão horizontal.",
            }
        return {"status": "pass", "message": f"Densidade: {(n_total/area):.2f} pts/m²", "detail": f"{(n_total/area):.2f}", "suggestion": ""}

    @staticmethod
    def _check_intensity(las: laspy.LasData, n_total: int) -> dict:
        if not hasattr(las, "intensity"):
            return {
                "status": "warning",
                "message": "Sem campo de intensidade",
                "detail": "",
                "suggestion": "Dados sem informação espectral.",
            }
        i_min, i_max = int(np.min(las.intensity)), int(np.max(las.intensity))
        if i_min < 0 or i_max > 65535:
            return {
                "status": "fail",
                "message": f"Intensidade fora do range: [{i_min}, {i_max}]",
                "detail": f"[{i_min}, {i_max}]",
                "suggestion": "Verifique valores de intensidade.",
            }
        return {"status": "pass", "message": f"Range [{i_min}, {i_max}] (válido)", "detail": f"[{i_min}, {i_max}]", "suggestion": ""}