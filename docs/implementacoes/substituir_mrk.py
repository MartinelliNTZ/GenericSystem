#!/usr/bin/env python3
"""
Script para substituir valores de altitude (Ellh) em arquivos MRK
baseados nos campos de um arquivo de dados (CSV, Shapefile .shp ou GeoPackage .gpkg).

Uso:
  python substituir_mrk.py                              (auto-detectar .csv/.shp/.gpkg)
  python substituir_mrk.py --dados caminho/arquivo.shp  (usar shapefile)
  python substituir_mrk.py --dados caminho/arquivo.gpkg (usar geopackage)
  python substituir_mrk.py --dados dados.csv             (usar csv)

O script procura arquivos de dados na pasta atual ou no caminho especificado.
Para detecção automática, segue a ordem: .gpkg, .shp, .csv correspondente ao MRK.

Configuração do mapeamento via dicionário MAPPING:
  - 'AbsZ'  ->  'Ellh'  (campo de altitude)
  - 'Latitude'  -> 'Lat'    (descomente se quiser)
  - 'Longitude' -> 'Lon'    (descomente se quiser)
"""

import os
import sys
import csv
import glob
import re
import argparse


# ============================================================
# CONFIGURAÇÃO: dicionário de mapeamento coluna_dados -> MRK
# ============================================================
MAPPING = {
    'Latitude': 'Lat',    # descomente se quiser
    'Longitude': 'Lon',   # descomente se quiser
    'AbsZ': 'Ellh',       # Coluna no dado -> campo no MRK (altitude)
}

# Pasta de saída
PASTA_RESULTADO = 'resultado'


