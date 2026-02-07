from __future__ import annotations

import sqlite3
from pathlib import Path

from data.food_store import init_db


def test_init_db_ingests_csv(tmp_path: Path):
    csv_path = tmp_path / "iodine.csv"
    csv_path.write_text(
        "Description,Category,Serving Size,Serving Measure,Iodine (mcg/serving),Min,Max\n"
        "Milk,Dairy,1,cup,56,45,65\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "test.db"

    repo = init_db(str(csv_path), str(db_path))

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM foods").fetchone()
        assert row[0] == 1

    assert repo.get_categories() == ["Dairy"]
