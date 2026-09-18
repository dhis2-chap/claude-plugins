# Numeric parity harness

The acceptance gate for a conversion is: **the chapkit service reproduces the
pre-conversion model's predictions.** Everything else (health, info, schema,
`chapkit test`) is wiring.

Commands below are illustrative. Confirm flags against `--help` and the live
guides before running them.

## 1. Capture the baseline before any service code exists

The goldens must come from the **legacy code** but the **new virtualenv**.
Mixing those up is the classic way to produce a meaningless parity check: old
code with old libraries versus new code with new libraries, and any diff is
unattributable.

```bash
REPO=~/dev/chap-models/<model>
WT=~/dev/chap-models/<model>-baseline
git -C "$REPO" worktree add "$WT" <base-sha>     # untouched legacy code
```

Then, **from the worktree**, run the legacy entry points with the branch's
environment:

```bash
cd "$WT"
uv run --project "$REPO" python -c "import <pkg>; print(<pkg>.__file__)"
# must print $WT/<pkg>/__init__.py   <- mandatory assertion
```

`uv run --project <dir>` resolves the environment from `<dir>` but keeps the
current working directory, and `''` (cwd) is first on `sys.path`, so the
worktree's own package shadows the copy installed into the venv. If the
`__file__` check ever prints the branch path, the baseline is not a baseline;
fall back to `PYTHONPATH=$WT` or `uv run --project $REPO --directory $WT`.

Capture, for each period type the model supports:

```bash
uv run --project "$REPO" python main.py train \
  "$REPO/example_data/monthly/training_data.csv" "$SCRATCH/model.json" \
  "$REPO/tests/golden/config.yaml"

uv run --project "$REPO" python main.py predict \
  "$SCRATCH/model.json" \
  "$REPO/example_data/monthly/historic_data.csv" \
  "$REPO/example_data/monthly/future_data.csv" \
  "$SCRATCH/monthly_a.csv" "$REPO/tests/golden/config.yaml"
```

Remove the worktree (`git worktree remove "$WT"`) only at the very end - you
will want it again if the lock changes.

## 2. Determinism check - run it twice

```bash
# same model marker, same config, different output file
uv run --project "$REPO" python main.py predict ... "$SCRATCH/monthly_b.csv" ...
cmp "$SCRATCH/monthly_a.csv" "$SCRATCH/monthly_b.csv"
```

This decides which parity class you are in, so do it before choosing a
tolerance.

| Class | Condition | Gate |
|---|---|---|
| **A - exact** | The two runs are byte-identical: the model seeds its RNG from the config and draws in a deterministic order | Demand exact equality on the same machine and venv. Compare with `rtol`/`atol` of `1e-6` only as a CI escape hatch against last-ulp BLAS/libm differences. Report "N / N cells exactly equal". |
| **B - distributional** | Runs differ: unseeded RNG, thread-order-dependent reductions, MCMC | Compare summary statistics, not cells: mean of per-cell means within ~1 %, per-cell relative differences in the 5-15 % range are normal sampling noise. State the expected band **before** you look at the result, and keep shape/column/row-order checks exact. Say plainly in the PR that the gate is distributional. |

If the model is class B, consider making it class A first by threading the seed
through the config - it is usually a small change and it buys a far stronger
gate. Do that as a separate, pre-conversion commit so it does not contaminate
the conversion diff.

## 3. What to commit

```
example_data/<monthly|weekly>/{training_data,historic_data,future_data}.csv
tests/golden/config.yaml            # a small user_option_values set
tests/golden/<dataset>_predictions.csv
tests/golden/VERSIONS.md
scripts/parity.py
```

- Keep the fixtures small. Lowering `n_samples` (e.g. 100 -> 25) shrinks the
  CSVs by 4x and still covers thousands of float cells.
- `future_data.csv` must have no `disease_cases` column (or an all-null one),
  because that is how chap-core posts the future frame.
- Cover **every** period type the service claims. `supported_period_type: any`
  means two code paths (different seasonal length, different period parsing); a
  monthly-only check leaves half the model unverified.
