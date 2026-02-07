from __future__ import annotations


def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Browse by Category" in res.data
    assert b"Today's Tracker" in res.data
    assert b"About This App" in res.data
    assert b"Low-iodine diets" in res.data
    assert b"https://github.com/elcap123/lid_lookup" in res.data
    assert b"Data Attribution" in res.data
    assert b"Daily Threshold" in res.data


def test_search_api(client):
    res = client.get("/api/search?q=milk")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["description"] == "Milk"


def test_category_api(client):
    res = client.get("/api/category/Protein")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["description"] == "Egg"


def test_tracker_flow(client):
    search = client.get("/api/search?q=milk")
    food_id = search.get_json()[0]["id"]

    res = client.post(
        "/api/tracker/add",
        json={"food_id": food_id, "local_date": "2026-02-07"},
    )
    data = res.get_json()
    assert res.status_code == 200
    assert data["count"] == 1
    assert data["items"][0]["quantity"] == 1

    res = client.post(
        "/api/tracker/update",
        json={"food_id": food_id, "quantity": 2, "local_date": "2026-02-07"},
    )
    data = res.get_json()
    assert data["items"][0]["quantity"] == 2
    assert data["total_iodine"] == 112

    res = client.post(
        "/api/tracker/remove",
        json={"food_id": food_id, "local_date": "2026-02-07"},
    )
    data = res.get_json()
    assert data["count"] == 0


def test_tracker_auto_reset(client):
    search = client.get("/api/search?q=egg")
    food_id = search.get_json()[0]["id"]

    client.post(
        "/api/tracker/add",
        json={"food_id": food_id, "local_date": "2026-02-07"},
    )
    res = client.get("/api/tracker?local_date=2026-02-08")
    data = res.get_json()
    assert data["count"] == 0


def test_tracker_item_limit(client):
    search = client.get("/api/search?q=milk")
    food_id = search.get_json()[0]["id"]

    with client.session_transaction() as sess:
        sess["tracker"] = {str(i): 1 for i in range(100, 160)}
        sess["tracker_date"] = "2026-02-07"

    res = client.post(
        "/api/tracker/add",
        json={"food_id": food_id, "local_date": "2026-02-07"},
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["error"] == "tracker item limit reached"
