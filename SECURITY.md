# Security policy

This pipeline connects to production factory ERPs over SQL Server, so
the security bar is higher than a typical side project. This document
describes what is protected, how, and how to report what isn't.

## Supported versions

Continuous deployment from `main`. The supported version is always the
latest commit on `main`.

## Threat model

Six defence layers protect the source ERP (documented in full in
README § Safety):

| Layer | Where | What it stops |
| --- | --- | --- |
| Config guard | `extract/config.py` | SA / admin credentials in `SOURCE_DB` |
| Query validator | `extract/extractor.py` | `SELECT *`, SQL injection, write keywords (`DROP`/`DELETE`/`INSERT`/`UPDATE`/`ALTER`/`TRUNCATE`/`EXEC`/`xp_`/`sp_`) |
| Pydantic models | `models/` | Bad data types, empty primary keys |
| Docker sandbox | `docker-compose.yml` | Host filesystem access, open ports other than those declared |
| Read-only DB user | `scripts/init_sandbox.sql` | Any write at the database level |
| Setup script | `scripts/setup_sandbox.py` | Running against non-localhost targets |

A vulnerability that bypasses any one of those layers — or defeats all
six in combination — is critical.

Additional surfaces:

- **FastAPI** — every endpoint is read-only; request bodies are
  validated by Pydantic before reaching a query.
- **Prefect flows** — orchestration only; they call into
  `extract/` which is already protected.
- **n8n workflows** — read-only to the FastAPI endpoints.

## Reporting a vulnerability

**Do not open a public GitHub issue for a security problem.**

Report privately via the GitHub security advisory form:

<https://github.com/Pawansingh3889/production-analytics-pipeline/security/advisories/new>

A good report has:

1. **What you found** — one-sentence description.
2. **Reproduction** — exact command, query, or configuration. If a
   write reaches the ERP, include the captured SQL.
3. **Which safety layer(s) were bypassed.**
4. **Impact** — what an attacker with this foothold could do.
5. **Suggested fix** — optional. A patch or test case is ideal.

## What to expect

| Severity | Initial response | Fix target |
| --- | --- | --- |
| Critical (write to ERP) | within 24 hours | within 3 days |
| High (read bypass) | within 5 days | within 10 days |
| Medium | within 7 days | next minor cycle |
| Low / info | within 14 days | when scoped |

Response times are honest estimates, not legal commitments.

## Coordinated disclosure

Default: **90 days** from report to public disclosure, with earlier
publication when the fix is deployed and the reporter agrees. Longer
windows where an upstream dependency fix is required (sqlparse,
SQLAlchemy, Prefect).

## Scope

**In scope:**

- `extract/`, `models/`, `dbt_production/`, `api/`, `workflow/`,
  `reports/`, `sql/`, `infra/`, `scripts/`
- Any configuration file (`.env.example`, `pyproject.toml`,
  `docker-compose.yml`, `Makefile`)
- The n8n workflow definitions in `n8n/`

**Out of scope:**

- Upstream dependency CVEs (report upstream; link the advisory here)
- Issues requiring local shell, `sudo`, or the ability to edit
  configuration at runtime on the host
- Social engineering of the maintainer or contributors
- Bugs in a factory's own ERP deployment (that's the vendor's surface)

## Previous advisories

None.
