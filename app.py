import os
from flask import Flask

from controllers.food_controller import create_food_api
from data.food_store import init_db
from views.main_view import create_main_view


def create_app(
    *,
    csv_path: str | None = None,
    db_path: str | None = None,
) -> Flask:
    app = Flask(__name__)

    base_dir = os.path.dirname(__file__)
    resolved_csv_path = csv_path or os.path.join(base_dir, "iodine_data.csv")
    resolved_db_path = db_path or os.path.join(base_dir, "iodine.db")
    food_repo = init_db(resolved_csv_path, resolved_db_path)

    app.register_blueprint(create_main_view(food_repo))
    app.register_blueprint(create_food_api(food_repo))

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5001)
