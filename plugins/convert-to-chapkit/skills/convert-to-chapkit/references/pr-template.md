# Conversion PR body template

Generalised from the `chap-models/mstl_arima` conversion PR. Keep it factual:
the reviewer's question is "can I believe the numbers did not move", and every
section exists to answer it. No emojis. No AI attribution lines. Conventional
Commits title (e.g. `feat: convert to chapkit 2 service`).

Fill in the bracketed parts, delete sections that do not apply, and never claim
a check you did not run - say it was skipped and why.

---

```markdown
## Summary

Converts `<repo>` from an `MLproject` + <CLI framework> into a chapkit <version>
service that chap-core can discover, configure, train and query over HTTP. The
numeric core (`<files>`) is unchanged<, apart from ...>, and the legacy
<CLI/scripts> <is reused verbatim as the shell command / was ported to
on_train/on_predict>, so predictions are <byte-identical / statistically
indistinguishable> to the pre-conversion code.

Follows the layout of `<reference repo>`. The full step log is in
`docs/migration-to-chapkit.md`.

## Decisions

| Topic | Choice | Why |
|---|---|---|
| Runner | `<ShellModelRunner(config_format="chap_core") running ...>` | <why> |
| Config | `<Name>Config(BaseConfig)` with `prediction_periods=<n>` and a `model_validator` that hoists `user_option_values` | chap-core posts tunables nested under `user_option_values` and never sends `prediction_periods`; without hoisting the script would run on defaults |
| Period type | `PeriodType.<...>` | <matches the old supported_period_type> |
| Layout | <flat / src / scripts> | <why> |
| Dependencies | `<pins>`, `uv.lock` committed | <why each non-obvious pin exists> |
| Removed | `MLproject`, `configurations/`, `<options>` | <why each removal is safe> |

## Numeric parity

Goldens were produced by the legacy <CLI> at `<base sha>` in a git worktree,
using the same locked environment as the service, with `<config>`
(`tests/golden/`). Legacy predict run twice was byte-identical. The service was
then driven with the same historic and future frames.

| kind | rows | sample cols | exactly equal cells | max abs diff | max rel diff | result |
|---|---|---|---|---|---|---|
| monthly (<dataset>, <n> locations, <h> periods) | <r> | <c> | <e> / <t> (<pct> %) | <a> | <rel> | PASS |
| weekly (<dataset>, <n> locations, <h> periods) | <r> | <c> | <e> / <t> (<pct> %) | <a> | <rel> | PASS |

Same result from `uv run pytest` (in-process TestClient), from
`scripts/parity.py` against a live service (legacy-CLI reference and
committed-golden reference)<, and after the <pkg> <x> to <y> bump (goldens
byte-identical across the bump)>.

<For a class B (stochastic) model, replace the table with the agreed
distributional criterion and its result, and say explicitly that the gate is
distributional, not exact.>

## Versions

Python <x>, chapkit <x>, servicekit <x>, <numerically relevant packages>. Full
table in `tests/golden/VERSIONS.md`. Wheel audit: all <n> runtime packages
install from wheels on manylinux x86_64 and aarch64 under cp313.

## Verification

- `uv run ruff format --check . && uv run ruff check .` clean
- `uv run pytest -v`: <n> passed (<t>)
- `uv run chapkit test --url <url>` and `<weekly invocation>`: ALL TESTS PASSED
- `scripts/parity.py` <kinds>: <result> (tables above)
- `chap eval --model-name <url> --run-config.is-chapkit-model` with <n> splits x
  <n> periods on <dataset>: completes and writes `eval.nc` (chap-core <version>)
- `make test-docker` (<arch> host, image <size>): build <t>, chapkit test
  <kinds> ALL TESTS PASSED
- GitHub Actions on ubuntu x86_64: `<jobs>` green

<Anything that could not be run goes here as "skipped, because ...", not
omitted.>

## Notes for reviewers

- <Any tolerance that had to be loosened, with the exact numbers: how many cells,
  how far off, in absolute and relative terms, and why that is physically
  negligible.>
- <Any upstream limitation, e.g. a released chap-core version that cannot consume
  a declared period_type, with the workaround.>
- <Registry / image coordinates.>
- <Backwards compatibility of stored chap-core configurations.>

## How to run

```
uv sync
uv run python main.py            # http://localhost:9090
uv run pytest -v
make test-docker
```
```

---

## Notes on writing it

- **The parity table is the PR.** Put it above the fold; a reviewer who reads
  nothing else should still see "5400 / 5400 cells exactly equal".
- **Keep separate claims separate.** "The dependency bump changed nothing" and
  "the conversion changed nothing" are two claims with two pieces of evidence.
  Merging them hides which one was actually tested.
- **Losses are decisions.** Every dropped MLproject field, every removed option,
  every loosened tolerance gets a row and a reason.
- **Point at the step log.** `docs/migration-to-chapkit.md` carries the detail;
  the PR carries the conclusions.
