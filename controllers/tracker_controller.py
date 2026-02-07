from __future__ import annotations

from datetime import date
from typing import Dict, Tuple

from flask import Blueprint, jsonify, request, session

from data.food_store import FoodRepository

MAX_TRACKER_ITEMS = 60


def create_tracker_api(food_repo: FoodRepository) -> Blueprint:
    bp = Blueprint("tracker_api", __name__)

    @bp.get("/api/tracker")
    def get_tracker():
        local_date = request.args.get("local_date", "").strip()
        if not local_date:
            return jsonify({"error": "local_date is required"}), 400

        _reset_if_new_day(local_date)
        return jsonify(_serialize_tracker(food_repo))

    @bp.post("/api/tracker/add")
    def add_item():
        data = request.get_json(silent=True) or {}
        food_id, local_date = _parse_payload(data)
        if not food_id or not local_date:
            return jsonify({"error": "food_id and local_date are required"}), 400

        _reset_if_new_day(local_date)
        tracker = _get_tracker()
        key = str(food_id)

        if key not in tracker and len(tracker) >= MAX_TRACKER_ITEMS:
            return jsonify({"error": "tracker item limit reached"}), 400

        tracker[key] = tracker.get(key, 0) + 1
        _set_tracker(tracker, local_date)
        return jsonify(_serialize_tracker(food_repo))

    @bp.post("/api/tracker/update")
    def update_item():
        data = request.get_json(silent=True) or {}
        food_id, local_date = _parse_payload(data)
        if not food_id or not local_date:
            return jsonify({"error": "food_id and local_date are required"}), 400

        quantity = data.get("quantity")
        if quantity is None:
            return jsonify({"error": "quantity is required"}), 400

        _reset_if_new_day(local_date)
        tracker = _get_tracker()
        key = str(food_id)
        next_qty = int(quantity)
        if next_qty <= 0:
            tracker.pop(key, None)
        else:
            tracker[key] = next_qty
        _set_tracker(tracker, local_date)
        return jsonify(_serialize_tracker(food_repo))

    @bp.post("/api/tracker/remove")
    def remove_item():
        data = request.get_json(silent=True) or {}
        food_id, local_date = _parse_payload(data)
        if not food_id or not local_date:
            return jsonify({"error": "food_id and local_date are required"}), 400

        _reset_if_new_day(local_date)
        tracker = _get_tracker()
        tracker.pop(str(food_id), None)
        _set_tracker(tracker, local_date)
        return jsonify(_serialize_tracker(food_repo))

    @bp.post("/api/tracker/clear")
    def clear_tracker():
        data = request.get_json(silent=True) or {}
        local_date = str(data.get("local_date", "")).strip()
        if not local_date:
            return jsonify({"error": "local_date is required"}), 400

        _set_tracker({}, local_date)
        return jsonify(_serialize_tracker(food_repo))

    return bp


def _parse_payload(data: dict) -> Tuple[int | None, str | None]:
    food_id = data.get("food_id")
    if food_id is not None:
        try:
            food_id = int(food_id)
        except (TypeError, ValueError):
            food_id = None
    local_date = str(data.get("local_date", "")).strip() or None
    return food_id, local_date


def _get_tracker() -> Dict[str, int]:
    return dict(session.get("tracker", {}))


def _set_tracker(tracker: Dict[str, int], local_date: str) -> None:
    session["tracker"] = tracker
    session["tracker_date"] = local_date
    session.modified = True


def _reset_if_new_day(local_date: str) -> None:
    current_date = session.get("tracker_date")
    if current_date != local_date:
        _set_tracker({}, local_date)


def _serialize_tracker(food_repo: FoodRepository) -> dict:
    tracker = _get_tracker()
    ids = [int(food_id) for food_id in tracker.keys()]
    foods = food_repo.by_ids(ids)
    by_id = {food.id: food for food in foods if food.id is not None}

    items = []
    total = 0.0
    for food_id_str, quantity in tracker.items():
        food_id = int(food_id_str)
        food = by_id.get(food_id)
        if not food:
            continue
        item_total = float(food.iodine_mcg) * float(quantity)
        total += item_total
        items.append(
            {
                "food": food.to_dict(),
                "quantity": quantity,
                "item_total": round(item_total, 2),
            }
        )

    return {
        "items": items,
        "total_iodine": round(total, 2),
        "count": len(items),
        "date": session.get("tracker_date") or date.today().isoformat(),
    }
