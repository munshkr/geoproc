.PHONY: run install test test-watch docs

run:
	poetry run uvicorn geoproc.server:app --reload

install:
	poetry install

test:
	poetry run pytest

test-watch:
	poetry run ptw -- -v

docs:
	poetry run sphinx-autobuild docs docs/_build/html
