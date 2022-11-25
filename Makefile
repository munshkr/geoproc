.PHONY: run install

run:
	poetry run uvicorn eotoolkit.server:app --reload

install:
	poetry install
