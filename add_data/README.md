# add_data/ — Scripts de carga de dados (DEV)

Pasta de scripts **somente para desenvolvimento**. Não faz parte do runtime do
Aetheris ToolBox.

## `seed_sub_os.py`

Semeia, **direto no Firebase (Cloud Firestore, coleção `banco_dados`)**, a
categorização **OS → SubOS → Cliente / Nome comercial / CNPJ**. O Firestore é a
fonte oficial: este script **nunca** grava JSON — os JSONs em `.BancoDados` são
consequência/backup gerados pelo sistema (pull / ATUALIZAR DADOS).

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
> os documentos `<os>` e o consolidado `banco_dados` na coleção `banco_dados`.
> Para materializar os JSONs locais, use **SINCRONIZAR NUVEM** no **Banco de
> Dados** (pull) — os JSONs são consequência do sistema.

### Resolução da pasta-mãe (nesta ordem)

1. `--mother "<pasta>"`
2. Variável de ambiente `AETHERIS_MOTHER_FOLDER`
3. Preferência `ProjectStructure.mother_folder`
   (`config/<APP_SLUG>_preferences.json`)

### Comportamento

- Agrupa por **número de OS** (normalizado, `039` → `39`): todas as pastas de
  uma OS ficam em um **único registro**.
- **Uma pasta = uma SubOS**: a SubOS é derivada da estrutura de pastas (a letra
  é lida do nome da pasta — ex.: `OS_181_RENNER_A_...` → `A`); não existem
  SubOS sem pasta.
- Mescla a categorização por **letra da SubOS**: preenche `client`,
  `commercial_name` e `cnpj` **sem apagar** `path`/`folders`/`years`.
- As pastas/anos ficam **dentro da SubOS** (não no nível da OS).
- Lê o estado atual **do Firestore** (documentos por OS) para preservar o que
  não é semeado; o refresh do plugin **Banco de Dados** preserva a categorização
  (ver `ProjectDatabaseService.build_os_record`).

> O formulário enviado por linha é:
> `{"sub_os": "A", "client": "...", "commercial_name": "...", "cnpj": "..."}`.
