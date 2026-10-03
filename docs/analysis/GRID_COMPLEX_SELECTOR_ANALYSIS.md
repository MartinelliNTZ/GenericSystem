# 📐 Análise Arquitetural: GridComplexSelector + ComplexSelector

> **Data:** 07/06/2026  
> **Última atualização:** 07/06/2026 (após desacoplamento)  
> **Contexto:** Revisão de widgets reutilizáveis do Aetheris ToolBox  
> **Arquivos analisados:**  
> - `resources/widgets/complex/GridComplexSelector.py` (~730 linhas)  
> - `resources/widgets/complex/ComplexSelector.py` (~635 linhas)  
> - `plugins/las_vector_converter/LasVectorConverterPlugin.py` (~580 linhas)  
> - `docs/skills/SKILL_PLUGIN_CONTRACT.md` (contratos do sistema)

---

## 📋 Sumário Executivo

| Gravidade | Tipo | Descrição | Status |
|-----------|------|-----------|--------|
| 🔴 **CRÍTICA** | Bug | Dynamic parent + callback chaining quebrado | ✅ **CORRIGIDO** |
| 🔴 **GRAVE** | Contrato | `ct` importado diretamente (viola Contrato 19) | ✅ **CORRIGIDO** |
| 🟡 **MÉDIA** | Design | Dupla-registro de callbacks no mesmo `parent_key` | ✅ **CORRIGIDO** |
| 🟡 **MÉDIA** | Código Morto | `Qt` importado e não utilizado (viola Contrato 9) | ✅ **CORRIGIDO** |
| 🟢 **LEVE** | Code Style | `QTimer` importado duas vezes (módulo + local) | ✅ **CORRIGIDO** |
| 🟢 **LEVE** | Design | Chaining frágil baseado em atributo de função | ✅ **MITIGADO** |
| 🟢 **LEVE** | API | Plugin acessava atributos privados do widget | ✅ **CORRIGIDO** |

---

## 🔴 1. BUG CRÍTICO: Dynamic Parent + Callback Chaining Quebrado ✅ CORRIGIDO

### 1.1 O Problema (Histórico)

GridComplexSelector usava um mecanismo de **chaining de callbacks** onde o plugin sobrescrevia `on_path_change` diretamente, quebrando a corrente de linking.

### 1.2 A Correção

O plugin agora usa **`set_on_input_changed()`** — API pública do GridComplexSelector que preserva o chaining interno:

```python
# ❌ ANTIGO (quebrava chaining)
self._grid_io["Entrada"].on_path_change = self._on_input_path_changed

# ✅ NOVO (preserva chaining)
self._grid_io.set_on_input_changed(self._on_input_changed)
```

O GridComplexSelector gerencia internamente:
1. Salva o callback original do ComplexSelector
2. Instala um wrapper que chama: callback original → linking → callback do plugin
3. O plugin nunca toca em `on_path_change` diretamente

### 1.3 API Pública para Callbacks

```python
# Para reagir a QUALQUER entrada (recomendado):
grid.set_on_input_changed(callback)  # callback(label, paths)

# Para reagir a um selector específico:
grid.set_on_changed("Entrada", callback)  # callback(paths)
```

---

## 🔴 2. VIOLAÇÃO DE CONTRATO: `ct` importado diretamente ✅ CORRIGIDO

### 2.1 O Problema (Histórico)

O `show_error()` usava `from resources.styles.ThemeManager import ct`, violando o Contrato 19.

### 2.2 A Correção

Substituído por `AppStyles.theme_colors()`:

```python
# ❌ ANTIGO (violava contrato)
from resources.styles.ThemeManager import ct
error_color = ct.theme.COLOR_DANGER

# ✅ NOVO (usa AppStyles)
from resources.styles.AppStyles import AppStyles
colors = AppStyles.theme_colors()
error_color = colors.get("COLOR_DANGER", "#FF4444")
```

---

## 🟡 3. DUPLO-REGISTRO DE CALLBACKS NO MESMO PARENT ✅ CORRIGIDO

### 3.1 O Problema (Histórico)

