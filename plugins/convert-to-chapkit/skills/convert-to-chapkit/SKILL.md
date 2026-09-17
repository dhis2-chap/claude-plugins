---
name: convert-to-chapkit
description: Use when the user wants to convert, migrate, or port an existing CHAP model repo (MLproject plus train/predict scripts, Python or R) into a chapkit 2.x service. Captures a pre-conversion baseline, maps every MLproject field, and gates the PR on numeric parity with the legacy predictions.
---

# Convert a CHAP model to a chapkit service

A CHAP model used to be a directory with an `MLproject` file and a pair of
train/predict scripts, run by chap-core through MLflow conventions. CHAP now
runs models as **chapkit** services: a FastAPI app exposing
`POST /api/v1/ml/$train` and `$predict`, an artifact store, a typed config
schema, and self-registration with chap-core.

This skill converts one repo, end to end, on a branch, with a PR. The
acceptance gate is **numeric parity**: the service must reproduce the
predictions the legacy code produced. Anything short of that is a rewrite
wearing a migration's clothes.

**Read `references/gotchas.md` in full before writing any code.** Most of the
ways a conversion goes wrong are silent: the service answers 200, the job
succeeds, and the numbers are quietly the defaults. That file is the list of
every one of them seen on a real conversion, with the fix.

This file deliberately does **not** restate CLI flags - `chapkit`, `chap` and
`uv` all drift between versions. Derive exact invocations from `--help` and the
live docs at runtime (step 0). Concrete commands live in the reference files,
each with a note to confirm them.

| Reference | Read it at |
|---|---|
| `references/gotchas.md` | before anything, and again whenever something fails |
| `references/mlproject-field-mapping.md` | step 0 and step 3 |
| `references/parity-harness.md` | steps 1 and 5 |
| `references/config-and-runner-snippets.md` | steps 2, 3 and 6 |
| `references/pytest-testclient.md` | steps 4 and 5 |
| `references/pr-template.md` | step 7 |

## Authoritative references - consult the live versions, not memory

Guides (read the ones relevant to the branch you take):

- MLproject migration checklist: https://dhis2-chap.github.io/chapkit/guides/mlproject-migration-checklist/
- `chapkit mlproject migrate`: https://dhis2-chap.github.io/chapkit/guides/mlproject-migrate/
- CLI scaffolding (`chapkit init` templates): https://dhis2-chap.github.io/chapkit/guides/cli-scaffolding/
- Shell-runner workspace contract: https://dhis2-chap.github.io/chapkit/guides/shell-runner-contract/
- Testing ML services (`chapkit test`): https://dhis2-chap.github.io/chapkit/guides/testing-ml-services/
- Deploying to chap-core: https://dhis2-chap.github.io/chapkit/guides/deploying-to-chap-core/
- ML workflows (runner types, `MLServiceInfo` fields): https://dhis2-chap.github.io/chapkit/guides/ml-workflows/
- Configuration management (`BaseConfig`, the config HTTP lifecycle): https://dhis2-chap.github.io/chapkit/guides/configuration-management/
- chapkit source (always current): https://github.com/dhis2-chap/chapkit

Reference repos - read the one closest to your case before writing code:

- https://github.com/chap-models/mstl_arima - **ShellModelRunner, Python.** The
  worked example this skill is distilled from: worktree baseline, golden
  fixtures, `scripts/parity.py`, `docs/migration-to-chapkit.md`.
- https://github.com/chap-models/chapkit_ewars_model - **ShellModelRunner, R/INLA.**
  Dockerfile, compose, publish workflow, R script contract.
- https://github.com/chap-models/chapkit_simple_multistep_model - **FunctionalModelRunner, Python.**
- https://github.com/dhis2-chap/chapkit-images - the base images.

If the user's repo already has a sibling in `chap-models` that was converted,
read that repo first. Matching the house style is worth more than inventing a
better one.

## Core principles

- **Baseline before code.** Capture the legacy model's predictions *before* any
  service code exists. Once the repo has changed you can no longer produce a
  trustworthy reference.
