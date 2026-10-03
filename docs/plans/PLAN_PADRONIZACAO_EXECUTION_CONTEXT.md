# Action Plan: ExecutionContext Standardization and Pipeline Flow

## 1. Identified Problems

### 1.1 Data Access — Dict vs Attributes
Currently `ExecutionContext` uses dictionary-style access:
```python
context.get("file_path", "")
context.get("target_bands", {})
context.set("split_result", result)
```

**Problem:** No autocomplete, no typing, no visible documentation.

**Solution:** Simple class variables in `ExecutionContext`:
```python
context.input_path       # str — direct attribute access
context.output_path      # str
context.files            # list[str] | None
```

### 1.2 Exclusive Parameters Mixed in Context
Currently step-specific parameters are loose in the context:
```python
context.get("points_per_part", 5_000_000)
context.get("threshold", 0)
context.get("target_bands", {})
```

**Problem:** Context becomes a "soup of keys" with no separation of flow vs. specific params.

**Solution:** Exclusive parameters are passed DIRECTLY in the step constructor:
```python
AsyncPipelineEngine(
    steps=[
        LasCheckStep(advance_input=False),
        LasBlackFilterStep(threshold=30, save_black_points=True),
        LasTilerStep(points_per_part=5_000_000),
        IdwInterpolatorStep(target_bands={...}, resolution_m=0.01),
    ],
    context={...},
)
```

### 1.3 Steps Don't Update input_path for Next Step
Currently each step receives fixed parameters and doesn't propagate its output as the next step's input.

**Solution:** Flow convention with `advance_input` flag:
- `advance_input=True` (default) → step TRANSFORMS data → calls `advance_input()` in `on_success()`
- `advance_input=False` → step only ANALYZES → does NOT call `advance_input()`

```
input_path = /data/root
output_path = /data/root

Step 1 (LasCheck, advance_input=False):
  → Reads: input_path
  → Saves report to: output_path/lascheck/
  → input_path stays = /data/root

Step 2 (LasBlackFilter, advance_input=True):
  → Reads: input_path (= /data/root)
  → Saves filtered LAS to: output_path/lasblackfilter/
  → advance_input: input_path = /data/root/lasblackfilter/

Step 3 (LasTiler, advance_input=True):
  → Reads: input_path (= /data/root/lasblackfilter/)
  → Saves tiles to: output_path/lastiler/
  → advance_input: input_path = /data/root/lastiler/

Step 4 (IdwInterpolator, advance_input=True):
  → Reads: input_path (= /data/root/lastiler/)
  → Saves rasters to: output_path/idwtiles/
  → advance_input: input_path = /data/root/idwtiles/
```

**Order can be inverted** — each step knows where to read from and where to save to. The pipeline works regardless of step order.

### 1.4 Step-Specific input_path (Exception)
In specific cases, a step can receive a different `input_path`:

```python
AsyncPipelineEngine(
    steps=[
        LasBlackFilterStep(),
        LasTilerStep(),
        IdwInterpolatorStep(),
        LasCheckStep(advance_input=False, input_path="D:/data/root/lasblackfilter/"),
    ],
    ...
)
```

Here the last `LasCheckStep` receives a specific `input_path` to analyze ONLY the filtered folder, ignoring the standard flow.

---

## 2. ExecutionContext Modifications

### 2.1 Canonical Attributes (Simple Class Variables)

No `@property` — direct class variables, no workarounds:

```python
class ExecutionContext:
    """
    Shared state container between all pipeline steps.
    
    Canonical attributes (direct access):
        input_path: str    — Input directory with files to process
        output_path: str   — Base directory where results will be saved
        files: list[str] | None — Specific file list (None = all in input_path)
        tool_key: str      — ToolKey for logging
    """

    input_path: str = ""
    """Input directory with files to process."""

    output_path: str = ""
    """Base directory where results will be saved."""

    files: list[str] | None = None
    """Specific file list to process. None = all files in input_path."""

    tool_key: str = ""
    """ToolKey for logging."""

    def __init__(self, initial_data: dict = None):
        self._data: dict = initial_data.copy() if initial_data else {}
        self._errors: list[Exception] = []
        self._is_cancelled: bool = False

        # Sync _data with class attributes
        if initial_data:
            if "input_path" in initial_data:
                self.input_path = initial_data["input_path"]
            if "output_path" in initial_data:
                self.output_path = initial_data["output_path"]
            if "files" in initial_data:
                self.files = initial_data["files"]
            if "tool_key" in initial_data:
                self.tool_key = initial_data["tool_key"]
```

