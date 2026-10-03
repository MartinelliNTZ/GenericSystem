# Análise: ResourceGovernor não evitou OOM no IDW

## 🔍 Diagnóstico

### O que aconteceu

```
[IDW] Grid: 274253x172546 px
[IDW] Tile ajustado: 10000000 -> 4338973 (por RAM)
[IDW] Grade de tiles calculada: 8x7 = 56 tiles, 4,338,973 pts/tile
[ERRO] Unable to allocate 6.30 GiB for an array with shape (24649, 34282) and data type float64
```

### Causa Raiz

O **ResourceGovernor foi criado e injetado corretamente** (via `PipelineRunner` → `AsyncPipelineEngine` → `IdwInterpolatorTask`), mas seu critério de avaliação é baseado em **quantidade de pontos**, não em **dimensão de pixels do grid**.

| O quê | Valor calculado | Fórmula |
|---|---|---|
| `estimated_ram` (task) | **~138 MB/tile** | `4.338.973 pts × 32 bytes` |
| RAM real necessária | **~6,30 GiB/tile** | `34.282 px × 24.649 px × 8 bytes (float64)` |
| RAM real total (paralelo) | **~50 GiB** | `~6,3 GiB × 8 workers joblib` |

O governor aprovou `can_execute(estimated_ram=138MB)` porque o headroom era > 138 MB. Mas a alocação real era **46× maior** que o estimado.

### Cadeia do Bug

```
estimated_ram = n_pontos * BYTES_PER_POINT = 4.338.973 * 32 = 138 MB
    ↓ governor.can_execute(138 MB) → True ✅ (headroom suficiente)
    ↓
_ajustar_tile_size() → 4.338.973 pts/tile (reduziu de 10M, mas baseado em pontos)
    ↓
calcular_tiles_por_densidade(4.3M pts/tile) → 56 tiles (apenas pontos!)
    ↓  tiles dividem o grid em 8×7
    ↓  tile_w = 274.253/8 = 34.282 px
    ↓  tile_h = 172.546/7 = 24.649 px
    ↓
idw_tile_para_disco() → np.meshgrid(xi, yi) → shape (24649, 34282) float64 → 6,30 GiB 💥
```

---

## 🛠️ Caminhos de Correção

### Caminho A — Adicionar `max_tile_pixels` ao cálculo de tiles ⭐ RECOMENDADO

**Arquivos afetados:**
- `utils/raster/InterpolatorUtils.py` — adicionar parâmetro `max_tile_pixels` à `calcular_tiles_por_densidade()`
- `plugins/idw_interpolator/IdwInterpolatorTask.py` — usar o novo parâmetro e adicionar verificação RAM após grid

**Descrição:**
Modificar `calcular_tiles_por_densidade()` para aceitar um parâmetro `max_tile_pixels` que limita o número máximo de pixels por tile. O número de tiles será calculado como:

```python
n_tiles_por_pontos = ceil(total_points / pontos_por_chunk)
n_tiles_por_pixels = ceil(total_pixels / max_tile_pixels)
n_tiles = max(n_tiles_por_pontos, n_tiles_por_pixels)
```

**Prós:** Simples, eficaz, resolve na origem.
**Contras:** Aumenta número de tiles para áreas com alta resolução.

---

### Caminho B — Incluir pixel RAM no `estimated_ram`

**Arquivos afetados:**
- `plugins/idw_interpolator/IdwInterpolatorTask.py` — modificar `estimated_ram`

**Descrição:**
Após calcular `width` e `height` do grid, recalcular `estimated_ram` para incluir as alocações de meshgrid:

```python
tile_pixels = (width * height) / n_tiles  
ram_meshgrid = tile_pixels * 8 * 2  # xi_grid + yi_grid
ram_query = tile_pixels * 16         # query_pts
ram_idw = tile_pixels * k * 8 * 5    # dist + idx + pesos + r_vals + g_vals + b_vals
```

