from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Optional

from models.food import Food


@dataclass(frozen=True)
class FoodRepository:
    db_path: str

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_categories(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM foods ORDER BY category"
            ).fetchall()
        return [row["category"] for row in rows]

    def search(self, query: str) -> List[Food]:
        if not query:
            return []
        like = f"%{query.lower()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT description, category, serving_size, serving_measure,
                       iodine_mcg, min, max
                FROM foods
                WHERE LOWER(description) LIKE ?
                ORDER BY description
                """,
                (like,),
            ).fetchall()
        return [Food.from_db_row(row) for row in rows]

    def by_category(self, category: str) -> List[Food]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT description, category, serving_size, serving_measure,
                       iodine_mcg, min, max
                FROM foods
                WHERE category = ?
                ORDER BY description
                """,
                (category,),
            ).fetchall()
        return [Food.from_db_row(row) for row in rows]


def init_db(csv_path: str, db_path: str) -> FoodRepository:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                serving_size TEXT NOT NULL,
                serving_measure TEXT NOT NULL,
                iodine_mcg REAL NOT NULL,
                min REAL,
                max REAL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_foods_category ON foods(category)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_foods_description ON foods(description)"
        )

        row = conn.execute("SELECT COUNT(*) AS count FROM foods").fetchone()
        count = row[0] if row else 0
        if count == 0:
            _ingest_csv(conn, csv_path)

    return FoodRepository(db_path=db_path)


def _ingest_csv(conn: sqlite3.Connection, csv_path: str) -> None:
    foods = list(_read_csv(csv_path))
    conn.executemany(
        """
        INSERT INTO foods (
            description, category, serving_size, serving_measure,
            iodine_mcg, min, max
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        foods,
    )


def _read_csv(csv_path: str) -> Iterable[tuple]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            food = Food.from_row(row)
            yield (
                food.description,
                food.category,
                food.serving_size,
                food.serving_measure,
                food.iodine_mcg,
                food.min,
                food.max,
            )
