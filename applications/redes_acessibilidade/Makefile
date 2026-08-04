PYTHON ?= python

.PHONY: install demo-data test run clean

install:
	$(PYTHON) -m pip install --no-build-isolation -e .

demo-data:
	$(PYTHON) scripts/create_demo_data.py

test:
	$(PYTHON) -m pytest -q

run: demo-data
	$(PYTHON) -m redes_acessibilidade.run --config config/demo.yml

clean:
	rm -rf outputs/demo/* data/raw/rede_demo.gpkg data/raw/territorios_demo.gpkg .pytest_cache
