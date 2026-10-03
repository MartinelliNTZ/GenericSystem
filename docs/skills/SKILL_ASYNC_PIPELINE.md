# Skill: Async Pipeline System (AsyncPipeline)

This skill documents the async pipeline system implemented in `core/papeline/`, describing its architecture, components, and how to create new pipelines.

---

## 📋 Overview

The system implements a **sequential async pipeline** composed of steps (`Steps`) executed one after another. Each step can execute heavy work in background and, upon completion, fires success/error callbacks that advance to the next step.

```
start → step 1 → async task → success callback → step 2 → ... → finish
```

## 🧱 Architecture

```
core/papeline/
├── __init__.py               — Public exports
├── ExecutionContext.py        — Shared state between steps (direct attribute access)
├── BaseTask.py                — Abstract wrapper for background work
├── BaseStep.py                — Abstract contract for pipeline steps
├── AsyncPipelineEngine.py     — Orchestrator (blocking thread.join)
├── PipelineRunner.py          — Executes pipeline in QThread (non-blocking)
├── ParallelStep.py            — Executes multiple substeps in parallel
├── step/
│   ├── __init__.py            — Exports concrete steps
│   ├── LasCheckStep.py        — Quality checks on LAS/LAZ files
│   ├── LasBlackFilterSteps.py — Black point filter (LasBlackFilterStep)
│   ├── LasTilerStep.py        — Split LAS/LAZ into parts
│   ├── IdwInterpolatorStep.py — IDW interpolation of LAS files
│   ├── MrkSteps.py            — MRK processing steps
│   └── DoclingSteps.py        — Docling document conversion steps
└── task/
    ├── __init__.py            — Exports concrete tasks
    ├── LasBlackFilterTask.py  — Task for black point filtering
    ├── LasTilerTask.py        — Task for splitting LAS files
    ├── IdwInterpolatorTask.py — Task for IDW interpolation
    ├── MrkSinglePipelineTask.py — Task for MRK processing
    └── DoclingPipelineTask.py   — Task for document conversion
```

---

## 📦 Components

### `ExecutionContext` — `core/papeline/ExecutionContext.py`

Shared state container between all pipeline steps.

**Access is via DIRECT ATTRIBUTES only — NO dict methods:**

```python
from core.papeline import ExecutionContext

# Create with keyword arguments (preferred)
ctx = ExecutionContext(
    input_path="D:/data/root",
    output_path="D:/data/root",
    tool_key="my_tool",
)

# Direct attribute access
ctx.input_path = "/new/path"
ctx.output_path = "/output/path"
ctx.tool_key = "my_tool"
ctx.files = ["file1.las", "file2.las"]  # None = all in input_path

# Step results storage
ctx.set_result("split_result", {"n_parts": 5, ...})
result = ctx.get_result("split_result", default={})

# Error handling
ctx.add_error(ValueError("something wrong"))
if ctx.has_errors():
    for err in ctx.errors:
        print(err)

# Cancellation
ctx.cancel()
if ctx.is_cancelled:
    ...

# Reset
ctx.clear()
```

**Canonical Attributes:**

| Attribute | Type | Origin | Description |
|-----------|------|--------|-------------|
| `input_path` | `str` | Plugin / Previous step | Input directory with files to process |
| `output_path` | `str` | Plugin (config) | Base directory to save results |
| `files` | `list[str] \| None` | Plugin | Specific file list (None = all in input_path) |
| `tool_key` | `str` | Plugin | ToolKey for logging |
| `errors` | `list[Exception]` | Auto | Error accumulator |
| `is_cancelled` | `bool` | Auto | Cancellation flag |
| `results` | `dict` | Steps | Step results storage |

> ⚠️ **NEVER** use `context.get()` or `context.set()`. These methods DON'T exist in the new system.

---

### `BaseTask` — `core/papeline/BaseTask.py`

Abstract class for executing heavy work in background.

```python
from core.papeline import BaseTask

class MyTask(BaseTask):
    def __init__(self, data: str):
        super().__init__(description=f"Process: {data}")
        self._data = data

    def _run(self) -> bool:
        # Heavy logic here
        result = self._data.upper()
        self.result = {"original": self._data, "upper": result}
        return True  # False if failed
```

**Attributes:**

| Attribute | Type | Description |
|----------|------|-------------|
| `description` | `str` | Description for logs |
| `exception` | `Exception \| None` | Caught exception |
| `result` | `Any` | Produced result |
| `on_success` | `callable \| None` | Success callback |
| `on_error` | `callable \| None` | Error callback |
| `is_cancelled` | `bool` | True if cancelled |

