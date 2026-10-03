import json
import os
import sys
import glob
from datetime import datetime, timedelta
from pathlib import Path

import requests
from ApiKeys import API_KEY
from dict import (
    maiores_clubes_mundo,
    maiores_clubes_brasil,
    maiores_selecoes,
    maiores_competicoes,
)


# ==================== UTILIDADES ====================
def _parse_date(date_str: str) -> str:
    """Retorna HH:MM (UTC) a partir de date_str do endpoint."""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return ""


def _norm(s: str) -> str:
    """Normaliza string para comparação (mantém acentos)."""
    if s is None:
        return ""
    return str(s).strip().upper()


def _matches(team_name: str, allowed_list: list[str]) -> bool:
    """Verifica se o time está na lista permitida."""
    t = _norm(team_name)
    if not t:
        return False
    allowed = {_norm(x) for x in allowed_list}
    return t in allowed


def _competition_matches(league_name: str) -> bool:
    """Verifica se a competição está na lista permitida."""
    return _norm(league_name) in {_norm(x) for x in maiores_competicoes}


# ==================== DATAS ====================
def get_today_and_yesterday():
    """Retorna (hoje, ontem) em formato YYYYMMDD e YYYY-MM-DD."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    return (
        today.strftime("%Y%m%d"),
        yesterday.strftime("%Y%m%d"),
        today.strftime("%Y-%m-%d"),
        yesterday.strftime("%Y-%m-%d"),
    )


# ==================== GERENCIAMENTO DE ARQUIVOS ====================
def ensure_json_folders():
    """Garante que as pastas necessárias existem."""
    Path("json").mkdir(exist_ok=True)
    Path("json/old").mkdir(exist_ok=True)


def file_exists(filename: str) -> bool:
    """Verifica se o arquivo existe."""
    return os.path.exists(filename)


def save_json(filename: str, data: dict):
    """Salva dados em JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SALVO] {filename}")


