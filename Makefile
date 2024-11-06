clean: format lint

lint:
	poetry run ruff check --fix .

format:
	poetry run ruff format .
