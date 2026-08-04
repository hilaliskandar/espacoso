PYTHON ?= python

.PHONY: install demo-data test run clean

install:
	$(PYTHON) -m pip install --no-build-isolation -e ".[dev]"

demo-data:
	$(PYTHON) scripts/create_demo_data.py --output-dir data/demo

test:
	$(PYTHON) -m pytest -q

run: demo-data
	$(PYTHON) -m maup_sensibilidade.run config/demo.yml

clean:
	rm -rf outputs/demo/* data/demo/* .pytest_cache
