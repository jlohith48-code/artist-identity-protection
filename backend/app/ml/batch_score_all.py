import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database import SessionLocal
from app.models.artist import Artist
from app.models.artist_profile import ArtistProfile
from app.models.fraud_score import FraudScore
from app.ml.scoring_service import score_profile

db = SessionLocal()

print("Clearing existing fraud scores...")
db.query(FraudScore).delete()
db.commit()

profiles = db.query(ArtistProfile).all()
print(f"Found {len(profiles)} profiles to score...")

scored_count = 0
for profile in profiles:
    artist = db.query(Artist).filter(Artist.id == profile.artist_id).first()
    if not artist:
        continue
    try:
        score_result = score_profile(artist.full_name, profile)
        fraud_score = FraudScore(
            profile_id=profile.id,
            name_similarity_score=score_result["name_similarity_score"],
            account_age_score=score_result["account_age_score"],
            growth_velocity_score=score_result["growth_velocity_score"],
            metadata_completeness_score=score_result["metadata_completeness_score"],
            overall_risk_score=score_result["overall_risk_score"],
            risk_label=score_result["risk_label"],
            model_version="v1",
        )
        db.add(fraud_score)
        scored_count += 1
    except Exception as e:
        print(f"Failed to score profile {profile.id}: {e}")

db.commit()
print(f"Done! Scored {scored_count} profiles.")
db.close()
