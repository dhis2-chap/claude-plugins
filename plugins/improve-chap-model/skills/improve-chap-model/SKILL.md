---
name: improve-chap-model
description: Use when the user wants to iteratively improve, optimize, or tune an existing CHAP model (a local folder or GitHub URL) that is evaluated on a dataset with the `chap` CLI. Drives an evaluate → understand → change → re-evaluate loop, optimizing log_crps, and tracks every experiment with git for reproducibility.
---

# Improve a CHAP model

Iteratively improve an existing CHAP model. You evaluate it on a fixed dataset
with the `chap` CLI, read its code to understand how it works, make targeted
changes to the **model code** and/or its **configuration file**, re-evaluate, and
keep only what measurably helps — tracking everything with git so any promising
result is reproducible.

This file deliberately does **not** restate the `chap` CLI reference. The CLI
changes between versions, so always derive the exact commands from the live docs
and from `chap --help` at runtime (step 0).

**Authoritative references — consult the live versions, do not rely on memory:**
- Evaluation workflow: https://chap.dhis2.org/chap-modeling-platform/chap-cli/evaluation-workflow/
- Running external models in CHAP: https://chap.dhis2.org/chap-modeling-platform/external_models/running_models_in_chap/
- Latest `chap` source (always current): https://github.com/dhis2-chap/chap-core (master)

## Core principles

- **One change per experiment.** Change one thing (a code edit *or* a config
  edit), so any metric movement is attributable.
- **Freeze the evaluation harness.** Same dataset, same backtest parameters, same
  config-passing mechanism across *all* experiments — otherwise results aren't
  comparable.
- **Optimize `log_crps`** (lower is better) as the primary metric; watch `crps`,
  RMSE, MAE and coverage as secondaries so an improvement in one doesn't
  unacceptably regress the others.
- **Track relentlessly.** Every experiment is a git commit plus a row in the
  experiment log; promising ones are clearly marked. Local git only — never push
  unless the user explicitly asks.
- **Never commit to a protected branch.** Treat `main`, `master`, and `stable`
  as read-only — never commit to, merge into, or move them. *All* commits
  (setup, baseline, and every experiment) go on your own branches. Successful
  changes stay on their branch and are reported back to the user, who decides
  whether to integrate them.

## 0. Orient — every run, before doing anything else

1. **Verify `chap` is available and working:** run `chap --version`. If it is
   missing, install the latest from https://github.com/dhis2-chap/chap-core
   (master) — e.g. `uv tool install chap-core --python 3.13` — and point the user
   there. If **several `chap` installs** are on PATH (e.g. a pyenv shim and a uv
   tool), they may be different versions with different commands; **ask the user
   which `chap` to use** and use that explicit path for every command afterward.
   - **Ask the user which chap version/source they want.** Features differ by
     version (e.g. the NetCDF `eval` command needs **chap-core ≥ 2.0.0**, which at
     time of writing lives on GitHub `master` as a `2.0.0.devN` build — the
     released `1.1.4` only has `evaluate`/`evaluate2`).
   - **A project-local install is often cleanest** — it pins the version with the
     model and avoids clobbering system installs:
     ```
     uv venv --python 3.13 .venv
     uv pip install --python .venv "chap-core @ git+https://github.com/dhis2-chap/chap-core.git"
     ```
     Then **use the explicit binary path** (`.venv/bin/chap`) for *every* command
     this session, and record the resolved version in the experiment log. Add
     `.venv/` to `.gitignore`.
2. **Read the live docs** (WebFetch both URLs above). They define the current
   evaluation workflow and the external-model contract.
