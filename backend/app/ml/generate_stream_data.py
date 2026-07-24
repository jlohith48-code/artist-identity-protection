import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import uuid
from datetime import date, timedelta
from app.database import SessionLocal
from app.models.artist import Artist
from app.models.song import Song
from app.models.artist_profile import ArtistProfile
from app.models.stream_snapshot import StreamSnapshot

db = SessionLocal()

print("Clearing existing stream snapshots...")
db.query(StreamSnapshot).delete()
db.commit()

fraud_artist_ids = set(
    p.artist_id for p in db.query(ArtistProfile).filter(ArtistProfile.is_verified_owner == False).all()
)

songs = db.query(Song).all()
print(f"Generating 30-day stream history for {len(songs)} songs...")

countries = ["India", "USA", "UK", "Canada", "Australia"]
created_count = 0

for song in songs:
    has_spike = song.artist_id in fraud_artist_ids and random.random() < 0.7
    base_streams = random.randint(50, 2000)
    current_total = base_streams
    spike_day = random.randint(15, 25) if has_spike else None

    for day_offset in range(30, 0, -1):
        snapshot_date = date.today() - timedelta(days=day_offset)

        if has_spike and (30 - day_offset) == spike_day:
            daily_delta = random.randint(5000, 20000)
        else:
            daily_delta = int(current_total * random.uniform(0.01, 0.05)) + random.randint(1, 20)

        current_total += daily_delta
        growth_rate = daily_delta / max(current_total - daily_delta, 1)

        snapshot = StreamSnapshot(
            id=uuid.uuid4(),
            song_id=song.id,
            snapshot_date=snapshot_date,
            stream_count=current_total,
            daily_delta=daily_delta,
            growth_rate=round(growth_rate, 4),
            top_country=random.choice(countries),
            flagged_anomaly=(daily_delta > 3000),
        )
        db.add(snapshot)
        created_count += 1

db.commit()
print(f"Created {created_count} stream snapshot records across {len(songs)} songs.")
db.close()
