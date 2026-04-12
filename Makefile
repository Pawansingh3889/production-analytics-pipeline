.PHONY: setup test run seed clean prefect-run prefect-serve export-powerbi lint format typecheck api

setup:
	pip install -r requirements.txt

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

clean:
	rm -rf data/*.db data/pipeline_state.json __pycache__