def load_json(filename: str) -> dict:
    """Carrega dados de JSON."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def move_old_files(today_date: str, yesterday_date: str):
    """Move arquivos antigos para json/old, exceto os _final.json."""
    ensure_json_folders()

    keep_files = {
        f"response_{today_date}.json",
        f"response_{today_date}_filtrado.json",
        f"response_{yesterday_date}_final.json",
        f"response_{yesterday_date}_final_filtrado.json",
    }

    response_files = [
        f for f in os.listdir(".")
        if f.startswith("response_") and f.endswith(".json")
    ]

    for file in response_files:
        if file not in keep_files:
            src = file
            dst = f"json/old/{file}"
            try:
                os.rename(src, dst)
                print(f"  [MOVIDO] {src} -> json/old/")
            except Exception as e:
                print(f"  [AVISO] Não foi possível mover {src}: {e}")


# ==================== API ====================
def fetch_fixtures(date_formatted: str) -> dict:
    """Faz requisição para a data no formato YYYY-MM-DD."""
    url = f"https://v3.football.api-sports.io/fixtures?date={date_formatted}"
    headers = {"x-apisports-key": API_KEY}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERRO] Falha na requisição para {date_formatted}: {e}")
        sys.exit(1)


# ==================== NORMALIZAÇÃO ====================
def normalize_fixtures(api_payload: dict):
    """Transforma payload em linhas prontas para tabela."""
    fixtures = api_payload.get("response") or []
    rows = []

    for fx in fixtures:
        fixture = fx.get("fixture", {})
        league = fx.get("league", {})
        teams = fx.get("teams", {})
        score = fx.get("score", {})

        home = (teams.get("home") or {}).get("name", "")
        away = (teams.get("away") or {}).get("name", "")
        status = (fixture.get("status") or {})
        status_long = status.get("long") or ""
        status_short = status.get("short") or ""

        ft = score.get("fulltime") or {}
        ht = score.get("halftime") or {}
        pen = score.get("penalty") or {}

        ht_home, ht_away = ht.get("home"), ht.get("away")
        ft_home, ft_away = ft.get("home"), ft.get("away")
        pen_home, pen_away = pen.get("home"), pen.get("away")

        if ft_home is not None and ft_away is not None:
            result = f"{ft_home}-{ft_away}"
        elif pen_home is not None and pen_away is not None:
            result = f"({pen_home}-{pen_away})"
        else:
            result = "-"

        comp = league.get("name") or ""
        round_ = league.get("round") or ""
        league_label = f"{comp} - {round_}".strip(" -")

        date_str = fixture.get("date")
        time_str = _parse_date(date_str)

        rows.append(
            {
                "id": fixture.get("id"),
                "data": (date_str or "")[:10] if date_str else "",
                "hora": time_str,
                "competicao": league_label,
                "status": status_short or status_long,
                "mandante": home,
                "visitante": away,
                "placar": result,
            }
        )

    return rows


def render_table(rows, max_rows=30):
    """Renderiza tabela formatada dos fixtures."""
    headers = ["Data", "Hora", "Competição", "Status", "Mandante", "Visitante", "Placar"]

    def col(i, key):
        vals = [str(r.get(key, "")) for r in rows[:max_rows]]
        return max([len(headers[i])] + [len(v) for v in vals])

    widths = [
        col(0, "data"),
        col(1, "hora"),
        col(2, "competicao"),
        col(3, "status"),
        col(4, "mandante"),
        col(5, "visitante"),
        col(6, "placar"),
    ]

    sep = " | "
    line = "-+-".join("-" * w for w in widths)

    out = []
    header_line = sep.join(headers[i].ljust(widths[i]) for i in range(len(headers)))
    out.append(header_line)
    out.append(line)

    for r in rows[:max_rows]:
        out.append(
            sep.join(
                [
                    str(r.get("data", "")).ljust(widths[0]),
                    str(r.get("hora", "")).ljust(widths[1]),
                    str(r.get("competicao", "")).ljust(widths[2]),
                    str(r.get("status", "")).ljust(widths[3]),
                    str(r.get("mandante", "")).ljust(widths[4]),
                    str(r.get("visitante", "")).ljust(widths[5]),
                    str(r.get("placar", "")).ljust(widths[6]),
                ]
            )
        )

    if len(rows) > max_rows:
        out.append(f"... (mostrando {max_rows} de {len(rows)} linhas)")

    return "\n".join(out)


# ==================== FILTRAGEM ====================
def filter_payload(payload: dict) -> dict:
    """Filtra o payload mantendo apenas times/competições de interesse."""
    response = payload.get("response") or []
    allowed_fixtures = []

    for item in response:
        fixture = item.get("fixture") or {}
        league = item.get("league") or {}
        teams = item.get("teams") or {}

        home = (teams.get("home") or {}).get("name")
        away = (teams.get("away") or {}).get("name")
        league_name = league.get("name")

        keep = (
            _matches(home, maiores_clubes_mundo)
            or _matches(away, maiores_clubes_mundo)
            or _matches(home, maiores_clubes_brasil)
            or _matches(away, maiores_clubes_brasil)
            or _matches(home, maiores_selecoes)
            or _matches(away, maiores_selecoes)
            or _matches(league_name, maiores_selecoes)
            or _competition_matches(league_name)
        )

        if keep:
            allowed_fixtures.append(item)

    out = dict(payload)
    out["response"] = allowed_fixtures
    out["filtered_results"] = len(allowed_fixtures)
    out["original_results"] = len(response)
    return out


# ==================== MAIN ====================
def main():
    print("\n" + "="*70)
    print("SCRIPT ÚNICO - FIXTURES, FILTRAGEM E GERENCIAMENTO")
    print("="*70 + "\n")

    today_date, yesterday_date, today_str, yesterday_str = get_today_and_yesterday()
    print(f"[INFO] Data hoje: {today_str} ({today_date})")
    print(f"[INFO] Data ontem: {yesterday_str} ({yesterday_date})\n")

    ensure_json_folders()

    # Nomes dos arquivos
    today_file = f"response_{today_date}.json"
    yesterday_final_file = f"response_{yesterday_date}_final.json"

    # ==================== STEP 1: VERIFICAR ARQUIVOS ====================
    print("[STEP 1] Verificando arquivos...")
    today_exists = file_exists(today_file)
    yesterday_exists = file_exists(yesterday_final_file)

    print(f"  {today_file}: {'✓ Existe' if today_exists else '✗ Não existe'}")
    print(f"  {yesterday_final_file}: {'✓ Existe' if yesterday_exists else '✗ Não existe'}\n")

    # ==================== STEP 2: REQUISIÇÕES DE API ====================
    print("[STEP 2] Requisições de API...")
    if not today_exists:
        print(f"  [FETCH] Obtendo fixtures para hoje ({today_str})...")
        payload_today = fetch_fixtures(today_str)
        save_json(today_file, payload_today)
    else:
        print(f"  [LOAD] Carregando {today_file}...")
        payload_today = load_json(today_file)

    if not yesterday_exists:
        print(f"  [FETCH] Obtendo fixtures para ontem ({yesterday_str})...")
        payload_yesterday = fetch_fixtures(yesterday_str)
        save_json(yesterday_final_file, payload_yesterday)
    else:
        print(f"  [LOAD] Carregando {yesterday_final_file}...")
        payload_yesterday = load_json(yesterday_final_file)

    print()

    # ==================== STEP 3: FILTRAGEM ====================
    print("[STEP 3] Aplicando filtros...")
    today_filtered = filter_payload(payload_today)
    yesterday_filtered = filter_payload(payload_yesterday)

    today_filtered_file = f"json/response_{today_date}_filtrado.json"
    yesterday_filtered_file = f"json/response_{yesterday_date}_final_filtrado.json"

    save_json(today_filtered_file, today_filtered)
    save_json(yesterday_filtered_file, yesterday_filtered)
    print()

    # ==================== STEP 4: LIMPEZA ====================
    print("[STEP 4] Movendo arquivos antigos...")
    move_old_files(today_date, yesterday_date)
    print()

    # ==================== STEP 5: EXIBIR RESULTADOS ====================
    print("="*70)
    print("RESUMO - HOJE")
    print("="*70)
    print(f"Original: {today_filtered.get('original_results')} | Filtrado: {today_filtered.get('filtered_results')}\n")
    today_rows = normalize_fixtures(today_filtered)
    print(render_table(today_rows, max_rows=20))

    print("\n" + "="*70)
    print("RESUMO - ONTEM (FINAL)")
    print("="*70)
    print(f"Original: {yesterday_filtered.get('original_results')} | Filtrado: {yesterday_filtered.get('filtered_results')}\n")
    yesterday_rows = normalize_fixtures(yesterday_filtered)
    print(render_table(yesterday_rows, max_rows=20))

    print("\n" + "="*70)
    print("✓ Script concluído com sucesso!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_today_and_yesterday():
    """Retorna (hoje, ontem) em formato YYYYMMDD."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    return today.strftime("%Y%m%d"), yesterday.strftime("%Y%m%d")


