.PHONY: clean test run

PYTHON ?= python

run:
	cd backend && $(PYTHON) main.py

test:
	cd backend && $(PYTHON) -m pytest tests/ -v

clean:
	cd backend && $(PYTHON) -c "from pathlib import Path; import shutil; \
Path('data/transactions.csv').unlink(missing_ok=True); \
shutil.rmtree('.pytest_cache', ignore_errors=True); \
[shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('__pycache__')]"
