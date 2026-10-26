# Skill: Banco de Dados — Firebase (Cloud) + Espelho JSON Offline

Esta skill descreve a arquitetura do **banco de dados oficial do projeto**
(Firebase / Cloud Firestore) e o **espelho offline em JSON** mantido dentro da
pasta-mãe, além do **log desacoplado** do banco de dados.

## Visão Geral

- O **Firebase (Cloud Firestore)** é o **banco de dados oficial**.
- Os dados têm **cópias offline (backup) em JSON** dentro da **pasta-mãe** (um
  JSON por OS + um consolidado). Esses JSONs são **escritos** pela classe de
  banco (`CloudProjectDatabase`) e **NUNCA lidos pela aplicação**.
- A sincronização é **bidirecional**:
  - `push` — "mandar atualizar a base" grava/atualiza o Firestore a partir dos
    JSONs locais.
  - `pull` — quando o Firestore recebe atualização (interna/online), os JSONs e
    a UI são atualizados a partir da nuvem.
- Todo registro do banco de dados é escrito no **canal de log `database`**
  (arquivo separado), desacoplado do log geral.

## Componentes

| Componente | Arquivo | Papel |
|---|---|---|
| `FirebaseConfig` | `core/firebase/FirebaseConfig.py` | Credenciais (Preferences `Firebase` / env vars) |
| `FirebaseAuthService` | `core/firebase/FirebaseAuthService.py` | Login/logout/refresh (Identity Toolkit) |
| `FirebaseServiceAccountAuth` | `core/firebase/FirebaseServiceAccountAuth.py` | Token OAuth2 da conta de serviço (Admin SDK) — cache + renovação |
| `FirebaseTokenProvider` | `core/firebase/FirebaseTokenProvider.py` | Resolve o token Bearer (conta de serviço ou usuário) |
| `FirestoreService` | `core/firebase/FirestoreService.py` | CRUD REST no Firestore (`get_document`, `save_document`, `save_documents`, `list_documents` — **paginado** via `nextPageToken`, `query_documents` — `runQuery` com ordenação/limite/igualdade, `delete_document`) |
| `CloudProjectDatabase` | `core/firebase/CloudProjectDatabase.py` | **CLASSE DE BANCO (Contrato 28)**: única porta de entrada dos registros de OS — lê/grava o Firestore (`load_orders`/`get_order`/`save_order`/`rebuild_consolidated`) e GERA os backups JSON |
| `CloudDatabaseSync` | `core/firebase/CloudDatabaseSync.py` | Materializa os documentos da coleção como JSONs locais (`pull`) |
| `FirebaseWorker` | `core/firebase/FirebaseWorker.py` | Execução assíncrona (QThread) |
| `ProjectDatabaseStore` | `core/database/ProjectDatabaseStore.py` | Gravação atômica dos backups JSON em `.BancoDados` (usada SÓ pela `CloudProjectDatabase`) |
| `CloudStructureDatabase` | `core/firebase/CloudStructureDatabase.py` | Classe de banco dos **snapshots da estrutura de pastas** (`estrutura_projetos`) e do **histórico de alterações** (`estrutura_changelog`): `load_snapshots`, `save_snapshots`, `save_changes`, `load_changes(limit, os_number="")` |
| `ProjectDatabaseService` | `plugins/project_database_manager/ProjectDatabaseService.py` | **NÃO cria OS**: re-escaneia as pastas das OS existentes e atualiza `folders`/`years` + `ProjectDatabaseWorker` |
| `ProjectDatabasePlugin` | `plugins/project_database_manager/ProjectDatabasePlugin.py` | UI: ATUALIZAR DADOS (consulta Firebase + re-escaneia, com modal de resumo) + SINCRONIZAR NUVEM (pull) |
| `ProjectDatabaseBackup` | `utils/ProjectDatabaseBackup.py` | ZIP diário do `.BancoDados` |

## Estrutura em disco (pasta-mãe)

```
<pasta-mãe>/.BancoDados/
├── banco_dados.json          ← consolidado (snapshot; também espelhado na nuvem)
├── <numero_os>.json           ← um JSON por OS (backup offline)
└── .cloud/
    └── meta.json              ← metadados da última sincronização
```

- Cada `*.json` do `.BancoDados` é o **espelho offline** de um documento da
  coleção Firestore `banco_dados` (o nome do arquivo é o `doc_id`).
- `.cloud/meta.json` guarda `collection`, `project_id`, `last_sync`,
  `last_push`, `last_pull` e as contagens. Fica numa subpasta para **nunca** ser
  confundido com um documento do banco.
- A gravação é **atômica** (`<arquivo>.tmp` + `os.replace`) em `ProjectDatabaseStore`
  e em `CloudDatabaseSync`.

## Registro de OS (schema)

