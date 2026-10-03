# -*- coding: utf-8 -*-
"""
LasUtil — Utilitário para arquivos LAS/LAZ
============================================
Fornece métodos estáticos para leitura de metadados de arquivos
LAS/LAZ, como contagem de pontos, verificação de bandas RGB, etc.

Uso:
    from utils.LasUtil import LasUtil

    info = LasUtil.get_info("c:/dados/nuvem.las")
    print(info["point_count"])   # 1_234_567
    print(info["has_rgb"])       # True
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict, Optional

import laspy
import numpy as np

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class LasLayerSource(BaseUtil):
    """
    Métodos estáticos para extração de metadados de arquivos LAS/LAZ.

    Todas as funções aceitam `tool_key: str = ToolKey.UNTRACEABLE.value`
    como parâmetro nomeado, conforme padrão BaseUtil.
    """

    # ══════════════════════════════════════════════════════════════════
    # API Pública — Metadados
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def get_info(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Retorna metadados básicos de um arquivo LAS/LAZ.

        Args:
            path: Caminho completo para o arquivo .las ou .laz.
            tool_key: ToolKey para logging.

        Returns:
            Dicionário com:
                - path           : str
                - point_count    : int
                - has_rgb        : bool
                - dimension_names: list[str] (nomes das dimensões)
                - error          : str | None (se houve falha)

        Raises:
            FileNotFoundError: se o arquivo não existir.
            ValueError: se a extensão não for .las/.laz.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")

        # Validações
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
                point_count = las.header.point_count
                dim_names = list(las.header.point_format.dimension_names)
                has_rgb = "red" in dim_names

            info: Dict[str, Any] = {
                "path": path,
                "point_count": point_count,
                "has_rgb": has_rgb,
                "dimension_names": dim_names,
                "error": None,
            }

            logger.info(
                "Metadados LAS obtidos",
                code="LAS_INFO",
                path=path,
                point_count=point_count,
                has_rgb=has_rgb,
            )
            return info

        except Exception as e:
            logger.error(
                "Erro ao ler metadados LAS",
                code="LAS_INFO_ERR",
                path=path,
                error=str(e),
            )
            return {
                "path": path,
                "point_count": 0,
                "has_rgb": False,
                "dimension_names": [],
                "error": str(e),
            }

    @staticmethod
    def get_point_count(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> int:
        """
        Retorna apenas o número total de pontos do arquivo LAS.

        Args:
            path: Caminho do arquivo.
            tool_key: ToolKey para logging.

        Returns:
            Número total de pontos (0 se erro).
        """
        try:
            info = LasLayerSource.get_info(path, tool_key=tool_key)
            return info.get("point_count", 0)
        except Exception:
            return 0

    @staticmethod
    def has_rgb(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Verifica se o arquivo LAS possui bandas RGB.

        Args:
            path: Caminho do arquivo.
            tool_key: ToolKey para logging.

        Returns:
            True se tem bandas 'red', 'green', 'blue'.
        """
        try:
            info = LasLayerSource.get_info(path, tool_key=tool_key)
            return info.get("has_rgb", False)
        except Exception:
            return False

    @staticmethod
    def get_bounding_box(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        sample_size: int = 10000,
    ) -> Dict[str, float]:
        """
        Retorna bounding box aproximada (lendo amostra de pontos).

        Args:
            path: Caminho do arquivo.
            tool_key: ToolKey para logging.
            sample_size: Nº máximo de pontos para amostragem.

        Returns:
            Dict com 'x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max'
            ou dict vazio se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        try:
            info = LasLayerSource.get_info(path, tool_key=tool_key)
            if info.get("error"):
                return {}

            las_read = laspy.read(path, count=min(sample_size, info["point_count"]))
            if len(las_read.points) == 0:
                return {}

            bbox = {
                "x_min": float(np.min(las_read.x)),
                "x_max": float(np.max(las_read.x)),
                "y_min": float(np.min(las_read.y)),
                "y_max": float(np.max(las_read.y)),
                "z_min": float(np.min(las_read.z)),
                "z_max": float(np.max(las_read.z)),
            }
            logger.info(f"Bounding box calculada: x[{bbox['x_min']:.2f}, {bbox['x_max']:.2f}] y[{bbox['y_min']:.2f}, {bbox['y_max']:.2f}]")
            return bbox

        except Exception as e:
            logger.error(
                "Erro ao calcular bounding box",
                code="LAS_BBOX_ERR",
                error=str(e),
            )
            return {}

    # ══════════════════════════════════════════════════════════════════
    # API Pública — Leitura de Arrays
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def get_rgb_arrays(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, np.ndarray]:
        """
        Lê as bandas RGB de um arquivo LAS como arrays numpy int64.

        Args:
            path: Caminho do arquivo LAS/LAZ.
            tool_key: ToolKey para logging.

        Returns:
            Dict com 'red', 'green', 'blue' (np.ndarray dtype int64)
            ou dict vazio se erro ou sem RGB.

        Raises:
            FileNotFoundError: se o arquivo não existir.
            ValueError: se a extensão não for .las/.laz.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")

        # Validações
        path = path.strip()
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz"):
            raise ValueError(
                f"Extensão inválida '{ext}'. Esperado .las ou .laz."
            )

        try:
            las = laspy.read(path)
            if not hasattr(las, "red") or not hasattr(las, "green") or not hasattr(las, "blue"):
                logger.warning(
                    "LAS não possui bandas RGB completas",
                    code="LAS_NO_RGB",
                    path=path,
                )
                return {}

            arrays = {
                "red": np.asarray(las.red, dtype=np.int64),
                "green": np.asarray(las.green, dtype=np.int64),
                "blue": np.asarray(las.blue, dtype=np.int64),
            }

            logger.info(
                "Arrays RGB lidos",
                code="LAS_RGB_READ",
                path=path,
                n_points=len(arrays["red"]),
            )
            return arrays

        except Exception as e:
            logger.error(
                "Erro ao ler arrays RGB do LAS",
                code="LAS_RGB_ERR",
                path=path,
                error=str(e),
            )
            return {}

    # ══════════════════════════════════════════════════════════════════
    # API Pública — Filtragem e Escrita
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def ensure_output_dir(
        output_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Garante que o diretório do arquivo de saída existe.

        Args:
            output_path: Caminho completo do arquivo de saída.
            tool_key: ToolKey para logging.

        Returns:
            True se o diretório existe ou foi criado, False se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        output_dir = os.path.dirname(output_path)
        if not output_dir:
            return True  # diretório atual sempre existe
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(
                "Diretório de saída garantido",
                code="LAS_OUT_DIR",
                path=output_dir,
            )
            return True
        except Exception as e:
            logger.error(
                "Erro ao criar diretório de saída",
                code="LAS_OUT_DIR_ERR",
                path=output_dir,
                error=str(e),
            )
            return False

    @staticmethod
    def create_filtered_las(
        las: laspy.LasData,
        mask: np.ndarray,
        output_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[int]:
        """
        Cria um novo arquivo LAS a partir de uma máscara booleana.

        Args:
            las: Objeto LasData original (fonte dos pontos e header).
            mask: Array booleano com True para pontos a manter.
            output_path: Caminho para salvar o novo arquivo.
            tool_key: ToolKey para logging.

        Returns:
            Número de pontos salvos, ou None se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        try:
            n_pontos = int(np.sum(mask))
            if n_pontos == 0:
                logger.warning(
                    "Máscara vazia — nenhum ponto para salvar",
                    code="LAS_EMPTY_MASK",
                    output=output_path,
                )
                return 0

            las_out = laspy.LasData(las.header)
            las_out.points = las.points[mask]

            if not LasLayerSource.ensure_output_dir(output_path, tool_key=tool_key):
                return None

            las_out.write(output_path)

            logger.info(
                "LAS filtrado salvo",
                code="LAS_FILTER_SAVED",
                output=output_path,
                n_points=n_pontos,
            )
            return n_pontos

        except Exception as e:
            logger.error(
                "Erro ao salvar LAS filtrado",
                code="LAS_FILTER_SAVE_ERR",
                output=output_path,
                error=str(e),
            )
            return None

    @staticmethod
    def resolve_output_path(
        input_path: str,
        suffix: str = "_filtrado",
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Resolve um caminho de saída com sufixo no nome do arquivo.

        Exemplo:
            input = "c:/dados/nuvem.las"
            suffix = "_filtrado"
            output_dir = "c:/saida"
            → "c:/saida/nuvem_filtrado.las"

        Se output_dir for None, usa o mesmo diretório do input.

        Args:
            input_path: Caminho do arquivo de entrada.
            suffix: Sufixo a adicionar antes da extensão.
            output_dir: Diretório de saída (None = mesmo do input).

        Returns:
            Caminho completo do arquivo de saída.
        """
        dir_origem = os.path.dirname(input_path) if output_dir is None else output_dir
        basename = os.path.splitext(os.path.basename(input_path))[0]
        ext = os.path.splitext(input_path)[1].lower()
        return os.path.join(dir_origem, f"{basename}{suffix}{ext}")

    # ══════════════════════════════════════════════════════════════════
    # API — Extração de Arrays para Interpolação
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def extract_point_arrays(
        path: str,
        bands: dict,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> dict:
        """
        Extrai arrays de coordenadas do LAS conforme bandas solicitadas.

        Args:
            path: Caminho do arquivo LAS/LAZ.
            bands: Dict {"r": bool, "g": bool, "b": bool, "z": bool}.
            tool_key: ToolKey para logging.

        Returns:
            {
                "x": np.ndarray,
                "y": np.ndarray,
                "z": np.ndarray | None,
                "red": np.ndarray | None,
                "green": np.ndarray | None,
                "blue": np.ndarray | None,
                "n_points": int,
            }
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        logger.info("Extraindo arrays do LAS", code="LAS_EXTRACT_ARRAYS", path=path)

        las = laspy.read(path)
        n_total = len(las.points)

        result = {
            "x": np.asarray(las.x, dtype=np.float64),
            "y": np.asarray(las.y, dtype=np.float64),
            "z": None,
            "red": None,
            "green": None,
            "blue": None,
            "n_points": n_total,
        }

        if bands.get("z", False):
            result["z"] = np.asarray(las.z, dtype=np.float64)

        if bands.get("r", False) and hasattr(las, "red"):
            red_raw = np.asarray(las.red, dtype=np.float64)
            result["red"] = (red_raw / 256 if np.max(red_raw) > 255 else red_raw).astype(np.uint8)

        if bands.get("g", False) and hasattr(las, "green"):
            green_raw = np.asarray(las.green, dtype=np.float64)
            result["green"] = (green_raw / 256 if np.max(green_raw) > 255 else green_raw).astype(np.uint8)

        if bands.get("b", False) and hasattr(las, "blue"):
            blue_raw = np.asarray(las.blue, dtype=np.float64)
            result["blue"] = (blue_raw / 256 if np.max(blue_raw) > 255 else blue_raw).astype(np.uint8)

        logger.info(
            "Arrays extraidos",
            code="LAS_EXTRACT_ARRAYS_DONE",
            n_points=n_total,
            has_r=result["red"] is not None,
            has_g=result["green"] is not None,
            has_b=result["blue"] is not None,
            has_z=result["z"] is not None,
        )
        return result

    @staticmethod
    def calcular_pixel_ideal(
        path: str,
        fator_conversao: float = 0.75,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> dict:
        """
        Calcula pixel ideal baseado na densidade da nuvem.

        Args:
            path: Caminho do arquivo LAS/LAZ.
            fator_conversao: Multiplicador do espacamento (default 0.75).
            tool_key: ToolKey para logging.

        Returns:
            {
                "n_pontos": int,
                "area_bbox_m2": float,
                "densidade_pts_m2": float,
                "espacamento_m": float,
                "espacamento_cm": float,
                "pixel_ideal_m": float,
                "pixel_ideal_cm": float,
                "bbox": {...},
            }
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        logger.info("Calculando pixel ideal", code="LAS_PIXEL_IDEAL", path=path)

        info = LasLayerSource.get_info(path, tool_key=tool_key)
        n_pontos = info.get("point_count", 0)
        if n_pontos == 0:
            logger.warning("LAS vazio — pixel ideal nao calculado", code="LAS_PIXEL_EMPTY")
            return {}

        bbox = LasLayerSource.get_bounding_box(path, tool_key=tool_key)
        if not bbox:
            return {}

        area = (bbox["x_max"] - bbox["x_min"]) * (bbox["y_max"] - bbox["y_min"])
        if area <= 0:
            logger.warning("Area bbox zero", code="LAS_PIXEL_AREA_ZERO")
            return {}

        densidade = n_pontos / area
        espacamento_m = 1.0 / (densidade ** 0.5)
        pixel_ideal_m = max(espacamento_m * fator_conversao, 0.01)
        pixel_ideal_cm = pixel_ideal_m * 100

        result = {
            "n_pontos": n_pontos,
            "area_bbox_m2": round(area, 4),
            "densidade_pts_m2": round(densidade, 4),
            "espacamento_m": round(espacamento_m, 6),
            "espacamento_cm": round(espacamento_m * 100, 2),
            "pixel_ideal_m": round(pixel_ideal_m, 6),
            "pixel_ideal_cm": round(pixel_ideal_cm, 2),
            "bbox": bbox,
        }

        logger.info(
            "Pixel ideal calculado",
            code="LAS_PIXEL_DONE",
            pixel_cm=pixel_ideal_cm,
            densidade=densidade,
        )
        return result

    # ══════════════════════════════════════════════════════════════════
    # API — Split de LAS em partes iguais
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def split_las(
        path: str,
        output_dir: str,
        pontos_por_parte: int = 10_000_000,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> dict:
        """
        Divide um arquivo LAS/LAZ em varios arquivos menores.

        Cada parte tera ate `pontos_por_parte` pontos (a ultima pode ter menos).
        Os arquivos de saida seguem o padrao:
            {output_dir}/{basename}_part_{n:04d}.las

        Args:
            path: Caminho do arquivo LAS/LAZ de entrada.
            output_dir: Pasta onde os arquivos serão salvos.
            pontos_por_parte: Maximo de pontos por arquivo.
            tool_key: ToolKey para logging.

        Returns:
            {
                "n_total": int,
                "n_partes": int,
                "pontos_por_parte": int,
                "arquivos": list[str],
                "error": str | None,
            }
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        logger.info(
            "Iniciando split do LAS",
            code="LAS_SPLIT_START",
            path=path,
            pontos_por_parte=pontos_por_parte,
        )

        # Validações
        path = path.strip()
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz"):
            raise ValueError(f"Extensao invalida '{ext}'. Esperado .las ou .laz.")

        try:
            las = laspy.read(path)
            n_total = len(las.points)
            basename = os.path.splitext(os.path.basename(path))[0]

            os.makedirs(output_dir, exist_ok=True)

            n_partes = max(1, int(math.ceil(n_total / pontos_por_parte)))
            arquivos: list[str] = []

            for i in range(n_partes):
                ini = i * pontos_por_parte
                fim = min(ini + pontos_por_parte, n_total)
                mask = np.zeros(n_total, dtype=bool)
                mask[ini:fim] = True

                nome_out = f"{basename}_part_{i+1:04d}.las"
                out_path = os.path.join(output_dir, nome_out)

                n_salvos = LasLayerSource.create_filtered_las(
                    las, mask, out_path, tool_key=tool_key,
                )
                if n_salvos is not None and n_salvos > 0:
                    arquivos.append(out_path)
                    logger.info(
                        f"Parte {i+1}/{n_partes} salva: {nome_out} ({n_salvos} pontos)",
                        code="LAS_SPLIT_PART",
                        parte=i+1,
                        total=n_partes,
                        n_pontos=n_salvos,
                        arquivo=out_path,
                    )

            result = {
                "n_total": n_total,
                "n_partes": n_partes,
                "pontos_por_parte": pontos_por_parte,
                "arquivos": arquivos,
                "error": None,
            }

            logger.info(
                "Split concluido",
                code="LAS_SPLIT_DONE",
                n_total=n_total,
                n_partes=n_partes,
                arquivos=len(arquivos),
            )
            return result

        except Exception as e:
            logger.error(
                "Erro ao dividir LAS",
                code="LAS_SPLIT_ERR",
                error=str(e),
            )
            return {
                "n_total": 0,
                "n_partes": 0,
                "pontos_por_parte": pontos_por_parte,
                "arquivos": [],
                "error": str(e),
            }

    # ══════════════════════════════════════════════════════════════════
    # API — Extração de Coordenadas (PointBoundaryPlugin)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def extract_points(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        sample: int = 0,
    ) -> tuple[np.ndarray, np.ndarray, dict]:
        """
        Extrai coordenadas (x, y) de um arquivo LAS/LAZ.

        Args:
            path: Caminho do arquivo .las ou .laz.
            tool_key: ToolKey para logging.
            sample: Se > 0, retorna no máximo 'sample' pontos (amostragem uniforme).

        Returns:
            (x_array, y_array, metadata) onde metadata contém:
                - n_total: total de pontos no arquivo
                - n_extraidos: pontos extraídos (após amostragem)
                - has_rgb: se tem bandas RGB
                - crs: CRS em formato string (se disponível no header)
                - fonte: "las"
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        logger.info("Extraindo pontos do LAS", code="LAS_EXTRACT_POINTS", path=path)

        las = laspy.read(path)
        n_total = len(las.points)

        x = np.asarray(las.x, dtype=np.float64)
        y = np.asarray(las.y, dtype=np.float64)

        has_rgb = hasattr(las, "red") and las.red is not None

        # Tenta extrair CRS do header
        crs = ""
        try:
            vlrs = las.header.vlrs
            for vlr in vlrs:
                if hasattr(vlr, "parsed_crs") and vlr.parsed_crs is not None:
                    crs = str(vlr.parsed_crs)
                    break
        except Exception:
            pass

        # Amostragem
        if sample > 0 and n_total > sample:
            step = max(1, n_total // sample)
            x = x[::step]
            y = y[::step]
            n_extraidos = len(x)
        else:
            n_extraidos = n_total

        metadata = {
            "n_total": n_total,
            "n_extraidos": n_extraidos,
            "has_rgb": has_rgb,
            "crs": crs,
            "fonte": "las",
        }

        logger.info(
            "Pontos extraidos do LAS",
            code="LAS_EXTRACT_DONE",
            n_total=n_total,
            n_extraidos=n_extraidos,
            has_rgb=has_rgb,
            crs=crs or "N/A",
        )
        return x, y, metadata
