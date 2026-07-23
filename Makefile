.PHONY: dev inspect test lint format

dev:
	python run.py

inspect:
	npx @modelcontextprotocol/inspector python run.py

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/ run.py

format:
	ruff format src/ tests/ run.py
