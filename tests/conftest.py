from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from app import create_app


@pytest.fixture()
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def app(tmp_path: Path, fixture_dir: Path):
    csv_path = tmp_path / "iodine.csv"
    shutil.copyfile(fixture_dir / "iodine_small.csv", csv_path)
    db_path = tmp_path / "test.db"

    app = create_app(csv_path=str(csv_path), db_path=str(db_path))
    app.config.update(TESTING=True)
    return app


@pytest.fixture()
def client(app):
    return app.test_client()
