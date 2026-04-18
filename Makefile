.PHONY: setup setup-dev test run seed clean prefect-run prefect-serve export-powerbi lint format typecheck api scanapi dashboard-install dashboard-dev infra-init infra-plan infra-apply infra-destroy n8n-start n8n-stop

setup:
	pip install -r requirements.txt

# Full dev environment. ScanAPI is installed via pipx (not pip) because
# its strict MarkupSafe / rich pins collide with Prefect + FastAPI.
setup-dev:
	pip install -r requirements-dev.txt
	python -m pip install --user pipx
	python -m pipx ensurepath
	python -m pipx install 'scanapi>=2.12.0'

test:
	python -m pytest tests/ -v

run:
	python -m workflow.daily_run --full

seed:
	python scripts/seed_mock_erp.py

prefect-run:
	python -m workflow.prefect_flow

prefect-serve:
	prefect server start

export-powerbi:
	python -m reports.powerbi_export

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy extract/ models/ workflow/

api:
	uvicorn api.main:app --reload --port 8000

# ScanAPI integration tests. Starts uvicorn on 127.0.0.1:8000 in the
# background, waits for /health to come up (10 s cap), runs the spec,
# tears down cleanly. Report lands in scanapi-report/ (gitignored —
# open scanapi-report/scanapi-report.html after the run).
#
# Override BASE_URL to target a staging or production deploy:
#   make scanapi BASE_URL=https://staging.example.com
scanapi:
	@echo "Starting uvicorn in the background..."
	@python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 & echo $$! > /tmp/uvicorn.pid
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
	  curl -fsS http://127.0.0.1:8000/health > /dev/null && break || sleep 1; \
	done
	@BASE_URL=$${BASE_URL:-http://127.0.0.1:8000} scanapi run scanapi/scanapi.yaml -o scanapi-report/scanapi-report.html; \
	  SCANAPI_EXIT=$$?; \
	  kill $$(cat /tmp/uvicorn.pid) 2>/dev/null || true; \
	  rm -f /tmp/uvicorn.pid; \
	  exit $$SCANAPI_EXIT

dashboard-install:
	cd dashboard && npm install

dashboard-dev:
	cd dashboard && npm run dev

clean:
	rm -rf data/*.db data/pipeline_state.json __pycache__ scanapi-report scanapi-report.html

n8n-start:
	cd n8n && docker-compose up -d

n8n-stop:
	cd n8n && docker-compose down

infra-init:
	cd infra && tofu init

infra-plan:
	cd infra && tofu plan

infra-apply:
	cd infra && tofu apply -auto-approve

infra-destroy:
	cd infra && tofu destroy -auto-approve
