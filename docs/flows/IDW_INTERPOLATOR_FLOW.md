# Fluxo do IdwInterpolatorPlugin

## Visão Geral

O **IdwInterpolatorPlugin** é responsável por interpolar nuvens de pontos LAS/LAZ em um grid regular utilizando o método **IDW (Inverse Distance Weighting)**. Ele permite a interpolação das bandas **R, G, B** e da **altura (Z)**, com opção de mesclar bandas RGB em um mosaico ou gerar bandas individuais.

---

## Arquitetura do Plugin

```
┌─────────────────────────────────────────────────────────────────┐
│                     IdwInterpolatorPlugin                       │
│                    (herda de BasePlugin)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐   ┌──────────────────────────────┐    │
│  │    UI (Widgets)     │   │    Pipeline & Execução        │    │
│  │                     │   │                              │    │
│  │  • ExecutionButtons │   │  • PipelineRunner            │    │
│  │  • GridSelector     │   │  • IdwInterpolatorStep       │    │
│  │  • GridCheckBox     │   │  • SignalManager             │    │
│  │  • GridDoubleSpinBox│   │  • ProcessStatisticsUtil     │    │
│  │  • GridLabel        │   │  • LasUtil                   │    │
│  │  • GroupPainel      │   │                              │    │
│  │  • SimpleLabel      │   │                              │    │
│  └─────────────────────┘   └──────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componentes da UI

### 1. ExecutionButtons (Botões de Ação)

Três botões padronizados conforme **Contrato 18**:

| Botão            | Tipo        | Descrição                                      |
|------------------|-------------|------------------------------------------------|
| CALCULAR PIXEL IDEAL | `secondary` | Calcula o pixel ideal baseado na densidade da nuvem |
| EXECUTAR         | `primary`   | Executa a interpolação IDW                     |
| CANCELAR         | `danger`    | Cancela a execução em andamento               |

**Estados dos botões ao longo do fluxo:**

| Estado                | PIXEL IDEAL | EXECUTAR | CANCELAR |
|-----------------------|:-----------:|:--------:|:--------:|
| Inicial (sem LAS)     | ❌ Desab.   | ❌ Desab.| ❌ Desab.|
| LAS carregado         | ✅ Hab.     | ✅ Hab.  | ❌ Desab.|
| Executando            | ❌ Desab.   | ❌ Desab.| ✅ Hab.  |
| Finalizado (sucesso)  | ✅ Hab.     | ✅ Hab.  | ❌ Desab.|
| Finalizado (erro)     | ✅ Hab.     | ✅ Hab.  | ❌ Desab.|

---

### 2. GroupPainel "Arquivo de Entrada"

Campos de seleção e informações sobre o arquivo LAS/LAZ:

| Widget         | Descrição                                         |
|----------------|---------------------------------------------------|
| **GridSelector** (LAS/LAZ) | Seletor de arquivo para abrir LAS/LAZ (`open_file`) |
| **GridSelector** (Raster)  | Seletor para salvar o GeoTIFF de saída (`save_file`) |
| **SimpleLabel** (info_las)     | Exibe número de pontos e se possui RGB            |
| **SimpleLabel** (info_bbox)    | Exibe bounding box do LAS (X min/max, Y min/max)  |
| **SimpleLabel** (info_densidade) | Exibe densidade em pts/m²                      |
| **SimpleLabel** (info_espacamento) | Exibe espaçamento e pixel ideal calculado    |

> Os 4 labels informativos ficam ocultos até que o **CALCULAR PIXEL IDEAL** seja pressionado.

---

### 3. GroupPainel "Target da Interpolação"

Define quais bandas serão interpoladas, em grid de **4 colunas** via `GridCheckBox`:

| Chave          | Rótulo           | Default | Descrição                                       |
|----------------|------------------|:-------:|-------------------------------------------------|
| `r`            | R (Vermelho)     | ✅      | Interpola banda vermelha                        |
| `g`            | G (Verde)        | ✅      | Interpola banda verde                           |
| `b`            | B (Azul)         | ✅      | Interpola banda azul                            |
| `z`            | Altura (Z)       | ❌      | Interpola altitude Z                            |
| `merge`        | Mesclar Bandas?  | ✅      | Se true: gera mosaico RGB. Se false: bandas .tif|
| `eliminar_tiles` | Eliminar Tiles | ✅      | Remove pastas de tiles após processamento       |

**Regras de validação:**
- `merge = true` REQUER que R, G e B estejam todos marcados (Z não entra no mosaico)
- Se não houver RGB no LAS, R, G, B são automaticamente desmarcados ao carregar o arquivo

---

### 4. GroupPainel "Parâmetros IDW"

Parâmetros numéricos configuráveis via `GridDoubleSpinBox`:

| Chave             | Rótulo        | Default    | Faixa             | Descrição                                     |
|-------------------|---------------|:----------:|:-----------------:|-----------------------------------------------|
| `resolution`      | Resolução (cm)| 1,00       | 0,1 – 100,0       | Tamanho do pixel em centímetros               |
| `fator_conversao` | Fator Conversão | 0,75     | 0,1 – 5,0         | Multiplicador do espaçamento (75% do ideal)   |
| `k`               | Vizinhos (k)  | 5          | 1 – 50            | Número de vizinhos mais próximos para IDW     |
| `power`           | Potência (p)  | 2,0        | 0,5 – 5,0         | Expoente da distância (2 = inverso quadrático)|
| `raio_max`        | Raio Máx (m)  | 0,50       | 0,01 – 10,0       | Raio máximo de busca em metros                |
| `overlap`         | Overlap (m)   | 3,0        | 0,0 – 10,0        | Sobreposição entre tiles para evitar artefatos|
| `pontos_por_tile` | Pontos/Tile   | 10.000.000 | 100k – 100M       | Número alvo de pontos por tile                |

---

### 5. GroupPainel "Resultados"

GridLabel com 2 colunas exibindo os resultados após execução:

| Chave         | Rótulo    | Exemplo                        |
|---------------|-----------|--------------------------------|
| `grid_dims`   | Grid (px) | "10.240 x 8.192 px"            |
| `resolucao`   | Resolução | "1,00 cm"                      |
| `n_tiles`     | N Tiles   | "24"                           |
| `tempo_idw`   | Tempo IDW | "—" (não populado, reservado)  |
| `output_path` | Saída     | "C:/output/raster.tif"         |
| `status`      | Status    | "Concluído"                    |

---

## Fluxo de Execução Completo

### Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INÍCIO                                       │
│  Plugin instanciado → _build_ui() constrói interface               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CARREGAMENTO DO LAS                              │
│  1. Usuário seleciona arquivo LAS/LAZ via GridSelector             │
│  2. Signal: edit.textChanged → _on_input_path_changed()            │
│  3. Verifica: extensão .las/.laz? arquivo existe?                  │
│  4. Chama _carregar_las(path)                                      │
│     a. LasUtil.get_info() → metadados (point_count, has_rgb)       │
│     b. Atualiza self._current_path e self._current_metadata        │
│     c. Se não tem RGB → desmarca R, G, B no GridCheckBox           │
│     d. Habilita botões EXECUTAR e PIXEL IDEAL                      │
│     e. Emite console_message com info do LAS                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│               CÁLCULO DO PIXEL IDEAL (opcional)                     │
│  1. Usuário clica "CALCULAR PIXEL IDEAL"                          │
│  2. _on_calc_ideal_pixel()                                         │
│  3. Lê fator_conversão do GridDoubleSpinBox                        │
│  4. LasUtil.calcular_pixel_ideal() processa o LAS:                 │
│     a. Calcula bounding box                                        │
│     b. Calcula densidade (pts/m²)                                  │
│     c. Calcula espaçamento médio entre pontos                      │
│     d. Aplica fator_conversão → pixel_ideal_cm =                  │
│        espaçamento_cm * fator_conversao                            │
│  5. Atualiza:                                                      │
│     • resolution no GridDoubleSpinBox                              │
│     • Labels informativos (bbox, densidade, espaçamento)           │
│  6. Em caso de erro → MessageBox.show_error()                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXECUÇÃO DA INTERPOLAÇÃO                         │
│  1. Usuário clica "EXECUTAR"                                       │
│  2. _on_executar() faz validações:                                 │
│     • LAS carregado?                                               │
│     • Caminho de saída definido?                                   │
│     • Ao menos uma banda selecionada?                              │
│     • Se merge=true → R, G e B todos marcados?                     │
│  3. Coleta parâmetros:                                             │
│     • resolution (cm → m)                                          │
│     • k, power, raio_max, overlap, pontos_por_tile                 │
│     • target_bands, merge_bands, eliminar_tiles                    │
│     • crs_str = "EPSG:31982"                                       │
│  4. Prepara UI:                                                    │
│     • Desabilita EXECUTAR e PIXEL IDEAL                            │
│     • Habilita CANCELAR                                            │
│     • Status badge → RUNNING                                       │
│     • GridLabel → "Processando..."                                 │
│  5. Estatísticas:                                                  │
│     • ProcessStatisticsUtil.start() com n_pontos                   │
│     • Estima tempo (~60s/500k pontos, min 30s, max 1h)            │
│  6. Sinais (SignalManager):                                        │
│     • execution_started.emit(tool_key)                             │
│     • hud_show.emit({message, timer, eta})                         │
│     • console_message.emit(infos)                                  │
│  7. Cria PipelineRunner:                                           │
│     • Step: IdwInterpolatorStep()                                  │
│     • Context: file_path, output_path, target_bands, merge_bands   │
│       resol_m, idw_k, idw_power, idw_raio_max, idw_overlap,       │
│       pontos_por_tile, crs_str, tool_key, eliminar_tiles           │
│  8. Conecta sinais do runner:                                      │
│     • finished_ok → _on_done                                       │
│     • failed → _on_error                                           │
│     • finished → _on_runner_finished                               │
│  9. Salva preferências (save_prefs)                                │
│ 10. runner.start() → execução em background thread                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌──────────────────────────────┐ ┌──────────────────────────────────┐
│        SUCESSO               │ │            ERRO                  │
│                              │ │                                  │
│  _on_done(context):          │ │  _on_error(message):             │
│  1. Extrai idw_result:       │ │  1. Log de erro                  │
│     • grid (width_px,        │ │  2. execution_cancelled.emit()   │
│        height_px)            │ │  3. console_message.emit(ERRO)   │
│     • parametros             │ │  4. status → "Erro"              │
│     • tiles (total, ok)      │ │  5. MessageBox.show_error()      │
│     • arquivos_gerados       │ │                                  │
│  2. Atualiza GridLabel:      │ └──────────┬───────────────────────┘
│     • grid_dims, resolucao   │            │
│     • n_tiles, output_path   │            │
│     • status → "Concluido"   │            │
│  3. statistics.end()         │            │
│  4. Sinais:                  │            │
│     • execution_finished     │            │
│     • progress_update(100%)  │            │
│     • console_message        │            │
│     • console_html (link     │            │
│       clicável para pasta)   │            │
└──────────┬───────────────────┘            │
           │                                │
           └──────────┬─────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FINALIZAÇÃO                                     │
│  _on_runner_finished():                                             │
│  1. self._runner = None                                             │
│  2. Reabilita EXECUTAR e PIXEL IDEAL (se LAS carregado)            │
│  3. Desabilita CANCELAR                                             │
│  4. Status badge → PRONTA                                           │
│  5. hud_hide.emit()                                                 │
│  6. progress_update(0%)                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Gerenciamento de Estado

### Variáveis de Instância

```python
self._current_path: str          # Caminho do LAS/LAZ atualmente carregado
self._current_metadata: dict     # Metadados do LAS (path, n_pontos, has_rgb)
self._runner: PipelineRunner | None  # Referência ao runner em background
```

### Badge de Status (self.page.set_badge)

| Badge    | Quando                         |
|----------|--------------------------------|
| `PRONTA` | UI pronta, aguardando ação     |
| `RUNNING`| Interpolação em andamento      |
| `ERROR`  | Erro ao carregar LAS           |

---

## Sistema de Preferências

O plugin salva/carrega preferências via `load_prefs()` e `save_prefs()`:

```python
preferences = {
    "last_path":   str,    # Último LAS carregado
    "last_output": str,    # Último caminho de saída
    "opts":        dict,   # Estado dos checkboxes (r, g, b, z, merge, eliminar_tiles)
    "params":      dict,   # Valores dos parâmetros IDW
}
```

- **`load_prefs()`**: Chamado na inicialização, carrega e aplica as preferências salvas anteriormente
- **`save_prefs()`**: Chamado ao clicar **EXECUTAR**, salva estado atual no cache de memória

---

## Sinais (SignalManager)

O plugin utiliza o SignalManager (Contratos 20 e 24) para comunicação entre componentes:

| Sinal                     | Quando                        | Efeito                                |
|---------------------------|-------------------------------|---------------------------------------|
| `execution_started`       | Início da execução            | Notifica outros componentes           |
| `execution_finished`      | Execução concluída com sucesso | Notifica conclusão                    |
| `execution_cancelled`     | Erro na execução              | Notifica falha                        |
| `hud_show`                | Início da execução            | Exibe HUD com progresso e ETA         |
| `hud_hide`                | Fim da execução               | Oculta HUD                            |
| `progress_update`         | Progresso                     | Atualiza barra de progresso           |
| `console_message`         | Eventos diversos              | Mensagens no console                  |
| `console_html`            | Finalização com sucesso       | Link clicável para pasta de saída     |

---

## Logs (Estrutura de Códigos)

Os logs seguem o padrão de `logger.info/error/debug` com códigos identificadores:

| Código                   | Nível | Contexto                        |
|--------------------------|:-----:|---------------------------------|
| `IDW_READY`              | INFO  | Plugin inicializado             |
| `IDW_SELECTOR_CHANGED`   | DEBUG | Campo de texto do selector alterado|
| `IDW_LAS_LOAD`           | INFO  | Iniciando carregamento do LAS   |
| `IDW_LAS_LOADED`         | INFO  | LAS carregado com sucesso       |
| `IDW_LAS_LOAD_ERR`       | ERROR | Erro ao carregar LAS            |
| `IDW_CALC_PIXEL`         | INFO  | Botão CALCULAR PIXEL IDEAL pressionado|
| `IDW_PIXEL_CALC_DONE`    | INFO  | Pixel ideal calculado           |
| `IDW_PIXEL_CALC_ERR`     | ERROR | Erro ao calcular pixel ideal    |
| `IDW_EXEC_BTN`           | INFO  | Botão EXECUTAR pressionado      |
| `IDW_EXEC_START`         | INFO  | Interpolação iniciada           |
| `IDW_NO_OUTPUT`          | WARN  | Nenhum caminho de saída         |
| `IDW_NO_TARGET`          | WARN  | Nenhuma banda selecionada       |
| `IDW_MOSAIC_INCOMPLETE`  | WARN  | Mosaico requer R,G,B juntos     |
| `IDW_OUTPUT_PATH`        | INFO  | Caminho de saída definido       |
| `IDW_CANCEL_BTN`         | INFO  | Botão CANCELAR pressionado      |
| `IDW_PIPELINE_DONE`      | INFO  | Pipeline executada com sucesso  |
| `IDW_PIPELINE_FAILED`    | ERROR | Pipeline falhou                 |
| `IDW_PREFS_LOAD`         | INFO  | Carregando preferências         |
| `IDW_PREFS_LOADED`       | INFO  | Preferências carregadas         |
| `IDW_PREFS_SAVED`        | INFO  | Preferências salvas no cache    |

---

## PipelineRunner e IdwInterpolatorStep

### PipelineRunner

Responsável por executar o pipeline em **background thread**, gerenciando:

- `start()` → inicia execução em thread separada
- `cancel()` → cancela execução em andamento
- `isRunning()` → verifica se está em execução
- Sinais: `finished_ok(context)`, `failed(message)`, `finished()`

### IdwInterpolatorStep

Step do pipeline que contém a lógica de interpolação IDW propriamente dita:

1. Divide a nuvem em **tiles** baseado em `pontos_por_tile` e `overlap`
2. Para cada tile, aplica interpolação IDW com os parâmetros (`k`, `power`, `raio_max`)
3. Gera rasters individuais por banda
4. Se `merge_bands = true` e RGB presente, mescla em mosaico RGB
5. Se `eliminar_tiles = true`, remove pastas de tiles temporárias
6. Retorna `idw_result` com:
   - `grid`: dimensões do grid (width_px, height_px)
   - `parametros`: resolução usada
   - `tiles`: total e OK
   - `arquivos_gerados`: lista de arquivos .tif gerados

---

## Fluxo de Validações (Antes da Execução)

```
EXECUTAR pressionado
    │
    ├── Runner já rodando? → Sim → MessageBox("Já existe em andamento")
    │
    ├── LAS carregado? → Não → MessageBox("Nenhum arquivo LAS carregado")
    │
    ├── Caminho de saída definido? → Não → MessageBox("Selecione onde salvar")
    │
    ├── Pelo menos uma banda (R,G,B,Z) selecionada? → Não → MessageBox
    │
    └── merge=true E tem alguma RGB mas faltando R/G/B?
                        → Sim → MessageBox("Mosaico requer R,G,B juntos")
                        → Não → OK → Inicia pipeline
```

---

## Contratos Seguidos

| Contrato | Descrição                                              |
|:--------:|--------------------------------------------------------|
| 11       | Widgets reutilizáveis (GridCheckBox, GridDoubleSpinBox, GridSelector, GridLabel) |
| 18       | ExecutionButtons padronizado                           |
| 20       | SignalManager para progresso/console                   |
| 24       | SignalManager apenas para comunicação entre componentes |

---

## Dependências Externas

| Módulo                    | Uso                                                    |
|---------------------------|--------------------------------------------------------|
| `LasUtil`                 | Leitura de metadados LAS/LAZ e cálculo de pixel ideal  |
| `ProcessStatisticsUtil`   | Estimativa de tempo restante baseada em histórico      |
| `MessageBox`              | Diálogos de aviso, erro e informação                   |
| `SignalManager`           | Singleton de comunicação entre componentes             |
| `PipelineRunner`          | Execução de pipeline em background thread              |
| `IdwInterpolatorStep`     | Lógica de interpolação IDW                             |
| `BasePlugin`              | Classe base para todos os plugins                      |