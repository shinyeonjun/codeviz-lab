def test_read_examples(client):
    response = client.get("/api/v1/examples", params={"language": "python"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert len(payload["data"]) >= 1
    assert all(item["language"] == "python" for item in payload["data"])

