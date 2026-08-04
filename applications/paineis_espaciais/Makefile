.PHONY: install demo run test clean

install:
	python -m pip install --upgrade pip setuptools wheel
	python -m pip install -e .[dev]

demo:
	python scripts/create_demo_data.py --output-dir data/demo

run: demo
	paineis-espaciais config/demo.yml

test:
	python -m pytest -q

clean:
	rm -rf outputs/demo data/demo .pytest_cache src/*.egg-info src/*/*.egg-info
