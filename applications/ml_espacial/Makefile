.PHONY: test run-v01 run-v02 run-v03 run-v04 prepare-natural-earth clean

test:
	python -m pytest -q

run-v01:
	python -m src.run_experiment --config config/experimento_sintetico.yml

run-v02:
	python -m src.run_experiment --config config/experimento_sintetico_v0_2.yml

run-v03:
	python -m src.run_experiment --config config/experimento_sintetico_v0_3.yml

prepare-natural-earth:
	python scripts/prepare_natural_earth.py

run-v04:
	python -m src.run_experiment --config config/experimento_natural_earth_v0_4.yml

clean:
	rm -rf outputs/*
