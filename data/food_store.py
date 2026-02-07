from __future__ import annotations

import csv
import re
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

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
                SELECT id, description, category, serving_size, serving_measure,
                       iodine_mcg, min, max, standardized_quantity, standardized_unit
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
                SELECT id, description, category, serving_size, serving_measure,
                       iodine_mcg, min, max, standardized_quantity, standardized_unit
                FROM foods
                WHERE category = ?
                ORDER BY description
                """,
                (category,),
            ).fetchall()
        return [Food.from_db_row(row) for row in rows]

    def by_ids(self, food_ids: Iterable[int]) -> List[Food]:
        ids = [int(food_id) for food_id in food_ids]
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, description, category, serving_size, serving_measure,
                       iodine_mcg, min, max, standardized_quantity, standardized_unit
                FROM foods
                WHERE id IN ({placeholders})
                """,
                ids,
            ).fetchall()
        return [Food.from_db_row(row) for row in rows]


def init_db(csv_path: str, db_path: str) -> FoodRepository:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
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
                max REAL,
                standardized_quantity REAL,
                standardized_unit TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_foods_category ON foods(category)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_foods_description ON foods(description)"
        )

        _ensure_standardized_columns(conn)

        row = conn.execute("SELECT COUNT(*) AS count FROM foods").fetchone()
        count = row[0] if row else 0
        if count == 0:
            _ingest_csv(conn, csv_path)
        else:
            _backfill_standardized_columns(conn)

    return FoodRepository(db_path=db_path)


def _ingest_csv(conn: sqlite3.Connection, csv_path: str) -> None:
    foods = list(_read_csv(csv_path))
    conn.executemany(
        """
        INSERT INTO foods (
            description, category, serving_size, serving_measure,
            iodine_mcg, min, max, standardized_quantity, standardized_unit
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        foods,
    )


def _read_csv(csv_path: str) -> Iterable[tuple]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            food = Food.from_row(row)
            standardized_quantity, standardized_unit = _standardize_measure(
                food.serving_size,
                food.serving_measure,
            )
            yield (
                food.description,
                food.category,
                food.serving_size,
                food.serving_measure,
                food.iodine_mcg,
                food.min,
                food.max,
                standardized_quantity,
                standardized_unit,
            )


def _ensure_standardized_columns(conn: sqlite3.Connection) -> None:
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(foods)").fetchall()
    }
    if "standardized_quantity" not in columns:
        conn.execute("ALTER TABLE foods ADD COLUMN standardized_quantity REAL")
    if "standardized_unit" not in columns:
        conn.execute("ALTER TABLE foods ADD COLUMN standardized_unit TEXT")


def _backfill_standardized_columns(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT id, serving_size, serving_measure
        FROM foods
        WHERE standardized_quantity IS NULL OR standardized_unit IS NULL
        """
    ).fetchall()

    updates: List[Tuple[Optional[float], Optional[str], int]] = []
    for row in rows:
        standardized_quantity, standardized_unit = _standardize_measure(
            row["serving_size"],
            row["serving_measure"],
        )
        updates.append((standardized_quantity, standardized_unit, row["id"]))

    if updates:
        conn.executemany(
            """
            UPDATE foods
            SET standardized_quantity = ?, standardized_unit = ?
            WHERE id = ?
            """,
            updates,
        )


_UNIT_PATTERNS = {
    "cup": re.compile(r"\\b(cup|cups)\\b"),
    "tbsp": re.compile(r"\\b(tbsp|tablespoon|tablespoons)\\b"),
    "tsp": re.compile(r"\\b(tsp|teaspoon|teaspoons)\\b"),
    "oz": re.compile(r"\\b(oz|ounce|ounces)\\b"),
    "g": re.compile(r"\\b(g|gram|grams)\\b"),
    "kg": re.compile(r"\\b(kg|kilogram|kilograms)\\b"),
    "ml": re.compile(r"\\b(ml|milliliter|milliliters)\\b"),
    "l": re.compile(r"\\b(l|liter|liters)\\b"),
    "lb": re.compile(r"\\b(lb|lbs|pound|pounds)\\b"),
}


def _standardize_measure(
    serving_size: str,
    serving_measure: str,
) -> tuple[Optional[float], Optional[str]]:
    quantity = _parse_quantity(serving_size)
    if quantity is None:
        return None, None

    unit = _normalize_unit(serving_measure)
    if unit is None:
        return None, None

    return quantity, unit


def _normalize_unit(measure: str) -> Optional[str]:
    if not measure:
        return None
    measure = measure.lower()
    for unit, pattern in _UNIT_PATTERNS.items():
        if pattern.search(measure):
            return unit
    return None


def _parse_quantity(value: str) -> Optional[float]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None

    if " " in value:
        parts = value.split()
        if len(parts) == 2:
            whole = _parse_quantity(parts[0])
            frac = _parse_fraction(parts[1])
            if whole is not None and frac is not None:
                return whole + frac

    frac = _parse_fraction(value)
    if frac is not None:
        return frac

    try:
        return float(value)
    except ValueError:
        return None


def _parse_fraction(value: str) -> Optional[float]:
    if "/" not in value:
        return None
    parts = value.split("/", 1)
    if len(parts) != 2:
        return None
    try:
        numerator = float(parts[0])
        denominator = float(parts[1])
        if denominator == 0:
            return None
        return numerator / denominator
    except ValueError:
        return None
