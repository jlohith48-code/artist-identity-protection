import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
from difflib import SequenceMatcher
from app.database import SessionLocal
from app.models.artist import Artist
from app.models.artist_profile import ArtistProfile
from app.models.song import Song

db = SessionLocal()

def name_similarity(name1, name2):
    return SequenceMatcher(None, name1.lower().strip(), name2.lower().strip()).ratio()

rows = []
profiles = db.query(ArtistProfile).all()

for profile in profiles:
    artist = db.query(Artist).filter(Artist.id == profile.artist_id).first()
    if not artist:
        continue

    songs = db.query(Song).filter(Song.artist_id == artist.id).all()
    songs_with_dates = [s for s in songs if s.written_on]
    if not songs_with_dates:
        continue

    oldest_song_date = min(s.written_on for s in songs_with_dates)

    sim_score = name_similarity(artist.full_name, profile.claimed_display_name or "")

    if profile.account_created_date:
        gap_days = (profile.account_created_date - oldest_song_date).days
    else:
        gap_days = 0
    account_age_score = max(0, min(1, gap_days / 365))

    growth_ratio = profile.monthly_listeners / (profile.follower_count + 1)
    growth_velocity_score = min(1, growth_ratio / 5000)

    fields = [profile.platform_profile_id, profile.profile_url, profile.claimed_display_name]
    completeness = sum(1 for f in fields if f) / len(fields)
    metadata_completeness_score = 1 - completeness

    rows.append({
        "profile_id": str(profile.id),
        "artist_name": artist.full_name,
        "claimed_name": profile.claimed_display_name,
        "is_verified_owner": profile.is_verified_owner,
        "name_similarity_score": round(sim_score, 3),
        "account_age_score": round(account_age_score, 3),
        "growth_velocity_score": round(growth_velocity_score, 3),
        "metadata_completeness_score": round(metadata_completeness_score, 3),
    })

df = pd.DataFrame(rows)
os.makedirs("app/ml/data", exist_ok=True)
df.to_csv("app/ml/data/profile_features.csv", index=False)

print("Feature engineering complete!")
print(f"Total profiles processed: {len(df)}")
print()
print("Average feature values by profile type (False = fraudulent, True = legitimate):")
print(df.groupby("is_verified_owner")[["name_similarity_score","account_age_score","growth_velocity_score","metadata_completeness_score"]].mean())

db.close()
