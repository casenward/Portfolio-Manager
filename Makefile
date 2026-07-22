.PHONY: clean test

PYTHON ?= python

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; \
Path('data/transactions.csv').unlink(missing_ok=True); \
shutil.rmtree('.pytest_cache', ignore_errors=True); \
[shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('__pycache__')]"

test:
	$(PYTHON) -m pytest test/ -v
