"""
Script para ler um arquivo LAS e gerar estatisticas em JSON + mosaico RGB GeoTIFF.

ARQUITETURA v5 — estagio por estagio com retomada automatica:

  [V5] BIGTIFF=YES em todas as escritas GTiff para suportar arquivos >4GB.
  [V5] Filtro de pontos pretos (R=G=B=0) removidos antes da interpolacao.
  [V5] LAS limpo (sem pontos pretos) salvo como <nome>_limpo.las.

  ESTAGIO 1 — Interpolacao IDW em tiles paralelos
    Cada tile e salvo individualmente em MOSAICO_PATH/tiles/R/, /G/, /B/
      tiles/R/tile_RRRR_CCCC.tif   (banda vermelha do tile)
      tiles/G/tile_RRRR_CCCC.tif   (banda verde   do tile)
      tiles/B/tile_RRRR_CCCC.tif   (banda azul    do tile)
    Se o trio ja existe em disco, o tile e pulado (retomada automatica).
    Resultado: subpastas /tiles/R/, /G/, /B/ com N arquivos GeoTIFF cada.

  ESTAGIO 2 — Mescla de tiles em bandas completas
    Todos os tiles/R/*.tif -> banda_R.tif  (grid completo, 1 banda)
    Todos os tiles/G/*.tif -> banda_G.tif
    Todos os tiles/B/*.tif -> banda_B.tif
    CORRECAO: posicao calculada manualmente pelo transform do tile,
    sem usar src.window(*src.bounds) que retornava (0,0) sempre.

  ESTAGIO 3 — Uniao das bandas em mosaico RGB
    banda_R.tif + banda_G.tif + banda_B.tif -> mosaico_rgb.tif  (3 bandas)

  ESTAGIO 4 — Recorte pelo poligono GPKG
    mosaico_rgb.tif -> mosaico_rgb_recortado.tif
    CORRECAO: mantem photometric=RGB, nodata=255 (fora do range 0-254) para
    distinguir areas recortadas de pixels pretos reais.

  ESTAGIO 5 — Geracao da banda alpha
    CORRECAO: alpha calculada pela mascara do poligono, nao pelo valor RGB.
    Pixel dentro do poligono = 255, fora = 0 -> mosaico_rgba_final.tif

CORRECOES v4:
  [V1] Bug da juncao: _mesclar_banda agora calcula posicao (r0,c0) manualmente
       a partir do transform do tile, sem usar src.window(*src.bounds) que
       sempre retornava (0,0). Todos os tiles eram escritos no canto superior
       esquerdo do memmap, sobrepondo-se uns aos outros.
  [V2] Bug do recorte: mantem photometric=RGB, usa nodata=255 (maximo uint8)
       em vez de nodata=0. Isso evita que pixels pretos reais (asfalto, sombras)
       sejam confundidos com area recortada.
  [V3] Bug da alpha: calculada pela mascara do poligono suavizado, nao pelo
       valor RGB. Antes, qualquer pixel preto legítimo dentro do poligono era
       marcado como transparente (alpha=0).
  [V4] Organizacao: tiles separados em pastas /R/, /G/, /B/ em vez de sufixo
       no nome do arquivo (tile_RRRR_CCCC_R.tif -> R/tile_RRRR_CCCC.tif).

CORRECOES v5:
  [V5] BIGTIFF=YES: todas as escritas GTiff usam BIGTIFF="YES" para evitar
       limite de ~4GB em arquivos grandes.
  [V5] Filtro de pontos pretos: antes da interpolacao, pontos com R=G=B=0
       sao removidos para evitar artefatos pretos no mosaico.
  [V5] LAS limpo salvo como arquivo separado.
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import json
import time
import datetime
import math
import glob
import laspy
import numpy as np
from shapely import concave_hull
from shapely.geometry import MultiPoint, mapping, Polygon
import fiona
from scipy.spatial import cKDTree
import rasterio
from rasterio.transform import from_origin, rowcol
from rasterio.enums import Resampling
from rasterio import mask as rio_mask
from rasterio.features import geometry_mask, geometry_window
from joblib import Parallel, delayed

# ── CONSTANTES ─────────────────────────────────────────────────────
LAS_FILE_PATH    = "DADOS2/DADOS2.las"
OUTPUT_PATH      = "SAIDA_DADOS2"
VALIDACAO_PATH   = os.path.join(OUTPUT_PATH, "validacao_concave")
MOSAICO_PATH     = os.path.join(OUTPUT_PATH, "mosaico")
TILES_PATH       = os.path.join(MOSAICO_PATH, "tiles")   # subpasta dos tiles
TILES_R_PATH     = os.path.join(TILES_PATH, "R")
TILES_G_PATH     = os.path.join(TILES_PATH, "G")
TILES_B_PATH     = os.path.join(TILES_PATH, "B")
CRS              = "EPSG:31982"
RATIO_INICIAL    = 0.10
RATIO_STEP       = 0.01
LIMIAR_ESCADA    = 12.0
SUAVISACAO       = 20
PIXEL_MINIMO_M   = 0.01
FATOR_CONVERSAO  = 0.75
OVERVIEW_LEVELS  = [2, 4, 8, 16, 32, 64]

# ── PARAMETROS IDW ─────────────────────────────────────────────────
IDW_K            = 5        # vizinhos mais proximos para IDW
IDW_POWER        = 2.0      # expoente da distancia (2 = inverso quadratico)
IDW_RAIO_MAX_M   = 0.50     # raio maximo de busca em metros

# ── PARAMETROS DE CHUNK ────────────────────────────────────────────
PONTOS_POR_CHUNK = 10_000_000
CHUNK_OVERLAP_M  = 3.0

# ── FILTRO DE PONTOS PRETOS ────────────────────────────────────────
# [V5] Remove pontos onde R, G e B sao todos iguais ou abaixo deste limiar.
# Valor 0 = remove apenas preto puro. Valores baixos (ex: 5) removem
# tambem pontos muito escuros que sao ruido.
FILTRO_PRETO_LIMIAR = 0
# ────────────────────────────────────────────────────────────────────


def log(msg: str):
    ts = datetime.datetime.now().strftime("[%H:%M:%S]")
    print(f"{ts} {msg}", flush=True)


def tempo_decorrido(tic: float, label: str):
    elapsed = time.perf_counter() - tic
    h = int(elapsed // 3600)
    m = int((elapsed % 3600) // 60)
    s = elapsed % 60
    log(f"[T] {label}: {h:02d}h{m:02d}m{s:06.3f}s")


def salvar_gpkg(geometry, path, name):
    schema = {"geometry": "Polygon", "properties": {"name": "str"}}
    with fiona.open(path, "w", driver="GPKG", schema=schema, crs=CRS) as dst:
        dst.write({"geometry": mapping(geometry), "properties": {"name": name}})


def _filtrar_pontos_pretos(las, limiar: int):
    """
    [V5] Identifica e remove pontos onde R, G e B estao todos abaixo do limiar.
    
    Retorna (las_limpo, n_removidos, n_total).
    Se nao houver RGB, retorna o LAS original com 0 removidos.
    """
    has_rgb = hasattr(las, "red") and las.red is not None
    if not has_rgb:
        return las, 0, len(las.points)

    red   = np.asarray(las.red, dtype=np.int64)
    green = np.asarray(las.green, dtype=np.int64)
    blue  = np.asarray(las.blue, dtype=np.int64)

    # [V5] Mascara: mantem pontos onde pelo menos uma banda > limiar
    mask_valido = (red > limiar) | (green > limiar) | (blue > limiar)
    n_total     = len(las.points)
    n_removidos = n_total - int(np.sum(mask_valido))

    if n_removidos == 0:
        log(f"  Filtro pontos pretos: nenhum ponto removido (limiar={limiar})")
        return las, 0, n_total

    # Aplica o filtro mantendo a estrutura completa do LAS
    las_limpo = laspy.LasData(las.header)
    las_limpo.points = las.points[mask_valido]

    log(f"  Filtro pontos pretos: removidos {n_removidos:,} / {n_total:,} "
        f"pontos (limiar={limiar})")
    return las_limpo, n_removidos, n_total


# ══════════════════════════════════════════════════════════════════════
# ESTAGIO 1 — funcao de worker: interpola um tile e salva em disco
# ══════════════════════════════════════════════════════════════════════

def _idw_tile_para_disco(chunk_idx, total_chunks,
                          tile_tag,
                          tile_bounds, grid_bounds, resol,
                          x_pts, y_pts, r_pts, g_pts, b_pts,
                          k, power, raio_max,
                          crs_str,
                          path_r_out, path_g_out, path_b_out):
    """
    Interpola um tile com IDW e salva tile_RRRR_CCCC.tif em
    pastas R/, G/, B/ separadas.

    Se os 3 arquivos ja existem, pula (retomada automatica).

    Retorna (chunk_idx, tile_tag, row0, row1, col0, col1, status)
    onde status = 'OK' | 'VAZIO' | 'PULADO' | 'ERRO'
    """
    t0 = time.perf_counter()

    # Retomada: se os 3 arquivos ja existem, pula
    if (os.path.exists(path_r_out) and
            os.path.exists(path_g_out) and
            os.path.exists(path_b_out)):
        elapsed = time.perf_counter() - t0
        log(f"    Tile {chunk_idx+1:>4}/{total_chunks} [{tile_tag}] | PULADO (ja existe) | {elapsed:.1f}s")
        # Precisa retornar row0/col0 para montar o grid — le do arquivo existente
        with rasterio.open(path_r_out) as src:
            # [V1] Calcula posicao manualmente pelo transform
            r0, c0 = rowcol(src.transform, src.bounds.left, src.bounds.top)
            row0 = int(r0)
            col0 = int(c0)
            row1 = row0 + src.height
            col1 = col0 + src.width
        return (chunk_idx, tile_tag, row0, row1, col0, col1, 'PULADO')

    x0_tile, x1_tile, y0_tile, y1_tile = tile_bounds
    min_x_g, max_x_g, min_y_g, max_y_g = grid_bounds

    # Indices de pixel do tile no grid global
    col0 = int(round((x0_tile - min_x_g) / resol))
    col1 = int(round((x1_tile - min_x_g) / resol))
    row0 = int(round((max_y_g - y1_tile) / resol))
    row1 = int(round((max_y_g - y0_tile) / resol))

    tile_w = col1 - col0
    tile_h = row1 - row0

    if tile_w <= 0 or tile_h <= 0:
        elapsed = time.perf_counter() - t0
        log(f"    Tile {chunk_idx+1:>4}/{total_chunks} [{tile_tag}] | DIM ZERO | {elapsed:.1f}s")
        return (chunk_idx, tile_tag, row0, row1, col0, col1, 'VAZIO')

    # Coleta pontos com overlap para evitar artefatos de borda
    x0_q = x0_tile - CHUNK_OVERLAP_M
    x1_q = x1_tile + CHUNK_OVERLAP_M
    y0_q = y0_tile - CHUNK_OVERLAP_M
    y1_q = y1_tile + CHUNK_OVERLAP_M

    mask = (
        (x_pts >= x0_q) & (x_pts <= x1_q) &
        (y_pts >= y0_q) & (y_pts <= y1_q)
    )
    n_locais = int(np.sum(mask))

    # Coordenadas do grid de saida (centros dos pixels)
    xi = min_x_g + (col0 + 0.5 + np.arange(tile_w)) * resol
    yi = max_y_g - (row0 + 0.5 + np.arange(tile_h)) * resol
    xi_grid, yi_grid = np.meshgrid(xi, yi)
    query_pts = np.column_stack((xi_grid.ravel(), yi_grid.ravel()))

    # Transform para o tile (necessario para salvar o GeoTIFF do tile)
    tile_transform = from_origin(
        min_x_g + col0 * resol,
        max_y_g - row0 * resol,
        resol, resol
    )

    if n_locais < k:
        # Tile vazio: salva zeros para manter o registro
        z = np.zeros((tile_h, tile_w), dtype=np.uint8)
        _salvar_tile_tif(path_r_out, z, tile_transform, crs_str)
        _salvar_tile_tif(path_g_out, z, tile_transform, crs_str)
        _salvar_tile_tif(path_b_out, z, tile_transform, crs_str)
        elapsed = time.perf_counter() - t0
        log(f"    Tile {chunk_idx+1:>4}/{total_chunks} [{tile_tag}] | pts={n_locais:>8} | {elapsed:6.1f}s | VAZIO")
        return (chunk_idx, tile_tag, row0, row1, col0, col1, 'VAZIO')

    # ── IDW ────────────────────────────────────────────────────────
    pts_locais = np.column_stack((x_pts[mask], y_pts[mask]))
    tree = cKDTree(pts_locais)
    dist, idx = tree.query(query_pts, k=k, workers=1)

    dist_min = dist[:, 0]
    valido = dist_min <= raio_max

    exato    = dist == 0.0
    hit_exato = exato.any(axis=1)

    with np.errstate(divide='ignore', invalid='ignore'):
        pesos = 1.0 / np.power(dist, power)

    if hit_exato.any():
        pesos[hit_exato] = np.where(exato[hit_exato], 1.0, 0.0)

    soma_pesos = pesos.sum(axis=1, keepdims=True)
    soma_pesos = np.where(soma_pesos == 0, 1.0, soma_pesos)
    pesos_norm = pesos / soma_pesos

    r_vals = r_pts[mask][idx]
    g_vals = g_pts[mask][idx]
    b_vals = b_pts[mask][idx]

    r_interp = (pesos_norm * r_vals).sum(axis=1)
    g_interp = (pesos_norm * g_vals).sum(axis=1)
    b_interp = (pesos_norm * b_vals).sum(axis=1)

    r_interp[~valido] = 0
    g_interp[~valido] = 0
    b_interp[~valido] = 0

    r_tile = np.clip(r_interp, 0, 255).astype(np.uint8).reshape(tile_h, tile_w)
    g_tile = np.clip(g_interp, 0, 255).astype(np.uint8).reshape(tile_h, tile_w)
    b_tile = np.clip(b_interp, 0, 255).astype(np.uint8).reshape(tile_h, tile_w)

    # ── SALVA TILES EM DISCO ───────────────────────────────────────
    _salvar_tile_tif(path_r_out, r_tile, tile_transform, crs_str)
    _salvar_tile_tif(path_g_out, g_tile, tile_transform, crs_str)
    _salvar_tile_tif(path_b_out, b_tile, tile_transform, crs_str)

    elapsed = time.perf_counter() - t0
    log(f"    Tile {chunk_idx+1:>4}/{total_chunks} [{tile_tag}] | pts={n_locais:>8} | {elapsed:6.1f}s")

    return (chunk_idx, tile_tag, row0, row1, col0, col1, 'OK')


def _salvar_tile_tif(path, arr, transform, crs_str):
    """Salva array uint8 2D como GeoTIFF de 1 banda com BIGTIFF=YES."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with rasterio.open(
        path, "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype=np.uint8,
        crs=crs_str,
        transform=transform,
        BIGTIFF="YES",  # [V5] Suporta arquivos >4GB
    ) as dst:
        dst.write(arr, 1)


