from __future__ import annotations

from flask import Blueprint, render_template

from data.food_store import FoodRepository


def create_main_view(food_repo: FoodRepository) -> Blueprint:
    bp = Blueprint("main_view", __name__)

    @bp.get("/")
    def index():
        return render_template("index.html", categories=food_repo.get_categories())

    return bp