def ensure_json_folders():
    """Garante que as pastas necessárias existem."""
    Path("json").mkdir(exist_ok=True)
    Path("json/old").mkdir(exist_ok=True)


def file_exists(filename: str) -> bool:
    """Verifica se o arquivo existe."""
    return os.path.exists(filename)


def move_old_files(today_date: str, yesterday_date: str):
    """Move arquivos antigos para json/old, exceto os _final.json."""
    # Arquivos que NÃO devem ser movidos
    keep_files = {
        f"response_{today_date}.json",
        f"response_{today_date}_filtrado.json",
        f"response_{yesterday_date}_final.json",
        f"response_{yesterday_date}_final_filtrado.json",
    }

    # Lista arquivos response_*.json
    response_files = [
        f for f in os.listdir(".")
        if f.startswith("response_") and f.endswith(".json")
    ]

    for file in response_files:
        if file not in keep_files:
            src = file
            dst = f"json/old/{file}"
            try:
                os.rename(src, dst)
                print(f"[MOVIDO] {src} -> json/old/")
            except Exception as e:
                print(f"[AVISO] Não foi possível mover {src}: {e}")


def run_command(cmd: list, description: str):
    """Executa um comando e valida."""
    print(f"\n[EXEC] {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"[✓] {description} concluído")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[✗] Erro ao executar {description}: {e}")
        sys.exit(1)


