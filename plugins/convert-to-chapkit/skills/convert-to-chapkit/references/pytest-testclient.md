# In-process service tests with pytest and TestClient

Drive the FastAPI app in-process through Starlette's `TestClient`: no port, no
container, no second terminal. With a `ShellModelRunner` the jobs still fork
real subprocesses into real temp workspaces, so nothing about the runner path is
mocked.

Add to the dev dependency group: `pytest>=8`, `httpx2>=2.13` (Starlette 1.6+
`TestClient` imports `httpx2`; with only `httpx` it still works but emits a
deprecation warning). Confirm against the installed Starlette version. In `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]      # so `from main import app` works when main.py is a root file
```

## `tests/__init__.py`

An empty file. Without it, pytest can import `conftest.py` twice under
different module names and `from tests.helpers import ...` creates a second copy
of the package's modules. Keep shared constants in `helpers.py`, not
`conftest.py`, for the same reason.

## `tests/conftest.py`

```python
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

# Must be set BEFORE `main` is imported: main.py reads DATABASE_URL at module
# import time. A file-backed SQLite database (not :memory:) so the background
# job worker and the polling requests share one database.
_DB_DIR = Path(tempfile.mkdtemp(prefix="<slug>_test_"))
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_DB_DIR}/test.db")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from tests.helpers import GOLDEN_DIR  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def golden_options() -> dict:
    """The user_option_values block the golden fixtures were produced with."""
    return yaml.safe_load((GOLDEN_DIR / "config.yaml").read_text())["user_option_values"]
```

The `# noqa: E402` comments are load-bearing: ruff's "module level import not at
top of file" would fail CI, and moving the imports up breaks the suite.

## `tests/helpers.py`

```python
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_DATA = REPO_ROOT / "example_data"
GOLDEN_DIR = REPO_ROOT / "tests" / "golden"

# A single job fits one model per location in a subprocess, after chapkit has
# copied the project into a fresh workspace. Generous on purpose: a slow CI
# runner should time out on the assertion, not on the clock.
JOB_TIMEOUT_SECONDS = 600


def read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV without losing the last ulp of any float."""
    return pd.read_csv(path, float_precision="round_trip")


def df_payload(df: pd.DataFrame) -> dict[str, Any]:
    """Serialize a pandas frame into chapkit's DataFrame wire format.

    NaN is not valid JSON; missing values become None, exactly as chap-core
    sends them.
    """
    rows = [
        [None if isinstance(v, float) and np.isnan(v) else v for v in row]
        for row in df.itertuples(index=False, name=None)
    ]
    return {"columns": df.columns.tolist(), "data": rows}


def wait_for_job(client: TestClient, job_id: str, timeout: int = JOB_TIMEOUT_SECONDS) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/v1/jobs/{job_id}").json()
        status = job.get("status")
        if status == "completed":
            return
        if status == "failed":
            pytest.fail(f"job {job_id} failed: {job.get('error')}")
        time.sleep(0.5)
    pytest.fail(f"job {job_id} did not complete within {timeout}s")


def create_config(client: TestClient, name: str, user_option_values: dict[str, Any]) -> str:
    """Create a config using the chap-core-shaped (nested) request body."""
    response = client.post(
        "/api/v1/configs",
        json={"name": name, "data": {"user_option_values": user_option_values}},
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def train(client: TestClient, config_id: str, data: pd.DataFrame) -> str:
    response = client.post("/api/v1/ml/$train", json={"config_id": config_id, "data": df_payload(data)})
    assert response.status_code in (200, 202), response.text
    body = response.json()
    wait_for_job(client, body["job_id"])
    return body["artifact_id"]          # straight off the 202 - no artifact listing needed


def predict(client: TestClient, artifact_id: str, historic: pd.DataFrame, future: pd.DataFrame) -> pd.DataFrame:
    response = client.post(
        "/api/v1/ml/$predict",
        json={"artifact_id": artifact_id, "historic": df_payload(historic), "future": df_payload(future)},
    )
    assert response.status_code in (200, 202), response.text
    body = response.json()
    wait_for_job(client, body["job_id"])

    download = client.get(f"/api/v1/artifacts/{body['artifact_id']}/$download")
    assert download.status_code == 200, download.text
    return pd.DataFrame(download.json())


def sample_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("sample_")]
```

## `tests/test_service.py` - the test set