Existiam dois métodos separados (`_connect_dynamic_listener` + `_connect_parent_listener`) que registravam callbacks no mesmo parent, causando sobrescrita.

### 3.2 A Correção

Unificado em um único método `_connect_output_listener()`:

```python
def _connect_output_listener(self, child_label: str, parent_key: str, dynamic_parent: bool = False):
    """Único listener para output com parent e opcional dynamic_parent."""
    parent_selector = self._selectors.get(parent_key)
    child_selector = self._selectors.get(child_label)
    if not parent_selector or not child_selector:
        return

    original_cb = parent_selector.on_path_change

    def unified_handler(paths: list[str]):
        # 1. Callback original (wrapper do usuário ou None)
        if original_cb:
            original_cb(paths)
        # 2. Se dynamic_parent, aplica modo no filho
        if dynamic_parent:
            self._apply_dynamic_mode(child_label)
        # 3. Gera output se necessário
        if child_label not in self._generating_output:
            should_generate = (
                self._self_generated.get(child_label, False)
                or not child_selector.get_paths()
            )
            if should_generate:
                self._generate_output(child_label, paths)

    parent_selector.on_path_change = unified_handler
```

---

## 🟡 4. CÓDIGO MORTO: `Qt` importado e não utilizado ✅ CORRIGIDO

### 4.1 O Problema (Histórico)

`ComplexSelector.py` importava `from PySide6.QtCore import Qt` sem nunca usar.

### 4.2 A Correção

Import removido.

---

## 🟢 5. `QTimer` importado duas vezes ✅ CORRIGIDO

### 5.1 O Problema (Histórico)

`GridComplexSelector.py` tinha `QTimer` importado no topo do módulo E localmente dentro de `show_error()`.

### 5.2 A Correção

Import local removido — usa o import global do topo.

---

## 🟢 6. NOVA API PÚBLICA: Desacoplamento Plugin ↔ Widget

Como parte do desacoplamento, foram adicionados métodos públicos ao GridComplexSelector para que o plugin **NUNCA** precise acessar atributos privados do widget.

### 6.1 `set_input_placeholder(label, placeholder)`

Substitui o acesso direto a `selector.edit.setPlaceholderText()`:

```python
# ❌ ANTIGO (acesso direto a sub-widget)
entrada.edit.setPlaceholderText("Selecione o arquivo...")

# ✅ NOVO (via API pública)
self._grid_io.set_input_placeholder("Entrada", "Selecione o arquivo...")
```

### 6.2 `set_input_file_filter(label, file_filter)`

Substitui o acesso direto a `selector.file_filter = value`:

```python
# ❌ ANTIGO (acesso direto a propriedade)
entrada.file_filter = self._LAS_FILTER

# ✅ NOVO (via API pública)
self._grid_io.set_input_file_filter("Entrada", self._LAS_FILTER)
```

### 6.3 `suspend_callbacks()` / `resume_callbacks(snapshot)`

Substitui o acesso direto a `_user_callbacks` para restaurar paths sem disparar re-avaliação:

```python
# ❌ ANTIGO (acesso a atributo privado)
saved_callback = self._grid_io._user_callbacks.get("Entrada")
self._grid_io.set_on_changed("Entrada", None)
# ... set_path ...
self._grid_io.set_on_changed("Entrada", saved_callback)

# ✅ NOVO (via API pública)
saved = self._grid_io.suspend_callbacks()
try:
    entrada.set_path(saved_path)
finally:
    self._grid_io.resume_callbacks(saved)
```

### 6.4 `set_fixed_name(fixed_name)` (ComplexSelector)

Permite atualizar dinamicamente o nome do arquivo de saída para o 📂 (suggest button):

```python
selector.set_fixed_name("lasvectorconverted.gpkg")
```

### 6.5 `set_output_extension()` — Sincronização com fixed_name

Agora `set_output_extension()` também atualiza o `fixed_name` do ComplexSelector, garantindo que o 📂 use a extensão atual do combo:

```python
# Quando o combo muda de "gpkg" → "shp":
self._grid_io.set_output_extension("Saída", "shp")
# → fixed_name muda de "lasvectorconverted.gpkg" para "lasvectorconverted.shp"
# → 📂 agora gera "lasvectorconverted.shp"
```

