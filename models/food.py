from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class Food:
    id: Optional[int]
    description: str
    category: str
    serving_size: str
    serving_measure: str
    iodine_mcg: float
    min: Optional[float]
    max: Optional[float]
    standardized_quantity: Optional[float]
    standardized_unit: Optional[str]

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Food":
        min_val = float(row["Min"]) if row["Min"] else None
        max_val = float(row["Max"]) if row["Max"] else None

        return cls(
            id=None,
            description=row["Description"],
            category=row["Category"],
            serving_size=row["Serving Size"],
            serving_measure=row["Serving Measure"],
            iodine_mcg=float(row["Iodine (mcg/serving)"]),
            min=min_val,
            max=max_val,
            standardized_quantity=None,
            standardized_unit=None,
        )

    @classmethod
    def from_db_row(cls, row: Mapping[str, Any]) -> "Food":
        return cls(
            id=row["id"] if "id" in row.keys() else None,
            description=row["description"],
            category=row["category"],
            serving_size=row["serving_size"],
            serving_measure=row["serving_measure"],
            iodine_mcg=float(row["iodine_mcg"]),
            min=row["min"],
            max=row["max"],
            standardized_quantity=row["standardized_quantity"],
            standardized_unit=row["standardized_unit"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "category": self.category,
            "serving_size": self.serving_size,
            "serving_measure": self.serving_measure,
            "iodine_mcg": self.iodine_mcg,
            "min": self.min,
            "max": self.max,
            "standardized_quantity": self.standardized_quantity,
            "standardized_unit": self.standardized_unit,
        }