- **Parity is the acceptance gate.** Not "the service starts", not "`chapkit
  test` passes". Those are wiring checks. The gate is: same inputs, same
  numbers.
- **Port, do not improve.** Carry the numeric core over byte for byte and keep
  `git diff <base> -- <model files>` empty. Improvements are a separate PR, made
  *after* the gate exists - that is exactly what the gate is for.
- **Map every MLproject field.** Each one ends up mapped or explicitly recorded
  as dropped with a reason. A field nobody looked at is a field that silently
  stopped working.
- **Keep the repo small.** The shell runner copies the whole project directory
  into a fresh workspace on every train and every predict.
- **Never commit to a protected branch.** Treat `main`, `master` and `stable` as
  read-only. All work goes on a feature branch. Do not push or open a PR until
  the user asks or the gate is green and you have told them.
- **Conventional Commits, no emojis, no AI attribution.** Applies to commit
  messages, branch names, PR titles and PR bodies.
- **Delegate heavy lifting, verify it yourself.** Long mechanical phases (the
  port, the test suite, the CI files) suit an Opus-class subagent given a
  written brief. Never take the subagent's word for a result: re-run lint,
  tests, the parity script and the docker build yourself before believing them.
- **Document every step as you go** in `docs/migration-to-chapkit.md`: commands
  run, decisions taken, dead ends, resolved versions, parity numbers. Write it
  honestly rather than tidily - the mistakes are the most useful part, and this
  log is what a future conversion reads.

## 0. Orient - every run, before touching anything

1. **Repo state.** Confirm the working tree is clean. Record the **base SHA**
   you are converting from - every parity claim is relative to it. Ask the user
   whether open PRs should be merged first, or note them as excluded.
2. **Branch.** Create a feature branch off the base (e.g.
   `feat/chapkit-service`). Never work on `main`.
3. **Tooling.** Record versions: `uv --version`, `python --version`,
   `chapkit --version` (or `uvx chapkit --version`), `chap --version` if
   installed, `docker info` (note it if the daemon is down - you will need it in
   step 2), `gh auth status`.
4. **Live docs.** Fetch the guides above that apply. They are the contract; this
   file is the procedure.
5. **Current CLI surface.** Run `chapkit --help`, `chapkit init --help`,
   `chapkit test --help`. Template names and flags have changed before and will
   again - read them, do not assume. Note that `init` is hidden **inside** a
   chapkit project, `test` is hidden **outside** one, and `mlproject` is hidden
   unless an `MLproject` file is in the current directory.
6. **Read the repo.** `MLproject`, the train/predict scripts, the config
   file(s), the dependency manifest, the `.gitignore`. Determine: Python or R;
   positional or flagged CLI; where the numeric core lives; whether the model
   fits at train time or at predict time; whether it is seeded.
7. **Extract the MLproject fields** into the table in
   `references/mlproject-field-mapping.md`. Fill it in now, while you are
   reading - not later from memory.
8. **Choose the runner with the user** (table below). State the trade-off and
   let them decide; many teams prefer Shell for consistency with the other
   chap-models repos even when Functional would work.
9. **Agree the example data and the golden config.** Which datasets, which
   period types, which `user_option_values`. If the repo has no example data,
   borrow from a sibling chap-models repo and say where it came from.
10. **Write the brief** before delegating anything: base SHA, branch, runner,
    layout, the field map, the commit sequence, the parity plan, what "done"
    means.

### Runner decision table

| Option | Use when | Cost |
|---|---|---|
| **ShellModelRunner (Python)** | The model already has a file-in / file-out CLI. The service shells out to the *same* code path the MLproject did, so the numeric core is carried over byte for byte - the strongest possible parity guarantee. | A subprocess per job; the project directory is copied per job. |
| **ShellModelRunner (R)** | Any R model. There is no other option. | Same, plus: no local testing without R - you test in Docker. |
| **FunctionalModelRunner (Python)** | Pure-Python model where you want in-process speed and no subprocess, and you are willing to rewrite the entry points. | Entry points are rewritten against `chapkit.data.DataFrame`, which introduces a conversion layer and therefore a place for drift to hide. Prefer Shell for a *migration*; Functional for greenfield. |
| **`chapkit mlproject migrate`** | You want the scaffold generated from the MLproject automatically. It always emits a `ShellModelRunner` and moves regenerated project metadata into `_old/`. | Generated code still needs the same hand-review: the config hoist, `prediction_periods`, pins, the frozen-core ruff excludes. Treat its output as a starting point, not an answer. |

Whichever you pick, `config_format="chap_core"` is the right default for a
migration: it writes the tunables nested under `user_option_values:`, which is
what existing chap-models scripts already read.

---

## 1. Baseline capture

**Read first:** `references/parity-harness.md`.

This happens **before any service code exists**. Do not skip ahead.

**Prerequisite:** the dependency half of step 2 (pins, `uv.lock`, the wheel
audit, the first `docker build`) must be done and committed *first*. Goldens are
produced with the new virtualenv, so a lock change afterwards means regenerating
and re-justifying every fixture. Do the `pyproject`/lock work, commit it, then
come back here. No *service* code is written in either step.

- Add the example data under `example_data/<period-type>/`. Cover every period
  type the service will claim - `supported_period_type: any` means two code
  paths, and a monthly-only check verifies half the model.
- Add `tests/golden/config.yaml` with a small `user_option_values` set (lowering
  the sample count keeps fixtures small without weakening the check).
- Create a git worktree at the base SHA, run the **legacy** entry points from it
  using the **new** virtualenv, and assert the imported package's `__file__`
  points into the worktree. That assertion is mandatory.
- Run predict twice and `cmp` the outputs. This decides whether the gate is
  class A (exact) or class B (distributional).
- Write `tests/golden/VERSIONS.md`: legacy commit, exact commands, resolved
  versions, determinism result, config, tolerance policy.
- Add `scripts/parity.py` (reference vs candidate, markdown table, non-zero exit
  on failure).

**Commit:** `test: add example data and legacy golden predictions`

## 2. Scaffold and pin

**Read first:** `references/config-and-runner-snippets.md`, the CLI scaffolding
and migrate guides.

- Generate the scaffold in a **scratch directory** (`chapkit init` is not
  available inside an existing chapkit project, and you do not want it rewriting
  the repo), then copy in only the files you need. Or copy them from the closest
  reference repo. Or run `chapkit mlproject migrate` in place and review what it
  produced.
- `pyproject.toml`: `requires-python = ">=3.13"` (chapkit 2 and the
  `chapkit-py` base image are 3.13); `chapkit>=2.x,<3`; the model's own deps,
  **pinned**; a PEP 735 `[dependency-groups] dev` with `pytest`, `httpx2`
  (Starlette 1.6+ `TestClient`; plain `httpx` only warns), `ruff`; `[tool.pytest.ini_options]` with `pythonpath = ["."]` if `main.py`
  sits at the root; ruff config with `target-version = "py313"`.
- **Add the frozen numeric core and `*.md` to `[tool.ruff] extend-exclude`
  before the first `ruff format .`.** Otherwise the formatter rewrites the one
  set of files whose byte-identity is the parity argument.
- `.python-version` = `3.13`.
- **Fix `.gitignore` first.** Legacy chap-models repos commonly ignore `*.csv`,
  `uv.lock` and `.python-version`, all of which this conversion must commit. Add
  `data/`, `*.db*`, `.pytest_cache/`, `.ruff_cache/` instead. Verify with
  `git check-ignore -v <path>`.
- `uv lock && uv sync --all-groups`, then **look at the resolved versions**, not
  just whether the import works. A transitive preference can silently hold a
  direct dependency back.
- **Audit wheels before goldens:** export the runtime closure and confirm every
  pinned package has a cp313 wheel for manylinux **x86_64 and aarch64**. macOS
  has a compiler; the chapkit base images do not.
- **Run `docker build` now**, not at the end. It is the only check that
  exercises the target platform. If the daemon is down, say so and ask the user
  to start it - a dependency change after goldens exist means regenerating and
  re-justifying them.

**Commit:** `build: move to uv with chapkit 2 and pin dependencies`

## 3. Port

**Read first:** `references/config-and-runner-snippets.md`,
`references/mlproject-field-mapping.md`.

### Universal

- Write the Config class: one field per `user_option` with the MLproject default
  and its title as `Field(description=...)`, plus a **default for
  `prediction_periods`**, plus the **`user_option_values` hoisting validator**.
  These two are the difference between a service that works and one that
  silently runs on defaults.
- Write `MLServiceInfo` / `ModelMetadata` from the `meta_data` block. Decide
  `min_prediction_periods` / `max_prediction_periods` and justify them in a
  comment.
- `ArtifactHierarchy`, the `DATABASE_URL` block, `MLServiceBuilder(...)
  .with_monitoring().with_registration(...).build()`, and a
  `if __name__ == "__main__": run_app(...)` block for local dev.
- Keep the numeric core untouched and prove it: `git diff <base> -- <files>`
  must be empty.

### Python, ShellModelRunner

- Move the legacy CLI into the package (e.g. `<pkg>/cli.py` plus
  `<pkg>/__main__.py`) so it is reachable as `python -m <pkg>`; leave the model
  modules alone.
- Commands reuse the legacy argument order verbatim, with MLproject parameter
  names replaced by chapkit placeholders. `config.yml` and the model filename
  are literal workspace-relative names.
- Verify immediately, before writing a single test: run `python -m <pkg> train`
  then `predict` by hand and `cmp` the output against the golden fixture.

### Python, FunctionalModelRunner

- `async def on_train(config, data, geo=None) -> Any` (any pickleable object,
  handed straight back to predict) and
  `async def on_predict(config, model, historic, future, geo=None) -> DataFrame`.
- `chapkit.data.DataFrame` is a Pydantic schema, **not** pandas: `.to_pandas()`
  in, `.from_pandas()` out. This is the single most common mistake on this path.
- Consider keeping console-script entry points whose flags match the shell
  placeholders, so switching runners later is a one-line change.

### R, ShellModelRunner

- Commands are `Rscript scripts/train.R --data {data_file}` and
  `Rscript scripts/predict.R --historic {historic_file} --future {future_file}
  --output {output_file}`. Named flags only - no positional args, no hardcoded
  paths.
- The scripts read `config.yml` with `yaml.load_file` and reach into
  `config$user_option_values$<name>` under `chap_core` format.
- **chapkit has no MLflow `adapters:` mechanism.** Port the column renames into
  an `apply_adapters()` helper in the script.
- `source("scripts/lib.R")` - paths are relative to the project root, not the
  script.
- Predictions: `time_period`, `location`, `sample_0 .. sample_N`,
  `write.csv(..., row.names = FALSE)`.
- Swap the base image to `chapkit-r`, `chapkit-r-tidyverse` or `chapkit-r-inla`.
  The Python Dockerfile cannot be patched into an R one; replace it.
- Expect `Rscript` to exit 127 on a laptop without R. That is not a bug - test
  R models in Docker.

**Commit:** `feat: expose <model> as a chapkit service`

## 4. Smoke tests

**Read first:** `references/pytest-testclient.md`, the testing guide.

- `chapkit test` against a running service: a wiring check on **synthetic** data.
  Run it for every period type the service claims; seasonal and weekly models
  need more rows than the default. Raise the timeout - the first job pays for
  workspace copying, JIT and per-location fits.
- pytest with an in-process `TestClient`: health, info, config schema defaults,
  config hoisting (nested and flat, flat wins), unseen-location fallback,
  future-row-order preservation, and an accepted-and-ignored test for every
  option you removed.
- `DATABASE_URL` must be set to a temp SQLite **file** before `main` is
  imported, and the `# noqa: E402` comments that makes necessary are
  load-bearing.
