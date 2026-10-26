.PHONY: install api bot test lint
install:
	pip install -e '.[dev]'
api:
	uvicorn app.main:app --reload
bot:
	python -m app.bot.main
test:
	pytest
lint:
	ruff check app tests
