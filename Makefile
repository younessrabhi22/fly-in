MAP ?= maps/easy/01_linear_path.txt

install:
	uv sync

run:
	uv run python main.py $(MAP)

debug:
	uv run python -m pdb main.py $(MAP)

clean:
	rm -rf __pycache__ .mypy_cache
	find . -type d -name "__pycache__" -exec rm -r {} +

lint:
	uv run flake8 .
	uv run mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .

lint-strict:
	uv run flake8 .
	uv run mypy --strict .
