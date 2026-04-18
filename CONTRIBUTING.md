# Contributing to production-analytics-pipeline

This pipeline ingests live factory ERP data. The same bar that applies to
production SQL applies to contributions: explicit, reversible, and
testable beats clever every time.

## The Prime Directive

**Never widen the read-only surface to the source ERP.** The six-layer
safety model in `README.md` exists because one buggy PR against a
production factory's ERP can cost a shift. Contributions that touch
`extract/`, `models/`, or the `SOURCE_DB` config must preserve every
existing layer and add a test that demonstrates it. If a change can't be
made read-only, open an issue to discuss before coding.

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/production-analytics-pipeline.git
cd production-analytics-pipeline
make setup       # install dependencies
make seed        # seed local mock ERP (SQLite) with synthetic data
make test        # run pytest
make api         # start FastAPI on localhost:8000
```

The seed script (`scripts/seed_mock_erp.py`) is the only database the test
suite touches. It is deterministic and contains no real customer, vessel,
or employee data.

## How to Contribute

1. **Find an issue** or open one describing the change. Good labels to
   watch: `good first issue`, `help wanted`, `safety`.
2. **Fork and branch.** `feature/<short-name>` or `bugfix/<short-name>`.
3. **Code, commit small.** One logical change per commit, conventional
   commit style (`feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `test:`). The
   existing history gives you examples.
4. **Test before you push.**
   - `make lint` — ruff must pass
   - `make typecheck` — mypy must pass
   - `make test` — pytest must pass
   Don't skip CI locally; GitHub Actions will just fail the same checks
   30 minutes later.
5. **Open the pull request.** Explain *what* changed, *why*, and what you
   tested. Reference the issue number. One-line bodies are fine for trivial
   doc fixes; anything that touches `extract/`, `models/`, or SQL needs a
   proper description.

## What belongs in each directory

| Path | What lands here |
|---|---|
| `extract/` | Watermark-based incremental load from the ERP. Add a safety test for any new file. |
| `models/` | Pydantic models for ERP rows. Type-level protection against bad data. |
| `dbt_production/` | Staging views and mart tables. dbt tests (`schema.yml`) are mandatory for new marts. |
| `api/` | FastAPI endpoints. One endpoint = one file + one test in `tests/`. |
| `workflow/` | Prefect flows and daily runs. Keep orchestration thin — logic lives in `extract/` and `dbt_production/`. |
| `reports/` | Power BI CSV exports. Pure functions on mart tables. |
| `sql/` | Reference queries (not imported by code). Useful as documentation. |
| `infra/` | OpenTofu. Never commit secrets, state files, or `.terraform/`. |
| `scripts/` | One-off helpers. Anything used in CI or a Make target belongs under `extract/` or `workflow/`. |

## Code Standards

- Python 3.11+.
- Line length 100 (ruff default; see `pyproject.toml`).
- Type hints on every public function. `make typecheck` must pass.
- Docstrings on every module and public function — explain the *why*, not
  just the *what*. A reviewer should be able to understand the trade-off
  you made without reading the git log.
- Tests for new code go under `tests/` in a file matching the module name
  (`extract/incremental.py` -> `tests/test_incremental.py`).

## Safety rules (non-negotiable)

- **No `SELECT *` in SQL against the ERP.** The query validator in
  `extract/extractor.py` already blocks it; don't try to work around it.
- **No credentials in code, commits, or issue text.** The sandbox README
  uses placeholder values; real credentials live in environment variables
  and in local `.env` files that are in `.gitignore`.
- **No writes to the source ERP.** The read-only user at the database
  level is the last line of defence, but your PR shouldn't rely on it.
- **Anonymise test data.** Synthetic names, batch codes, customers,
  vessels. Never commit a CSV or SQL fixture containing real operator
  initials or customer orders.

## Running safety checks locally

```bash
# full check before opening a PR
make lint typecheck test
```

If any of these fail, the PR will fail CI too — fix them first.

## Reporting bugs

Open an issue with:

- Steps to reproduce (the pipeline command, the Prefect flow name, the
  API endpoint path).
- Expected vs actual behaviour.
- Python version, OS, whether you're on the SQLite dev setup or a live
  SQL Server.
- A redacted traceback if applicable — **never** paste production data.

## Feature requests

Open an issue describing:

- The factory problem it solves.
- Which directory it affects.
- Whether it needs a new dependency (most answers should be "no").

## Recognition

Merged PRs land in the git history permanently. Substantial contributions
are called out in the `README.md` credits section when appropriate.
