# `check` is the only supported entry point: it orders lint -> type -> test
# because mypy needs the generated stubs that ruff's fix step can invalidate.
check:
	uv run ruff check --fix weather tests
	uv run mypy weather
	uv run pytest -q

serve:
	uv run uvicorn weather.app:api --reload --port 8100
