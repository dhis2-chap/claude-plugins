# Config and runner snippets

Shapes taken from working chap-models services on chapkit 2.0.x. Check the
installed chapkit before copying - imports and field names can move between
minor versions.

## The Config class

```python
from typing import cast

from chapkit import BaseConfig
from pydantic import Field, HttpUrl, model_validator


class MyModelConfig(BaseConfig):
    """Tunables for a single train/predict run - the MLproject `user_options` block."""

    # BaseConfig declares prediction_periods with NO default and chap-core never
    # sends it, so without this every chap-core config POST is a 422.
    prediction_periods: int = Field(default=3, description="Number of periods to predict into the future")

    # One field per surviving MLproject user_option, same default, MLproject title
    # as the description (it is what /api/v1/configs/$schema shows an operator).
    n_samples: int = Field(default=100, description="Number of probabilistic samples")
    log_transform: bool = Field(default=True, description="Fit on log1p(disease_cases)")
    random_seed: int = Field(default=42, description="Random seed for sampling")

    # Hyphenated legacy key that the script reads verbatim:
    # n_lags: int = Field(default=3, alias="n-lags", description="Number of lags")

    # Reserved BaseConfig field - override the default rather than redeclaring:
    # additional_continuous_covariates: list[str] = Field(
    #     default_factory=lambda: ["rainfall", "mean_temperature"], description="..."
    # )

    @model_validator(mode="before")
    @classmethod
    def _hoist_user_option_values(cls, data: object) -> object:
        """Accept chap-core's nested `user_option_values` payload as flat fields.

        chap-core posts `{"name": ..., "user_option_values": {...}}`. BaseConfig sets
        extra="allow", so without this hook the dict is stored verbatim as an unknown
        extra field, every declared tunable keeps its default, and
        dump_config_yaml(..., "chap_core") then emits
        `user_option_values: {user_option_values: {...}, n_samples: 100}` - the script
        reads the defaults and silently ignores what was requested.

        setdefault means flat keys win over nested ones, so `chapkit test` (flat) and
        chap-core (nested) land on the same object.
        """
        if not isinstance(data, dict):
            return data
        payload = cast(dict[str, object], data)
        nested = payload.get("user_option_values")
        if not isinstance(nested, dict):
            return payload
        hoisted: dict[str, object] = {k: v for k, v in payload.items() if k != "user_option_values"}
        for key, value in cast(dict[str, object], nested).items():
            hoisted.setdefault(key, value)
        return hoisted
```

Verify by hand before trusting it:

```python
MyModelConfig.model_validate({"name": "x", "user_option_values": {"n_samples": 7}}).n_samples   # 7
MyModelConfig.model_validate({"n_samples": 3, "user_option_values": {"n_samples": 7}}).n_samples  # 3
dump_config_yaml(cfg, "chap_core")   # user_option_values.n_samples: 7, no double nesting
```

## ShellModelRunner - Python

```python
from chapkit.ml import ShellModelRunner

runner: ShellModelRunner[MyModelConfig] = ShellModelRunner(
    train_command="python -m my_package train {data_file} model.json config.yml",
    predict_command=(
        "python -m my_package predict model.json {historic_file} {future_file} {output_file} config.yml"
    ),
    config_format="chap_core",
)
```

- `{data_file}` -> `data.csv`, `{historic_file}` -> `historic.csv`,
  `{future_file}` -> `future.csv`, `{output_file}` -> `predictions.csv`, all
  workspace-relative.
- `model.json` and `config.yml` are literal filenames: chapkit always writes
  `config.yml` into the workspace, and the whole train workspace (including
  whatever train wrote) is zipped, stored as the `ml_training_workspace`
  artifact, and restored into the predict workspace.
- `python -m <package>` rather than a console script: chapkit runs the command
  with the workspace as `cwd`, and `cwd` is on `sys.path`, so the copied package
  resolves without the project being installed into the workspace. `python`
  resolves to the venv interpreter locally (`uv run ...` puts `.venv/bin` on
  `PATH`) and in the image (`/app/.venv/bin`).
