def explain_fraud_score(artist_name, claimed_name, scores):
    reasons = []

    if scores['name_similarity_score'] < 0.95:
        reasons.append(f"the profile name (\"{claimed_name}\") doesn't exactly match the real artist's name (\"{artist_name}\")")

    if scores['account_age_score'] > 0.3:
        reasons.append("this account claims a large song catalog despite being created very recently")

    if scores['growth_velocity_score'] > 0.3:
        reasons.append("the ratio of monthly listeners to followers is unusually high, a pattern often linked to bot-driven streaming")

    if scores['metadata_completeness_score'] > 0.3:
        reasons.append("the profile is missing key information (like a platform ID or profile URL) that legitimate profiles usually have")

    risk_label = scores['risk_label'].replace('_', ' ')

    if not reasons:
        return f"This profile was scored as {risk_label}. No strong individual red flags were found, but the combination of signals crossed the model's threshold."

    if len(reasons) == 1:
        explanation = f"This profile was flagged as {risk_label} because {reasons[0]}."
    else:
        explanation = f"This profile was flagged as {risk_label} for several reasons: " + "; ".join(reasons) + "."

    return explanation