def main():
    print("\n" + "="*60)
    print("ORQUESTRADOR - FIXTURES E FILTRAGEM POR DATA")
    print("="*60 + "\n")

    today_date, yesterday_date = get_today_and_yesterday()
    print(f"[INFO] Data hoje: {today_date}")
    print(f"[INFO] Data ontem: {yesterday_date}\n")

    ensure_json_folders()

    # Arquivos esperados
    today_file = f"response_{today_date}.json"
    yesterday_final_file = f"response_{yesterday_date}_final.json"

    today_exists = file_exists(today_file)
    yesterday_exists = file_exists(yesterday_final_file)

    print(f"[CHECK] {today_file}: {'✓ Existe' if today_exists else '✗ Não existe'}")
    print(f"[CHECK] {yesterday_final_file}: {'✓ Existe' if yesterday_exists else '✗ Não existe'}\n")

    # Executar a.py se faltarem arquivos
    if not today_exists or not yesterday_exists:
        print("[INFO] Faltam arquivos, vou executar requisições...\n")
        run_command(["python", "a.py"], "Requisição de fixtures (a.py)")
    else:
        print("[INFO] Arquivos de hoje e ontem já existem, pulando requisições.\n")

    # Executar outro.py (filtro)
    run_command(["python", "outro.py"], "Filtragem de fixtures (outro.py)")

    # Mover arquivos antigos
    print(f"\n[CLEANUP] Movendo arquivos antigos para json/old/...")
    move_old_files(today_date, yesterday_date)

    print("\n" + "="*60)
    print("✓ Orquestração concluída com sucesso!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
import json
import os
import sys
import glob

from dict import (
    maiores_clubes_mundo,
    maiores_clubes_brasil,
    maiores_selecoes,
    maiores_competicoes,
)


def _norm(s: str) -> str:
    if s is None:
        return ""
    # mantém acentos para bater com strings do dict, mas normaliza espaços/uppercase
    return str(s).strip().upper()


def _matches(team_name: str, allowed_list: list[str]) -> bool:
    t = _norm(team_name)
    if not t:
        return False
    allowed = {_norm(x) for x in allowed_list}
    return t in allowed


def _competition_matches(league_name: str) -> bool:
    """Verifica se a competição está na lista permitida."""
    return _norm(league_name) in {_norm(x) for x in maiores_competicoes}


def filter_payload(payload: dict) -> dict:
    response = payload.get("response") or []

    allowed_fixtures = []
    for item in response:
        fixture = item.get("fixture") or {}
        league = item.get("league") or {}
        teams = item.get("teams") or {}

        home = ((teams.get("home") or {}).get("name"))
        away = ((teams.get("away") or {}).get("name"))
        league_name = league.get("name")

        # regra: mantem se qualquer lado for time grande do mundo/BR, ou seleção, ou competição grande
        keep = (
            _matches(home, maiores_clubes_mundo)
            or _matches(away, maiores_clubes_mundo)
            or _matches(home, maiores_clubes_brasil)
            or _matches(away, maiores_clubes_brasil)
            or _matches(home, maiores_selecoes)
            or _matches(away, maiores_selecoes)
            or _matches(league_name, maiores_selecoes)
            or _competition_matches(league_name)
        )

        if keep:
            allowed_fixtures.append(item)

    # mantém o mesmo formato do payload, mas com response filtrado
    out = dict(payload)
    out["response"] = allowed_fixtures
    out["filtered_results"] = len(allowed_fixtures)
    out["original_results"] = len(response)
    return out


def main():
    import glob
    
    # Find all response_*.json files (but not filtrado or final_filtrado)
    files = glob.glob("response_*.json")
    
    # Filter out already-processed files
    files_to_process = [
        f for f in files 
        if not f.endswith("_filtrado.json") and not f.endswith("_final_filtrado.json")
    ]

    if not files_to_process:
        print("[INFO] Nenhum arquivo para processar.")
        return

    print(f"[INFO] Processando {len(files_to_process)} arquivo(s)...\n")

    for in_path in files_to_process:
        print(f"[PROCESSING] {in_path}...")
        
        if not os.path.exists(in_path):
            print(f"  [AVISO] Arquivo não encontrado: {in_path}")
            continue

        with open(in_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        filtered = filter_payload(payload)

        # Gerar nome do arquivo filtrado
        if in_path.endswith("_final.json"):
            out_path = in_path.replace("_final.json", "_final_filtrado.json")
        else:
            out_path = in_path.replace(".json", "_filtrado.json")

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)

        print(f"  [SALVO] {out_path}")
        print(f"  Original: {filtered.get('original_results')} | Filtrado: {filtered.get('filtered_results')}\n")


if __name__ == "__main__":
    main()

import json
from datetime import datetime, timedelta

import requests
from ApiKeys import API_KEY


def _parse_date(date_str: str) -> str:
    """Retorna HH:MM (UTC) a partir de date_str do endpoint."""
    if not date_str:
        return ""
    try:
        # Ex: '2026-07-07T15:30:00+00:00'
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return ""


def _safe_score(score: dict, key: str):
    if not score:
        return None
    return score.get(key, {}).get("home"), score.get(key, {}).get("away")


def normalize_fixtures(api_payload: dict):
    """Transforma payload do endpoint em uma lista de linhas prontas para tabela."""
    fixtures = api_payload.get("response") or []

    rows = []
    for fx in fixtures:
        fixture = fx.get("fixture", {})
        league = fx.get("league", {})
        teams = fx.get("teams", {})
        score = fx.get("score", {})

        home = (teams.get("home") or {}).get("name", "")
        away = (teams.get("away") or {}).get("name", "")

        status = (fixture.get("status") or {})
        status_long = status.get("long") or ""
        status_short = status.get("short") or ""

        # placar: tenta FT (fulltime). Se vier None, deixa vazio.
        ft = score.get("fulltime") or {}
        ht = score.get("halftime") or {}
        pen = score.get("penalty") or {}

        ht_home, ht_away = ht.get("home"), ht.get("away")
        ft_home, ft_away = ft.get("home"), ft.get("away")
        pen_home, pen_away = pen.get("home"), pen.get("away")

        if ft_home is not None and ft_away is not None:
            result = f"{ft_home}-{ft_away}"
        elif pen_home is not None and pen_away is not None:
            result = f"({pen_home}-{pen_away})"
        else:
            result = "-"

        comp = league.get("name") or ""
        round_ = league.get("round") or ""
        league_label = f"{comp} - {round_}".strip(" -")

        date_str = fixture.get("date")
        time_str = _parse_date(date_str)

        rows.append(
            {
                "id": fixture.get("id"),
                "data": (date_str or "")[:10] if date_str else "",
                "hora": time_str,
                "competicao": league_label,
                "status": status_short or status_long,
                "mandante": home,
                "visitante": away,
                "placar": result,
            }
        )

    return rows


def render_table(rows, max_rows=30):
    # cabeçalho
    headers = ["Data", "Hora", "Competição", "Status", "Mandante", "Visitante", "Placar"]

    # largura dinâmica simples
    def col(i, key):
        vals = [str(r.get(key, "")) for r in rows[:max_rows]]
        return max([len(headers[i])] + [len(v) for v in vals])

    widths = [
        col(0, "data"),
        col(1, "hora"),
        col(2, "competicao"),
        col(3, "status"),
        col(4, "mandante"),
        col(5, "visitante"),
        col(6, "placar"),
    ]

    sep = " | "
    line = "-+-".join("-" * w for w in widths)

    out = []
    header_line = sep.join(headers[i].ljust(widths[i]) for i in range(len(headers)))
    out.append(header_line)
    out.append(line)

    for r in rows[:max_rows]:
        out.append(
            sep.join(
                [
                    str(r.get("data", "")).ljust(widths[0]),
                    str(r.get("hora", "")).ljust(widths[1]),
                    str(r.get("competicao", "")).ljust(widths[2]),
                    str(r.get("status", "")).ljust(widths[3]),
                    str(r.get("mandante", "")).ljust(widths[4]),
                    str(r.get("visitante", "")).ljust(widths[5]),
                    str(r.get("placar", "")).ljust(widths[6]),
                ]
            )
        )

    if len(rows) > max_rows:
        out.append(f"... (mostrando {max_rows} de {len(rows)} linhas)")

    return "\n".join(out)


def main():
    # Today and yesterday dates
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    
    today_date_fmt = today.strftime("%Y%m%d")
    yesterday_date_fmt = yesterday.strftime("%Y%m%d")

    headers = {"x-apisports-key": API_KEY}

    # Fetch today's fixtures
    print(f"[FETCH] Obtendo fixtures para hoje ({today_str})...")
    url_today = f"https://v3.football.api-sports.io/fixtures?date={today_str}"
    resp = requests.get(url_today, headers=headers, timeout=30)
    resp.raise_for_status()
    payload_today = resp.json()

    today_file = f"response_{today_date_fmt}.json"
    with open(today_file, "w", encoding="utf-8") as f:
        json.dump(payload_today, f, ensure_ascii=False, indent=2)
    print(f"[SALVO] {today_file}")

    # Fetch yesterday's fixtures
    print(f"[FETCH] Obtendo fixtures para ontem ({yesterday_str})...")
    url_yesterday = f"https://v3.football.api-sports.io/fixtures?date={yesterday_str}"
    resp = requests.get(url_yesterday, headers=headers, timeout=30)
    resp.raise_for_status()
    payload_yesterday = resp.json()

    yesterday_file = f"response_{yesterday_date_fmt}_final.json"
    with open(yesterday_file, "w", encoding="utf-8") as f:
        json.dump(payload_yesterday, f, ensure_ascii=False, indent=2)
    print(f"[SALVO] {yesterday_file}")

    # Display today's results
    rows_today = normalize_fixtures(payload_today)
    print(f"\nTotal fixtures hoje: {len(rows_today)}")
    print(render_table(rows_today, max_rows=30))

    # Display yesterday's results
    rows_yesterday = normalize_fixtures(payload_yesterday)
    print(f"\nTotal fixtures ontem: {len(rows_yesterday)}")
    print(render_table(rows_yesterday, max_rows=30))


if __name__ == "__main__":
    main()