- `config_format="chap_core"` nests the tunables under `user_option_values:`,
  which is what existing chap-models scripts already read - often meaning the
  legacy script needs no edits at all.

## ShellModelRunner - R

```python
runner: ShellModelRunner[MyModelConfig] = ShellModelRunner(
    train_command="Rscript scripts/train.R --data {data_file}",
    predict_command=(
        "Rscript scripts/predict.R --historic {historic_file} --future {future_file} --output {output_file}"
    ),
    config_format="chap_core",
)
```

R side:

- Parse named flags off `commandArgs(trailingOnly = TRUE)`; fall back to the
  conventional filenames (`data.csv`, `historic.csv`, `future.csv`,
  `predictions.csv`) when a flag is absent. The flag names must match the
  placeholders in the command string.
- `library(yaml); config <- yaml.load_file("config.yml")`, then
  `config$user_option_values$<name>` under `chap_core` format. Guard with
  `file.exists()` and supply defaults.
- `read.csv(...)` for the frames; add `disease_cases <- NA` to the future frame
  when the column is absent.
- chapkit has **no** MLflow-style `adapters:` map. Port those renames into an
  `apply_adapters()` helper in the script (copy, do not rename, so both column
  sets coexist).
- Save the model with `saveRDS(model, "model.rds")` in train; `readRDS` it in
  predict. If the legacy model fits at predict time, train can legitimately be a
  validate-and-touch-a-marker no-op.
- Write predictions with
  `colnames(out) <- c("time_period", "location", paste0("sample_", 0:(s - 1)))`
  and `write.csv(out, preds_fn, row.names = FALSE)`.
- `source("scripts/lib.R")` - relative to the project root, not the script.

## FunctionalModelRunner - Python, in process

```python
from chapkit.data import DataFrame as ChapDataFrame
from chapkit.ml import FunctionalModelRunner
from geojson_pydantic import FeatureCollection


async def on_train(
    config: MyModelConfig,
    data: ChapDataFrame,
    geo: FeatureCollection | None = None,
) -> Any:                                   # any pickleable object
    df = data.to_pandas()
    return fit_model(df, config)


async def on_predict(
    config: MyModelConfig,
    model: Any,                             # exactly what on_train returned
    historic: ChapDataFrame,
    future: ChapDataFrame,
    geo: FeatureCollection | None = None,
) -> ChapDataFrame:
    predictions = model.predict(historic.to_pandas(), future.to_pandas(), config)
    return ChapDataFrame.from_pandas(predictions)


runner: FunctionalModelRunner[MyModelConfig] = FunctionalModelRunner(
    on_train=on_train,
    on_predict=on_predict,
    # on_validate_train=..., on_validate_predict=...   # optional $validate hooks
)
```

`chapkit.data.DataFrame` is a Pydantic schema, not pandas: `.to_pandas()` in,
`.from_pandas()` out. chapkit pickles the returned model itself - no paths, no
`pickle.dump` in your code. The returned frame needs `time_period`, `location`
and a contiguous `sample_0 .. sample_N` block.

## Service info and the builder tail

