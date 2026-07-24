.PHONY: clean test run

PYTHON ?= python

run:
	$(PYTHON) main.py

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; \
Path('data/transactions.csv').unlink(missing_ok=True); \
shutil.rmtree('.pytest_cache', ignore_errors=True); \
[shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('__pycache__')]"