**Prós:** O governor teria bloqueado com a estimativa real.
**Contras:** `estimated_ram` é usado em `BaseTask.run()` ANTES de `_run()`, onde `width`/`height` ainda não são conhecidos. Precisaria de verificação adicional dentro de `_run()`.

---

### Caminho C — Verificação RAM dentro de `_run()` após grid

**Arquivos afetados:**
- `plugins/idw_interpolator/IdwInterpolatorTask.py` — adicionar verificação após Estágio 2

**Descrição:**
Adicionar uma chamada ao governor com `estimated_ram` realista após calcular as dimensões do grid e tiles:

```python
# Após calcular tiles
ram_estimada = max((tile_h * tile_w) * 8 * 6, 1)  # 6 arrays float64 do meshgrid+IDW
can, reason = self._governor.can_execute(estimated_ram=ram_estimada * min(n_cpus, 8))
if not can:
    # Reduzir tile size ou abortar
```

**Prós:** Pode reduzir tiles dinamicamente. 
**Contras:** Mais complexo, adiciona lógica condicional.

---

### Caminho D — Check periódico dentro de `idw_tile_para_disco`

**Arquivos afetados:**
- `utils/raster/InterpolatorUtils.py` — adicionar verificação antes do meshgrid

**Descrição:**
Antes de criar `np.meshgrid`, verificar se `tile_h * tile_w` ultrapassa um limiar e, se sim, retornar erro para que o task possa reagir.

**Prós:** Proteção local no ponto mais crítico.
**Contras:** Não evita a alocação — só reporta o erro depois de já ter consumido recursos para chegar lá. A task falharia de qualquer forma.

---

### Caminho E — PipelineRunner com `can_execute` antes de cada stage grande

**Arquivos afetados:**
- `core/papeline/AsyncPipelineEngine.py` — adicionar `governor.assert_can_execute()` no loop
- `core/papeline/BaseStep.py` — adicionar método `required_ram()` opcional

**Descrição:**
Cada step pode implementar `required_ram()` que retorna a RAM estimada. A engine consulta o governor antes de executar cada step.

**Prós:** Arquiteturalmente correto, desacoplado.
**Contras:** Muda contrato do `BaseStep`, impacto em todos os steps existentes.

---

## ✅ Decisão: Combinar Caminhos A + C

A solução escolhida combina:

1. **Caminho A**: Modificar `calcular_tiles_por_densidade()` para aceitar `max_tile_pixels` e calcular tiles baseado em **pontos** E **pixels** (o que for maior).
2. **Caminho C**: Após calcular grid e tiles em `_run()`, verificar RAM realista com o governor.

### Parâmetros escolhidos

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `MAX_TILE_PIXELS` | 10.000.000 | ≈ 3.162×3.162 px → meshgrid ~160 MB |
| `BYTES_PER_PIXEL_ESTIMATE` | 8 × 6 = 48 bytes | xi_grid + yi_grid + query_pts + dist + idx + pesos |

### Arquivos a modificar

1. `utils/raster/InterpolatorUtils.py` — `calcular_tiles_por_densidade()` ganha parâmetro `max_tile_pixels`
2. `plugins/idw_interpolator/IdwInterpolatorTask.py` — chama com `max_tile_pixels`, adiciona verificação RAM pós-grid

---

## 🔗 Integração com SystemMonitorService

Como parte da centralização de dados do sistema, o `ResourceGovernor` agora expõe
`system_stats()` que retorna CPU + RAM unificados, e o `SystemMonitorService`
passou a consumir **exclusivamente** do `ResourceGovernor` em vez de chamar
`psutil` diretamente.

### Regras de arquitetura


4. **Nenhum consumidor importa CpuGovernor ou RamGovernor** — tudo passa pelo ResourceGovernor

### Fluxo de dados

