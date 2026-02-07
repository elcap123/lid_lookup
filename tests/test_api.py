from __future__ import annotations


def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Browse by Category" in res.data


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
