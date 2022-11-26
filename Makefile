.PHONY: run install

run:
	poetry run uvicorn eoproc.server:app --reload

install:
	poetry install