**Internal flow:**
1. `run()` is called
2. `run()` calls `_run()` (real logic)
3. If `_run()` throws exception → caught in `self.exception`, returns `False`
4. If `_run()` returns `True` → `self.result` contains the result
5. `finished(success)` is called after completion
6. `success=True` → fires `on_success(self.result)`
7. `success=False` → fires `on_error(self.exception)`

> ⚠️ **Important:** BaseTask is NOT QThread. To execute in thread without freezing UI, use `PipelineRunner`.

---

### `BaseStep` — `core/papeline/BaseStep.py`

Abstract contract that defines a pipeline step. Now with **flow control attributes**:

```python
from core.papeline import BaseStep, ExecutionContext, BaseTask

class MyStep(BaseStep):
    subfolder = "mystep"        # Output subfolder name
    advance_input = True        # If True, automatically advances input_path

    def __init__(self, my_param: int = 10, advance_input: bool = True, input_path: str = ""):
        self._my_param = my_param
        self.advance_input = advance_input
        self._custom_input_path = input_path  # Optional custom input_path

    def name(self) -> str:
        return "mystep"

    def should_run(self, context: ExecutionContext) -> bool:
        path = self._custom_input_path or context.input_path
        return bool(path)

    def create_task(self, context: ExecutionContext) -> BaseTask | None:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        return MyTask(files=files, param=self._my_param)

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set_result("my_result", result)
        self.advance_input(context)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)
```

**New BaseStep Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `subfolder` | `str` | `""` | Output subfolder name (e.g. 'lascheck', 'lasblackfilter') |
| `advance_input` | `bool` | `True` | If True, calls advance_input() in on_success() |

**New BaseStep Methods:**

| Method | Return | Description |
|--------|--------|-------------|
| `advance_input(context)` | `None` | Updates `context.input_path` to point to step's output subfolder |
| `resolve_files(context, *extensions)` | `list[str]` | Returns files from `context.files` or lists directory |
| `output_subdir(context)` | `str` | Returns `output_path/subfolder/`, creates if not exists |

**Required Methods:**

| Method | Required | Description |
|--------|----------|-------------|
| `name()` | ✅ | Unique identifier |
| `create_task(context)` | ✅ | Creates `BaseTask \| None` |
| `on_success(context, result)` | ✅ | Success callback (default: calls advance_input if advance_input==True) |

**Optional Methods:**

| Method | Required | Description |
|--------|----------|-------------|
| `should_run(context)` | ❌ | If `False`, step is skipped |
| `on_error(context, exception)` | ❌ | Error handling |
| `rollback(context)` | ❌ | Undo changes |
| `run_inline(context)` | ❌ | Synchronous execution |

---

### `PipelineRunner` — `core/papeline/PipelineRunner.py`

Executes N steps sequentially in a QThread, without freezing the UI. **This is what plugins use.**

```python
from core.papeline import PipelineRunner
from core.papeline.step.LasTilerStep import LasTilerStep

runner = PipelineRunner(
    steps=[LasTilerStep(points_per_part=5_000_000)],
    input_path="D:/data/root",
    output_path="D:/data/root",
    tool_key="my_tool",
    parent=self,
)
runner.finished_ok.connect(self._on_done)
runner.failed.connect(self._on_error)
runner.start()
```

**Signals (Qt):**

| Signal | Type | Description |
|--------|------|-------------|
| `finished_ok` | `Signal(object)` | ExecutionContext on successful completion |
| `failed` | `Signal(str)` | Error message |

> The `PipelineRunner` creates an internal `ResourceGovernor` with GLOBAL 90% policy automatically.

---

## 🧠 ResourceGovernor — Resource Governance

The `ResourceGovernor` is a RAM memory governance system integrated into the pipeline to prevent OOM (Out Of Memory).

### Architecture

```
core/governor/
├── RamGovernor.py              — Monitors RAM (system, process) via psutil
├── RamLimitPolicy.py           — Limit strategies (GLOBAL 90%, DEDICATED 50%)
└── ResourceGovernor.py         — Orchestrator: can_execute(), recommended_tile_size()
```

### How it works (transparent to plugin)

The `PipelineRunner` **creates a ResourceGovernor automatically**.
**The plugin, step and task don't need to know about the governor's existence.**