def ler_dados_csv(caminho_csv: str):
    """Lê CSV e retorna lista de dicts."""
    with open(caminho_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


def ler_dados_geo(caminho: str):
    """
    Lê Shapefile (.shp) ou GeoPackage (.gpkg) usando geopandas.
    Retorna lista de dicts, convertendo tipos numpy para string.
    """
    import geopandas as gpd
    import numpy as np

    gdf = gpd.read_file(caminho)
    # Remove coluna geometry se existir, não é relevante aqui
    if 'geometry' in gdf.columns:
        gdf = gdf.drop(columns=['geometry'])

    # Converte tipos numpy para tipos nativos Python
    linhas = []
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
                d[col] = ''
            else:
                d[col] = str(val)
        linhas.append(d)

    return linhas


def ler_dados(caminho: str):
    """Detecta formato e lê dados."""
    ext = os.path.splitext(caminho)[1].lower()

    if ext == '.csv':
        return ler_dados_csv(caminho)
    elif ext in ('.shp', '.gpkg'):
        return ler_dados_geo(caminho)
    else:
        raise ValueError(f"Formato não suportado: {ext}. Use .csv, .shp ou .gpkg")


def encontrar_arquivo_dados(nome_mrk: str, caminhos_dados: list = None):
    """
    Encontra o arquivo de dados correspondente ao MRK.
    Se caminhos_dados for fornecido, procura entre eles.
    Caso contrário, busca automática: MrkFile_{MRK}.csv, ou .shp/.gpkg com nome similar.
    """
    nome_base = os.path.splitext(nome_mrk)[0]

    if caminhos_dados:
        for caminho in caminhos_dados:
            if not os.path.exists(caminho):
                continue
            # Se é um único arquivo de dados, usa ele
            if os.path.isfile(caminho):
                return caminho
            # Se é diretório, procura dentro
            if os.path.isdir(caminho):
                for f in os.listdir(caminho):
                    if f.lower().startswith(nome_base.lower()) or \
                       f.lower().startswith(f'mrkfile_{nome_base.lower()}'):
                        ext = os.path.splitext(f)[1].lower()
                        if ext in ('.csv', '.shp', '.gpkg'):
                            return os.path.join(caminho, f)
        return None

    # Busca automática na pasta atual
    padroes = [
        f'MrkFile_{nome_mrk}.csv',
        f'mrkfile_{nome_mrk}.csv',
        f'{nome_base}.csv',
        f'{nome_base}.shp',
        f'{nome_base}.gpkg',
    ]
    for padrao in padroes:
        if os.path.exists(padrao):
            return padrao

    # Busca com glob para ser flexível
    for ext in ('.gpkg', '.shp', '.csv'):
        for f in glob.glob(f'*{ext}'):
            if nome_base.lower() in f.lower() or nome_mrk.lower() in f.lower():
                return f

    return None


def parse_mrk_line(line: str):
    """
    Analisa uma linha do MRK (formato TSV) e retorna:
      - parts: lista das colunas (split por tab)
      - substituicoes: dict {nome_campo: {valor_str, len}}
      - indices: dict {nome_campo: indice_da_coluna_em_parts}
    """
    parts = line.split('\t')
    substituicoes = {}
    indices = {}

    for i, col in enumerate(parts):
        col_stripped = col.strip()
        for campo in ['Lat', 'Lon', 'Ellh']:
            pattern = rf'^(.+),{re.escape(campo)}$'
            match = re.match(pattern, col_stripped)
            if match:
                valor_str = match.group(1).strip()
                substituicoes[campo] = {
                    'valor_str': valor_str,
                    'len': len(valor_str)
                }
                indices[campo] = i
                break

    return parts, substituicoes, indices


def pad_valor(valor_original: str, novo_valor: str) -> str:
    """
    Ajusta o novo valor para ter o MESMO comprimento do valor original,
    preservando a posição decimal.
    """
    tam_original = len(valor_original)
    novo = novo_valor

    if len(novo) == tam_original:
        return novo

    if '.' in valor_original:
        if '.' in novo:
            partes_orig = valor_original.split('.')
            partes_novo = novo.split('.')
            casas_orig = len(partes_orig[1]) if len(partes_orig) > 1 else 0
            casas_novo = len(partes_novo[1]) if len(partes_novo) > 1 else 0

            if casas_novo < casas_orig:
                novo = novo + '0' * (casas_orig - casas_novo)
            elif casas_novo > casas_orig:
                novo = partes_novo[0] + '.' + partes_novo[1][:casas_orig]

            if len(novo) < tam_original:
                dif = tam_original - len(novo)
                novo = novo + '0' * dif
        else:
            partes_orig = valor_original.split('.')
            casas_orig = len(partes_orig[1]) if len(partes_orig) > 1 else 0
            novo = novo + '.' + '0' * casas_orig
            if len(novo) < tam_original:
                dif = tam_original - len(novo)
                novo = novo + '0' * dif

        if len(novo) > tam_original:
            novo = novo[:tam_original]

        return novo

    if len(novo) < tam_original:
        novo = novo + '0' * (tam_original - len(novo))
    elif len(novo) > tam_original:
        novo = novo[:tam_original]

    return novo


def build_mrk_line(parts, indices, novos_valores: dict,
                   substituicoes_originais: dict) -> str:
    """Reconstrói a linha do MRK preservando a tabulação."""
    for campo, novo_valor in novos_valores.items():
        if campo in indices:
            idx = indices[campo]
            col_original = parts[idx].strip()
            valor_original = substituicoes_originais[campo]['valor_str']
            novo_valor_padded = pad_valor(valor_original, novo_valor)

            match = re.match(r'^.*(,' + re.escape(campo) + r')$', col_original)
            if match:
                sufixo = match.group(1)
                parts[idx] = f'{novo_valor_padded}{sufixo}'

    return '\t'.join(parts)


def processar_mrk(caminho_mrk: str, dados_dict_list: list,
                  pasta_destino: str, nome_arquivo_dados: str):
    """
    Processa um MRK com os dados fornecidos.
    """
    nome_base = os.path.basename(caminho_mrk)
    caminho_saida = os.path.join(pasta_destino, nome_base)

    with open(caminho_mrk, 'r', encoding='utf-8') as f_mrk:
        linhas_mrk = f_mrk.readlines()

    linhas_saida = []
    total_substituicoes = 0
    total_linhas_mrk = len(linhas_mrk)
    total_linhas_dados = len(dados_dict_list)
    qtd_linhas = min(total_linhas_mrk, total_linhas_dados)

    for idx_mrk in range(qtd_linhas):
        linha_mrk_raw = linhas_mrk[idx_mrk]
        linha_mrk_sem_nl = linha_mrk_raw.rstrip('\n').rstrip('\r')
        row_dados = dados_dict_list[idx_mrk]

        parts, substituicoes, indices = parse_mrk_line(linha_mrk_sem_nl)

        novos_valores = {}
        for col_dados, campo_mrk in MAPPING.items():
            if col_dados in row_dados and campo_mrk in indices:
                novo_valor = row_dados[col_dados].strip()
                valor_antigo = substituicoes[campo_mrk]['valor_str']
                if novo_valor and novo_valor != valor_antigo:
                    novos_valores[campo_mrk] = novo_valor
                    total_substituicoes += 1
                    print(
                        f"  [{nome_base}] Linha {idx_mrk + 1}: "
                        f"Ellh: '{valor_antigo}' (len={len(valor_antigo)}) -> "
                        f"'{novo_valor}' (len={len(novo_valor)})"
                    )

        if novos_valores:
            linha_modificada = build_mrk_line(parts, indices, novos_valores,
                                              substituicoes)
            if linha_mrk_raw.endswith('\r\n'):
                linhas_saida.append(linha_modificada + '\r\n')
            elif linha_mrk_raw.endswith('\n'):
                linhas_saida.append(linha_modificada + '\n')
            else:
                linhas_saida.append(linha_modificada + '\n')
        else:
            linhas_saida.append(linha_mrk_raw)

    if total_linhas_mrk > qtd_linhas:
        for idx_mrk in range(qtd_linhas, total_linhas_mrk):
            linhas_saida.append(linhas_mrk[idx_mrk])

    with open(caminho_saida, 'w', encoding='utf-8') as f_out:
        f_out.writelines(linhas_saida)

    print(f"\n  >> Arquivo gerado: {caminho_saida}")
    print(f"  >> Total de substituições de Ellh: {total_substituicoes}")
    return total_substituicoes


def main():
    parser = argparse.ArgumentParser(
        description='Substitui valores de altitude (Ellh) em arquivos MRK '
                    'a partir de dados em CSV, Shapefile (.shp) ou GeoPackage (.gpkg).'
    )
    parser.add_argument(
        '--dados', '-d', nargs='+',
        help='Arquivo(s) ou pasta(s) com dados (.csv, .shp, .gpkg). '
             'Se omitido, busca automaticamente.'
    )
    parser.add_argument(
        '--mrk', nargs='+',
        help='Arquivo(s) .MRK específico(s) para processar. '
             'Se omitido, processa todos .MRK da pasta.'
    )
    parser.add_argument(
        '--saida', default=PASTA_RESULTADO,
        help=f'Pasta de saída (padrão: {PASTA_RESULTADO})'
    )
    args = parser.parse_args()

    pasta_destino = args.saida
    os.makedirs(pasta_destino, exist_ok=True)

    # Encontra arquivos MRK
    if args.mrk:
        arquivos_mrk = []
        for padrao in args.mrk:
            if os.path.isfile(padrao):
                arquivos_mrk.append(padrao)
            else:
                arquivos_mrk.extend(glob.glob(padrao))
    else:
        arquivos_mrk = glob.glob('*.MRK')

    if not arquivos_mrk:
        print("Nenhum arquivo .MRK encontrado!")
        sys.exit(1)

    total_geral = 0

    for caminho_mrk in sorted(arquivos_mrk):
        nome_mrk = os.path.basename(caminho_mrk)

        # Encontra arquivo de dados correspondente
        caminho_dados = encontrar_arquivo_dados(nome_mrk, args.dados)

        if not caminho_dados or not os.path.exists(caminho_dados):
            print(f"\n[AVISO] Nenhum arquivo de dados encontrado para {nome_mrk}")
            continue

        print(f"\n{'='*60}")
        print(f"MRK: {nome_mrk}")
        print(f"Dados: {caminho_dados}")
        print(f"{'='*60}")

        try:
            dados = ler_dados(caminho_dados)
        except Exception as e:
            print(f"  ERRO ao ler {caminho_dados}: {e}")
            continue

        total = processar_mrk(caminho_mrk, dados, pasta_destino, caminho_dados)
        total_geral += total

    print(f"\n{'='*60}")
    print(f"FINALIZADO! Total de substituições de Ellh: {total_geral}")
    print(f"Arquivos gerados em: {os.path.abspath(pasta_destino)}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()