### 2.2 Keep `get()`/`set()` for Compatibility

```python
    def set(self, key: str, value: Any) -> ExecutionContext:
        """Stores value in context. Returns self for fluent interface."""
        self._data[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves value from context."""
        return self._data.get(key, default)
```

### 2.3 Remove Obsolete Class Variables

Remove:
```python
INPUT_PATH = None   # ❌ REMOVE
OUTPUT_PATH = None  # ❌ REMOVE
TOOL_KEY = None     # ❌ REMOVE
```

---

## 3. BaseStep Modifications

### 3.1 New Attributes

```python
class BaseStep(ABC):
    """Contract that defines a pipeline step."""

    # ── Step configuration attributes ──────────────────────────
    subfolder: str = ""
    """Output subfolder name (e.g. 'lascheck', 'lasblackfilter'). 
    Used to create output_path/subfolder/ automatically."""

    advance_input: bool = True
    """
    If True (default): step TRANSFORMS data → calls advance_input() in on_success()
    If False: step only ANALYZES → does NOT call advance_input()
    """
```

### 3.2 New Method: `advance_input()`

```python
    def advance_input(self, context: ExecutionContext) -> None:
        """
        Updates input_path to point to the step's output subfolder.
        Called automatically in on_success() if advance_input == True.
        """
        if self.subfolder:
            context.input_path = os.path.join(context.output_path, self.subfolder)
```

### 3.3 New Method: `resolve_files()`

```python
    def resolve_files(self, context: ExecutionContext, *extensions: str) -> list[str]:
        """
        Returns the list of files to process.
        - If context.files is set, returns context.files
        - Otherwise, lists all files with given extensions in context.input_path
        """
        if context.files is not None:
            return context.files
        files = []
        for ext in extensions:
            pattern = os.path.join(context.input_path, f"*{ext}")
            files.extend(glob.glob(pattern))
        return sorted(files)
```

### 3.4 New Method: `output_subdir()`

```python
    def output_subdir(self, context: ExecutionContext) -> str:
        """
        Returns the full output subfolder path.
        E.g.: output_path + "/" + subfolder
        Creates the folder if it doesn't exist.
        """
        if not self.subfolder:
            return context.output_path
        subdir = os.path.join(context.output_path, self.subfolder)
        os.makedirs(subdir, exist_ok=True)
        return subdir
```

### 3.5 on_success() with Automatic advance_input

```python
    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """
        Default callback: if advance_input == True, advances input_path.
        Transforming steps OVERRIDE this method to map results.
        Analyzing steps (advance_input=False) don't need to do anything.
        """
        if self.advance_input:
            self.advance_input(context)
```

---

## 4. Concrete Step Modifications

### 4.1 LasCheckStep

```python
class LasCheckStep(BaseStep):
    subfolder = "lascheck"
    advance_input = False  # Only analyzes, doesn't transform

    def __init__(self, advance_input: bool = False, input_path: str = ""):
        self.advance_input = advance_input
        self._custom_input_path = input_path  # Step-specific input_path (optional)

    def name(self) -> str:
        return "lascheck"

    def should_run(self, context: ExecutionContext) -> bool:
        path = self._custom_input_path or context.input_path
        return bool(path)

    def run_inline(self, context: ExecutionContext) -> dict:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        # ... process each file ...
        report_path = os.path.join(self.output_subdir(context), "check_report.json")
        return {"check_results": results, "report_path": report_path}
```

### 4.2 LasBlackFilterStep

```python
class LasBlackFilterStep(BaseStep):
    subfolder = "lasblackfilter"
    advance_input = True  # Transforms data

    def __init__(self, threshold: int = 0, save_black_points: bool = False, 
                 advance_input: bool = True, input_path: str = ""):
        self._threshold = threshold
        self._save_black_points = save_black_points
        self.advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "lasblackfilter"

    def create_task(self, context: ExecutionContext) -> LasBlackFilterTask:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        return LasBlackFilterTask(
            files=files,
            output_dir=self.output_subdir(context),
            threshold=self._threshold,
            save_black_points=self._save_black_points,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("filter_result", result)
        self.advance_input(context)
```

### 4.3 LasTilerStep

```python
class LasTilerStep(BaseStep):
    subfolder = "lastiler"
    advance_input = True

    def __init__(self, points_per_part: int = 5_000_000,
                 advance_input: bool = True, input_path: str = ""):
        self._points_per_part = points_per_part
        self.advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "lastiler"

    def create_task(self, context: ExecutionContext) -> LasTilerTask:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        return LasTilerTask(
            files=files,
            output_dir=self.output_subdir(context),
            points_per_part=self._points_per_part,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("split_result", result)
        self.advance_input(context)
```

