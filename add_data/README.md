# add_data/ — Scripts de carga de dados (DEV)

Pasta de scripts **somente para desenvolvimento**. Não faz parte do runtime do
Aetheris ToolBox.

## `seed_os.py`

Cria/atualiza, **direto no Firebase (Cloud Firestore, coleção `banco_dados`)**, a
BASE de OS já existente: um registro por OS (a chave é **TEXTO** e pode conter
**LETRA**, ex.: `169A`) com o cliente, o nome comercial, o CNPJ e a **pasta
associada** (caminho **RELATIVO** à pasta-mãe — portável entre computadores).

O Firestore é a **fonte oficial**. Os backups JSON em `.BancoDados` são gerados
pela **classe de banco** `CloudProjectDatabase` (o script nunca grava JSON). A
criação de **novas** OS é feita pelo sistema, na ferramenta **Acompanhamento de
OS** (botão CRIAR OS).

### Uso

```powershell
# Usa a pasta-mãe da preferência do Gerenciador de Estrutura
python add_data/seed_os.py

# Pasta-mãe explícita
python add_data/seed_os.py --mother "C:/caminho/pasta-mae"

# Só mostra o resumo (não envia nada ao Firebase)
python add_data/seed_os.py --dry-run
```

> ⚠️ O script exige credenciais Firebase (conta de serviço ou login). Ele grava
> os documentos `<os>` e o consolidado `banco_dados` na coleção `banco_dados`
> via `CloudProjectDatabase`.

### Resolução da pasta-mãe (nesta ordem)

1. `--mother "<pasta>"`
2. Variável de ambiente `AETHERIS_MOTHER_FOLDER`
3. Preferência `ProjectStructure.mother_folder`
   (`config/<APP_SLUG>_preferences.json`)

### Comportamento

- A chave da OS é a **mesma chave do nome da pasta** (`OS_039_Bunge` → `039`,
  `OS_169B_DARRO` → `169B`): zeros à esquerda e letra são preservados.
- **Uma pasta = UMA OS**: cada registro é uma OS independente (o sistema de SubOS
  foi eliminado).
- O `path` é gravado **RELATIVO à pasta-mãe** (ex.: `OS_039_Bunge`).
- Mescla a categorização: preenche `client`, `commercial_name` e `cnpj` **sem
  apagar** `path`/`folders`/`years`.
- As pastas/anos são varridos da pasta da OS em disco.

> Lê o estado atual **do Firestore** (via `CloudProjectDatabase.load_orders`)
> para preservar o que não é semeado.

> O formulário enviado por OS é:
> `{"os": "169B", "name": "", "path": "...", "folders": [...], "years": [...],
> "client": "...", "commercial_name": "...", "cnpj": "..."}`.

## `migrate_os_keys.py`

Migração ÚNICA do esquema ANTIGO (`os` sem zeros + lista `sub_os`) para o esquema
NOVO (**sem SubOS**): a chave de cada registro passa a ser a chave da pasta
(`39` → `039`; `169` + SubOS `B` → `169B`) e cliente/nome comercial/CNPJ/caminho/
pastas/anos/bases (`limites`/`zonas_manejo`) passam para o PRÓPRIO registro.

```powershell
# Só mostra o plano (não grava nada)
python add_data/migrate_os_keys.py --dry-run

# Migra (Firestore + backups JSON) — faz backup do .BancoDados antes
python add_data/migrate_os_keys.py

# Renumera/renomeia a chave de uma OS (pasta renomeada) — repetível
python add_data/migrate_os_keys.py --rename 377=393
```

> Antes de gravar, o script copia `<pasta-mãe>/.BancoDados` para
> `<pasta-mãe>/.BancoDados_backup_<AAAAMMDDHHMMSS>` e, ao final, remove do
> Firestore os documentos das chaves antigas.

> `--rename ANTIGA=NOVA` força a chave de uma OS que foi **renumerada** (a pasta
> nova é localizada no disco pela chave NOVA — ex.: `377` → `OS_393_ELDORADO`);
> o documento antigo é removido e o novo passa a apontar para a pasta atual.
