.PHONY: run install

run:
	poetry run uvicorn geoproc.server:app --reload

install:
	poetry install