- For an R model, `chapkit test` against the container replaces the pytest suite.

**Artefacts:** `tests/__init__.py`, `tests/conftest.py`, `tests/helpers.py`,
`tests/test_service.py`. They are committed together with the parity tests from
step 5, under that step's commit message.

## 5. Numeric parity

**Read first:** `references/parity-harness.md`.

- Add the golden parity tests to the pytest suite (one per period type): exact
  column list, exact `(time_period, location)` order, `assert_allclose` with
  `rtol` **and** `atol` from env (`PARITY_RTOL` / `PARITY_ATOL`, both `1e-6`).
  Relative tolerance alone fails on near-zero samples across platforms.
- Run the gate three ways and require all three to agree: pytest; the parity
  script against a live service with the legacy CLI as reference; the parity
  script with `--golden` against the committed fixture.
- Print and record the exactly-equal cell count. "5400 / 5400 cells exactly
  equal" is a stronger statement than "within tolerance", and the difference
  belongs in the PR.
- Never loosen shape, column list or row order. Never regenerate a golden to
  make a failing test pass.
- If a dependency change forces a regeneration, regenerate from the worktree
  with the identical procedure and report it as a **separate claim** from the
  conversion parity.
- Optional: `chap eval --run-config.is-chapkit-model` against the running
  service exercises the real chap-core path end to end, and
  `chap export-metrics` compares legacy and service evaluations. Check the
  `period_type: any` entry in `references/gotchas.md` first - a released
  chap-core may refuse to talk to a service that declares it.

