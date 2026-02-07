from __future__ import annotations

from flask import Blueprint, jsonify, request

from data.food_store import FoodRepository


def create_food_api(food_repo: FoodRepository) -> Blueprint:
    bp = Blueprint("food_api", __name__)

    @bp.get("/api/search")
    def search():
        query = request.args.get("q", "").strip().lower()
        if not query:
            return jsonify([])
        results = [food.to_dict() for food in food_repo.search(query)]
        return jsonify(results)

    @bp.get("/api/category/<category_name>")
    def category(category_name: str):
        items = food_repo.by_category(category_name)
        return jsonify([food.to_dict() for food in items])

    return bp