```python
from core.papeline import PipelineRunner

# The runner already creates the governor internally — plugin does nothing
runner = PipelineRunner(
    steps=[MyStep()],
    input_path="D:/data",
    output_path="D:/data",
    parent=self,
)
runner.finished_ok.connect(self._on_done)
runner.failed.connect(self._on_error)
runner.start()
```

### Where the governor acts (totally transparent)

1. **`PipelineRunner.run()`** — creates `ResourceGovernor` with `GLOBAL 90%` policy
2. **`AsyncPipelineEngine._run_loop()`** — before each task, checks `governor.can_execute()`
3. **`BaseTask.run()`** — checks governor before executing `_run()`

---

## 🔄 Step Flow Convention (advance_input)

Steps now follow a **flow convention** with `subfolder` and `advance_input`:

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
  → advance_input: context.input_path = /data/root/lasblackfilter/

Step 3 (LasTiler, advance_input=True):
  → Reads: input_path (= /data/root/lasblackfilter/)
  → Saves tiles to: output_path/lastiler/
  → advance_input: context.input_path = /data/root/lastiler/

Step 4 (IdwInterpolator, advance_input=True):
  → Reads: input_path (= /data/root/lastiler/)
  → Saves rasters to: output_path/idwtiles/
  → advance_input: context.input_path = /data/root/idwtiles/
```

**Order can be inverted** — each step knows where to read from and where to save to. The pipeline works regardless of step order.

### Steps that TRANSFORM vs Steps that ANALYZE

| Type | advance_input | Examples | Behavior |
|------|---------------|----------|----------|
| **Transform** | `True` (default) | LasBlackFilter, LasTiler, IdwInterpolator | Calls `advance_input()` → next step uses output folder |
| **Analyze** | `False` | LasCheck | Does NOT call `advance_input()` → next step uses same folder |

### Step-Specific input_path (Exception)

A step can receive its own `input_path` in the constructor for specific cases:

```python
LasCheckStep(
    advance_input=False,
    input_path="D:/data/root/lasblackfilter/",  # Overrides context.input_path
)
```

This overrides `context.input_path` ONLY for that step.

---

## 🎯 Complete Pipeline Examples

### Standard Pipeline (recommended)

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
    input_path="D:/data/root",
    output_path="D:/data/root",
    tool_key=ToolKey.IDW_INTERPOLATOR.value,
    parent=self,
)
runner.finished_ok.connect(self._on_done)
runner.failed.connect(self._on_error)
runner.start()
```

### Pipeline with Step-Specific input_path

```python
runner = PipelineRunner(
    steps=[
        LasBlackFilterStep(threshold=30),
        LasTilerStep(points_per_part=5_000_000),
        IdwInterpolatorStep(target_bands={"r": True, "g": True, "b": True}),
        LasCheckStep(advance_input=False, input_path="D:/data/root/lasblackfilter/"),
    ],
    input_path="D:/data/root",
    output_path="D:/data/root",
    parent=self,
)
```

---

## 📝 Step-Specific Parameters

Parameters are passed **DIRECTLY in the step constructor**, NOT in the context:

| Step | Constructor Parameters |
|------|------------------------|
| `LasCheckStep` | `advance_input=False`, `input_path=""` |
| `LasBlackFilterStep` | `threshold: int=0`, `save_black_points: bool=False`, `advance_input=True`, `input_path=""` |
| `LasTilerStep` | `points_per_part: int=5_000_000`, `advance_input=True`, `input_path=""` |
| `IdwInterpolatorStep` | `target_bands: dict`, `merge_bands: bool=True`, `resolution_m: float=0.01`, `idw_k: int=5`, `idw_power: float=2.0`, `idw_max_radius: float=0.5`, `idw_overlap: float=3.0`, `crs_str: str="EPSG:31982"`, `delete_tiles: bool=True`, `save_las: bool=False`, `advance_input=True`, `input_path=""` |
| `DoclingConvertStep` | `columnar: bool=False`, `manual_columns: int=0` |
| `MrkProcessStep` | (reads from context.results) |

---

## 🔧 Concrete Tasks

### `LasBlackFilterTask`

```python
from core.papeline.task import LasBlackFilterTask

task = LasBlackFilterTask(
    files=["file1.las", "file2.las"],
    output_dir="filtered/",
    threshold=30,
    save_black_points=True,
)
```

### `LasTilerTask`

```python
from core.papeline.task import LasTilerTask

task = LasTilerTask(
    files=["file1.las", "file2.las"],
    output_dir="tiles/",
    points_per_part=5_000_000,
)
```

### `IdwInterpolatorTask`

