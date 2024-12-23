# Makefiles provide a handy way to codify commands. Instead of having to copy
# paste commands from a README, you can  execute them as "make <command>": for
# example "make all" or "make run". If your system doesn't include make, or if
# you just want to avoid it, you can always run the commands directly.

lint:
	black .
	ruff check --fix --show-fixes
	pyright .
unit-test:
	python -m pytest -m "not integration" --disable-warnings
integration-test:
	python -m pytest -m integration --disable-warnings
unit-test-coverage:
	python -m pytest -m "not integration" --cov-report term-missing --cov=src