def _calcular_tiles_por_densidade(x_pts, y_pts,
                                   min_x_g, max_x_g, min_y_g, max_y_g,
                                   resol, pontos_por_chunk):
    """
    Divide a area em tiles com ~pontos_por_chunk pontos cada.

    Retorna lista de (x0, x1, y0, y1, row, col) — bounds geograficos + indices.
    """
    n_total   = len(x_pts)
    n_alvo    = max(1, int(math.ceil(n_total / pontos_por_chunk)))

    lado      = max(1, int(math.ceil(math.sqrt(n_alvo))))
    n_cols    = lado
    n_rows    = int(math.ceil(n_alvo / n_cols))

    dx = (max_x_g - min_x_g) / n_cols
    dy = (max_y_g - min_y_g) / n_rows

    tiles = []
    for row in range(n_rows):
        for col in range(n_cols):
            x0 = min_x_g + col       * dx
            x1 = min_x_g + (col + 1) * dx
            y0 = min_y_g + row       * dy
            y1 = min_y_g + (row + 1) * dy
            tiles.append((x0, x1, y0, y1, row, col))

    log(f"  Grade de tiles: {n_cols} colunas x {n_rows} linhas = {len(tiles)} tiles")
    log(f"  Pontos totais: {n_total:,} | alvo por tile: {pontos_por_chunk:,}")
    log(f"  Tile size geografico: {dx:.1f} m x {dy:.1f} m")
    n_rows_px = int(round(dy / resol))
    n_cols_px = int(round(dx / resol))
    log(f"  Tile size em pixels: ~{n_cols_px} x {n_rows_px}")

    return tiles


