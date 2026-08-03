PYTHON ?= python

.PHONY: install demo run test clean

install:
	$(PYTHON) -m pip install --no-build-isolation -e ".[test]"

demo:
	$(PYTHON) scripts/create_demo_data.py --output data/raw

run: demo
	PYTHONPATH=src $(PYTHON) -m dados_espaciais.run --config config/demo.yml

test:
	PYTHONPATH=src $(PYTHON) -m pytest -q

clean:
	rm -rf outputs .pytest_cache