### 6.6 `fixed_name` sem extensão

O `fixed_name` pode ser definido sem extensão (ex: `"lasvectorconverted"`). O `_generate_output()` adiciona a extensão automaticamente se `extension` estiver definida:

```python
# Spec:
"fixed_name": "lasvectorconverted",  # sem extensão

# set_output_extension("Saída", "gpkg") → fixed_name vira "lasvectorconverted.gpkg"
# _generate_output() → se extension="gpkg" e fixed_name="lasvectorconverted"
#                      → output_name = "lasvectorconverted.gpkg"
```

---

## 📊 COMPARATIVO: Atributo vs Signal

| Aspecto | Atributo (`on_path_change = func`) | Signal (`path_changed = Signal(list)`) |
|---------|-----------------------------------|----------------------------------------|
| Múltiplos listeners | ❌ Apenas 1 | ✅ Ilimitados |
| Sobrescrita segura | ❌ Fácil de quebrar | ✅ Conecta sem conflito |
| Desconexão | `= None` | `.disconnect()` |
| Chain automático | Manual (wrapper) | Automático |
| Type safety | ❌ None | ✅ Signal tipado |
| Debugging | Difícil (qual função está setada?) | Fácil (slots listados) |
| Manutenção | Frágil | Robusto |

**Nota:** O chaining via wrapper + `set_on_input_changed()` mitiga o problema de sobrescrita, mas a migração para Signal ainda é a solução definitiva recomendada.

---

## 🛠️ CHECKLIST DE CORREÇÕES

- [x] **CRÍTICO**: Substituir `on_path_change` por `set_on_input_changed()` no plugin
- [x] **CRÍTICO**: Plugin não acessa mais atributos privados do widget
- [x] **GRAVE**: Substituir `from resources.styles.ThemeManager import ct` por `AppStyles`
- [x] **MÉDIO**: Unificar `_connect_dynamic_listener` + `_connect_parent_listener` em método único
- [x] **MÉDIO**: Remover `from PySide6.QtCore import Qt` não utilizado
- [x] **LEVE**: Remover import local duplicado de `QTimer`
- [x] **LEVE**: Adicionar `set_input_placeholder()`, `set_input_file_filter()`, `suspend_callbacks()`, `resume_callbacks()`
- [x] **LEVE**: `set_output_extension()` sincroniza `fixed_name` do ComplexSelector
- [x] **LEVE**: `fixed_name` sem extensão + append automático em `_generate_output()`
- [ ] **FUTURO**: Migrar `on_path_change` para `Signal` do PySide6

---

## 🔗 IMPACTO NOS PLUGINS EXISTENTES

| Plugin | Arquivo | Uso Antigo | Uso Novo |
|--------|---------|------------|----------|
| LasVectorConverter | `LasVectorConverterPlugin.py` | `on_path_change = callback` | `set_on_input_changed(callback)` |
| LasVectorConverter | `LasVectorConverterPlugin.py` | `entrada.edit.setPlaceholderText()` | `set_input_placeholder()` |
| LasVectorConverter | `LasVectorConverterPlugin.py` | `entrada.file_filter = value` | `set_input_file_filter()` |
| LasVectorConverter | `LasVectorConverterPlugin.py` | `_user_callbacks` acesso direto | `suspend_callbacks()`/`resume_callbacks()` |

---

## 📌 CONCLUSÃO

O desacoplamento foi concluído com sucesso. O plugin `LasVectorConverter` agora:

1. **NÃO acessa** atributos privados do widget (`_user_callbacks`, `edit`, `file_filter`)
2. **USA** apenas API pública (`set_on_input_changed`, `set_input_placeholder`, `set_input_file_filter`, `suspend_callbacks`, `resume_callbacks`)
3. **O chaining** de linking/dynamic_parent é preservado automaticamente
4. **A extensão** do output é dinâmica: combo → `set_output_extension()` → sincroniza `fixed_name` → 📂 usa extensão atual

A migração para `Signal` do PySide6 continua sendo a solução definitiva recomendada para eliminar completamente a fragilidade do chaining via atributo de função.