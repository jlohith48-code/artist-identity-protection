def test_song_registration_and_duplicate_detection(client):
    # Register artist first
    art_res = client.post(
        "/auth/register",
        json={
            "full_name": "Songwriter Artist",
            "email": "songwriter@example.com",
            "password": "password123"
        }
    )
    artist_id = art_res.json()["artist_id"]

    song_payload = {
        "artist_id": artist_id,
        "title": "Original Anthem",
        "language": "English",
        "lyrics": "This is a unique song written for testing ownership registration fingerprints."
    }

    # Register song 1
    res1 = client.post("/songs/", json=song_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert "lyrics_hash" in data1
    assert data1["title"] == "Original Anthem"

    # Duplicate registration attempt should return 409 Conflict
    res2 = client.post("/songs/", json=song_payload)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"]

def test_song_paraphrase_similarity_warning(client):
    art_res = client.post(
        "/auth/register",
        json={
            "full_name": "Paraphrase Artist",
            "email": "paraphrase@example.com",
            "password": "password123"
        }
    )
    artist_id = art_res.json()["artist_id"]

    # Song 1
    client.post("/songs/", json={
        "artist_id": artist_id,
        "title": "Melody One",
        "lyrics": "Walk through the starlight under the midnight sky."
    })

    # Song 2 (similar text)
    res2 = client.post("/songs/", json={
        "artist_id": artist_id,
        "title": "Melody Two",
        "lyrics": "Walking through starlight under midnight sky."
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2.get("similarity_warning") is not None
