# add_data/ — Scripts de carga de dados (DEV)

Pasta de scripts **somente para desenvolvimento**. Não faz parte do runtime do
Aetheris ToolBox.

## `seed_sub_os.py`

Semeia o banco de dados (`.BancoDados`) com a categorização
**OS → SubOS → Cliente / Nome comercial / CNPJ**. As SubOS são gravadas na
chave `sub_os` de cada registro de OS (JSON individual e consolidado).

### Uso

```powershell
# Usa a pasta-mãe da preferência do Gerenciador de Estrutura
python add_data/seed_sub_os.py

# Pasta-mãe explícita
python add_data/seed_sub_os.py --mother "C:/caminho/pasta-mae"

# Só mostra o resumo (não grava nada)
python add_data/seed_sub_os.py --dry-run

# Grava e envia para o Firebase (Firestore) — coleção banco_dados
python add_data/seed_sub_os.py --push
```

> ⚠️ O seed **grava apenas local** (`.BancoDados`). Use `--push` (ou, no app,
> abra o **Banco de Dados** e clique **ATUALIZAR DADOS**) para espelhar no
> Firestore.

### Resolução da pasta-mãe (nesta ordem)

1. `--mother "<pasta>"`
2. Variável de ambiente `AETHERIS_MOTHER_FOLDER`
3. Preferência `ProjectStructure.mother_folder`
   (`config/<APP_SLUG>_preferences.json`)

### Comportamento

- Agrupa por **número de OS** (normalizado, `039` → `39`): todas as pastas de
  uma OS ficam em um **único registro**.
- Mescla a categorização por **letra da SubOS**: preenche `client`,
  `commercial_name` e `cnpj` **sem apagar** `path`/`folders`/`years`.
- Varre a pasta-mãe e **anexa a pasta de cada SubOS** (a letra é lida do nome da
  pasta — ex.: `OS_181_RENNER_A_...` → `A`).
- O refresh do plugin **Banco de Dados** preserva a categorização (ver
  `ProjectDatabaseService.build_os_record`).

> O formulário gravado por linha é:
> `{"sub_os": "A", "client": "...", "commercial_name": "...", "cnpj": "..."}`.