**Commit:** `test: in-process service tests with golden parity`

## 6. Docs, CI and Docker

- `Dockerfile` from the scaffold with the model's deltas (what to `COPY`, cache
  env vars pointed at `/tmp` for read-only containers). `.dockerignore` that
  keeps `example_data/`, `tests/`, `docs/`, `scripts/` out of `/work`.
- `compose.yml` (host 9090 -> container 8000, hardening, tmpfs `/tmp`, named
  volume for the database, registration env vars commented out with `$$register`)
  and a GHCR variant.
- `Makefile`: `run`, `build`, `test`, `test-docker`, `parity`, `lint`, `check`,
  `clean`.
- `.github/workflows/ci.yml` (lint + test, and a docker-build job that starts the
  container and runs `chapkit test` against it) and `publish-docker.yml`.
- `CLAUDE.md` with the project rules: no emojis, no tool attribution,
  Conventional Commits.
- `README.md`: quickstart, a **runnable** curl sequence (config -> `$train` ->
  poll -> `$predict` -> poll -> `$download`) using the chap-core-shaped config
  body, smoke-test invocations, docker, the config table, and the parity
  section. Execute the curl sequence before committing it; do not ship
  pseudo-code.
- `docs/migration-to-chapkit.md`: finish the step log.

**Commits:** `ci: add docker packaging, makefile and github workflows` then
`docs: describe chapkit service usage and migration`

