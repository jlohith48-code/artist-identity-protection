from datetime import date
from difflib import SequenceMatcher

def name_similarity(name1, name2):
    return SequenceMatcher(None, name1.lower().strip(), name2.lower().strip()).ratio()

def compute_profile_features(artist_full_name, profile):
    sim_score = name_similarity(artist_full_name, profile.claimed_display_name or "")

    if profile.account_created_date:
        days_since_created = max(1, (date.today() - profile.account_created_date).days)
    else:
        days_since_created = 1

    songs_per_day = (profile.total_songs or 0) / days_since_created
    catalog_velocity_score = min(1, songs_per_day / 0.3)

    growth_ratio = profile.monthly_listeners / (profile.follower_count + 1)
    growth_velocity_score = min(1, growth_ratio / 5000)

    fields = [profile.platform_profile_id, profile.profile_url, profile.claimed_display_name]
    completeness = sum(1 for f in fields if f) / len(fields)
    metadata_completeness_score = 1 - completeness

    return {
        "name_similarity_score": round(sim_score, 3),
        "catalog_velocity_score": round(catalog_velocity_score, 3),
        "growth_velocity_score": round(growth_velocity_score, 3),
        "metadata_completeness_score": round(metadata_completeness_score, 3),
    }
