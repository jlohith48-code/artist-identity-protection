def test_evidence_endpoints(client):
    # Fetch pending evidence list
    res = client.get("/evidence/pending")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Fetch all evidence
    res_all = client.get("/evidence/")
    assert res_all.status_code == 200
    assert isinstance(res_all.json(), list)
