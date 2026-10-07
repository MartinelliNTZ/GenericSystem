# add_data/ — Scripts de carga de dados (DEV)

Pasta de scripts **somente para desenvolvimento**. Não faz parte do runtime do
Aetheris ToolBox.

## `seed_sub_os.py`

Cria, **direto no Firebase (Cloud Firestore, coleção `banco_dados`)**, a BASE de
OS já existente: um registro por OS com as suas **SubOS** (cliente, nome
comercial e CNPJ) e a **pasta associada** (caminho **RELATIVO** à pasta-mãe —
portável entre computadores). Toda OS ganha ao menos a **SubOS A**.

O Firestore é a **fonte oficial**. Os backups JSON em `.BancoDados` são gerados
pela **classe de banco** `CloudProjectDatabase` (o script nunca grava JSON). A
criação de **novas** OS é feita pelo sistema, na ferramenta **Acompanhamento de
OS** (botão CRIAR OS).

### Uso

```powershell
# Usa a pasta-mãe da preferência do Gerenciador de Estrutura
python add_data/seed_sub_os.py

# Pasta-mãe explícita
python add_data/seed_sub_os.py --mother "C:/caminho/pasta-mae"

# Só mostra o resumo (não envia nada ao Firebase)
python add_data/seed_sub_os.py --dry-run
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

- Agrupa por **número de OS** (normalizado, `039` → `39`): todas as pastas de
  uma OS ficam em um **único registro**.
- **Uma pasta = uma SubOS**: a SubOS é derivada da estrutura de pastas (a letra
  é lida do nome da pasta — ex.: `OS_181_RENNER_A_...` → `A`).
- O `path` de cada SubOS é gravado **RELATIVO à pasta-mãe** (ex.: `OS_039_Bunge`).
- Mescla a categorização por **letra da SubOS**: preenche `client`,
  `commercial_name` e `cnpj` **sem apagar** `path`/`folders`/`years`.
- **Garante a SubOS A** em toda OS.
- As pastas/anos ficam **dentro da SubOS** (não no nível da OS).

> Lê o estado atual **do Firestore** (via `CloudProjectDatabase.load_orders`)
> para preservar o que não é semeado.

> O formulário enviado por linha é:
> `{"sub_os": "A", "path": "...", "folders": [...], "years": [...],
> "client": "...", "commercial_name": "...", "cnpj": "..."}`.