3. **Discover the current commands from the installed CLI** — it is the ground
   truth for invocation:
   - `chap --help` — find the evaluation command that **produces a NetCDF (`.nc`)
     file**. Prefer **`eval`**; if absent, fall back to `evaluate2`, then
     `evaluate`. (The command name has changed across versions — do not assume.)
   - `chap <eval-cmd> --help` — read its exact arguments (model, dataset, output,
     `--backtest-params.*`, `--model-configuration-yaml`, the tracking flag —
     `--run-config.track` in chap 2.0.0 — `--dry-run`, etc.). Do not assume flag
     names; copy them from the help output.
   - `chap export-metrics --help` — for computing comparable metrics from `.nc`
     files.

## 1. Acquire and prepare the model

- Confirm the model source with the user: a **local folder** or a **GitHub URL**.
  - GitHub URL → `git clone` it into a working directory.
  - Local folder that is **not** a git repo → `git init` and commit the pristine
    state as the first commit.
  - Local folder that **is** a git repo → make sure the working tree is clean
    before starting.
- Note the **pristine baseline** ref (e.g. `main`/`master` or the initial commit)
  and leave it untouched. **Immediately create a working branch off it** (e.g.
  `git checkout -b improve/setup`) and make every commit — setup, baseline, and
  experiments — on your own branches. Never commit to or move `main`/`master`/
  `stable`.
- Confirm the model is CHAP-compatible: read its `MLproject` and the `train` /
  `predict` entry points it declares (see the running-external-models docs).

## 2. Set up the fixed evaluation harness

Everything here is chosen **once** and then frozen for the whole session.

- **Dataset — ask the user.** Normally this is a **local CSV path** in CHAP
  format. Only if the user has none, fall back to a documented public example CSV
  (confirm the URL from the live docs) or a built-in dataset.
- **Initial model configuration — ask the user** for a config file (YAML or
  JSON). This is passed to the eval command via `--model-configuration-yaml` and
  is a first-class lever you will tune (step 5).
- **Backtest parameters.** Pick `--backtest-params` (`n-periods`, `n-splits`,
  `stride`) per the docs/defaults and keep them constant for every experiment.
