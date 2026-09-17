# Gotchas

Every item here was hit or verified on a real conversion. Read the whole file
before writing code - most of these are silent, and the expensive ones produce a
service that answers 200 with wrong numbers.

Legend: **[mstl]** = observed on the `chap-models/mstl_arima` MLproject ->
chapkit conversion; **[ewars]** = the R/INLA reference; **[multistep]** = the
`FunctionalModelRunner` reference; **[docs]** = stated in the chapkit guides.

## Config and the chap-core contract

| Symptom | Cause | Fix |
|---|---|---|
| Every chap-core config POST is a `422`, but `chapkit test` works | `BaseConfig` declares `prediction_periods: int` with **no default**, and chap-core never sends it (it carries the horizon in the future frame) | Declare `prediction_periods: int = Field(default=3, description=...)` on your Config subclass. **[mstl] [multistep]** |
| Service answers 200, jobs succeed, numbers are the defaults - the requested tunables were ignored | chap-core posts `{"name": ..., "user_option_values": {...}}`. `BaseConfig` has `extra="allow"`, so the nested dict is stored verbatim as an unknown extra, every declared field keeps its default, and `dump_config_yaml(..., "chap_core")` then emits `user_option_values: {user_option_values: {...}, n_samples: <default>}` | Add a `@model_validator(mode="before")` that hoists `user_option_values` keys to the top level with `setdefault` (flat keys win), **and** use `ShellModelRunner(config_format="chap_core")`. See `config-and-runner-snippets.md`. This is the failure a smoke test will not catch and a parity test will. **[mstl]** |
| Script reads only defaults out of `config.yml` | `config_format` mismatch: the default `"flat"` writes every tunable at the top level, but chap-models scripts read `config["user_option_values"][...]` / `config$user_option_values$...` | `config_format="chap_core"` for any migrated repo. `"flat"` is for greenfield `chapkit init` projects. **[docs]** |
| `KeyError: '<name>'` reading `config.yml` | A `user_options` entry was never declared on the Config class, so it is not in the emitted YAML | Add the typed field. **[docs]** |
| YAML key does not match what the script expects (`n-lags` vs `n_lags`) | Python attribute names cannot be hyphenated | `n_lags: int = Field(default=3, alias="n-lags")`; chapkit serialises with `by_alias=True`. **[docs]** |
| `run_info.prediction_length` has no effect | chapkit does not feed it to the runner; the horizon is whatever the future frame contains | Ignore it. Use `prediction_periods` for anything the script needs, and let row count drive the horizon. **[mstl]** |
| Removing a config field turns every stored chap-core configuration into a 422 | A strict Config class | Keep `BaseConfig`'s `extra="allow"` and the script's own unknown-key filter (`ModelConfig.from_user_options`-style). Test the whole path: HTTP body -> stored config -> `dump_config_yaml` -> the model's config object. **[mstl]** |

## Data, runners and the prediction contract

| Symptom | Cause | Fix |
|---|---|---|
| `AttributeError: 'DataFrame' object has no attribute 'sort_values'` on the first training job | `chapkit.data.DataFrame` is a Pydantic schema, not pandas | `.to_pandas()` on the way in, `ChapDataFrame.from_pandas(df)` on the way out. `FunctionalModelRunner` only. **[multistep]** |
| Missing values arrive as `None`, not `NaN` | `NaN` is not valid JSON | Convert on both sides: `None if isinstance(v, float) and np.isnan(v) else v` when posting; expect `None` when reading. `future_data.csv` usually has no `disease_cases` column at all, or has it all-null. **[mstl] [multistep]** |
| chap-core rejects or misaligns the predictions | The output contract is not met | `predictions.csv` (or the returned frame) must have `time_period`, `location`, and a **contiguous** `sample_0 .. sample_N` block, all finite. A deterministic model emits `sample_0` only. Row order must equal the future frame's row order - chap-core matches positionally. **[docs] [mstl]** |
| Predictions look plausible but are wrong per row | The runner or a refactor sorted the future frame. Sampling models draw per row in iteration order from one seeded generator | Write a shuffled-future test: shuffle the future frame, assert the output `(time_period, location)` order equals the input order. **[mstl]** |
| `Prediction script did not create output file at ...` | The predict script exited 0 without writing to `{output_file}` | Exit non-zero when predictions cannot be produced, so the failure stores a diagnostic workspace artifact you can download. **[docs]** |
| Script cannot find `model.rds` / `model.json` | It was not written by train, or was written outside the workspace | The train workspace (including whatever train wrote) is zipped, stored as the `ml_training_workspace` artifact, and restored into the predict workspace. Write to a plain relative filename. **[docs]** |
| A helper file the script reads at startup is missing | It was excluded from the copy | The whole project directory is copied per job (minus `.git`, `.venv`, `__pycache__`, build artefacts). Keep the repo small: every excluded megabyte is copied on every train and every predict. **[docs]** |
| The script runs from the wrong directory | `cwd` is the temp workspace root, not the script's directory | Use workspace-relative paths; `source("scripts/lib.R")`, not `source("lib.R")`. **[ewars]** |

