# CLAUDE.md

## Project Overview

Flask web app for browsing iodine content in foods. Data is loaded from a CSV (`iodine_data.csv`) into a SQLite database (`iodine.db`) on startup. Users can search foods by name or browse by category.

## Architecture

MVC pattern with Flask Blueprints:

- **Models** (`models/food.py`) — `Food` frozen dataclass with `from_row`, `from_db_row`, `to_dict` methods
- **Data** (`data/food_store.py`) — `FoodRepository` (SQLite-backed) with `search`, `by_category`, `get_categories`; `init_db` handles schema creation and CSV ingestion
- **Controllers** (`controllers/food_controller.py`) — REST API blueprint (`/api/search`, `/api/category/<name>`)
- **Views** (`views/main_view.py`) — Renders `index.html` with category list

App factory: `create_app()` in `app.py` accepts optional `csv_path` and `db_path` for testability.

## Tech Stack

- Python, Flask
- SQLite (via `sqlite3` stdlib)
- Jinja2 templates, plain CSS
- pytest for testing

## Commands

- **Run dev server:** `python app.py` (port 5001)
- **Run tests:** `pytest`

## Code Conventions

- Use `from __future__ import annotations` in all Python files
- Frozen dataclasses for models
- Type hints on function signatures
- Blueprint factory functions (e.g., `create_food_api(repo) -> Blueprint`)
- Dependency injection via app factory — pass `FoodRepository` to blueprints
- Tests use `tmp_path` fixtures with test CSV data; see `tests/conftest.py` for shared fixtures
