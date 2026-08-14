"""
db_writer.py
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_engine():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL not set. Add it to your .env file in backend/, e.g.\n"
            "DATABASE_URL=postgresql://user:password@localhost:5432/artist_protection"
        )
    return create_engine(DATABASE_URL)

def lookup_artist_id(conn, artist_name):
    result = conn.execute(
        text("SELECT id FROM artists WHERE lower(full_name) = lower(:name) LIMIT 1"),
        {"name": artist_name},
    ).fetchone()
    return result[0] if result else None

def save_evidence_records(records):
    engine = get_engine()
    inserted = 0
    skipped = 0

    with engine.begin() as conn:
        for record in records:
            for credit in record.credits:
                existing = conn.execute(
                    text("""
                        SELECT id FROM ownership_evidence
                        WHERE source_url = :source_url
                          AND matched_artist_name = :artist_name
                          AND role = :role
                    """),
                    {
                        "source_url": record.video_url,
                        "artist_name": credit.matched_artist,
                        "role": credit.role,
                    },
                ).fetchone()

                if existing:
                    skipped += 1
                    continue

                artist_id = lookup_artist_id(conn, credit.matched_artist)

                conn.execute(
                    text("""
                        INSERT INTO ownership_evidence (
                            matched_artist_id, matched_artist_name, source_type, source_url,
                            video_title, channel_id, channel_confidence, evidence_type,
                            match_type, role, raw_credit_text, stage_name_tag, status
                        ) VALUES (
                            :artist_id, :artist_name, 'youtube', :source_url,
                            :video_title, :channel_id, :channel_confidence, :evidence_type,
                            :match_type, :role, :raw_credit_text, :stage_name_tag, :status
                        )
                    """),
                    {
                        "artist_id": artist_id,
                        "artist_name": credit.matched_artist,
                        "source_url": record.video_url,
                        "video_title": record.video_title,
                        "channel_id": record.channel_id,
                        "channel_confidence": record.confidence,
                        "evidence_type": record.evidence_type,
                        "match_type": credit.match_type,
                        "role": credit.role,
                        "raw_credit_text": credit.raw_match,
                        "stage_name_tag": credit.tag,
                        "status": record.status,
                    },
                )
                inserted += 1

    return {"inserted": inserted, "skipped_duplicates": skipped}