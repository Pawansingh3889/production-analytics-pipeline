.PHONY: setup test run seed clean

setup:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

run:
	python -m workflow.daily_run --full

seed:
	python scripts/seed_mock_erp.py

clean:
	rm -rf data/*.db data/pipeline_state.json __pycache__
