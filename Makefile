.PHONY: run install docs

run:
	poetry run uvicorn geoproc.server:app --reload

install:
	poetry install

docs:
	poetry run sphinx-autobuild docs docs/_build/html