Finally, remove the legacy runner surface once everything above is green:

**Commit:** `chore: remove MLproject and legacy entry points`

## 7. PR

**Read first:** `references/pr-template.md`.

- Re-run the whole gate yourself on the tip of the branch: lint, pytest,
  `chapkit test` for every period type, the parity script both ways, the docker
  build and `test-docker`. Record what you ran and what you could not.
- Remove the baseline worktree.
- Push the branch and open the PR only when the user has asked for it, or tell
  them it is ready and wait. Never merge, and never push to a protected branch.
- The PR body carries: summary, decisions table, the parity table, versions, the
  verification list (including skipped items and why), reviewer notes, and how
  to run it. No emojis, no attribution lines.

---

## Checklist

- [ ] Base SHA recorded; feature branch created; protected branches untouched.
- [ ] Every MLproject field mapped or explicitly dropped with a reason.
- [ ] Runner chosen with the user.
- [ ] `pyproject`, lock and pins done; wheels verified for linux amd64 and
      arm64; `docker build` run **before** goldens.
- [ ] `.gitignore` un-ignores `uv.lock`, `*.csv`, `.python-version`.
- [ ] Frozen numeric core excluded from ruff before the first format run.
- [ ] Baseline captured from a worktree of the base SHA with the new venv, and
      the `__file__` provenance check passed.
- [ ] Determinism established (predict twice, `cmp`); parity class chosen.
- [ ] `prediction_periods` has a default; `user_option_values` are hoisted.
- [ ] Every period type the service claims is covered by data and by tests.
- [ ] Parity green three ways; exactly-equal cell counts recorded.
- [ ] `git diff <base> -- <numeric core>` is empty (or every hunk is justified).
- [ ] Docker image builds and `chapkit test` passes against the container.
- [ ] `docs/migration-to-chapkit.md` is complete and honest about dead ends.
- [ ] Conventional Commits, no emojis, no attribution lines, nothing pushed
      without the user's say-so.
