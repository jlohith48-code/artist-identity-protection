import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="The Ledger - Artist Ownership Registry", page_icon="🖋", layout="wide")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ink-navy: #1a1f2e;
    --ink-navy-dark: #10131c;
    --parchment: #f2ead9;
    --parchment-line: #cdb98a;
    --burgundy: #7a2e3a;
    --burgundy-dark: #5c2029;
    --brass: #b8933f;
    --sage: #4a7c59;
    --ink-text: #2b2620;
    --cream-text: #ede6d6;
}

.stApp { background-color: var(--ink-navy); font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background-color: var(--ink-navy-dark); border-right: 2px solid var(--brass); }
[data-testid="stSidebar"] * { color: var(--cream-text) !important; font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] label { font-size: 0.95rem; padding: 2px 0; }

h1 { font-family: 'Spectral', serif !important; color: var(--cream-text) !important; font-weight: 600 !important; }
h2, h3 { font-family: 'Spectral', serif !important; color: var(--cream-text) !important; font-weight: 500 !important; }
p, span, div, label { color: var(--cream-text); }

.eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--brass);
    font-size: 0.78rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: -0.6rem;
    display: block;
}

.stButton > button {
    background-color: var(--burgundy);
    color: var(--cream-text);
    border: 1px solid var(--brass);
    border-radius: 3px;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    letter-spacing: 0.03em;
    padding: 0.5rem 1.2rem;
}
.stButton > button:hover { background-color: var(--burgundy-dark); border-color: var(--brass); color: var(--cream-text); }

[data-testid="stMetric"] {
    background-color: var(--parchment);
    border: 1px solid var(--parchment-line);
    border-radius: 6px;
    padding: 14px 16px;
}
[data-testid="stMetricValue"] { color: var(--ink-text) !important; font-family: 'Spectral', serif !important; }
[data-testid="stMetricLabel"] { color: var(--burgundy) !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; }

.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stDateInput input {
    background-color: var(--parchment) !important;
    color: var(--ink-text) !important;
    border: 1px solid var(--parchment-line) !important;
    font-family: 'Inter', sans-serif !important;
}

.stDataFrame { border: 1px solid var(--parchment-line); border-radius: 6px; }

.registry-stamp {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    width: 130px;
    height: 130px;
    border: 3px double var(--burgundy);
    border-radius: 50%;
    transform: rotate(-6deg);
    color: var(--burgundy);
    font-family: 'Spectral', serif;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.85rem;
    background: rgba(122, 46, 58, 0.06);
    margin: 12px 0;
    line-height: 1.3;
}

.hash-chip {
    font-family: 'IBM Plex Mono', monospace;
    background: var(--ink-navy-dark);
    border: 1px solid var(--brass);
    color: var(--brass);
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 0.8rem;
    display: inline-block;
}

hr { border-color: var(--parchment-line) !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def api_request(method, path, json=None, params=None):
    """Clean HTTP helper attaching JWT Authorization header if available."""
    url = f"{API_BASE}{path}"
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.request(method, url, json=json, params=params, headers=headers, timeout=10)
        if res.status_code == 401:
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)
        return res
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend server API")
        return None