## `chapkit test` and local smoke testing

| Symptom | Cause | Fix |
|---|---|---|
| `chapkit test` passes but proves nothing about your data | Its data is **synthetic** - `time_period`, `location`, `disease_cases`, `population` and a few `feature_N` columns | Treat it as a wiring check only. Numeric truth comes from the parity harness. **[docs]** |
| `chapkit test` fails on a seasonal or weekly model | Defaults are `--rows 250`, `--predict-rows 150`, monthly. A weekly panel at 250 rows has under a year of history, shorter than a 52-period season | `chapkit test --period-type weekly --rows 520 --predict-rows 300`. Confirm flags with `chapkit test --help`. **[mstl] [docs]** |
| `X in predict methods must have same columns as X in fit` | Lag-based model; the historic window is shorter than the training window | Raise `--predict-rows`. **[docs]** |
| `KeyError: "['<col>'] not in index"` at train | A hardcoded column was not declared as a `required_covariate`, so the generator did not emit it | Add it to `MLServiceInfo.required_covariates`. **[docs]** |
| Job times out | Default `--timeout` is 60 s; the first job may JIT-compile, fit per location, and copy the project into a fresh workspace | `--timeout 300` (R/INLA typically needs `180`+). Use a generous timeout in pytest too (600 s is not excessive). **[mstl] [ewars]** |
| `chapkit test` is not in `--help` | The `test` subcommand only appears **inside** a chapkit project; `init` only appears **outside** one; `mlproject run`/`migrate` only appear when an `MLproject` file is in cwd | Run the command from the right directory. Do not conclude the subcommand does not exist. **[mstl]** |
| Docs or older notes mention `--template ml`, `ml-shell` or `task` | Stale template names | Current names are `fn-py`, `shell-py`, `shell-r`, `shell-r-tidyverse`, `shell-r-inla`. Always read `chapkit init --help` at runtime rather than trusting any written list. **[mstl] [multistep]** |
| `Training script exited with code 127` when testing an R model on a laptop | `Rscript` is not on the host, and `--start-service` spawns `main.py` in the **host's** Python | Expected. Test R models in Docker only: build the image, run it, then `chapkit test --url http://localhost:<port>`. **[ewars] [docs]** |
| Polling never finishes | Wrong endpoint | Poll `GET /api/v1/jobs/{job_id}` and read `status` (`completed` / `failed`). There is no `$status` action. The `$train` and `$predict` 202 responses already carry both `job_id` and `artifact_id` - use the `artifact_id` from the response rather than listing artifacts. **[mstl]** |
| Cannot reach the service locally | Port confusion | Run it as `uv run python main.py`, which the `if __name__ == "__main__":` block binds to **9090** by default; the container listens on **8000** and compose maps `9090:8000`. **[mstl]** |

## Packaging, lockfile and Docker

