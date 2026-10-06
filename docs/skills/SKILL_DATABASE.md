# Skill: Banco de Dados — Firebase (Cloud) + Espelho JSON Offline

Esta skill descreve a arquitetura do **banco de dados oficial do projeto**
(Firebase / Cloud Firestore) e o **espelho offline em JSON** mantido dentro da
pasta-mãe, além do **log desacoplado** do banco de dados.

## Visão Geral

- O **Firebase (Cloud Firestore)** é o **banco de dados oficial**.
- Os dados têm **cópias offline em JSON** dentro da **pasta-mãe** (um JSON por
  OS + um consolidado). Esses JSONs funcionam como **backups** consultáveis.
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
| `FirestoreService` | `core/firebase/FirestoreService.py` | CRUD REST no Firestore (`get_document`, `save_document`, `save_documents`, `list_documents`, `delete_document`) |
| `CloudDatabaseSync` | `core/firebase/CloudDatabaseSync.py` | Sincroniza um diretório de JSONs ↔ uma coleção Firestore (`push` / `pull`) |
| `FirebaseWorker` | `core/firebase/FirebaseWorker.py` | Execução assíncrona (QThread) |
| `ProjectDatabaseStore` | `plugins/project_database_manager/ProjectDatabaseStore.py` | Gravação atômica dos JSONs em `.BancoDados` |
| `ProjectDatabaseService` | `plugins/project_database_manager/ProjectDatabaseService.py` | Monta os registros + `ProjectDatabaseWorker` |
| `ProjectDatabasePlugin` | `plugins/project_database_manager/ProjectDatabasePlugin.py` | UI: ATUALIZAR DADOS (push) + SINCRONIZAR NUVEM (pull) |
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

### Push (local → Firebase)

```
Usuário clica ATUALIZAR DADOS
  → ProjectDatabaseWorker varre a pasta-mãe (background)
  → ProjectDatabasePlugin._save_database grava .BancoDados/*.json (atômico)
  → ProjectDatabasePlugin._push_to_cloud_async()
      → FirebaseWorker(CloudDatabaseSync.push, <local_dir>, "banco_dados")
          → para cada *.json: FirestoreService.save_document("banco_dados", <stem>, dados)
          → CloudDatabaseSync grava .cloud/meta.json
```

- O push só ocorre se houver **sessão Firebase ativa**
  (`FirebaseAuthService.is_authenticated()`); caso contrário, é ignorado com log
  `PDB_PUSH_OFFLINE`.

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

## Regras

1. **O Firestore é a fonte oficial**; o JSON em `.BancoDados` é o espelho/backup offline.
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
