import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

def explain_fraud_score(artist_name, claimed_name, scores):
    client = get_client()

    prompt = f'''A fraud detection model flagged a music streaming profile. Here is the data:

Real artist name: {artist_name}
Name shown on profile: {claimed_name}
Name similarity score (1.0 = identical): {scores['name_similarity_score']}
Catalog velocity score (0-1, higher = songs appeared suspiciously fast): {scores['account_age_score']}
Growth velocity score (0-1, higher = unnatural listener-to-follower ratio): {scores['growth_velocity_score']}
Metadata completeness score (0-1, higher = more missing profile info): {scores['metadata_completeness_score']}
Overall risk score: {scores['overall_risk_score']}
Risk label: {scores['risk_label']}

Write a 2-3 sentence, plain-English explanation of why this profile was flagged, for a non-technical artist to understand. Be direct and specific about which signals mattered most.'''

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"(AI explanation unavailable: {str(e)[:100]}). Risk label: {scores['risk_label']}, overall score: {scores['overall_risk_score']}."
