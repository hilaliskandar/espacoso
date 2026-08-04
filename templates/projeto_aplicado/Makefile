PYTHON ?= python

.PHONY: install demo-data test run clean

install:
	$(PYTHON) -m pip install --no-build-isolation -e .

demo-data:
	$(PYTHON) scripts/create_demo_data.py

test:
	$(PYTHON) -m pytest -q

run: demo-data
	$(PYTHON) -m projeto_aplicado.run --config config/projeto.yml

clean:
	rm -rf outputs/* data/raw/territorios_demo.gpkg .pytest_cache __pycache__