### 4.4 IdwInterpolatorStep

```python
class IdwInterpolatorStep(BaseStep):
    subfolder = "idwtiles"
    advance_input = True

    def __init__(self, target_bands: dict = None, merge_bands: bool = True,
                 resolution_m: float = 0.01, idw_k: int = 5, idw_power: float = 2.0,
                 idw_max_radius: float = 0.5, idw_overlap: float = 3.0,
                 crs_str: str = "EPSG:31982", delete_tiles: bool = True,
                 save_las: bool = False,
                 advance_input: bool = True, input_path: str = ""):
        self._target_bands = target_bands or {}
        self._merge_bands = merge_bands
        self._resolution_m = resolution_m
        self._idw_k = idw_k
        self._idw_power = idw_power
        self._idw_max_radius = idw_max_radius
        self._idw_overlap = idw_overlap
        self._crs_str = crs_str
        self._delete_tiles = delete_tiles
        self._save_las = save_las
        self.advance_input = advance_input
        self._custom_input_path = input_path

    def name(self) -> str:
        return "idwtiles"

    def create_task(self, context: ExecutionContext) -> IdwInterpolatorTask:
        path = self._custom_input_path or context.input_path
        return IdwInterpolatorTask(
            input_dir=path,
            output_path=os.path.join(self.output_subdir(context), "merged.tif"),
            target_bands=self._target_bands,
            merge_bands=self._merge_bands,
            resolution_m=self._resolution_m,
            idw_k=self._idw_k,
            idw_power=self._idw_power,
            idw_max_radius=self._idw_max_radius,
            idw_overlap=self._idw_overlap,
            crs_str=self._crs_str,
            delete_tiles=self._delete_tiles,
            save_las=self._save_las,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("idw_result", result)
        self.advance_input(context)
```

---

## 5. AsyncPipelineEngine Modifications

### 5.1 Automatic _custom_input_path Injection

If the step has `_custom_input_path`, the engine uses that value instead of `context.input_path`:

```python
def _run_loop(self, blocking: bool) -> None:
    while self._is_running and not self._is_cancelled:
        step = self._steps[self._current_index]

        # If step has custom input_path, override in context
        custom_path = getattr(step, "_custom_input_path", None)
        if custom_path:
            self._context.input_path = custom_path

        # ... execute step ...
```

---

## 6. Canonical Variables

### 6.1 ExecutionContext Attributes

| Variable | Type | Origin | Description |
|----------|------|--------|-------------|
| `input_path` | `str` | Plugin / Previous step | Input directory with files |
| `output_path` | `str` | Plugin (config) | Base directory to save results |
| `files` | `list[str] \| None` | Plugin | Specific file list (None = all) |
| `tool_key` | `str` | Plugin | ToolKey for logging |

### 6.2 Step Attributes (defined in each concrete step)

| Attribute | Type | Where defined | Description |
|-----------|------|---------------|-------------|
| `subfolder` | `str` | Step constant | Output subfolder name |
| `advance_input` | `bool` | Step constructor | If True, calls advance_input() |
| `_custom_input_path` | `str` | Constructor (optional) | Step-specific input_path |

### 6.3 Step-Specific Parameters

| Step | Parameters (passed in constructor) |
|------|-------------------------------------|
| `LasCheckStep` | `advance_input=False`, `input_path=""` |
| `LasBlackFilterStep` | `threshold: int=0`, `save_black_points: bool=False`, `advance_input=True`, `input_path=""` |
| `LasTilerStep` | `points_per_part: int=5_000_000`, `advance_input=True`, `input_path=""` |
| `IdwInterpolatorStep` | `target_bands: dict`, `merge_bands: bool=True`, `resolution_m: float=0.01`, `idw_k: int=5`, `idw_power: float=2.0`, `idw_max_radius: float=0.5`, `idw_overlap: float=3.0`, `crs_str: str="EPSG:31982"`, `delete_tiles: bool=True`, `save_las: bool=False`, `advance_input=True`, `input_path=""` |

---

## 7. Complete Pipeline Example