# ══════════════════════════════════════════════════════════════════════
# ESTAGIO 2 — mescla tiles de uma banda em arquivo completo via memmap
# ══════════════════════════════════════════════════════════════════════

def _mesclar_banda(nome_banda, tile_paths, height, width, transform, crs_str,
                   out_path, chunk_linhas=2048):
    """
    Le todos os tiles de uma banda e os escreve num GeoTIFF completo.

    [V1] CORRECAO: calcula posicao (r0,c0) manualmente a partir do transform
    de cada tile, em vez de usar src.window(*src.bounds) que sempre retornava
    (0,0) porque o tile e o raster inteiro — o window relativo a si proprio
    sempre comeca em (0,0).
    """
    tic = time.perf_counter()
    log(f"  [{nome_banda}] Mesclando {len(tile_paths)} tiles -> {out_path}")

    # Buffer em disco
    bin_path = out_path.replace(".tif", ".bin")
    mm = np.memmap(bin_path, dtype=np.uint8, mode="w+", shape=(height, width))

    for tp in tile_paths:
        if not os.path.exists(tp):
            continue
        with rasterio.open(tp) as src:
            data = src.read(1)

            # [V1] CORRECAO: calcula posicao manualmente pelo transform
            # rowcol retorna (row, col) no grid global para o canto superior
            # esquerdo do tile
            r0, c0 = rowcol(transform, src.bounds.left, src.bounds.top)
            r0 = int(r0)
            c0 = int(c0)

            r1 = r0 + data.shape[0]
            c1 = c0 + data.shape[1]

            # Clipa ao grid
            r0c  = max(0, r0);  r1c = min(height, r1)
            c0c  = max(0, c0);  c1c = min(width,  c1)
            if r1c <= r0c or c1c <= c0c:
                continue
            th   = r1c - r0c
            tw   = c1c - c0c
            mm[r0c:r1c, c0c:c1c] = data[:th, :tw]

    mm.flush()

    # Escreve o GeoTIFF com LZW por chunks de linhas
    with rasterio.open(
        out_path, "w",
        driver="GTiff",
        height=height, width=width,
        count=1, dtype=np.uint8,
        crs=crs_str, transform=transform,
        compress="lzw", predictor=2,
        tiled=True, blockxsize=512, blockysize=512,
        BIGTIFF="YES",  # [V5] Suporta arquivos >4GB
    ) as dst:
        for rs in range(0, height, chunk_linhas):
            re  = min(rs + chunk_linhas, height)
            win = rasterio.windows.Window(0, rs, width, re - rs)
            dst.write(mm[rs:re, :], 1, window=win)

    del mm
    try:
        os.remove(bin_path)
    except OSError:
        pass

    tempo_decorrido(tic, f"Mescla {nome_banda}")
    return out_path


