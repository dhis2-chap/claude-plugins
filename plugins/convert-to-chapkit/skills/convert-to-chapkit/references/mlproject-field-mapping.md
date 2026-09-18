# MLproject field -> chapkit destination

Fill this table in during step 0 and keep it in
`docs/migration-to-chapkit.md`. Every row must end up either mapped or
explicitly recorded as dropped, with a reason. A field you never looked at is a
field that silently stops working.

Confirm the current chapkit API against the installed version (`python -c
"import chapkit; print(chapkit.__version__)"`) and the live guides; the table
below reflects chapkit 2.0.x.

## Service identity and metadata

| MLproject | chapkit destination | Notes |
|---|---|---|
| `name` | `MLServiceInfo.id` (slug) and `pyproject.toml` `[project].name` | `id` is the registration identity in chap-core. Do not change it after shipping. |
| `meta_data.display_name` | `MLServiceInfo.display_name` | Shown in the DHIS2 Modeling App. |
| `meta_data.description` | `MLServiceInfo.description` | |
| `meta_data.author` | `ModelMetadata.author` | |
| `meta_data.author_note` | `ModelMetadata.author_note` | Easy to forget. It is an MLproject field; dropping it loses information. |
| `meta_data.author_assessed_status` | `ModelMetadata.author_assessed_status` (`AssessedStatus.green/yellow/orange/red/gray`) | Migrate defaults to `yellow`. Keep whatever the MLproject claimed unless the user says otherwise. |
| `meta_data.contact_email` | `ModelMetadata.contact_email` | |
| `meta_data.organization` | `ModelMetadata.organization` | |
| `meta_data.organization_logo_url` | `ModelMetadata.organization_logo_url` | |
| `meta_data.citation_info` | `ModelMetadata.citation_info` | |
| `meta_data.repository_url` / `documentation_url` | `ModelMetadata` fields of the same names | Check they exist on the installed chapkit before using. |
| (none) | `MLServiceInfo.version` | Keep in step with `pyproject.toml` `[project].version`. |
| (none) | `git_revision`, `chapkit_version`, `servicekit_version` on `/api/v1/info` | Filled automatically. `git_revision` comes from the `GIT_REVISION` env var, set by a Docker build arg. |

## Contract fields

| MLproject | chapkit destination | Notes |
|---|---|---|
| `supported_period_type: monthly\|weekly\|any` | `MLServiceInfo.period_type=PeriodType.monthly/weekly/any` | `any` means the model detects the granularity itself. See the gotcha about chap-core 2.3.0 rejecting `any`. |
| `required_covariates: [...]` | `MLServiceInfo.required_covariates=[...]` | Any column the scripts index by name belongs here, or `chapkit test`'s synthetic data will not contain it and train fails with `KeyError: "['<col>'] not in index"`. |
| `allow_free_additional_continuous_covariates: true\|false` | `MLServiceInfo.allow_free_additional_continuous_covariates` | Same name. |
| `target: disease_cases` | no per-service field | chapkit has no `target`. Record it in the migration doc and keep the scripts' own constant. |
| (none) | `MLServiceInfo.min_prediction_periods` / `max_prediction_periods` | A judgement call you must make and justify (e.g. `1` and `104` = two years of weekly periods). |
| `requires_geo: true` | the `{geo_file}` placeholder / `geo.json` in the workspace | Only when the scripts read polygons. |
| `adapters: {a: b, ...}` | **no chapkit equivalent** | chapkit does not apply MLflow-style column adapters. Port the renames into the script itself (an `apply_adapters()` helper). This is the single biggest non-Python-specific code change in an R conversion. |

## `user_options` -> Config class

Each `user_options` entry becomes a `Field` on a `BaseConfig` subclass in
`main.py`. The MLproject `title`/`description` becomes `Field(description=...)`
- it is what `/api/v1/configs/$schema` shows to an operator, so do not leave it
empty.

| MLproject `type` | Python annotation |
|---|---|
| `integer` | `int` |
| `number` | `float` |
| `string` | `str` |
| `boolean` | `bool` |
| `path` | `str` (a workspace-relative path) |

Rules:

- A `user_options` entry **with** a default -> `Field(default=<same value>, description=...)`.
  The default must match the MLproject exactly, or the first parity run fails.
- A `user_options` entry **without** a default -> required field. chap-core must
  then supply it on every config POST. Prefer giving it the same default the
  script already falls back to.
- `prediction_periods` is **always** added with a default even if the MLproject
  does not declare it. `BaseConfig` declares it with no default and chap-core
  never sends it.
- **Hyphenated / non-identifier names.** A script that reads `config$["n-lags"]`
  needs `n_lags: int = Field(default=3, alias="n-lags", description=...)`.
  chapkit serialises `config.yml` with `by_alias=True`, so the YAML key matches
  the script.
- `additional_continuous_covariates` is a reserved `BaseConfig` field. Override
  its default (e.g. `default_factory=lambda: ["rainfall", "mean_temperature"]`)
  rather than declaring a new field, when the model has a legacy default set.