Cada registro da lista `projects` do consolidado (e cada `*.json`) representa
**UMA OS**, que corresponde a **UMA pasta em disco**. A OS é **TEXTO** e pode
conter **LETRA** (ex.: `169A`): a letra é o que diferencia as OS de um mesmo
projeto. O registro guarda TUDO no próprio nível — cliente, nome comercial, CNPJ,
caminho e pastas/anos criados:

```json
{
  "os": "181C",
  "name": "",
  "path": "OS_181C_RENNER_Grupo Salazar - Faz Rio Alegre",
  "folders": ["01_Acessos_Plataforma_IA_AGLIBS", "05_ASA"],
  "years": ["2024"],
  "client": "Grupo Salazar - Faz Rio Alegre",
  "commercial_name": "GRUPO JCN",
  "cnpj": "",
  "updated_at": "2026-10-06T16:40:00"
}
```

- **`os`** é a chave da OS em TEXTO: os zeros à esquerda são PRESERVADOS
  (`OS_039_Bunge` → `039`) e a letra faz parte da chave (`OS_169B_DARRO` → `169B`).
  É ela que dá nome ao documento/JSON (`039.json`, `169B.json`).
- **O campo/list `sub_os` NÃO existe mais** — o sistema de SubOS foi eliminado:
  cada pasta é uma OS independente (uma pasta = uma OS).
- A chave sai do nome da pasta por `ProjectStructureUtil.extract_os` (primeiro
  campo após `OS_`) e é normalizada por `normalize_os` (maiúsculas, zeros e letra
  preservados).
- O `path` é gravado **RELATIVO à pasta-mãe** (ex.: `OS_039_Bunge`), resolvido em
  runtime por `ProjectStructureUtil.resolve_path` — portável entre computadores.
- Quando a ferramenta **Base de Limites** importa um vetor, ela grava no registro
  da OS a chave **`limites`** (via `CloudProjectDatabase.save_order`):

  ```json
  "limites": {
    "inserted_at": "2026-10-21T16:57:00",
    "file": "OS_039_Bunge/08_LIMITES/TALHOES/039_limites.shp",
    "source": "P230_001_01_OURO_VERDE_TALHOES.shp",
    "source_path": "Z:/PROJETOS_2022/OS_230/SHP/P230_001_01_OURO_VERDE_TALHOES.shp",
    "features": 12,
    "area_ha": 1234.5678
  }
  ```

  - `file` é **RELATIVO à pasta-mãe** (portável) e aponta para a cópia do limite
    dentro do projeto (`08_LIMITES/TALHOES`). Quando o arquivo está **fora** da
    pasta-mãe (ex.: projeto em outro drive), o caminho **ABSOLUTO** é gravado
    (`LimitesService._stored_file_path`) para o registro continuar abrindo no
    Explorer.
  - `source` é apenas o **NOME do arquivo** do vetor importado e `source_path` é o
    **caminho completo** do vetor (como foi selecionado na Base de Limites) —
    gravado para rastrear de onde o shape veio.
  - Ao **ATUALIZAR** pela Base de Limites, o mesmo objeto é reescrito na OS
    (`inserted_at`, `file`, `source`, `source_path`, `features` e `area_ha` do novo
    vetor) — as
    feições antigas das OS do vetor são substituídas no completão, no arquivo da
    OS e na cópia do projeto.
  - O **ATUALIZAR DADOS** do Banco de Dados preserva `limites` — ele só reescreve
    `folders`/`years` de cada OS.
- No modo **Zonas de Manejo** a mesma ferramenta grava a chave **`zonas_manejo`**
  no registro da OS (mesma estrutura, com `file` apontando para
  `13_ZONAS_DE_MANEJO/<OS>_zonas_manejo.shp`). As duas chaves convivem no registro
  e também são preservadas pelo ATUALIZAR DADOS.
- O seed **cria a base de OS** (OS + cliente + pasta) direto no Firestore via
  `CloudProjectDatabase` (`add_data/seed_os.py`). Novas OS são criadas pelo
  **Acompanhamento de OS** (botão CRIAR OS; só a chave é obrigatória — pode conter
  letra, ex.: `169A`).
- O **Banco de Dados** (ATUALIZAR DADOS) **não cria OS**: consulta o Firestore as
  OS existentes, re-escaneia as pastas e atualiza `folders`/`years`, exibindo um
  modal de resumo. Plugins têm **zero contato** com o JSON (Contrato 28).

