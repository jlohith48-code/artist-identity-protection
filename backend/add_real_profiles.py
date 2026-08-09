import requests

API_BASE = "http://127.0.0.1:8000"

real_names = ["Chandrabose", "Ramajogayya Sastry", "Vairamuthu", "Vivek Velmurugan",
              "Javed Akhtar", "Amitabh Bhattacharya", "Rafeeq Ahamed", "Vayalar Ramavarma",
              "Ed Sheeran", "Taylor Swift", "Chethan Kumar"]

impersonate = {"Chethan Kumar", "Chandrabose", "Vairamuthu", "Ed Sheeran"}

artists = requests.get(f"{API_BASE}/artists/").json()
songs = requests.get(f"{API_BASE}/songs/").json()

def alter_name(name):
    return name.replace(" ", "") + "_Official"

count = 0
for artist in artists:
    if artist["full_name"] not in real_names:
        continue

    artist_songs = [s for s in songs if s["artist_id"] == artist["id"]]
    if not artist_songs:
        continue

    legit_payload = {
        "artist_id": artist["id"],
        "platform": "Spotify",
        "platform_profile_id": f"spfy_{artist['id'][:8]}",
        "profile_url": f"https://open.spotify.com/artist/{artist['id'][:16]}",
        "claimed_display_name": artist["full_name"],
        "is_verified_owner": True,
        "monthly_listeners": 45000,
        "follower_count": 12000,
        "total_songs": len(artist_songs),
        "account_created_date": "2015-01-01",
    }
    res = requests.post(f"{API_BASE}/profiles/", json=legit_payload)
    if res.status_code == 200:
        print(f"Legit profile: {artist['full_name']}")
        count += 1

    if artist["full_name"] in impersonate:
        fake_payload = {
            "artist_id": artist["id"],
            "platform": "Spotify",
            "platform_profile_id": None,
            "profile_url": None,
            "claimed_display_name": alter_name(artist["full_name"]),
            "is_verified_owner": False,
            "monthly_listeners": 280000,
            "follower_count": 34,
            "total_songs": len(artist_songs),
            "account_created_date": "2026-07-01",
        }
        res = requests.post(f"{API_BASE}/profiles/", json=fake_payload)
        if res.status_code == 200:
            print(f"Impersonator profile: {alter_name(artist['full_name'])}")
            count += 1

print(f"\nDone. {count} profiles created.")