```python
runner = PipelineRunner(
    steps=[
        LasCheckStep(advance_input=False),                    # Analyzes → /output/lascheck/
        LasBlackFilterStep(threshold=30, save_black_points=True), # Filters → /output/lasblackfilter/ → advance
        LasCheckStep(advance_input=False),                    # Re-analyzes filtered
        LasTilerStep(points_per_part=5_000_000),              # Tiles → /output/lastiler/ → advance
        IdwInterpolatorStep(                                  # Interpolates → /output/idwtiles/ → advance
            target_bands={"r": True, "g": True, "b": True, "z": True},
            resolution_m=0.01,
        ),
    ],
    context={
        "input_path": "D:/data/root",
        "output_path": "D:/data/root",
        "tool_key": ToolKey.IDW_INTERPOLATOR.value,
    },
    parent=self,
)
```

### Example with Specific input_path

```python
runner = PipelineRunner(
    steps=[
        LasBlackFilterStep(threshold=30),
        LasTilerStep(points_per_part=5_000_000),
        IdwInterpolatorStep(target_bands={"r": True, "g": True, "b": True}),
        LasCheckStep(advance_input=False, input_path="D:/data/root/lasblackfilter/"),
    ],
    context={
        "input_path": "D:/data/root",
        "output_path": "D:/data/root",
        "tool_key": ToolKey.IDW_INTERPOLATOR.value,
    },
    parent=self,
)
```

---

## 8. Implementation Order

### Phase 1 — ExecutionContext (core)
- [ ] 1.1 Add class variables: `input_path`, `output_path`, `files`, `tool_key`
- [ ] 1.2 Sync `__init__` to populate variables from initial dict
- [ ] 1.3 Keep `get()`/`set()` for legacy compatibility
- [ ] 1.4 Remove class variables `INPUT_PATH`, `OUTPUT_PATH`, `TOOL_KEY`

### Phase 2 — BaseStep (core)
- [ ] 2.1 Add attribute `subfolder: str = ""`
- [ ] 2.2 Add attribute `advance_input: bool = True`
- [ ] 2.3 Add method `advance_input(context)`
- [ ] 2.4 Add method `resolve_files(context, *extensions)`
- [ ] 2.5 Add method `output_subdir(context)`
- [ ] 2.6 Modify default `on_success()` to call `advance_input()` if `advance_input == True`

### Phase 3 — AsyncPipelineEngine
- [ ] 3.1 Check `_custom_input_path` in step and override `context.input_path` if present

### Phase 4 — Steps (refactor one by one)
- [x] 4.1 `LasCheckStep` → add `subfolder`, `advance_input=False`, `__init__` with parameters
- [x] 4.2 `LasBlackFilterStep` → add `subfolder`, `__init__` with exclusive parameters
- [x] 4.3 `LasTilerStep` → add `subfolder`, `__init__` with exclusive parameters
- [x] 4.4 `IdwInterpolatorStep` → add `subfolder`, `__init__` with exclusive parameters
- [ ] 4.5 `MrkSteps` → keep compatibility (don't use LAS pipeline)

---

## 9. New/Updated Contracts

### Contract 27 — ExecutionContext Canonical Attributes
```
ExecutionContext has class variables for direct access:
- input_path, output_path, files, tool_key

NEVER use @property or getters/setters for these attributes.
Direct access: context.input_path = "/path"
```

### Contract 28 — Exclusive Parameters in Step Constructor
```
Step-specific parameters are passed DIRECTLY in the constructor:
    LasBlackFilterStep(threshold=30, save_black_points=True)

NEVER mix exclusive parameters in ExecutionContext.
Context contains ONLY: input_path, output_path, files, tool_key.
```

### Contract 29 — advance_input (Transform vs Analyze)
```
Every step defines advance_input:
- True (default): step TRANSFORMS data → advance_input() in on_success()
- False: step only ANALYZES → does NOT advance input_path

Transforming steps: LasBlackFilter, LasTiler, IdwInterpolator
Analyzing steps: LasCheck
```

### Contract 30 — subfolder Constant in Step
```
Each step defines subfolder as a class constant:
    subfolder = "lascheck"  # Output subfolder name

output_subdir is derived automatically: output_path + "/" + subfolder
```

### Contract 31 — Step-Specific input_path (Exception)
```
A step can receive its own input_path in the constructor for specific cases:
    LasCheckStep(advance_input=False, input_path="D:/data/root/lasblackfilter/")

This overrides context.input_path ONLY for that step.
Use sparingly — the standard is to use context.input_path.
```

---

## 10. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing plugins | Keep `get()`/`set()` as fallback; migrate gradually |
| Steps expecting single file vs directory | `resolve_files()` returns list; step decides if processing 1 or N |
| Compatibility with MrkSteps/DoclingSteps | Don't use `subfolder`/`advance_input`; keep `get()`/`set()` |
| User forgetting required parameter | Constructor has sensible defaults; validation in `should_run()` |