```python
from core.papeline.task import IdwInterpolatorTask

task = IdwInterpolatorTask(
    input_dir="path/to/las/files",
    output_path="output/raster.tif",
    target_bands={"r": True, "g": True, "b": True, "z": True},
    resolution_m=0.01,
)
```

### `MrkSinglePipelineTask`

```python
from core.papeline.task import MrkSinglePipelineTask

task = MrkSinglePipelineTask(
    mrk_path="data/file.mrk",
    data_path="data/file.gpkg",
    mapping={"Lat": "Lat", "Lon": "Lon", "Ellh": "Ellh"},
    output_dir="output/",
)
```

### `DoclingPipelineTask`

```python
from core.papeline.task import DoclingPipelineTask

task = DoclingPipelineTask(
    file_path="document.pdf",
    columnar=True,
    manual_columns=0,
)
```

---

## ✅ Step Writing Rules

### Rule 1: Step-Specific params go in the constructor

```python
# ✅ CORRECT
class MyStep(BaseStep):
    def __init__(self, threshold: int = 0, advance_input: bool = True, input_path: str = ""):
        self._threshold = threshold
        self.advance_input = advance_input
        self._custom_input_path = input_path

# ❌ WRONG — don't get params from context
class MyStep(BaseStep):
    def create_task(self, context):
        threshold = context.results.get("threshold", 0)  # NO!
```

### Rule 2: Use resolve_files() for file listing

```python
# ✅ CORRECT
def create_task(self, context):
    path = self._custom_input_path or context.input_path
    files = self.resolve_files(context, ".las", ".laz")
    return MyTask(files=files, ...)

# ❌ WRONG — manual glob
def create_task(self, context):
    files = glob.glob(os.path.join(context.input_path, "*.las"))  # NO!
```

### Rule 3: Use output_subdir() for output paths

```python
# ✅ CORRECT
def create_task(self, context):
    output = self.output_subdir(context)
    return MyTask(output_dir=output, ...)

# ❌ WRONG — manual path construction
def create_task(self, context):
    output = os.path.join(context.output_path, "mystep")  # NO!
```

### Rule 4: Transform steps call advance_input, analyze steps don't

```python
# ✅ CORRECT — Transform step
class MyTransformStep(BaseStep):
    subfolder = "mytransform"
    advance_input = True

    def on_success(self, context, result):
        context.set_result("my_result", result)
        self.advance_input(context)  # Next step uses mytransform/ folder

# ✅ CORRECT — Analyze step
class MyAnalyzeStep(BaseStep):
    subfolder = "myanalyze"
    advance_input = False

    def on_success(self, context, result):
        context.set_result("my_analysis", result)
        # No advance_input — next step uses same folder
```

### Rule 5: Use context.set_result() / context.get_result() for results

```python
# ✅ CORRECT
context.set_result("my_key", {"data": 42})
data = context.get_result("my_key", {})

# ❌ WRONG — no get/set methods
context["my_key"] = 42  # NO!
context.get("my_key")    # NO!
```

### Rule 6: Use get_logger(context)

```python
# ✅ CORRECT — gets tool_key from context automatically
class MyStep(BaseStep):
    def should_run(self, context):
        logger = self.get_logger(context)
        logger.info("Checking...", code="MY_CHECK")
```

---

## ✅ Checklist for Creating a New Pipeline

- [ ] Created tasks in `core/papeline/task/` inheriting from `BaseTask`?
- [ ] Created steps in `core/papeline/step/` inheriting from `BaseStep`?
- [ ] Step has `subfolder` class attribute defined?
- [ ] Step has `advance_input` defined (True for transform, False for analyze)?
- [ ] Step constructor accepts step-specific params + `advance_input` + `input_path`?
- [ ] Task receives named parameters (NOT dict)?
- [ ] Step uses `get_logger(context)` (NOT own logger)?
- [ ] Step uses `resolve_files()` for file listing?
- [ ] Step uses `output_subdir()` for output paths?
- [ ] Step uses `context.set_result()` / `context.get_result()`?
- [ ] Transform steps call `advance_input()` in `on_success()`?
- [ ] Step does NOT know which step comes before or after?
- [ ] Updated `__init__.py` in `step/` and/or `task/`?

---

## 🔗 References

- Standardization plan: `docs/plans/PLAN_PADRONIZACAO_EXECUTION_CONTEXT.md`
- System contracts: `docs/skills/SKILL_PLUGIN_CONTRACT.md`
- Step catalog: `core/papeline/step/__init__.py`
- Task catalog: `core/papeline/task/__init__.py`