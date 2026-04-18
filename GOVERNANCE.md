# Production Analytics Pipeline governance

This pipeline moves real factory data. The governance mirrors that:
clear decision-making, strict scope, no surprises in code that runs
against a production ERP.

## Roles

### Maintainer

Currently: **[@Pawansingh3889](https://github.com/Pawansingh3889)**.

Final decision on:

- merges to `main`
- dependency additions (every new package is a new attack surface)
- changes to `extract/`, `models/`, or the six-layer safety model
- this governance document

Commits to:

- replying to issues and PRs within **7 calendar days**
- merging green, in-scope PRs within **14 calendar days** of the last
  review comment being addressed
- giving first-time contributors explicit go-ahead before they invest
  serious time on anything touching the safety surface

### Triage collaborator

Granted to contributors with three merged, in-scope PRs. Can label,
assign, and close duplicate / off-topic issues. Cannot merge or change
repository settings.

### Contributor

Anyone who files an issue or opens a PR. No paperwork.

## Decisions

Small changes (docs, tests, bug fixes, single-file refactors) — one
maintainer approval on the PR.

Larger changes — anything touching `extract/`, `models/`, the dbt
project, the FastAPI layer's shape, or adding a dependency — start as
an **issue with a proposal**. Proposal template:

1. the operational problem it solves
2. the change in bullet form
3. alternatives considered
4. which of the six safety layers it affects, if any

## Issue assignment (first-PR-wins)

1. Comment "I'd like to work on this" — 7-day soft claim.
2. Expire silently after 7 days; anyone may pick up.
3. If two PRs land, the first to pass CI and request review wins.

## Scope discipline

Hard lines that will not move on this project:

- **Read-only to the source ERP.** Every change that touches
  `extract/` must preserve all six safety layers documented in README.
  PRs that widen the write surface, even accidentally, get rejected
  and reopened with the safety work up front.
- **No `SELECT *` against the ERP.** The query validator in
  `extract/extractor.py` already blocks it; contributions must not
  try to work around it.
- **No credentials in code.** Ever. `.env` files are in `.gitignore`
  by default; tests and fixtures use placeholders.
- **Anonymised test data only.** The seed in `scripts/seed_mock_erp.py`
  is the only permissible source of example rows.

## Release cadence

Continuous deployment via CI. No tagged releases today. If that
changes:

- SemVer starting at 0.x
- breaking changes get one minor version of deprecation notice
- `CHANGELOG.md` will land before the first non-zero release

## Security

See `SECURITY.md`. Security issues route via private advisory, not
public issues.

## Changes to this document

Via PR from the maintainer. Community input welcome in issues.
