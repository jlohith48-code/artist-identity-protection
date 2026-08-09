import pandas as pd
import requests

API_BASE = "http://127.0.0.1:8000"
FILE_PATH = "song_registration_template_csv.xlsx"

df = pd.read_excel(FILE_PATH)
records = df.to_dict('records')

def clean(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if s == "" or s.lower() in ("nan", "none"):
        return None
    return s

def clean_email(val):
    s = clean(val)
    if s is None:
        return None
    return s.replace(" ", "")

cleaned = []
last_name, last_email, last_state = None, None, None

for r in records:
    title = clean(r.get("song_title"))
    if not title:
        continue

    name = clean(r.get("artist_full_name")) or last_name
    email = clean_email(r.get("artist_email")) or last_email
    state = clean(r.get("artist_state")) or last_state
    last_name, last_email, last_state = name, email, state

    if not email:
        continue

    lyrics = clean(r.get("lyrics"))
    if lyrics is None or lyrics.upper() == "PASTE REAL LYRICS HERE" or "placeholder lyrics" in (lyrics or "").lower():
        lyrics = f"Sample placeholder lyrics for demonstration purposes - not the artist's actual work. (Entry for: {title})"

    written_on = clean(r.get("written_on"))
    if written_on:
        written_on = written_on[:10]

    cleaned.append({
        "artist_full_name": name,
        "artist_email": email,
        "artist_state": state,
        "song_title": title,
        "language": clean(r.get("language")) or "Other",
        "lyrics": lyrics,
        "youtube_url": clean(r.get("youtube_url")),
        "production_house": clean(r.get("production_house")),
        "written_on": written_on,
    })

print(f"Prepared {len(cleaned)} songs to register.\n")

registered_artists = {}
success_count = 0
fail_count = 0

for row in cleaned:
    email = row["artist_email"]
    if email not in registered_artists:
        payload = {
            "full_name": row["artist_full_name"],
            "email": email,
            "phone": None,
            "iprs_id": None,
            "state": row["artist_state"],
        }
        res = requests.post(f"{API_BASE}/artists/", json=payload)
        if res.status_code == 200:
            registered_artists[email] = res.json()["id"]
            print(f"Registered artist: {row['artist_full_name']}")
        elif res.status_code == 400:
            all_artists = requests.get(f"{API_BASE}/artists/").json()
            existing = next((a for a in all_artists if a["email"] == email), None)
            if existing:
                registered_artists[email] = existing["id"]
                print(f"Artist already on file, reusing: {row['artist_full_name']}")
            else:
                print(f"FAILED to register or find artist: {row['artist_full_name']} - {res.text}")
                fail_count += 1
                continue
        else:
            print(f"FAILED to register artist {row['artist_full_name']}: {res.text}")
            fail_count += 1
            continue

    artist_id = registered_artists[email]
    song_payload = {
        "artist_id": artist_id,
        "title": row["song_title"],
        "language": row["language"],
        "lyrics": row["lyrics"],
        "youtube_url": row["youtube_url"],
        "production_house": row["production_house"],
        "written_on": row["written_on"],
    }
    res = requests.post(f"{API_BASE}/songs/", json=song_payload)
    if res.status_code == 200:
        print(f"  Registered song: {row['song_title']}")
        success_count += 1
    elif res.status_code == 409:
        print(f"  Skipped duplicate: {row['song_title']}")
    else:
        print(f"  FAILED song '{row['song_title']}': {res.text}")
        fail_count += 1

print(f"\nDone. {success_count} songs registered, {fail_count} failures.")