def main():
    t0 = time.perf_counter()
    os.makedirs(OUTPUT_PATH,      exist_ok=True)
    os.makedirs(VALIDACAO_PATH,   exist_ok=True)
    os.makedirs(MOSAICO_PATH,     exist_ok=True)
    os.makedirs(TILES_PATH,       exist_ok=True)
    # [V4] Pastas separadas para cada banda
    os.makedirs(TILES_R_PATH,     exist_ok=True)
    os.makedirs(TILES_G_PATH,     exist_ok=True)
    os.makedirs(TILES_B_PATH,     exist_ok=True)

    # ── LEITURA DO LAS ──────────────────────────────────────────────
    tic = time.perf_counter()
    log(f"Abrindo: {LAS_FILE_PATH}")
    las = laspy.read(LAS_FILE_PATH)
    tempo_decorrido(tic, "Leitura do LAS")

    # [V5] Filtro de pontos pretos antes de qualquer processamento
    log("\n=== Filtro de pontos pretos (R=G=B=0) ===")
    t_filtro = time.perf_counter()
    las, n_removidos, n_total = _filtrar_pontos_pretos(las, FILTRO_PRETO_LIMIAR)
    tempo_decorrido(t_filtro, "Filtro de pontos pretos")

    # [V5] Salva LAS limpo se houve remocao
    if n_removidos > 0:
        las_limpo_path = LAS_FILE_PATH.replace(".las", "_limpo.las")
        tic = time.perf_counter()
        las.write(las_limpo_path)
        tempo_decorrido(tic, "Salvar LAS limpo")
        log(f"  LAS limpo salvo: {las_limpo_path}  ({len(las.points):,} pontos)")

    x = np.asarray(las.x, dtype=np.float64)
    y = np.asarray(las.y, dtype=np.float64)
    z = np.asarray(las.z, dtype=np.float64)

    min_x, max_x = float(np.min(x)), float(np.max(x))
    min_y, max_y = float(np.min(y)), float(np.max(y))
    min_z, max_z = float(np.min(z)), float(np.max(z))
    n_pontos = len(las.points)

    log(f"Total de pontos: {n_pontos:,}")
    log(f"Bbox X: {min_x:.2f} a {max_x:.2f}")
    log(f"Bbox Y: {min_y:.2f} a {max_y:.2f}")

    # ── RGB ─────────────────────────────────────────────────────────
    has_rgb = hasattr(las, "red") and las.red is not None
    if has_rgb:
        red_raw   = np.asarray(las.red,   dtype=np.float64)
        green_raw = np.asarray(las.green, dtype=np.float64)
        blue_raw  = np.asarray(las.blue,  dtype=np.float64)

        if np.max(red_raw) > 255:
            red_8   = (red_raw   / 256).astype(np.uint8)
            green_8 = (green_raw / 256).astype(np.uint8)
            blue_8  = (blue_raw  / 256).astype(np.uint8)
            log("RGB convertido de 16-bit para 8-bit")
        else:
            red_8   = red_raw.astype(np.uint8)
            green_8 = green_raw.astype(np.uint8)
            blue_8  = blue_raw.astype(np.uint8)

        rgb_min = {
            "red":   int(np.min(red_raw)),
            "green": int(np.min(green_raw)),
            "blue":  int(np.min(blue_raw)),
        }
        rgb_max = {
            "red":   int(np.max(red_raw)),
            "green": int(np.max(green_raw)),
            "blue":  int(np.max(blue_raw)),
        }
        del red_raw, green_raw, blue_raw
    else:
        red_8 = green_8 = blue_8 = None
        rgb_min = rgb_max = None
        log("AVISO: o arquivo LAS nao possui bandas RGB. Mosaico nao sera gerado.")

    # ── VALIDACAO CONCAVE HULL ──────────────────────────────────────
    log(f"\n=== Validacao Concave (ratio {RATIO_INICIAL} -> descendo {RATIO_STEP} ate escada) ===")
    t_val = time.perf_counter()

    tic = time.perf_counter()
    log("  Preparando 100k pontos para Concave Hull...")
    step_v   = max(1, n_pontos // 100_000)
    x_v      = x[::step_v]
    y_v      = y[::step_v]
    coords_v = np.column_stack((x_v, y_v))
    mp_v     = MultiPoint(coords_v)
    log(f"    Total pontos usados: {len(x_v):,}")
    tempo_decorrido(tic, "Preparar pontos")

    hull_ref = concave_hull(mp_v, ratio=RATIO_INICIAL)
    area_ref = hull_ref.area
    log(f"  Area de referencia (ratio={RATIO_INICIAL}): {area_ref:.4f} m2")

    gpkg_ref_path = os.path.join(VALIDACAO_PATH, f"concave_r{RATIO_INICIAL:.3f}.gpkg")
    salvar_gpkg(hull_ref, gpkg_ref_path, f"concave_r{RATIO_INICIAL:.3f}")

    step_int                = int(round(RATIO_STEP   * 1000))
    current_int             = int(round(RATIO_INICIAL * 1000))
    ratio_ideal             = RATIO_INICIAL
    hull_final              = hull_ref
    area_anterior           = area_ref
    ultimo_ratio_processado = RATIO_INICIAL
    resultados_validacao    = []
    encontrou_escada        = False

    while current_int > 0 and not encontrou_escada:
        current_int -= step_int
        if current_int < 0:
            current_int = 0
        ratio_atual = current_int / 1000
        if ratio_atual == ultimo_ratio_processado:
            continue

        tic  = time.perf_counter()
        hull = concave_hull(mp_v, ratio=ratio_atual)
        area = hull.area
        pct  = (area / area_ref) * 100
        queda_pct = ((area_anterior - area) / area_anterior) * 100 if area_anterior > 0 else 0
        elapsed   = time.perf_counter() - tic

        log(f"  r={ratio_atual:.3f}: {area:.2f} m2 = {pct:.2f}% | queda={queda_pct:.2f}% | {elapsed:.3f}s")
        salvar_gpkg(hull,
                    os.path.join(VALIDACAO_PATH, f"concave_r{ratio_atual:.3f}.gpkg"),
                    f"concave_r{ratio_atual:.3f}")

        resultados_validacao.append({
            "ratio":              round(ratio_atual, 3),
            "area_m2":            round(area, 4),
            "porcentagem":        round(pct, 2),
            "queda_porcentagem":  round(queda_pct, 2),
            "tempo_s":            round(elapsed, 3),
        })

        if queda_pct > LIMIAR_ESCADA and ratio_atual < RATIO_INICIAL:
            ratio_ideal  = round(ultimo_ratio_processado, 3)
            hull_final   = hull
            log(f"\n  >>> ESCADA em r={ratio_atual:.3f} (queda={queda_pct:.2f}%)")
            log(f"  >>> Ratio ideal = {ratio_ideal:.3f}")
            encontrou_escada = True
            break

        area_anterior           = area
        ultimo_ratio_processado = ratio_atual
        if ratio_atual == 0.0:
            break

    if not encontrou_escada:
        ratio_ideal = round(ultimo_ratio_processado, 3)
        hull_final  = hull
        log(f"\n  >>> Nenhuma escada. Usando ratio = {ratio_ideal}")

    tempo_decorrido(t_val, "Validacao completa")

    area_hull = hull_final.area
    log(f"\n  Area hull (ratio={ratio_ideal:.3f}): {area_hull:.4f} m2")

    tic = time.perf_counter()
    log(f"  Suavisacao (buffer +{SUAVISACAO}m / -{SUAVISACAO}m)...")
    hull_suavizado = hull_final.buffer(SUAVISACAO, resolution=16).buffer(-SUAVISACAO, resolution=16)
    area_suavizada = hull_suavizado.area
    tempo_decorrido(tic, "Suavisacao")

    gpkg_final_path = os.path.join(OUTPUT_PATH, f"limite_concave_r{ratio_ideal:.3f}_suavizado.gpkg")
    salvar_gpkg(hull_suavizado, gpkg_final_path, f"limite_concave_r{ratio_ideal:.3f}_suavizado")
    log(f"\nPoligono salvo: {gpkg_final_path}")
    log(f"Area hull:      {area_hull:.4f} m2")
    log(f"Area suavizada: {area_suavizada:.4f} m2")

    # ── DENSIDADE E PIXEL IDEAL ─────────────────────────────────────
    area_bbox      = (max_x - min_x) * (max_y - min_y)
    densidade_bbox = n_pontos / area_bbox      if area_bbox      > 0 else 0.0
    densidade_real = n_pontos / area_suavizada if area_suavizada > 0 else 0.0

    log(f"\nDensidade (bbox):            {densidade_bbox:.4f} pts/m2")
    log(f"Densidade REAL (poligono):   {densidade_real:.4f} pts/m2")

    if densidade_real > 0:
        espacamento_m  = 1.0 / (densidade_real ** 0.5)
        espacamento_cm = espacamento_m * 100
        pixel_ideal_m  = max(espacamento_m * FATOR_CONVERSAO, PIXEL_MINIMO_M)
        pixel_ideal_cm = pixel_ideal_m * 100
    else:
        espacamento_m = espacamento_cm = 0.0
        pixel_ideal_m  = PIXEL_MINIMO_M
        pixel_ideal_cm = PIXEL_MINIMO_M * 100

    log(f"\n  --- Pixel Ideal ---")
    log(f"  Espacamento:  {espacamento_cm:.2f} cm / ponto")
    log(f"  Pixel ideal:  {pixel_ideal_cm:.2f} cm ({pixel_ideal_m*1000:.1f} mm)")

    # ══════════════════════════════════════════════════════════════════
    # GERACAO DO MOSAICO — estagio por estagio
    # ══════════════════════════════════════════════════════════════════
    tiff_rgb_path       = None
    tiff_recortado_path = None
    tiff_final_path     = None
    banda_R_path        = None
    banda_G_path        = None
    banda_B_path        = None

    if has_rgb:
        log(f"\n{'='*65}")
        log("MOSAICO RGB + ALPHA — arquitetura por estagios")
        log(f"{'='*65}")
        t_mosaico = time.perf_counter()

        x_m = x
        y_m = y
        r_m = red_8.astype(np.float32)
        g_m = green_8.astype(np.float32)
        b_m = blue_8.astype(np.float32)

        # ── GRID GLOBAL ────────────────────────────────────────────
        tic   = time.perf_counter()
        resol = pixel_ideal_m

        min_x_g = float(x_m.min())
        max_x_g = float(x_m.max())
        min_y_g = float(y_m.min())
        max_y_g = float(y_m.max())

        width  = int(np.ceil((max_x_g - min_x_g) / resol))
        height = int(np.ceil((max_y_g - min_y_g) / resol))
        transform = from_origin(min_x_g, max_y_g, resol, resol)

        log(f"\n  Grid (bounds REAIS dos pontos):")
        log(f"    X: [{min_x_g:.2f}, {max_x_g:.2f}]")
        log(f"    Y: [{min_y_g:.2f}, {max_y_g:.2f}]")
        log(f"    Dimensoes: {width:,} x {height:,} pixels (resol={resol*100:.2f} cm)")
        tempo_decorrido(tic, "Calcular grid")

        # ── TILES ──────────────────────────────────────────────────
        tic   = time.perf_counter()
        tiles = _calcular_tiles_por_densidade(
            x_m, y_m,
            min_x_g, max_x_g, min_y_g, max_y_g,
            resol, PONTOS_POR_CHUNK
        )
        total_tiles = len(tiles)
        log(f"  Total tiles: {total_tiles}")
        tempo_decorrido(tic, "Calcular tiles")

        # ══════════════════════════════════════════════════════════
        # ESTAGIO 1 — Interpolacao paralela, salva tiles em disco
        # ══════════════════════════════════════════════════════════
        log(f"\n{'─'*65}")
        log(f"ESTAGIO 1 — Interpolacao IDW -> tiles em {TILES_PATH}")
        log(f"  Pastas: {TILES_R_PATH}/, {TILES_G_PATH}/, {TILES_B_PATH}/")
        log(f"{'─'*65}")
        log(f"  IDW: k={IDW_K}, p={IDW_POWER}, raio={IDW_RAIO_MAX_M}m, overlap={CHUNK_OVERLAP_M}m")
        log(f"  Tiles ja existentes serao pulados automaticamente.")
        tic = time.perf_counter()

        grid_bounds = (min_x_g, max_x_g, min_y_g, max_y_g)

        # Prepara caminhos dos tiles
        tile_jobs = []
        for idx, (x0, x1, y0, y1, t_row, t_col) in enumerate(tiles):
            tag   = f"{t_row:04d}_{t_col:04d}"
            # [V4] Pastas separadas por banda
            pr    = os.path.join(TILES_R_PATH, f"tile_{tag}.tif")
            pg    = os.path.join(TILES_G_PATH, f"tile_{tag}.tif")
            pb    = os.path.join(TILES_B_PATH, f"tile_{tag}.tif")
            tile_jobs.append((idx, tag, (x0, x1, y0, y1), pr, pg, pb))

        n_pendentes = sum(
            1 for _, _, _, pr, pg, pb in tile_jobs
            if not (os.path.exists(pr) and os.path.exists(pg) and os.path.exists(pb))
        )
        log(f"  Tiles pendentes: {n_pendentes}/{total_tiles}")

        results = Parallel(n_jobs=-1, verbose=0)(
            delayed(_idw_tile_para_disco)(
                idx, total_tiles,
                tag,
                tile_bounds, grid_bounds, resol,
                x_m, y_m, r_m, g_m, b_m,
                IDW_K, IDW_POWER, IDW_RAIO_MAX_M,
                CRS,
                pr, pg, pb
            )
            for idx, tag, tile_bounds, pr, pg, pb in tile_jobs
        )

        n_ok     = sum(1 for r in results if r[6] == 'OK')
        n_pulado = sum(1 for r in results if r[6] == 'PULADO')
        n_vazio  = sum(1 for r in results if r[6] == 'VAZIO')
        n_erro   = sum(1 for r in results if r[6] == 'ERRO')
        tempo_decorrido(tic, "ESTAGIO 1 — Interpolacao IDW")
        log(f"  Resultado: OK={n_ok} | PULADO={n_pulado} | VAZIO={n_vazio} | ERRO={n_erro}")

        del x_m, y_m, r_m, g_m, b_m

        # ══════════════════════════════════════════════════════════
        # ESTAGIO 2 — Mescla tiles em bandas isoladas
        # ══════════════════════════════════════════════════════════
        log(f"\n{'─'*65}")
        log("ESTAGIO 2 — Mescla de tiles -> bandas isoladas")
        log(f"{'─'*65}")
        tic = time.perf_counter()

        banda_R_path = os.path.join(MOSAICO_PATH, "banda_R.tif")
        banda_G_path = os.path.join(MOSAICO_PATH, "banda_G.tif")
        banda_B_path = os.path.join(MOSAICO_PATH, "banda_B.tif")

        # [V4] Busca tiles nas pastas separadas
        tiles_R = sorted(glob.glob(os.path.join(TILES_R_PATH, "tile_*.tif")))
        tiles_G = sorted(glob.glob(os.path.join(TILES_G_PATH, "tile_*.tif")))
        tiles_B = sorted(glob.glob(os.path.join(TILES_B_PATH, "tile_*.tif")))

        log(f"  Tiles encontrados: R={len(tiles_R)} G={len(tiles_G)} B={len(tiles_B)}")

        _mesclar_banda("R", tiles_R, height, width, transform, CRS, banda_R_path)
        _mesclar_banda("G", tiles_G, height, width, transform, CRS, banda_G_path)
        _mesclar_banda("B", tiles_B, height, width, transform, CRS, banda_B_path)

        tempo_decorrido(tic, "ESTAGIO 2 — Mescla bandas")
        log(f"  Bandas isoladas salvas:")
        log(f"    {banda_R_path}")
        log(f"    {banda_G_path}")
        log(f"    {banda_B_path}")
        log("  >>> Valide as bandas isoladas antes de prosseguir <<<")

        # ══════════════════════════════════════════════════════════
        # ESTAGIO 3 — Une bandas em mosaico RGB completo
        # ══════════════════════════════════════════════════════════
        log(f"\n{'─'*65}")
        log("ESTAGIO 3 — Uniao das bandas -> mosaico_rgb.tif")
        log(f"{'─'*65}")
        tic = time.perf_counter()

        tiff_rgb_path = os.path.join(MOSAICO_PATH, "mosaico_rgb.tif")
        CHUNK_LINHAS  = 2048

        with rasterio.open(banda_R_path) as src_r, \
             rasterio.open(banda_G_path) as src_g, \
             rasterio.open(banda_B_path) as src_b:

            meta = src_r.meta.copy()
            meta.update({
                "count":       3,
                "compress":    "lzw",
                "predictor":    2,
                "photometric": "RGB",
                "tiled":       True,
                "blockxsize":  512,
                "blockysize":  512,
                "BIGTIFF":     "YES",   # [V5] Suporta arquivos >4GB
            })
            with rasterio.open(tiff_rgb_path, "w", **meta) as dst:
                for rs in range(0, height, CHUNK_LINHAS):
                    re  = min(rs + CHUNK_LINHAS, height)
                    win = rasterio.windows.Window(0, rs, width, re - rs)
                    dst.write(src_r.read(1, window=win), 1, window=win)
                    dst.write(src_g.read(1, window=win), 2, window=win)
                    dst.write(src_b.read(1, window=win), 3, window=win)

        tempo_decorrido(tic, "ESTAGIO 3 — mosaico_rgb.tif")
        sz = os.path.getsize(tiff_rgb_path) / 1e6
        log(f"  Salvo: {tiff_rgb_path}  ({sz:.1f} MB)")

        # ══════════════════════════════════════════════════════════
        # ESTAGIO 4 — Recorte pelo poligono GPKG
        # ══════════════════════════════════════════════════════════
        log(f"\n{'─'*65}")
        log("ESTAGIO 4 — Recorte pelo poligono suavizado")
        log(f"{'─'*65}")
        tic = time.perf_counter()

        tiff_recortado_path = os.path.join(MOSAICO_PATH, "mosaico_rgb_recortado.tif")

        with rasterio.open(tiff_rgb_path) as src:
            # [V2] nodata=0 e problema: 0 e preto legitimo.
            # Usamos nodata=255 (maximo uint8) que fica fora do range esperado
            # de 0-254 para pixels de dados. Mas cuidado: isso pode conflitar
            # com pixels 255 reais.
            # Solucao melhor: crop=True + filled=True, e depois preenchemos
            # com nodata=255 explicito.
            # O recorte ja mascara pixels fora do poligono com nodata.
            out_img, out_transform = rio_mask.mask(
                src, [mapping(hull_suavizado)],
                crop=True,
                nodata=255,  # [V2] 255 = fora do poligono (diferente de preto=0)
                filled=True,
            )
            out_meta = src.meta.copy()
            out_meta.update({
                "height":      out_img.shape[1],
                "width":       out_img.shape[2],
                "transform":   out_transform,
                "compress":    "lzw",
                "predictor":   2,
                "nodata":      255,  # [V2]
                "tiled":       True,
                "blockxsize":  512,
                "blockysize":  512,
                "photometric": "RGB",  # [V2] Mantem photometric
                "BIGTIFF":     "YES",   # [V5] Suporta arquivos >4GB
            })
            with rasterio.open(tiff_recortado_path, "w", **out_meta) as dst:
                dst.write(out_img)

        h_rec = out_img.shape[1]
        w_rec = out_img.shape[2]
        del out_img
        tempo_decorrido(tic, "ESTAGIO 4 — Recorte")
        sz = os.path.getsize(tiff_recortado_path) / 1e6
        log(f"  Salvo: {tiff_recortado_path}  ({sz:.1f} MB, {w_rec:,}x{h_rec:,} px)")

        # ══════════════════════════════════════════════════════════
        # ESTAGIO 5 — Banda alpha + RGBA final
        # ══════════════════════════════════════════════════════════
        log(f"\n{'─'*65}")
        log("ESTAGIO 5 — Banda alpha + mosaico_rgba_final.tif")
        log(f"{'─'*65}")
        tic = time.perf_counter()

        # [V3] CORRECAO: alpha calculada pela mascara do poligono suavizado,
        # nao pelo valor RGB dos pixels.
        # Abrimos o raster recortado e calculamos quais pixels estao DENTRO
        # do poligono usando geometry_mask.
        with rasterio.open(tiff_recortado_path) as src_rec:
            # Cria mascara do poligono no espaco do raster recortado
            # invert=False: True onde DENTRO do poligono
            alpha_mask = ~geometry_mask(
                [mapping(hull_suavizado)],
                transform=src_rec.transform,
                invert=False,  # Queremos True dentro, False fora
                out_shape=(src_rec.height, src_rec.width),
            )
            # Converte para uint8: 255 dentro, 0 fora
            alpha = np.where(alpha_mask, np.uint8(255), np.uint8(0))

            # Cria RGBA final
            tiff_final_path = os.path.join(MOSAICO_PATH, "mosaico_rgba_final.tif")

            meta = src_rec.meta.copy()
            meta.update({
                "count":       4,
                "compress":    "lzw",
                "predictor":   2,
                "tiled":       True,
                "blockxsize":  512,
                "blockysize":  512,
                "BIGTIFF":     "YES",   # [V5] Suporta arquivos >4GB
            })
            # Remove nodata e photometric que nao se aplicam a RGBA
            meta.pop("nodata", None)
            # RGBA usa photometric RGB + alpha, ou podemos remover
            meta.pop("photometric", None)

            with rasterio.open(tiff_final_path, "w", **meta) as dst:
                for banda in range(1, 4):
                    dst.write(src_rec.read(banda), banda)
                dst.write(alpha, 4)

        del alpha, alpha_mask

        tempo_decorrido(tic, "ESTAGIO 5 — RGBA final")

        # ── OVERVIEWS ──────────────────────────────────────────────
        tic = time.perf_counter()
        log(f"  Gerando overviews ({OVERVIEW_LEVELS})...")
        try:
            from osgeo import gdal
            gdal.SetConfigOption("COMPRESS_OVERVIEW", "DEFLATE")
            gdal.SetConfigOption("PREDICTOR_OVERVIEW", "2")
            ds = gdal.Open(tiff_final_path, gdal.GA_ReadOnly)
            if ds is not None:
                ds.BuildOverviews("AVERAGE", OVERVIEW_LEVELS)
                ds = None
                log(f"  Overviews -> {tiff_final_path}.ovr")
            else:
                log("  AVISO: gdal.Open retornou None")
        except ImportError:
            log("  osgeo.gdal nao disponivel — overviews pulados")
            log("  (instale gdal ou execute: gdaladdo -r average mosaico_rgba_final.tif 2 4 8 16)")
        tempo_decorrido(tic, "Overviews")

        # ── CHECK FINAL ────────────────────────────────────────────
        log(f"\n{'─'*65}")
        log("CHECK FINAL")
        log(f"{'─'*65}")
        tic = time.perf_counter()
        with rasterio.open(tiff_final_path) as src:
            log(f"  Arquivo:    {tiff_final_path}")
            log(f"  Dimensoes:  {src.width:,} x {src.height:,} pixels")
            log(f"  Bandas:     {src.count}  (1=R 2=G 3=B 4=Alpha)")
            log(f"  CRS:        {src.crs}")
            log(f"  Resolucao:  {src.res[0]*100:.2f} cm")
            log(f"  Compressao: {src.compression.value}")
            alp       = src.read(4)
            n_valid   = int(np.sum(alp > 0))
            total_px  = alp.size
            pct_valid = n_valid / total_px * 100 if total_px > 0 else 0
            log(f"  Pixels validos (alpha>0): {n_valid:,} / {total_px:,} ({pct_valid:.2f}%)")
            b = src.bounds
            log(f"  Bbox: x[{b.left:.2f}, {b.right:.2f}] y[{b.bottom:.2f}, {b.top:.2f}]")
            log(f"  Tamanho: {os.path.getsize(tiff_final_path)/1e6:.2f} MB")
        tempo_decorrido(tic, "Check raster")

        log(f"\n  Arquivos gerados:")
        log(f"    tiles/R/     -> {total_tiles} TIFs (R)")
        log(f"    tiles/G/     -> {total_tiles} TIFs (G)")
        log(f"    tiles/B/     -> {total_tiles} TIFs (B)")
        log(f"    banda_R.tif   -> {os.path.getsize(banda_R_path)/1e6:.1f} MB")
        log(f"    banda_G.tif   -> {os.path.getsize(banda_G_path)/1e6:.1f} MB")
        log(f"    banda_B.tif   -> {os.path.getsize(banda_B_path)/1e6:.1f} MB")
        log(f"    mosaico_rgb.tif           -> {os.path.getsize(tiff_rgb_path)/1e6:.1f} MB")
        log(f"    mosaico_rgb_recortado.tif -> {os.path.getsize(tiff_recortado_path)/1e6:.1f} MB")
        log(f"    mosaico_rgba_final.tif    -> {os.path.getsize(tiff_final_path)/1e6:.1f} MB")

        tempo_decorrido(t_mosaico, "MOSAICO COMPLETO")

    else:
        log("\n  AVISO: LAS sem bandas RGB. Mosaico nao gerado.")

    # ── JSON ──────────────────────────────────────────────────────
    stats = {
        "arquivo":          LAS_FILE_PATH,
        "numero_de_pontos": n_pontos,
        "bounding_box": {
            "x": {"min": min_x, "max": max_x},
            "y": {"min": min_y, "max": max_y},
            "z": {"min": min_z, "max": max_z},
        },
        "altimetria": {"min": min_z, "max": max_z},
        "rgb":        {"min": rgb_min, "max": rgb_max},
        "concave_hull": {
            "ratio_inicial":                 RATIO_INICIAL,
            "ratio_step":                    RATIO_STEP,
            "limiar_escada_porcentagem":      LIMIAR_ESCADA,
            "ratio_ideal":                   round(ratio_ideal, 3),
            "area_hull_m2":                  round(area_hull, 4),
            "suavisacao_buffer_m":           SUAVISACAO,
            "area_suavizada_m2":             round(area_suavizada, 4),
            "arquivo_gpkg":                  gpkg_final_path,
        },
        "densidade_pontos_por_m2": {
            "bounding_box":    round(densidade_bbox, 4),
            "poligono_suavizado": round(densidade_real, 4),
        },
        "pixel_ideal": {
            "espacamento_m":  round(espacamento_m, 6),
            "espacamento_cm": round(espacamento_cm, 2),
            "fator_conversao": FATOR_CONVERSAO,
            "pixel_m":        round(pixel_ideal_m, 6),
            "pixel_cm":       round(pixel_ideal_cm, 2),
            "pixel_mm":       round(pixel_ideal_m * 1000, 1),
            "pixel_minimo_m": PIXEL_MINIMO_M,
        },
        "mosaico": {
            "gerado":              has_rgb,
            "metodo":              f"IDW cKDTree k={IDW_K} p={IDW_POWER} raio={IDW_RAIO_MAX_M}m",
            "pontos_usados":       n_pontos,
            "reamostagem":         "NENHUMA",
            "pontos_por_tile":     PONTOS_POR_CHUNK,
            "overlap_m":           CHUNK_OVERLAP_M,
            "pixel_m":             round(pixel_ideal_m, 6),
            "pixel_cm":            round(pixel_ideal_cm, 2),
            "overviews":           OVERVIEW_LEVELS,
            "compressao":          "lzw",
            "bigtiff":             "YES",  # [V5]
            "filtro_pontos_pretos": {
                "aplicado":        n_removidos > 0,
                "limiar":          FILTRO_PRETO_LIMIAR,
                "removidos":       n_removidos,
                "total_original":  n_total,
                "restantes":       n_pontos,
            },
            "arquivos": {
                "tiles_dir":       TILES_PATH,
                "banda_R":         banda_R_path,
                "banda_G":         banda_G_path,
                "banda_B":         banda_B_path,
                "mosaico_rgb":     tiff_rgb_path,
                "rgb_recortado":   tiff_recortado_path,
                "rgba_final":      tiff_final_path,
            },
        } if has_rgb else {"gerado": False, "motivo": "LAS sem bandas RGB"},
        "validacao_resultados": resultados_validacao,
    }

    json_path = os.path.join(OUTPUT_PATH, "estatisticas_las.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    log(f"\nJSON salvo: {json_path}")

    log("\n--- TEMPO TOTAL ---")
    tempo_decorrido(t0, "Execucao completa")


if __name__ == "__main__":
    main()