```
psutil
  ├── RamGovernor (ResourceGovernor._ram)
  │     └── snapshot() → percent_system, used_system_human, total_human
  │
  └── CpuGovernor (ResourceGovernor._cpu)
        └── percent(), count_physical(), count_logical()
              │
              ▼
    ResourceGovernor  ← ponto unico de acesso (dados BRUTOS apenas)
      ├── system_stats()         →  {"cpu": 45.2, "ram": 72.8}
      ├── cpu_percent()          →  45.2
      ├── cpu_count_physical()   →  8
      ├── cpu_count_logical()    →  16
      └── ram_snapshot()         →  {percent_system, used_system_human, total_human}
              │
              ▼
    SystemMonitorService._build_tooltips()  ← tooltips NO CONSUMIDOR
      ├── phys = governor.cpu_count_physical()
      ├── log  = governor.cpu_count_logical()
      ├── cpu_tip = f"CPU: {cpu}% ({phys} cores fisicos, {log} logicos)"
      ├── snap   = governor.ram_snapshot()
      └── ram_tip = f"RAM: {ram}% ({snap['used']} / {snap['total']} usados)"
              │
              ▼
    GridPercentView (generico — N indicadores)
      ├── set("cpu", 45.2, tooltip=cpu_tip)
      └── set("ram", 72.8, tooltip=ram_tip)
              │
              ├── mouse sobre CPU → tooltip CPU (info de CPU)
              ├── mouse sobre RAM → tooltip RAM (info de RAM)
              └── mouse fora      → fallback "CPU: 45.2%  RAM: 72.8%"
```

### Mudanças realizadas

| Arquivo | Tipo | O quê muda |
|---|---|---|
| `core/governor/CpuGovernor.py` | 🔧 MODIFICAR | Remove `tooltip()` (governor nao sabe o que é tooltip). Mantém `percent()`, `count_physical()`, `count_logical()` como métodos de instância. `max_workers()`/`n_jobs()` como `@classmethod` (retrocompatível) |
| `core/governor/ResourceGovernor.py` | 🔧 MODIFICAR | Remove `cpu_tooltip()`/`ram_tooltip()`. Adiciona `cpu_count_physical()`, `cpu_count_logical()`, `ram_snapshot()` — métodos genéricos que retornam dados brutos |
| `core/monitor/SystemMonitorService.py` | 🔧 MODIFICAR | Importa APENAS `ResourceGovernor`. Tooltips montadas em `_build_tooltips()` a partir de `governor.cpu_percent()`, `governor.cpu_count_physical()`, `governor.cpu_count_logical()`, `governor.ram_snapshot()` |
| `resources/widgets/grid/GridPercentView.py` | 🔧 CORRIGIR | Docstring genérica (sem menção a CPU/RAM). Tooltip individual por item SEMPRE funciona (antes só com callback). Mouse sobre CPU → tooltip CPU, mouse sobre RAM → tooltip RAM |
| `core/config/MenuManager.py` | 🔧 MODIFICAR | Cria `ResourceGovernor` e o injeta no `SystemMonitorService` |
| `core/governor/RamGovernor.py` | 🔧 CORRIGIR | `_record_history()` movido para dentro de `if include_history:`; `except` com `as e` + `LogUtils` |
| `docs/skills/SKILL_WIDGETS.md` | 📝 ATUALIZAR | Adiciona `GridPercentView` ao catálogo de widgets |

### Benefícios

1. **Fonte única de verdade** — `psutil` é chamado apenas pelo `RamGovernor` e `CpuGovernor`
2. **Dados consistentes** — CPU e RAM vêm do mesmo ciclo de polling
3. **Governor aware** — o monitor reflete as mesmas métricas que o governor usa para decisões
4. **Sem quebra de contrato** — `SystemMonitorService` mantém mesma API pública (`start()`, `stop()`, `poll_once()`, `stats_updated`)
5. **LogUtils em vez de logging bruto** — `RamGovernor` usa `LogUtils` com `ToolKey.SYSTEM` (Contrato 3 e 26)
6. **Governors não sabem o que é tooltip** — retornam apenas dados; formatação é responsabilidade do consumidor
7. **GridPercentView é genérico** — pode exibir qualquer N indicadores, sem acoplamento a CPU/RAM
8. **Nenhum import de sub-governor fora do pacote** — `SystemMonitorService` importa APENAS `ResourceGovernor`
