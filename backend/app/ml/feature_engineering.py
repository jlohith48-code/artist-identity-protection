import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
from datetime import date
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
    if not songs:
        continue

    sim_score = name_similarity(artist.full_name, profile.claimed_display_name or "")

    if profile.account_created_date:
        days_since_created = max(1, (date.today() - profile.account_created_date).days)
    else:
        days_since_created = 1

    songs_per_day = profile.total_songs / days_since_created
    catalog_velocity_score = min(1, songs_per_day / 0.3)

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
        "catalog_velocity_score": round(catalog_velocity_score, 3),
        "growth_velocity_score": round(growth_velocity_score, 3),
        "metadata_completeness_score": round(metadata_completeness_score, 3),
    })

df = pd.DataFrame(rows)
os.makedirs("app/ml/data", exist_ok=True)
df.to_csv("app/ml/data/profile_features.csv", index=False)

print("Feature engineering complete!")
print(f"Total profiles processed: {len(df)}")
print()
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print("Average feature values by profile type (False = fraudulent, True = legitimate):")
print(df.groupby("is_verified_owner")[["name_similarity_score","catalog_velocity_score","growth_velocity_score","metadata_completeness_score"]].mean())

db.close()