- Dropping a `user_option` later is only non-breaking because `BaseConfig` sets
  `extra="allow"` and the script's own `from_user_options`-style filter discards
  unknown keys. Keep that filter, and test the whole path.

## `entry_points` -> runner commands

`ShellModelRunner` copies the whole project directory into a fresh temp
workspace per job, writes the input files at the workspace root, and runs the
command with the workspace as `cwd`. Placeholder substitution:

| MLproject parameter | chapkit placeholder | Resolves to |
|---|---|---|
| `{train_data}` | `{data_file}` | `data.csv` |
| `{historic_data}` | `{historic_file}` | `historic.csv` |
| `{future_data}` | `{future_file}` | `future.csv` |
| `{out_file}` | `{output_file}` | `predictions.csv` |
| `{model}` | a literal relative filename you choose (`model.rds`, `model.json`, `model.pickle`) | not a placeholder; the train workspace is restored before predict, so the file is simply still there |
| `{model_config}` | the literal `config.yml` | chapkit always writes it at the workspace root |
| `{polygons}` | `{geo_file}` | `geo.json`, or an empty string when the request had no geo |

Non-canonical MLproject parameter names are fine when you write the command by
hand; they only matter to `chapkit mlproject migrate`, which prompts for a
filename (or takes `--param NAME=FILENAME`). Confirm the current placeholder set
with the shell-runner-contract guide.

Also:

- Keep every path **workspace-relative**. No absolute paths, no assumptions
  about where the checkout lives.
- `source("lib.R")` becomes `source("scripts/lib.R")` if the helper moved into
  `scripts/` - cwd is the project root, not the script's directory.
- Prefer `python -m <package>` over a console script for Python: cwd is on
  `sys.path`, so the copied package resolves without the project being
  installed into the workspace.

## Environment fields -> Dockerfile and pyproject

| MLproject | chapkit destination |
|---|---|
| `uv_env: pyproject.toml` | the generated `pyproject.toml` plus `uv sync --frozen --no-dev --no-install-project` in the Dockerfile |
| `python_env: pyenv.yaml` / `conda_env: environment.yaml` | merge the dependency list into `[project.dependencies]`, pinning anything unpinned |
| `renv_env: renv.lock` | keep `renv.lock`; the R base image restores it. `chapkit-r*` images carry R and the common package stack |
| `docker_env.image` | the `FROM` line. `chapkit-py` (Python), `chapkit-r`, `chapkit-r-tidyverse`, `chapkit-r-inla` (amd64 only) |

Base-image choice: Python only -> `ghcr.io/dhis2-chap/chapkit-py:latest`
(Python 3.13). R with INLA -> `chapkit-r-inla` (amd64 only; pin
`--platform=linux/amd64` and add `platform:` to compose). R with
tidyverse/forecast/fable -> `chapkit-r-tidyverse`. Plain R ->
`chapkit-r`. Confirm the current list against the chapkit-images repo.

## Configuration files

| Legacy | chapkit |
|---|---|
| `configurations/<name>.yaml` (a saved user-option set) | a `POST /api/v1/configs` body. Document the exact JSON in the README. |
| example / isolated-run scripts (`isolated_run.R`, `evaluate_one_step.py`) | delete, or keep under `scripts/` if genuinely useful |

---

## Blank copy - fill this in

```markdown
### MLproject field map (<repo>, base commit <sha>)

| MLproject field | Value in this repo | chapkit destination | Done |
|---|---|---|---|
| name |  | MLServiceInfo.id |  |
| meta_data.display_name |  | MLServiceInfo.display_name |  |
| meta_data.description |  | MLServiceInfo.description |  |
| meta_data.author |  | ModelMetadata.author |  |
| meta_data.author_note |  | ModelMetadata.author_note |  |
| meta_data.author_assessed_status |  | ModelMetadata.author_assessed_status |  |
| meta_data.contact_email |  | ModelMetadata.contact_email |  |
| meta_data.organization |  | ModelMetadata.organization |  |
| meta_data.organization_logo_url |  | ModelMetadata.organization_logo_url |  |
| meta_data.citation_info |  | ModelMetadata.citation_info |  |
| supported_period_type |  | MLServiceInfo.period_type |  |
| required_covariates |  | MLServiceInfo.required_covariates |  |
| allow_free_additional_continuous_covariates |  | MLServiceInfo.allow_free_... |  |
| target |  | (no chapkit field - note only) |  |
| adapters |  | hand-written in the script |  |
| requires_geo |  | {geo_file} |  |
| user_options.<name> | type / default / title | Config field + Field(description=) |  |
| (injected) | - | prediction_periods default |  |
| entry_points.train.command |  | ShellModelRunner(train_command=...) |  |
| entry_points.predict.command |  | ShellModelRunner(predict_command=...) |  |
| uv_env / python_env / conda_env / renv_env |  | pyproject.toml / renv.lock + Dockerfile |  |
| docker_env |  | Dockerfile FROM |  |
| configurations/*.yaml |  | POST /api/v1/configs body in the README |  |
| (new) | - | MLServiceInfo.min/max_prediction_periods |  |
```