```python
PARITY_RTOL = float(os.getenv("PARITY_RTOL", "1e-6"))
PARITY_ATOL = float(os.getenv("PARITY_ATOL", "1e-6"))
```

| Test | What it pins down |
|---|---|
| `test_health` | service boots; database and registration subsystems healthy |
| `test_info` | `id`, `display_name`, `period_type`, `required_covariates`, `allow_free_additional_continuous_covariates`, author metadata - i.e. the MLproject contract fields survived |
| `test_config_schema_defaults` | every surviving `user_option` is in `GET /api/v1/configs/$schema` with the MLproject default and a non-empty description, removed options are absent, and `required` is empty (chap-core posts only `user_option_values`) |
| `test_config_hoists_user_option_values` | a chap-core-shaped POST lands on the declared fields; `prediction_periods` gets its default; no leftover `user_option_values` extra |
| `test_config_flat_fields_win_over_nested` | unit test on the class: flat only, nested only, both (flat wins) |
| `test_<kind>_reproduces_legacy_golden` | one per period type: exact column list, exact `(time_period, location)` order, `assert_allclose(rtol, atol)` over the sample cells |
| `test_unseen_location_fallback` | a future row for a location absent from training still returns finite, non-negative samples |
| `test_future_row_order_preserved` | future frame shuffled with a fixed `random_state`; output row order equals input row order |
| `test_legacy_<removed>_options_are_accepted_and_ignored` | one per removed config field: HTTP body -> stored config -> `dump_config_yaml` -> the model's config object, without paying for a job |

The golden assertion:

```python
def _assert_matches_golden(predictions, golden, label):
    assert list(predictions.columns) == list(golden.columns), f"{label}: column list changed"
    assert len(predictions) == len(golden), f"{label}: row count changed"
    for key in ("time_period", "location"):
        assert predictions[key].astype(str).tolist() == golden[key].astype(str).tolist(), (
            f"{label}: {key} order changed"
        )

    cols = sample_columns(golden)
    got = predictions[cols].to_numpy(dtype=float)
    want = golden[cols].to_numpy(dtype=float)

    exact = int(np.count_nonzero(got == want))
    print(f"\n{label}: {exact} / {got.size} cells exactly equal to the legacy golden output")

    np.testing.assert_allclose(got, want, rtol=PARITY_RTOL, atol=PARITY_ATOL)
```

Printing the exactly-equal count matters: it is the number that goes in the PR,
and it distinguishes "identical" from "within tolerance".

The hoisting test, verbatim from the real suite:

```python
def test_config_hoists_user_option_values(client):
    response = client.post(
        "/api/v1/configs",
        json={"name": "pytest-hoist", "data": {"user_option_values": {"n_samples": 7}}},
    )
    assert response.status_code in (200, 201), response.text
    data = client.get(f"/api/v1/configs/{response.json()['id']}").json()["data"]
    assert data["n_samples"] == 7
    assert data["prediction_periods"] == 3          # chap-core never sends it
    assert "user_option_values" not in data         # the nested dict must not survive
```

The extra-field compatibility test (run it for every option you remove):

```python
def test_legacy_season_length_options_are_accepted_and_ignored(client):
    response = client.post(
        "/api/v1/configs",
        json={"name": "pytest-legacy", "data": {"user_option_values": {"season_length_monthly": 6, "n_samples": 7}}},
    )
    assert response.status_code in (200, 201), response.text
    data = client.get(f"/api/v1/configs/{response.json()['id']}").json()["data"]
    assert data["season_length_monthly"] == 6, "extra fields must survive, not 422"

    written = yaml.safe_load(dump_config_yaml(MyConfig.model_validate(data), "chap_core"))
    assert written["user_option_values"]["season_length_monthly"] == 6      # carried into config.yml
    model_config = ModelConfig.from_user_options(written["user_option_values"])
    assert not hasattr(model_config, "season_length_monthly")               # and filtered before the model
```

## Notes

- Share one training artifact across the tests that do not need their own, with
  a session-scoped fixture. Training is the expensive part.
- `FunctionalModelRunner` models do not fork subprocesses, so their suites run
  in seconds and can keep the default timeout much lower.
- For an **R** model this whole approach fails on a laptop without R installed
  (`Rscript` -> exit 127). Test R services in Docker with `chapkit test` instead
  and say so in the PR.

Working reference:
https://github.com/chap-models/mstl_arima/tree/main/tests