```python
import os
from pathlib import Path

from chapkit.api import AssessedStatus, MLServiceBuilder, MLServiceInfo, ModelMetadata, PeriodType
from chapkit.artifact import ArtifactHierarchy

info = MLServiceInfo(
    id="chap-my-model",                       # stable slug; the registration identity
    display_name="My Model",
    version="0.2.0",                          # keep in step with pyproject
    description="...",                        # from MLproject meta_data.description
    model_metadata=ModelMetadata(
        author="...",
        author_note="...",                    # MLproject meta_data.author_note
        author_assessed_status=AssessedStatus.yellow,
        contact_email="...",
        organization="HISP Centre, University of Oslo",
        organization_logo_url=HttpUrl("https://..."),  # HttpUrl, not str: a bare string fails basedpyright
        citation_info="...",
    ),
    period_type=PeriodType.any,               # MLproject supported_period_type
    min_prediction_periods=1,
    max_prediction_periods=104,               # justify this number in a comment
    allow_free_additional_continuous_covariates=False,
    required_covariates=[],                   # every column the scripts index by name
)

hierarchy = ArtifactHierarchy(
    name="my_model",
    level_labels={0: "ml_training_workspace", 1: "ml_prediction"},
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/chapkit.db")
if DATABASE_URL.startswith("sqlite") and ":///" in DATABASE_URL:
    db_path = Path(DATABASE_URL.split("///")[1])
    db_path.parent.mkdir(parents=True, exist_ok=True)

app = (
    MLServiceBuilder(
        info=info,
        config_schema=MyModelConfig,
        hierarchy=hierarchy,
        runner=runner,
        database_url=DATABASE_URL,
    )
    .with_monitoring()                        # /metrics
    # No-op unless SERVICEKIT_ORCHESTRATOR_URL is set; see compose.yml.
    .with_registration(keepalive_interval=15)
    .build()
)


if __name__ == "__main__":
    from chapkit.api import run_app

    # Port 9090 matches the compose host port and avoids the usual busy ports.
    run_app("main:app", reload=False, port=9090)
```

The `DATABASE_URL` block must run at module import time - the test suite sets
the env var before importing `main` and relies on that ordering.

## Dockerfile deltas

Start from the scaffold (`chapkit init --template shell-py` or the migrate
template) and change only what the model needs:

```dockerfile
FROM ghcr.io/dhis2-chap/chapkit-py:latest     # Python 3.13 + uv
# R instead: chapkit-r / chapkit-r-tidyverse / chapkit-r-inla
# INLA is amd64-only: FROM --platform=linux/amd64 ...

USER root
RUN id -u chapkit >/dev/null 2>&1 \
    || (groupadd --gid 1000 chapkit && useradd --uid 1000 --gid 1000 --no-create-home --shell /usr/sbin/nologin chapkit)

WORKDIR /work
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/app/.venv uv sync --frozen --no-dev --no-install-project

ARG GIT_REVISION=""
ENV GIT_REVISION=${GIT_REVISION}

# The scaffold copies scripts/. A package entry point copies the package instead:
COPY main.py ./
COPY my_package/ ./my_package/

RUN mkdir -p /work/data && chown -R chapkit:chapkit /work/data
# Writable paths only under /work/data (SQLite volume) and /tmp (workspaces).
# NUMBA_CACHE_DIR matters for any numba-backed stack: the JIT cache is otherwise
# written next to the installed package, which fails under read_only: true.
ENV HOME=/tmp \
    MPLCONFIGDIR=/tmp \
    XDG_CACHE_HOME=/tmp/.cache \
    NUMBA_CACHE_DIR=/tmp/numba_cache
USER chapkit

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`--no-install-project` is correct when the project is served as a script tree
rather than installed: the runner copies `/work` into the workspace and runs
there.

`.dockerignore`: the scaffold list plus `example_data/`, `tests/`, `docs/`,
`scripts/` when they are not needed at runtime - smaller `/work` means a smaller
per-job workspace copy.

`compose.yml`: host `9090` -> container `8000`, `init: true`, `read_only: true`,
`no-new-privileges`, `cap_drop: ALL`, `user: chapkit:chapkit`, a named volume at
`/work/data`, a tmpfs at `/tmp`, and the registration env vars commented out
with the literal `$$register` escaping.

Worked examples:
https://github.com/chap-models/mstl_arima (ShellModelRunner, Python),
https://github.com/chap-models/chapkit_ewars_model (ShellModelRunner, R/INLA),
https://github.com/chap-models/chapkit_simple_multistep_model (FunctionalModelRunner).