> A ferramenta **Acompanhamento de OS** (`plugins/os_tracker/`) consome esse
> registro para exibir os dados da OS selecionada no painel **Dados Gerais** —
> OS, cliente, pastas/anos criados e as infos de cada base (`limites`/`zonas_manejo`:
> feições e área em hectares — `OsTrackerService.asset_info`) — e o painel
> **Atalhos**, que exibe **um botão por link registrado** (`LIMITES`/`ZONAS DE
> MANEJO`) abrindo a pasta do arquivo, cujo caminho é resolvido por
> `asset_file_path` (absoluto → relativo à pasta-mãe → relativo à pasta da OS).
> No painel **Últimas alterações no banco** fica o changelog da estrutura
> (`CloudStructureDatabase.load_changes`, ordenado por `detected_at`).

## Autenticação

A ordem de prioridade na resolução do token (``Bearer``) é definida pelo
`FirebaseTokenProvider`:

1. **Conta de serviço (Admin SDK)** — se `service_account_path` apontar para um
   JSON válido, o `FirebaseServiceAccountAuth` obtém um token OAuth2 e o usa em
   todas as chamadas REST. **Não exige Web API Key nem login de usuário.**
2. **Sessão de usuário** — sem conta de serviço, usa o `id_token` do login
   e-mail/senha (Preferences `Firebase`).

- `FirebaseTokenProvider.get_token()` → token atual (conta de serviço primeiro).
- `FirebaseTokenProvider.has_credentials()` → True se houver qualquer credencial.
- `FirebaseTokenProvider.refresh()` → renova (usado no tratamento de 401).
- O token da conta de serviço é **cacheado** e renovado ~60s antes de expirar,
  com escopos `datastore` + `devstorage.read_write`.
- Requer o pacote `google-auth` (ver `requirements.txt`).

Configuração mínima (seção `Firebase` em `config/<APP_SLUG>_preferences.json`):

```json
"Firebase": {
  "project_id": "verrafarmer",
  "service_account_path": "config/verrafarmer-firebase-adminsdk-XXXX.json"
}
```

> A `api_key` (**Web API Key**) só é necessária no modo usuário. Com conta de
> serviço, `project_id` + `service_account_path` bastam.

## Fluxo de Sincronização

### Atualização (ATUALIZAR DADOS → Firebase)

```
Usuário clica ATUALIZAR DADOS
  → FirebaseWorker(CloudProjectDatabase.load_orders) consulta as OS existentes no Firestore
  → ProjectDatabaseWorker re-escaneia as pastas das OS (background)
  → FirebaseWorker(CloudProjectDatabase.save_orders) grava no Firestore
      → e a própria classe gera os backups JSON (atômico): .BancoDados/*.json + consolidado
  → modal de resumo (MessageBox.show_info)
```

- Exige **credenciais Firebase** (`FirebaseTokenProvider.has_credentials()`).
- A leitura é **somente** do Firestore; com a base vazia/offline a ferramenta
  fica **vazia** — nunca há fallback para o JSON local.

### Pull (Firebase → local)

```
Usuário clica SINCRONIZAR NUVEM
  → FirebaseWorker(CloudDatabaseSync.pull, <local_dir>, "banco_dados")
      → FirestoreService.list_documents("banco_dados") → {doc_id: dados}
      → grava <local_dir>/<doc_id>.json (atômico)
      → CloudDatabaseSync grava .cloud/meta.json
  → ProjectDatabasePlugin._on_pull_result() → _load_from_disk() → _render()
```

- Exige sessão ativa e pasta-mãe configurada (validações em `_on_sync_clicked`).

## Log Desacoplado do Banco de Dados

O registro do banco é escrito num **canal separado** do log geral, para não
misturar com o log de execução do app (mesmo padrão do `LogUtils`):

- `LogUtils` aceita `channel=`; o canal padrão é `main`; o canal do banco é
  `LogUtils.DATABASE_CHANNEL` (`"database"`).
- Arquivos: canal `main` → `log/<ts>_<APP_SLUG>.json`; canal `database` →
  `log/database/<ts>_database.json` (JSONL, um JSON por linha).
- Acesso: `BaseUtil._get_logger(tool_key, class_name, channel=LogUtils.DATABASE_CHANNEL)`.
- `FirestoreService` e `CloudDatabaseSync` já emitem nesse canal.
- `LogCleanup.run(max_files=5, channel="database")` limpa o canal (no `BootStrap`).

```python
from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil

db_logger = BaseUtil._get_logger(
    ToolKey.PROJECT_DATABASE.value, "CloudDatabaseSync",
    channel=LogUtils.DATABASE_CHANNEL,
)
db_logger.info("Push concluído", code="CSYNC_PUSH_DONE", collection="banco_dados")
```

Cada evento do canal carrega também o campo `channel` no JSON.

## API — FirestoreService

```python
from core.firebase.FirestoreService import FirestoreService

data = FirestoreService.get_document("banco_dados", "068")            # dict | None
ok = FirestoreService.save_document("banco_dados", "068", {...})       # bool
n = FirestoreService.save_documents("banco_dados", {"068": {...}})     # int
docs = FirestoreService.list_documents("banco_dados")                  # {doc_id: dados}
ok = FirestoreService.delete_document("banco_dados", "068")            # bool
```