def page_header(eyebrow, title, subtitle=None):
    st.markdown(f'<span class="eyebrow">{eyebrow}</span>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.write(subtitle)

def stamp(main_text, sub_text=""):
    st.markdown(
        f'<div class="registry-stamp">{main_text}<br><span style="font-size:0.7rem;font-weight:400;">{sub_text}</span></div>',
        unsafe_allow_html=True
    )

def youtube_video_id_from_url(url):
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    return ""

st.sidebar.markdown("### 🖋 The Ledger")
st.sidebar.caption("Ownership registry for songwriters")

# Sidebar Authentication Section
if "token" in st.session_state and st.session_state.get("user"):
    user = st.session_state["user"]
    st.sidebar.markdown(f"👤 **{user.get('full_name', 'Artist')}** ({user.get('role', 'artist')})")
    if st.sidebar.button("Sign Out"):
        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        st.rerun()
else:
    with st.sidebar.expander("🔑 Sign In / Authenticate", expanded=False):
        login_email = st.text_input("Email", key="side_email")
        login_pass = st.text_input("Password", type="password", key="side_pass")
        if st.button("Sign In", key="side_login_btn"):
            if login_email and login_pass:
                res = requests.post(f"{API_BASE}/auth/login", json={"email": login_email, "password": login_pass})
                if res.status_code == 200:
                    data = res.json()
                    st.session_state["token"] = data["access_token"]
                    st.session_state["user"] = {
                        "id": data["artist_id"],
                        "full_name": data["full_name"],
                        "email": data["email"],
                        "role": data["role"]
                    }
                    st.success("Signed in")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

page = st.sidebar.radio("", ["Home", "Register Artist", "Register Song", "Fraud Dashboard", "Report Impersonation", "Review Suggested Credits"], label_visibility="collapsed")

if page == "Home":
    page_header("THE LEDGER", "A registry for songs and the people who wrote them", "Every entry here is timestamped and fingerprinted the moment it's filed - so no one else can claim it later.")
    health = api_request("GET", "/health")
    if health and health.status_code == 200:
        data = health.json()
        st.success(f"Connected to Registry API v{data.get('version', '2.0.0')}")

elif page == "Register Artist":
    page_header("ENTRY 01 - ESTABLISH IDENTITY", "Register as an artist")
    with st.form("artist_form"):
        full_name = st.text_input("Full Name*")
        email = st.text_input("Email*")
        password = st.text_input("Password*", type="password")
        phone = st.text_input("Phone (optional)")
        iprs_id = st.text_input("IPRS ID (optional)")
        state = st.selectbox("State", ["Karnataka", "Tamil Nadu", "Maharashtra", "Delhi", "Kerala", "Other"])
        submitted = st.form_submit_button("Add my name to the ledger")

        if submitted:
            if not full_name or not email or not password:
                st.error("Full Name, Email, and Password are required")
            else:
                payload = {
                    "full_name": full_name,
                    "email": email,
                    "password": password,
                    "phone": phone or None,
                    "iprs_id": iprs_id or None,
                    "state": state
                }
                res = api_request("POST", "/auth/register", json=payload)
                if res and res.status_code == 200:
                    data = res.json()
                    st.session_state["token"] = data["access_token"]
                    st.session_state["user"] = {
                        "id": data["artist_id"],
                        "full_name": data["full_name"],
                        "email": data["email"],
                        "role": data["role"]
                    }
                    stamp("ENTERED", full_name.split()[0] if full_name else "")
                    st.success(f"Registered and signed in as {data['full_name']}")
                    st.json(data)
                elif res:
                    st.error(f"Registration Error: {res.json().get('detail', res.text)}")

elif page == "Register Song":
    page_header("ENTRY 02 - FILE OWNERSHIP PROOF", "Register a song")

    artists_res = api_request("GET", "/artists/")
    artists = artists_res.json() if artists_res and artists_res.status_code == 200 else []

    if artists:
        artist_options = {f"{a['full_name']} ({a['email']})": a['id'] for a in artists}
        selected_artist_label = st.selectbox("Filing as", list(artist_options.keys()))
        selected_artist_id = artist_options[selected_artist_label]

        with st.form("song_form"):
            title = st.text_input("Song Title*")
            language = st.selectbox("Language", ["Tamil", "Kannada", "Hindi", "Telugu", "English", "Other"])
            lyrics = st.text_area("Lyrics*", height=150, help="Used to generate ownership proof. Never stored as raw text.")
            youtube_url = st.text_input("YouTube URL (optional)")
            production_house = st.text_input("Production House (optional)")
            written_on = st.date_input("Date Written", value=date.today())
            submitted = st.form_submit_button("File this song")

            if submitted:
                if not title or not lyrics:
                    st.error("Title and Lyrics are required")
                else:
                    payload = { 
                        "artist_id": selected_artist_id, "title": title, "language": language, "lyrics": lyrics,
                        "youtube_url": youtube_url or None, "production_house": production_house or None,
                        "written_on": str(written_on),
                    }
                    res = api_request("POST", "/songs/", json=payload)
                    if res and res.status_code == 200:
                        data = res.json()
                        if data.get("similarity_warning"):
                            st.warning(f"Similarity Alert: {data['similarity_warning']}")
                        stamp("FILED", title[:14])
                        st.success("Song filed with a timestamped ownership fingerprint.")
                        st.markdown(f'<span class="hash-chip">{data["lyrics_hash"][:32]}...</span>', unsafe_allow_html=True)
                        st.json(data)
                    elif res and res.status_code == 409:
                        st.error(res.json().get('detail'))
                    elif res:
                        st.error(f"Error: {res.json().get('detail', res.text)}")
    else:
        st.warning("No artists on the ledger yet. Register one first.")

elif page == "Fraud Dashboard":
    page_header("ENTRY 03 - MONITOR THE REGISTRY", "Fraud Detection Dashboard", "Every platform profile on file, scored for impersonation risk.")

    res = api_request("GET", "/profiles/fraud-scores/all")
    if res and res.status_code == 200 and res.json():
        df = pd.DataFrame(res.json())

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Filed Profiles", len(df))
        col2.metric("High Risk", len(df[df['risk_label'] == 'high_risk']))
        col3.metric("Medium Risk", len(df[df['risk_label'] == 'medium_risk']))
        col4.metric("Low Risk", len(df[df['risk_label'] == 'low_risk']))

        st.subheader("Risk Distribution")
        col_a, col_b = st.columns(2)
        with col_a:
            risk_counts = df['risk_label'].value_counts().reset_index()
            risk_counts.columns = ['risk_label', 'count']
            color_map = {"high_risk": "#7a2e3a", "medium_risk": "#b8933f", "low_risk": "#4a7c59"}
            fig_pie = px.pie(risk_counts, names='risk_label', values='count', color='risk_label', color_discrete_map=color_map, title="Profiles by Risk Level")
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#ede6d6")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_b:
            fig_scatter = px.scatter(df, x='follower_count', y='monthly_listeners', color='risk_label', color_discrete_map=color_map,
                                      hover_data=['artist_name', 'claimed_display_name'], title="Listeners vs Followers", log_x=True, log_y=True)
            fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#ede6d6")
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("Ask the ledger why")
        flagged = df[df['risk_label'].isin(['high_risk', 'medium_risk'])]
        if not flagged.empty:
            profile_options = {f"{row['claimed_display_name']} - {row['risk_label']} ({round(row['overall_risk_score']*100)}% risk)": row['profile_id'] for _, row in flagged.iterrows()}
            selected_label = st.selectbox("Pick a flagged profile", list(profile_options.keys()))
            selected_profile_id = profile_options[selected_label]
            if st.button("Explain this flag"):
                explain_res = api_request("GET", f"/profiles/{selected_profile_id}/explain")
                if explain_res and explain_res.status_code == 200:
                    st.info(explain_res.json()["explanation"])
                else:
                    st.error("Could not generate explanation")
        else:
            st.write("Nothing flagged yet.")

        st.subheader("Full Register")
        display_df = df[['artist_name', 'claimed_display_name', 'platform', 'is_verified_owner', 'monthly_listeners', 'follower_count', 'overall_risk_score', 'risk_label']].copy()
        display_df = display_df.sort_values('overall_risk_score', ascending=False)

        def highlight_risk(row):
            if row['risk_label'] == 'high_risk': return ['background-color: #4a1515'] * len(row)
            elif row['risk_label'] == 'medium_risk': return ['background-color: #4a3a15'] * len(row)
            else: return ['background-color: #1a3a1a'] * len(row)

        st.dataframe(display_df.style.apply(highlight_risk, axis=1), use_container_width=True, height=400)
    else:
        st.info("No fraud scores available yet.")

elif page == "Report Impersonation":
    page_header("ENTRY 04 - FILE A CLAIM", "Report an Impersonator", "Naming the specific profile using your identity.")

    artists_res = api_request("GET", "/artists/")
    artists = artists_res.json() if artists_res and artists_res.status_code == 200 else []
    scores_res = api_request("GET", "/profiles/fraud-scores/all")
    all_scores = scores_res.json() if scores_res and scores_res.status_code == 200 else []

    if artists:
        artist_options = {f"{a['full_name']} ({a['email']})": a['id'] for a in artists}
        selected_artist_label = st.selectbox("Filing as", list(artist_options.keys()))
        selected_artist_id = artist_options[selected_artist_label]

        flagged = [s for s in all_scores if s['risk_label'] in ('high_risk', 'medium_risk')]

        if flagged:
            st.subheader("Flagged profiles on file")
            flagged_df = pd.DataFrame(flagged)[['profile_id', 'artist_name', 'claimed_display_name', 'platform', 'overall_risk_score', 'risk_label']]
            st.dataframe(flagged_df, use_container_width=True)

            profile_options = {f"{s['claimed_display_name']} - {s['risk_label']} ({round(s['overall_risk_score']*100)}% risk)": s['profile_id'] for s in flagged}
            selected_profile_label = st.selectbox("Which one is impersonating you?", list(profile_options.keys()))
            selected_profile_id = profile_options[selected_profile_label]

            evidence = st.text_area("Evidence / Notes (optional)", placeholder="e.g. links to your official YouTube channel, production house confirmation, etc.")

            if st.button("File this claim"):
                payload = {"artist_id": selected_artist_id, "fake_profile_id": selected_profile_id, "evidence_summary": evidence or None}
                res = api_request("POST", "/reports/", json=payload)
                if res and res.status_code == 200:
                    stamp("CLAIMED")
                    st.success("Claim filed. It's on record.")
                    st.json(res.json())
                elif res:
                    st.error(f"Error: {res.json().get('detail', res.text)}")
        else:
            st.info("Nothing flagged to claim yet.")

        st.subheader("Your filed claims")
        reports_res = api_request("GET", f"/reports/artist/{selected_artist_id}")
        if reports_res and reports_res.status_code == 200:
            reports = reports_res.json()
            if reports:
                st.dataframe(pd.DataFrame(reports)[['status', 'evidence_summary', 'submitted_at']], use_container_width=True)
            else:
                st.write("Nothing filed yet.")
    else:
        st.warning("No artists on the ledger yet. Register one first.")

elif page == "Review Suggested Credits":
    page_header("ENTRY 05 - VERIFY EXTERNAL CLAIMS", "Review Suggested Credits",
                "Credits pulled from YouTube that couldn't be auto-confirmed. Confirm what's really yours - rejected ones are never used as evidence.")

    pending_res = api_request("GET", "/evidence/pending")
    pending = pending_res.json() if pending_res and pending_res.status_code == 200 else []

    if not pending:
        st.success("Nothing pending review right now - all caught up.")
    else:
        st.write(f"**{len(pending)} item(s) waiting for review**")
        st.markdown("---")

        for item in pending:
            evidence_id = item["id"]
            artist_name = item["matched_artist_name"]
            source_url = item["source_url"]
            video_title = item.get("video_title", "Untitled Video")
            channel_confidence = item.get("channel_confidence", "medium")
            evidence_type = item.get("evidence_type", "mention_only")
            role = item.get("role", "unknown")
            raw_credit_text = item.get("raw_credit_text")
            stage_name_tag = item.get("stage_name_tag")

            video_id = youtube_video_id_from_url(source_url)
            col1, col2 = st.columns([1, 3])

            with col1:
                if video_id:
                    st.image(f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg", use_container_width=True)

            with col2:
                st.markdown(f"**{video_title}**")
                st.markdown(f"[Open on YouTube]({source_url})")

                badge = "Weak match" if evidence_type == "mention_only" else "Partial match"
                st.markdown(f'<span class="hash-chip">{badge} · channel trust: {channel_confidence}</span>', unsafe_allow_html=True)

                st.markdown(f"**Suggested artist:** {artist_name}")
                if stage_name_tag:
                    st.markdown(f"**Also credited as:** {stage_name_tag}")
                if role and role != "unknown":
                    st.markdown(f"**Suggested role:** {role}")

                if raw_credit_text and "no structured field found" not in raw_credit_text:
                    st.code(raw_credit_text, language=None)
                else:
                    st.caption("No specific credit line found - the name just appeared somewhere in the title/description.")

                btn_col1, btn_col2, _ = st.columns([1, 1, 3])
                with btn_col1:
                    if st.button("Yes, this is mine", key=f"confirm_{evidence_id}"):
                        res = api_request("PATCH", f"/evidence/{evidence_id}/status", json={"status": "confirmed"})
                        if res and res.status_code == 200:
                            stamp("CONFIRMED", artist_name.split()[0] if artist_name else "")
                            st.rerun()
                        elif res:
                            st.error(res.json().get("detail", "Error confirming evidence"))
                with btn_col2:
                    if st.button("Not mine", key=f"reject_{evidence_id}"):
                        res = api_request("PATCH", f"/evidence/{evidence_id}/status", json={"status": "rejected"})
                        if res and res.status_code == 200:
                            st.rerun()
                        elif res:
                            st.error(res.json().get("detail", "Error rejecting evidence"))

            st.markdown("---")
