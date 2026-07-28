import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date

API_BASE = "http://127.0.0.1:8000"

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

st.sidebar.markdown("### 🖋 The Ledger")
st.sidebar.caption("Ownership registry for songwriters")
page = st.sidebar.radio("", ["Home", "Register Artist", "Register Song", "Fraud Dashboard", "Report Impersonation"], label_visibility="collapsed")

if page == "Home":
    page_header("THE LEDGER", "A registry for songs and the people who wrote them", "Every entry here is timestamped and fingerprinted the moment it's filed - so no one else can claim it later.")
    try:
        health = requests.get(f"{API_BASE}/health", timeout=3)
        if health.status_code == 200:
            st.success("Connected to the registry")
    except requests.exceptions.ConnectionError:
        st.error("Can't reach the registry backend. Make sure your FastAPI server is running.")

elif page == "Register Artist":
    page_header("ENTRY 01 - ESTABLISH IDENTITY", "Register as an artist")
    with st.form("artist_form"):
        full_name = st.text_input("Full Name*")
        email = st.text_input("Email*")
        phone = st.text_input("Phone (optional)")
        iprs_id = st.text_input("IPRS ID (optional)")
        state = st.selectbox("State", ["Karnataka", "Tamil Nadu", "Maharashtra", "Delhi", "Kerala", "Other"])
        submitted = st.form_submit_button("Add my name to the ledger")

        if submitted:
            if not full_name or not email:
                st.error("Full Name and Email are required")
            else:
                payload = {"full_name": full_name, "email": email, "phone": phone or None, "iprs_id": iprs_id or None, "state": state}
                try:
                    res = requests.post(f"{API_BASE}/artists/", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        stamp("ENTERED", full_name.split()[0] if full_name else "")
                        st.success(f"You're on the ledger. Artist ID: {data['id']}")
                        st.json(data)
                    else:
                        st.error(f"Error: {res.json().get('detail', res.text)}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot reach backend server")

elif page == "Register Song":
    page_header("ENTRY 02 - FILE OWNERSHIP PROOF", "Register a song")

    try:
        artists_res = requests.get(f"{API_BASE}/artists/")
        artists = artists_res.json() if artists_res.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        artists = []
        st.error("Cannot reach backend server")

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
                    try:
                        res = requests.post(f"{API_BASE}/songs/", json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            if data.get("similarity_warning"):
                                st.warning(f"Similarity Alert: {data['similarity_warning']}")
                            stamp("FILED", title[:14])
                            st.success("Song filed with a timestamped ownership fingerprint.")
                            st.markdown(f'<span class="hash-chip">{data["lyrics_hash"][:32]}...</span>', unsafe_allow_html=True)
                            st.json(data)
                        elif res.status_code == 409:
                            st.error(res.json().get('detail'))
                        else:
                            st.error(f"Error: {res.json().get('detail', res.text)}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot reach backend server")
    else:
        st.warning("No artists on the ledger yet. Register one first.")

elif page == "Fraud Dashboard":
    page_header("ENTRY 03 - MONITOR THE REGISTRY", "Fraud Detection Dashboard", "Every platform profile on file, scored for impersonation risk.")

    try:
        res = requests.get(f"{API_BASE}/profiles/fraud-scores/all")
        if res.status_code == 200 and res.json():
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
                    try:
                        explain_res = requests.get(f"{API_BASE}/profiles/{selected_profile_id}/explain")
                        if explain_res.status_code == 200:
                            st.info(explain_res.json()["explanation"])
                        else:
                            st.error("Could not generate explanation")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot reach backend server")
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
            st.info("No fraud scores yet. Register some artist profiles first (via the API /docs page).")
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach backend server")

elif page == "Report Impersonation":
    page_header("ENTRY 04 - FILE A CLAIM", "Report an Impersonator", "Naming the specific profile using your identity.")

    try:
        artists_res = requests.get(f"{API_BASE}/artists/")
        artists = artists_res.json() if artists_res.status_code == 200 else []
        scores_res = requests.get(f"{API_BASE}/profiles/fraud-scores/all")
        all_scores = scores_res.json() if scores_res.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        artists = []
        all_scores = []
        st.error("Cannot reach backend server")

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
                try:
                    res = requests.post(f"{API_BASE}/reports/", json=payload)
                    if res.status_code == 200:
                        stamp("CLAIMED")
                        st.success("Claim filed. It's on record.")
                        st.json(res.json())
                    else:
                        st.error(f"Error: {res.json().get('detail', res.text)}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot reach backend server")
        else:
            st.info("Nothing flagged to claim yet.")

        st.subheader("Your filed claims")
        try:
            reports_res = requests.get(f"{API_BASE}/reports/artist/{selected_artist_id}")
            if reports_res.status_code == 200:
                reports = reports_res.json()
                if reports:
                    st.dataframe(pd.DataFrame(reports)[['status', 'evidence_summary', 'submitted_at']], use_container_width=True)
                else:
                    st.write("Nothing filed yet.")
        except requests.exceptions.ConnectionError:
            pass
    else:
        st.warning("No artists on the ledger yet. Register one first.")