- Todos aceitam `tool_key=` (default `ToolKey.FIREBASE.value`) e logam no canal `database`.
- A conversão Python ↔ `fields` do Firestore é automática
  (`dict_to_firestore` / `firestore_to_dict`).

## API — CloudDatabaseSync

```python
from core.firebase.CloudDatabaseSync import CloudDatabaseSync
from core.enum.ToolKey import ToolKey

res = CloudDatabaseSync.push(local_dir, "banco_dados", tool_key=ToolKey.PROJECT_DATABASE.value)
# res -> {"pushed": int, "failed": int, "collection": "banco_dados"}

res = CloudDatabaseSync.pull(local_dir, "banco_dados", overwrite=True,
                             tool_key=ToolKey.PROJECT_DATABASE.value)
# res -> {"pulled": int, "skipped": int, "collection": "banco_dados"}

meta = CloudDatabaseSync.read_meta(local_dir)
```

## Snapshots da estrutura de pastas (changelog)

Além dos registros de OS, o Firestore guarda o retrato da **estrutura de
pastas** de cada OS e o histórico das alterações detectadas:

| Coleção | Documento | Conteúdo |
|---|---|---|
| `estrutura_projetos` | `<nome da pasta da OS>_<hash>` | `scope`, `os`, `folders_count`, `files_count`, `updated_at` e `blob` (gzip+base64 com `folders`, `files`, `sizes` e `modified`). O `blob` mantém o documento abaixo do limite de **1 MiB** do Firestore |
| `estrutura_changelog` | `<scope>_<AAAAMMDDHHMMSS><seq>` | `scope`, `os`, listas de criados/removidos/modificados, `renamed_files`/`moved_files` e `folder_renames`/`folder_moves`, `detected_at`, `detected_by`/`detected_by_email` (quem executou a conferência) e `machine`; na PRIMEIRA detecção da OS o documento é compacto (`first_run: true`, sem as listas) |

- Gravadas **exclusivamente** por `CloudStructureDatabase` (os plugins não
  tocam no Firestore).
- Os snapshots são lidos na abertura do Gerenciador de Estrutura para comparar
  com o disco e gerar o changelog (banco + `.DOCX` dentro de cada OS).
- `load_changes(limit)` devolve as últimas alterações **mais recentes primeiro**
  (`query_documents` com `orderBy: detected_at DESC`). Com `os_number`, filtra
  por igualdade em `os` (índice de campo único) e ordena em memória — é o que
  alimenta o painel **"Últimas alterações da OS"** do Acompanhamento de OS.
- Snapshots de pastas que não existem mais são removidos (`delete_document`).

## Regras

1. **O Firestore é a fonte oficial**; o JSON em `.BancoDados` é um **backup**
   ESCRITO pela classe de banco (`CloudProjectDatabase`) — **nunca lido pela
   aplicação** (Contrato 28).
2. Todo `*.json` do `.BancoDados` é tratado como documento da coleção `banco_dados`
   (nome do arquivo = `doc_id`).
3. Os metadados de sync **nunca** ficam na raiz do `.BancoDados` (usar
   `.cloud/meta.json`) para não virarem documento nem serem removidos pelo
   `prune_projects`.
4. Toda gravação local é **atômica** (tmp + replace).
5. Operações de rede do banco rodam em **background** (`FirebaseWorker`), nunca na
   GUI thread.
6. O log do banco usa **exclusivamente** o canal `LogUtils.DATABASE_CHANNEL`.
7. `core/` **não** importa `plugins/`; a costura entre o espelho local e o plugin
   fica dentro de `plugins/project_database_manager/`.
8. Nada de credenciais em texto puro: credenciais ficam em
   `config/.firebase_auth.enc` (`FirebaseCredentialManager`); config em
   Preferences/env vars (`FirebaseConfig`).

## Checklist

- [ ] Push/pull apenas com sessão ativa e pasta-mãe válida.
- [ ] Toda gravação (JSON local e documento Firestore) logada no canal `database`.
- [ ] Gravação local atômica (tmp + replace).
- [ ] Rede em `FirebaseWorker` (UI responsiva).
- [ ] `.cloud/meta.json` preservado (não tratado como documento).
- [ ] Docs e `docs/data/changelog.txt` atualizados (Contrato 12).

## Referências

- `docs/skills/SKILL_PROJECT.md` — sistema de projetos e a ferramenta de banco.
- `docs/skills/SKILL_COMUNICATION.md` — regras de `LogUtils` (incluindo canais).
- `docs/skills/SKILL_UTILS.md` — helpers compartilhados.
