import os
from typing import Optional
from flask import Flask

from controllers.food_controller import create_food_api
from controllers.tracker_controller import create_tracker_api
from data.food_store import init_db
from views.main_view import create_main_view


def create_app(
    *,
    csv_path: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
        "SESSION_COOKIE_SECURE", "0"
    ) == "1"

    base_dir = os.path.dirname(__file__)
    resolved_csv_path = csv_path or os.path.join(base_dir, "iodine_data.csv")
    resolved_db_path = db_path or os.path.join(base_dir, "iodine.db")
    food_repo = init_db(resolved_csv_path, resolved_db_path)

    app.register_blueprint(create_main_view(food_repo))
    app.register_blueprint(create_food_api(food_repo))
    app.register_blueprint(create_tracker_api(food_repo))

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5001)
