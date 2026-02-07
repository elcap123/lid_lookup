import csv
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

FOODS = []
CATEGORIES = []
FOODS_BY_CATEGORY = {}


def parse_csv():
    foods = []
    categories = []
    foods_by_category = {}

    csv_path = os.path.join(os.path.dirname(__file__), "iodine_data.csv")
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["Category"]
            min_val = float(row["Min"]) if row["Min"] else None
            max_val = float(row["Max"]) if row["Max"] else None

            food = {
                "description": row["Description"],
                "category": cat,
                "serving_size": row["Serving Size"],
                "serving_measure": row["Serving Measure"],
                "iodine_mcg": float(row["Iodine (mcg/serving)"]),
                "min": min_val,
                "max": max_val,
            }
            foods.append(food)

            if cat not in foods_by_category:
                categories.append(cat)
                foods_by_category[cat] = []
            foods_by_category[cat].append(food)

    return foods, categories, foods_by_category


FOODS, CATEGORIES, FOODS_BY_CATEGORY = parse_csv()


@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


@app.route("/api/search")
def search():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify([])
    results = [f for f in FOODS if query in f["description"].lower()]
    return jsonify(results)


@app.route("/api/category/<category_name>")
def category(category_name):
    items = FOODS_BY_CATEGORY.get(category_name, [])
    return jsonify(items)


if __name__ == "__main__":
    app.run(debug=True)
