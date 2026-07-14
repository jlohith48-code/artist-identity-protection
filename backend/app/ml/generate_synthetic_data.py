import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import uuid
from datetime import datetime, timedelta, date
from faker import Faker
from app.database import SessionLocal
from app.models.artist import Artist
from app.models.song import Song
from app.models.artist_profile import ArtistProfile
from app.utils.hashing import generate_lyrics_hash, generate_lyrics_preview

fake = Faker('en_IN')
db = SessionLocal()

def random_date(start_year=2010, end_year=2024):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def slightly_alter_name(name):
    alterations = [
        lambda n: n + " Official",
        lambda n: n.replace("a", "aa", 1) if "a" in n else n + "1",
        lambda n: n.replace(" ", "_"),
        lambda n: n + str(random.randint(1, 99)),
        lambda n: n[:-1] if len(n) > 3 else n + "x",
    ]
    return random.choice(alterations)(name)

print("Generating synthetic artists and songs...")

artists_created = []
for i in range(30):
    artist = Artist(
        id=uuid.uuid4(),
        full_name=fake.name(),
        email=fake.unique.email(),
        phone=fake.phone_number()[:15],
        iprs_id=f"IPRS{random.randint(10000,99999)}" if random.random() > 0.3 else None,
        state=random.choice(["Karnataka", "Tamil Nadu", "Maharashtra", "Delhi", "Kerala"]),
        verified_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(artist)
    artists_created.append(artist)

db.commit()
print(f"Created {len(artists_created)} artists")

songs_created = []
for artist in artists_created:
    num_songs = random.randint(2, 8)
    for _ in range(num_songs):
        lyrics = fake.paragraph(nb_sentences=5)
        written = random_date()
        song = Song(
            id=uuid.uuid4(),
            artist_id=artist.id,
            title=fake.sentence(nb_words=4).rstrip('.'),
            language=random.choice(["Tamil", "Kannada", "Hindi", "Telugu", "English"]),
            lyrics_hash=generate_lyrics_hash(lyrics),
            lyrics_preview=generate_lyrics_preview(lyrics),
            youtube_url=f"https://youtube.com/watch?v={fake.uuid4()[:11]}",
            production_house=fake.company(),
            written_on=written,
            registered_at=datetime.utcnow(),
        )
        db.add(song)
        songs_created.append(song)

db.commit()
print(f"Created {len(songs_created)} songs")

print("Generating legitimate profiles...")
legit_count = 0
for artist in artists_created:
    artist_songs = [s for s in songs_created if s.artist_id == artist.id]
    if not artist_songs:
        continue
    oldest_song_date = min(s.written_on for s in artist_songs)
    account_created = oldest_song_date - timedelta(days=random.randint(30, 365))

    profile = ArtistProfile(
        id=uuid.uuid4(),
        artist_id=artist.id,
        platform="Spotify",
        platform_profile_id=fake.uuid4()[:22],
        profile_url=f"https://open.spotify.com/artist/{fake.uuid4()[:22]}",
        claimed_display_name=artist.full_name,
        is_verified_owner=True,
        monthly_listeners=random.randint(500, 50000),
        follower_count=random.randint(100, 20000),
        total_songs=len(artist_songs),
        account_created_date=account_created,
        first_seen_at=datetime.utcnow(),
    )
    db.add(profile)
    legit_count += 1

db.commit()
print(f"Created {legit_count} legitimate verified profiles")

print("Generating fraudulent impersonator profiles...")
fraud_count = 0
fraud_targets = random.sample(artists_created, k=10)
for artist in fraud_targets:
    artist_songs = [s for s in songs_created if s.artist_id == artist.id]
    if not artist_songs:
        continue

    fake_account_created = date.today() - timedelta(days=random.randint(1, 90))
    has_url = random.random() > 0.6
    has_platform_id = random.random() > 0.5

    profile = ArtistProfile(
        id=uuid.uuid4(),
        artist_id=artist.id,
        platform="Spotify",
        platform_profile_id=fake.uuid4()[:22] if has_platform_id else None,
        profile_url=f"https://open.spotify.com/artist/{fake.uuid4()[:22]}" if has_url else None,
        claimed_display_name=slightly_alter_name(artist.full_name),
        is_verified_owner=False,
        monthly_listeners=random.randint(50000, 500000),
        follower_count=random.randint(1, 50),
        total_songs=len(artist_songs),
        account_created_date=fake_account_created,
        first_seen_at=datetime.utcnow(),
    )
    db.add(profile)
    fraud_count += 1

db.commit()
print(f"Created {fraud_count} fraudulent impersonator profiles")

db.close()
print("Done! Synthetic data generation complete.")