| Symptom | Cause | Fix |
|---|---|---|
| `Failed to build <pkg>` / `No such file or directory: 'g++'` in `docker build` | The resolved version publishes **no cp313 wheel**, so it compiles from source. macOS has a compiler; the chapkit base images do not | Pin to a version with wheels. Audit the whole runtime closure **before** producing goldens: `uv export --frozen --no-dev --no-hashes -o req.txt`, then query `https://pypi.org/pypi/<name>/<version>/json` for a cp313 wheel on manylinux **x86_64 and aarch64** (`py3-none-any` counts for both). **[mstl]** |
| A direct dependency silently resolved two minor versions back | A newer transitive preference constrained it. Leaving `pandas` unpinned pulled pandas 3, which `statsforecast>=2.1` forbids, so the resolver chose `statsforecast==2.0.1` - the last release with no cp313 wheels. Nothing warned; the model imported and produced correct numbers | Look at the resolved versions, not just whether the import works. When you pin package A to work around package B, **say so in a comment** in `pyproject.toml`, or someone will lift the pin. **[mstl]** |
| The dependency bug is found after the goldens exist | `docker build` was left until the end | Run `docker build` **early** - before goldens, not after the PR. It is the only check that exercises the target platform. **[mstl]** |
| The first prediction job fails in a hardened container | numba (and matplotlib, and anything with a cache) writes next to the installed package; `read_only: true` forbids it | `ENV HOME=/tmp MPLCONFIGDIR=/tmp XDG_CACHE_HOME=/tmp/.cache NUMBA_CACHE_DIR=/tmp/numba_cache` and a tmpfs on `/tmp` in compose. Cheap insurance even when numba is not currently in the lock. **[mstl]** |
| Example data, `uv.lock` or `.python-version` are missing from git | The legacy repo's `.gitignore` ignores `*.csv`, `uv.lock` and `.python-version` | Un-ignore all three before committing anything. Add `data/`, `*.db*`, `.pytest_cache/`, `.ruff_cache/` instead. Check `git check-ignore -v <path>` when a file mysteriously does not stage. **[mstl]** |
| Service registers, then 404s / never appears in chap-core | `$register` written instead of `$$register` in compose YAML - compose expands `$register` as a variable | Use `SERVICEKIT_ORCHESTRATOR_URL: http://chap:8000/v2/services/$$register`, and `depends_on: chap: condition: service_healthy`. **[docs]** |
| Container is Python 3.11/3.12 shaped | `ghcr.io/dhis2-chap/chapkit-py` is **Python 3.13**, and chapkit 2 requires it | `requires-python = ">=3.13"`, `.python-version` = `3.13`, `target-version = "py313"` in ruff. **[mstl]** |
| R image refuses to run on Apple Silicon | `chapkit-r-inla` is amd64 only | `FROM --platform=linux/amd64 ...` plus `platform: linux/amd64` in compose; expect emulation. **[ewars]** |

## Lint, formatting and the frozen core

| Symptom | Cause | Fix |
|---|---|---|
| `git diff <base> -- <model files>` is no longer empty after the first lint run | `ruff format` reformatted the numeric core - reordered an import, joined wrapped expressions. All cosmetic, all fatal to the claim "the numbers cannot have moved, the code is byte-identical" | Add the frozen files to `[tool.ruff] extend-exclude` **before** the first `ruff format .`, and `git checkout <base> -- <those files>` to undo damage already done. **[mstl]** |
| Documentation code snippets get reflowed | ruff >= 0.16 formats Python code blocks inside Markdown | Add `"*.md"` to `extend-exclude`. **[mstl]** |
| CI fails with `E402 module level import not at top of file` in `conftest.py` | `DATABASE_URL` must be set before `main` is imported, so the imports are genuinely not at the top | Keep the `# noqa: E402` comments. They are load-bearing. **[mstl]** |

## Parity and tolerances

| Symptom | Cause | Fix |
|---|---|---|
| The "baseline" matches the new code suspiciously well, or not at all | The baseline was run with the old libraries and the new code with new libraries, so any diff is unattributable | Run the **legacy code** from a git worktree of the base commit using the **new** virtualenv, and assert `<pkg>.__file__` points into the worktree. See `parity-harness.md`. **[mstl]** |
| A parity diff appears out of nowhere on re-read | pandas' fast float parser differs in the last ulp | `pd.read_csv(..., float_precision="round_trip")` on both sides. **[mstl]** |
| Relative-tolerance parity passes locally, fails on Linux CI on a handful of cells | Values near zero. A sample of ~0.003 cases differs by ~5e-8 across libm implementations: negligible absolutely, ~1e-5 relatively | Compare with **both** `rtol` and `atol` (`np.testing.assert_allclose(got, want, rtol=PARITY_RTOL, atol=PARITY_ATOL)`, both defaulting to `1e-6` and both env-overridable). Never loosen shape, column list or row order. **[mstl]** |
| Cells where the reference is exactly 0 blow up the relative diff | Division by zero; clipped samples are legitimately 0 | Define relative difference only where the reference is non-zero; count `inf` when the reference is 0 and the candidate is not. **[mstl]** |
| A deliberate behaviour change (dropping an option) cannot be shown to be safe | No gate existed before the edit | Build the parity gate first. "Removing an option cannot change results because its default equalled the constant" is an argument; a passing golden test is the proof. **[mstl]** |

## chap-core integration

| Symptom | Cause | Fix |
|---|---|---|
| `chap eval` aborts with `ValidationError ... period_type Input should be 'weekly' or 'monthly' [input_value='any']` | chap-core 2.3.0's chapkit client validates `/api/v1/info` against its own `PeriodType` enum, which has no `any`. chap-core `main` accepts it | Not a defect in your service. Verify the rest of the path by temporarily setting `PeriodType.monthly`, run `chap eval`, then revert. Say so in the PR. **[mstl]** |
| `chap eval` never gets past config creation | The chap-core-shaped config body is not handled | This is the `user_option_values` hoist again. `chap eval --run-config.is-chapkit-model` is the cheapest end-to-end check of the real chap-core path. **[mstl]** |