- **MLflow tracking (optional, don't let it block you).** Enable the tracking
  flag (`--run-config.track` in chap 2.0.0) so each run is logged to MLflow. It
  needs two environment variables, or the run errors out:
  ```
  export MLFLOW_TRACKING_URI="file://$PWD/mlruns"   # a local file store works fine
  export MLFLOW_ALLOW_FILE_STORE=true                # required to allow a file store
  ```
  `mlruns/` is large — gitignore it. If MLflow setup gets in the way, **drop the
  tracking flag and proceed** — the committed git experiment log is the primary,
  authoritative record; MLflow is a bonus.
- **Define the canonical command once and freeze it in a committed script**
  (e.g. `experiments/run_eval.sh`) so every experiment runs the byte-identical
  invocation. Example shape (adapt to what `--help` shows):
  - Evaluate: `chap <eval-cmd> <model> <dataset.csv> <out>.nc --model-configuration-yaml <config> --run-config.track --backtest-params.n-splits <N> ...`
  - Compare: `chap export-metrics --input-files <a>.nc --input-files <b>.nc ... --output-file comparison.csv`
- **Validate the frozen command with `--dry-run` before the first real run** — it
  surfaces missing env vars, bad flags, or column-mapping issues cheaply, before
  you pay for a full (possibly slow) evaluation.

## 3. Baseline evaluation

- **Mind the cost.** Many CHAP models fit per-location, per-split (e.g. 400+
  locations × 7 splits = thousands of fits), so a single evaluation can take many
  minutes. Tell the user the expected cost up front. **Run evals in the
  background and monitor for completion** rather than blocking. If iteration is
  too slow, you may *screen* hypotheses on a reduced dataset/fewer splits — but
  always confirm a promising result on the full **frozen** harness before
  declaring it an improvement (only the frozen harness is comparable).
- Run the harness on the **pristine** model → `experiments/baseline.nc`.
- Run `export-metrics` with **no** `--metric-ids` once to list every metric the
  installed version supports; confirm `log_crps` (and `crps`) are present. Then
  record `log_crps` (primary), `crps`, RMSE, MAE, and coverage ratios.
- Create the experiment log `experiments/EXPERIMENTS.md` (a markdown table, see
  below) and keep the running `experiments/comparison.csv`.
- **Set up `.gitignore` for chap artifacts** (reproducibility comes from the
  committed code/config + the frozen command, not these large files):
  - `*.nc` — NetCDF eval outputs.
  - `runs/` — chap's per-run working directories (one per evaluation, large).
  - `mlruns/` and `.venv/` if you created them.
  - **Watch for a pre-existing global `*.csv` ignore** in the model repo — it can
    silently swallow your dataset and the experiment `comparison.csv`. Add an
    exception so the log is committable, e.g. `!experiments/comparison*.csv`.
- Commit the baseline state, the frozen `run_eval.sh`, and the log **on your
  working branch** (e.g. `improve/setup`) — never on `main`/`master`/`stable`.

## 4. Understand the model

Read the model thoroughly before changing it: `MLproject`, the train/predict
scripts, the configuration file, and the dependency manifest (`renv.lock`,
`requirements.txt`, etc.). Write a short summary of how it works and identify
concrete **leverage points** for improvement — e.g. covariates/features, lag
structure, the distribution/link function, priors, and hyperparameters — noting
for each whether it is tuned via the **config file** or the **model code**.

## 5. Iterative improvement loop

For each experiment (run one hypothesis at a time):

1. **Branch** from the setup/baseline branch (or the current best branch) — never
   from a protected branch: `git checkout -b exp/<short-desc>`.
2. **Make one change**, on exactly one of two levers:
   - **(a) Config file** — hyperparameters, covariate selection, priors, etc.
   - **(b) Model code** — train/predict logic, feature engineering, etc.
   Record which lever you used. Keep the changed config file in the working copy
   so it is committed with the experiment.
3. **Re-run the identical harness** (same dataset, same backtest params, same
   config-passing mechanism) → `experiments/exp_<n>.nc`.
4. **Compare** with `export-metrics` against the baseline and the current best.
5. **Decide** on `log_crps` (lower wins), checking the secondaries don't regress
   unacceptably:
   - **Improved** → commit; mark it promising (tag or branch, e.g.
     `promising/<desc>`) and advance the "best" pointer; append a log row.
   - **Not improved / regressed** → still commit it on its branch (so the negative
     result is recorded and not retried), append a log row noting the regression,
     and return to the current best for the next hypothesis.
6. **Log every experiment** (regardless of outcome).

## 6. Tracking and reproducibility

- **Experiment log** (`experiments/EXPERIMENTS.md`) — one committed row per
  experiment:

  | # | branch / commit | lever (code/config) | hypothesis / change | log_crps | crps | rmse | mae | coverage | verdict | mlflow run id | notes |
  |---|---|---|---|---|---|---|---|---|---|---|---|

- **Two complementary tracking layers:** this human-readable git log (the
  authoritative record) **and**, optionally, MLflow (via the tracking flag). When
  MLflow is on, put the run id in the log row so the two line up.
- Every experiment is a descriptive git commit; promising ones are clearly
  tagged/branched. Any experiment reproduces via `git checkout <ref>` plus the
  frozen `chap` command.
- **Local git only — never push** to a remote unless the user explicitly asks.

## 7. Stop and report

- **Before starting the loop, ask the user the stopping condition:** a fixed
  number of experiments, "keep going until I say stop", or "stop after N
  consecutive experiments with no improvement". Honor it.
- When stopping, report: the best model vs. baseline (metric deltas), which
  changes helped and which hurt, and the **exact reproduction steps** (the git
  ref to check out and the frozen `chap` command to run).
- **Name the branch** that holds the best result and leave it there. Do **not**
  merge it into `main`/`master`/`stable` or push it — integration is the user's
  decision. End by telling the user which branch to review.
