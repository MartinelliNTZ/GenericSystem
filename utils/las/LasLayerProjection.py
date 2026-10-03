# -*- coding: utf-8 -*-
"""
LasLayerProjection — Utilitário para CRS e Reprojeção de LAS/LAZ
==================================================================
Classe irmã de LasLayerSource, herda de BaseUtil.
Fornece métodos para leitura de CRS e reprojeção de nuvens LAS/LAZ.

Uso:
    from utils.las.LasLayerProjection import LasLayerProjection

    crs = LasLayerProjection.get_crs("nuvem.las")
    result = LasLayerProjection.reproject_las(
        "nuvem.las", "nuvem_reprojetada.las",
        target_crs="EPSG:31983", source_crs="EPSG:4326",
    )
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import laspy
import numpy as np

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil

# ── Tenta importar pyproj ──────────────────────────────────────────────
try:
    from pyproj import CRS as PyProjCRS, Transformer
    _HAS_PYPROJ = True
except ImportError:
    _HAS_PYPROJ = False


class LasLayerProjection(BaseUtil):
    """
    Métodos estáticos para leitura de CRS e reprojeção de arquivos LAS/LAZ.

    Todas as funções aceitam `tool_key: str = ToolKey.UNTRACEABLE.value`
    como parâmetro nomeado, conforme padrão BaseUtil.
    """

    # ══════════════════════════════════════════════════════════════════
    # API — Arquivo .mdata (metadado de projeção)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _mdata_path(las_path: str) -> str:
        """Retorna o caminho do arquivo .mdata associado ao LAS."""
        base = os.path.splitext(las_path)[0]
        return f"{base}.mdata"

    @staticmethod
    def save_mdata(
        las_path: str,
        epsg_code: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Salva um arquivo .mdata com o CRS ao lado do LAS.

        O arquivo .mdata é um JSON com:
            {"epsg": 4326}

        Args:
            las_path: Caminho do arquivo LAS/LAZ associado.
            epsg_code: Código EPSG completo (ex: "EPSG:31983") ou vazio.
            tool_key: ToolKey para logging.

        Returns:
            True se salvou, False se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "LasLayerProjection")

        if not epsg_code or ":" not in epsg_code:
            logger.warning(
                "EPSG inválido — não salvando .mdata",
                code="LAS_MDATA_INVALID_EPSG",
                epsg=epsg_code,
            )
            return False

        try:
            code = int(epsg_code.split(":")[1])
            mdata = {"epsg": code}
            mpath = LasLayerProjection._mdata_path(las_path)

            with open(mpath, "w", encoding="utf-8") as f:
                json.dump(mdata, f, indent=2)

            logger.info(
                "Arquivo .mdata salvo",
                code="LAS_MDATA_SAVED",
                path=mpath,
                epsg=code,
            )
            return True

        except Exception as e:
            logger.error(
                "Erro ao salvar .mdata",
                code="LAS_MDATA_SAVE_ERR",
                error=str(e),
            )
            return False

    @staticmethod
    def read_mdata(
        las_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Lê o CRS de um arquivo .mdata associado ao LAS.

        Args:
            las_path: Caminho do arquivo LAS/LAZ.
            tool_key: ToolKey para logging.

        Returns:
            String "EPSG:XXXX" se encontrado, ou vazia.
        """
        logger = BaseUtil._get_logger(tool_key, "LasLayerProjection")
        mpath = LasLayerProjection._mdata_path(las_path)

        if not os.path.isfile(mpath):
            return ""

        try:
            with open(mpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            code = data.get("epsg", 0)
            if code and isinstance(code, int) and code > 0:
                crs_str = f"EPSG:{code}"
                logger.info(
                    "CRS lido do arquivo .mdata",
                    code="LAS_MDATA_READ",
                    path=mpath,
                    crs=crs_str,
                )
                return crs_str

            logger.warning(
                ".mdata encontrado mas sem EPSG válido",
                code="LAS_MDATA_INVALID",
                path=mpath,
            )
            return ""

        except Exception as e:
            logger.error(
                "Erro ao ler .mdata",
                code="LAS_MDATA_READ_ERR",
                path=mpath,
                error=str(e),
            )
            return ""

    # ══════════════════════════════════════════════════════════════════
    # API Pública — CRS
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def get_crs(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Lê o CRS (Coordinate Reference System) de um arquivo LAS/LAZ.

        Estratégias de extração (em ordem):
        1. `parsed_crs` dos VLRs (mais comum, retorna objeto CRS)
        2. WKT string em VLRs do tipo OGR WKT / LASF_Projection
        3. GeoTIFF keys em VLRs do tipo GeoKeyDirectoryTag
        4. Arquivo .mdata (JSON com {"epsg": N}) ao lado do LAS

        Args:
            path: Caminho completo para o arquivo .las ou .laz.
            tool_key: ToolKey para logging.

        Returns:
            String no formato "EPSG:XXXX" se encontrado,
            ou string vazia se não foi possível determinar o CRS.

        Raises:
            FileNotFoundError: se o arquivo não existir.
            ValueError: se a extensão não for .las/.laz.
        """
        logger = BaseUtil._get_logger(tool_key, "LasLayerProjection")

        path = path.strip()
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz"):
            raise ValueError(
                f"Extensão inválida '{ext}'. Esperado .las ou .laz."
            )

        try:
            with laspy.open(path) as las:
                vlrs = las.header.vlrs

                # ── Estratégia 1: parsed_crs ────────────────────────
                for vlr in vlrs:
                    parsed = getattr(vlr, "parsed_crs", None)
                    if parsed is not None:
                        crs_str = str(parsed)
                        logger.info(
                            "CRS encontrado via parsed_crs",
                            code="LAS_CRS_VIA_PARSED",
                            path=path,
                            crs=crs_str,
                        )
                        return crs_str

                # ── Estratégia 2: WKT em VLRs ───────────────────────
                for vlr in vlrs:
                    record_id = getattr(vlr, "record_id", None)
                    description = getattr(vlr, "description", "").lower()
                    if record_id == 34735 or "wkt" in description or "crs" in description:
                        raw = getattr(vlr, "raw_bytes", None) or getattr(vlr, "data", None)
                        if raw:
                            try:
                                wkt_str = raw.decode("utf-8", errors="ignore").strip().strip("\x00")
                                if wkt_str and _HAS_PYPROJ:
                                    crs_obj = PyProjCRS(wkt_str)
                                    if crs_obj:
                                        epsg = crs_obj.to_epsg()
                                        if epsg:
                                            crs_str = f"EPSG:{epsg}"
                                            logger.info(
                                                "CRS encontrado via WKT VLR",
                                                code="LAS_CRS_VIA_WKT",
                                                path=path,
                                                crs=crs_str,
                                            )
                                            return crs_str
                            except Exception:
                                pass

                # ── Estratégia 3: GeoTIFF keys ──────────────────────
                for vlr in vlrs:
                    record_id = getattr(vlr, "record_id", None)
                    if record_id == 34735:  # GeoKeyDirectoryTag
                        raw = getattr(vlr, "raw_bytes", None) or getattr(vlr, "data", None)
                        if raw and _HAS_PYPROJ:
                            try:
                                import struct
                                data = raw
                                if isinstance(data, bytes):
                                    n_keys = struct.unpack_from("<H", data, 2)[0] if len(data) >= 4 else 0
                                    for i in range(n_keys):
                                        offset = 8 + i * 8
                                        if offset + 8 <= len(data):
                                            key_id, tiff_tag, count, value = struct.unpack_from("<HHHH", data, offset)
                                            if key_id == 3072:
                                                if value > 0:
                                                    crs_str = f"EPSG:{value}"
                                                    logger.info(
                                                        "CRS encontrado via GeoTIFF key",
                                                        code="LAS_CRS_VIA_GEOTIFF",
                                                        path=path,
                                                        crs=crs_str,
                                                    )
                                                    return crs_str
                            except Exception:
                                pass

            # ── Estratégia 4: .mdata ────────────────────────────────
            crs_mdata = LasLayerProjection.read_mdata(path, tool_key=tool_key)
            if crs_mdata:
                logger.info(
                    "CRS encontrado via .mdata",
                    code="LAS_CRS_VIA_MDATA",
                    path=path,
                    crs=crs_mdata,
                )
                return crs_mdata

            logger.warning(
                "Nenhum CRS encontrado no LAS (tentadas 4 estratégias)",
                code="LAS_CRS_NOT_FOUND",
                path=path,
            )
            return ""

        except Exception as e:
            logger.error(
                "Erro ao ler CRS do LAS",
                code="LAS_CRS_ERR",
                path=path,
                error=str(e),
            )
            return ""

    # ══════════════════════════════════════════════════════════════════
    # API Pública — Reprojeção
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def reproject_las(
        input_path: str,
        output_path: str,
        target_crs: str,
        source_crs: str = "",
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Reprojeta (transforma CRS) uma nuvem de pontos LAS/LAZ.

        Lê o arquivo de entrada, transforma as coordenadas X, Y, Z
        usando pyproj.Transformer e salva um novo arquivo LAS.

        Args:
            input_path: Caminho do arquivo LAS/LAZ de entrada.
            output_path: Caminho para salvar o LAS reprojetado.
            target_crs: CRS de destino (ex: "EPSG:31983").
            source_crs: CRS de origem. Se vazio, tenta detectar
                        automaticamente do header do LAS.
            tool_key: ToolKey para logging.

        Returns:
            Dicionário com:
                - n_points    : int  (pontos processados)
                - output_path : str  (caminho do arquivo salvo)
                - source_crs  : str  (CRS de origem usado)
                - target_crs  : str  (CRS de destino)
                - error       : str | None

        Raises:
            FileNotFoundError: se o arquivo de entrada não existir.
            ValueError: se extensão inválida ou pyproj não disponível.
            RuntimeError: se a transformação falhar.
        """
        logger = BaseUtil._get_logger(tool_key, "LasLayerProjection")

        # ── Validações ──────────────────────────────────────────────
        input_path = input_path.strip()
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

        ext = os.path.splitext(input_path)[1].lower()
        if ext not in (".las", ".laz"):
            raise ValueError(
                f"Extensão inválida '{ext}'. Esperado .las ou .laz."
            )

        if not _HAS_PYPROJ:
            raise ValueError(
                "pyproj não está instalado. "
                "Execute: pip install pyproj"
            )

        if not target_crs:
            raise ValueError("target_crs é obrigatório.")

        # ── Detecta CRS de origem se não informado ──────────────────
        if not source_crs:
            source_crs = LasLayerProjection.get_crs(input_path, tool_key=tool_key)
            if not source_crs:
                raise ValueError(
                    "CRS de origem não pôde ser detectado automaticamente. "
                    "Informe source_crs manualmente."
                )
            logger.info(
                "CRS de origem detectado automaticamente",
                code="LAS_REPROJ_SRC_AUTO",
                source_crs=source_crs,
            )

        logger.info(
            "Iniciando reprojeção LAS",
            code="LAS_REPROJ_START",
            input_path=input_path,
            output_path=output_path,
            source_crs=source_crs,
            target_crs=target_crs,
        )

        try:
            # ── Lê o LAS ────────────────────────────────────────────
            las = laspy.read(input_path)
            n_total = len(las.points)

            if n_total == 0:
                logger.warning(
                    "LAS vazio — nenhum ponto para reprojetar",
                    code="LAS_REPROJ_EMPTY",
                )
                return {
                    "n_points": 0,
                    "output_path": output_path,
                    "source_crs": source_crs,
                    "target_crs": target_crs,
                    "error": "LAS vazio",
                }

            # ── Cria o transformer ──────────────────────────────────
            src_crs_obj = PyProjCRS(source_crs)
            tgt_crs_obj = PyProjCRS(target_crs)
            transformer = Transformer.from_crs(
                src_crs_obj, tgt_crs_obj, always_xy=True
            )

            # ── Transforma coordenadas ──────────────────────────────
            x = np.asarray(las.x, dtype=np.float64)
            y = np.asarray(las.y, dtype=np.float64)
            z = np.asarray(las.z, dtype=np.float64)

            x_new, y_new, z_new = transformer.transform(x, y, z)

            # ── Atualiza os arrays no LAS ───────────────────────────
            las.x = x_new
            las.y = y_new
            las.z = z_new

            # ── Garante diretório de saída ──────────────────────────
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # ── Salva o LAS reprojetado ─────────────────────────────
            las.write(output_path)

            # ── Salva .mdata com o CRS de destino ──────────────────
            LasLayerProjection.save_mdata(output_path, target_crs, tool_key=tool_key)

            result = {
                "n_points": n_total,
                "output_path": output_path,
                "source_crs": source_crs,
                "target_crs": target_crs,
                "error": None,
            }

            logger.info(
                "LAS reprojetado com sucesso",
                code="LAS_REPROJ_DONE",
                n_points=n_total,
                output_path=output_path,
                source_crs=source_crs,
                target_crs=target_crs,
            )
            return result

        except Exception as e:
            logger.error(
                "Erro ao reprojetar LAS",
                code="LAS_REPROJ_ERR",
                input_path=input_path,
                error=str(e),
            )
            return {
                "n_points": 0,
                "output_path": output_path,
                "source_crs": source_crs,
                "target_crs": target_crs,
                "error": str(e),
            }