- Prefer data with a few real NaNs - it exercises the NaN -> None conversion and
  the script's own dropna.

`tests/golden/VERSIONS.md` records: the legacy commit, the exact commands, the
resolved versions of every numerically relevant package plus Python and the
platform, the determinism result, the config used, the tolerance policy, and a
"do not regenerate casually" note.

## 4. The compare script (`scripts/parity.py`)

Shape it as reference vs candidate:

- **reference**: the legacy CLI re-run live, or, with `--golden`, the committed
  fixture produced by the pre-conversion code. Both are worth supporting - the
  first catches drift in the shared script, the second is the frozen contract.
- **candidate**: a running chapkit service, driven exactly the way chap-core
  drives it:
  1. `POST /api/v1/configs` with `{"name": ..., "data": {"user_option_values": {...}}}`
  2. `POST /api/v1/ml/$train` with `{"config_id", "data": <df payload>}` -> 202 with `{"job_id", "artifact_id"}`
  3. poll `GET /api/v1/jobs/{job_id}` until `completed` (fail on `failed`)
  4. `POST /api/v1/ml/$predict` with `{"artifact_id", "historic", "future"}` -> 202
  5. poll again
  6. `GET /api/v1/artifacts/{artifact_id}/$download` using the id from the 202

Comparison rules:

- Column list, row count and `(time_period, location)` order: **exact**, abort
  on any difference, and name the first differing row.
- `sample_*` cells: numeric, with `rtol` from `PARITY_RTOL` and `atol` from
  `PARITY_ATOL` (both `1e-6`).
- Read both sides with `pd.read_csv(..., float_precision="round_trip")`.
- Relative difference only where the reference is non-zero; `inf` where the
  reference is 0 and the candidate is not.
- Print a markdown row and exit non-zero on failure:

```
| kind | rows | sample cols | exactly equal cells | max abs diff | max rel diff | result |
|---|---|---|---|---|---|---|
| monthly | 216 | 25 | 5400 / 5400 (100.00 %) | 0.000e+00 | 0.000e+00 | PASS |
```

That table goes straight into the PR body.

Full working implementation to copy and adapt:
https://github.com/chap-models/mstl_arima/blob/main/scripts/parity.py

## 5. Run the gate three ways

1. `uv run pytest` - in-process `TestClient`, golden fixtures (see
   `pytest-testclient.md`). This is what CI runs.
2. `scripts/parity.py --kind <...>` against a live service, with the legacy CLI
   as reference.
3. `scripts/parity.py --kind <...> --golden` against the committed fixture.

All three must agree. (1) proves CI will catch a regression; (2) proves the
HTTP path, not just the in-process one; (3) proves the fixture itself is still
the contract.

## 6. Regenerate goldens only when the lock changes - and diff them separately

A dependency change after the goldens exist forces a regeneration, and a
regeneration is a *second* claim that must be kept apart from the conversion
claim:

- *claim 1*: `<pkg> A -> B` changed nothing. Evidence:
  `git diff --stat tests/golden` is empty after regenerating with the identical
  procedure, or a table of exactly what moved.
- *claim 2*: the chapkit conversion changed nothing. Evidence: the parity table.

Regenerate from the worktree with the same procedure, re-run the determinism
check, update `VERSIONS.md`, and say so in the commit message. Never regenerate
a golden to make a failing test pass - that deletes the gate.

## 7. Optional: chap-core evaluation

Cheap end-to-end proof that the real chap-core path works (not a numeric gate -
chap-core backtests on its own splits):

```bash
chap eval --model-name http://localhost:9090 \
  --dataset-csv example_data/monthly/training_data.csv \
  --output-file "$SCRATCH/eval.nc" --run-config.is-chapkit-model \
  --backtest-params.n-splits 2 --backtest-params.n-periods 3
```

If you want numbers out of it, `chap export-metrics --input-files a.nc
--input-files b.nc --output-file comparison.csv` compares a legacy-model
evaluation against the service evaluation on the same splits. Confirm flags with
`chap eval --help` and `chap export-metrics --help`; they drift between
versions. Note the `period_type: any` gotcha before promising this will run on a
released chap-core.
