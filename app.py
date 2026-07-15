import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Artist Identity & Ownership Protection", page_icon="🎵", layout="wide")

st.sidebar.title("🎵 Artist Protection System")
page = st.sidebar.radio("Navigate", ["Home", "Register Artist", "Register Song", "Fraud Dashboard"])

if page == "Home":
    st.title("Artist Identity & Ownership Protection System")
    st.write("Protecting lyricists and artists from identity theft and streaming fraud.")
    try:
        health = requests.get(f"{API_BASE}/health", timeout=3)
        if health.status_code == 200:
            st.success("Backend is connected and running")
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach backend. Make sure your FastAPI server is running.")

elif page == "Register Artist":
    st.title("Register a New Artist")
    with st.form("artist_form"):
        full_name = st.text_input("Full Name*")
        email = st.text_input("Email*")
        phone = st.text_input("Phone (optional)")
        iprs_id = st.text_input("IPRS ID (optional)")
        state = st.selectbox("State", ["Karnataka", "Tamil Nadu", "Maharashtra", "Delhi", "Kerala", "Other"])
        submitted = st.form_submit_button("Register Artist")

        if submitted:
            if not full_name or not email:
                st.error("Full Name and Email are required")
            else:
                payload = {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone or None,
                    "iprs_id": iprs_id or None,
                    "state": state,
                }
                try:
                    res = requests.post(f"{API_BASE}/artists/", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Artist registered! ID: {data['id']}")
                        st.json(data)
                    else:
                        st.error(f"Error: {res.json().get('detail', res.text)}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot reach backend server")

elif page == "Register Song":
    st.title("Register a Song (Ownership Proof)")

    try:
        artists_res = requests.get(f"{API_BASE}/artists/")
        artists = artists_res.json() if artists_res.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        artists = []
        st.error("Cannot reach backend server")

    if artists:
        artist_options = {f"{a['full_name']} ({a['email']})": a['id'] for a in artists}
        selected_artist_label = st.selectbox("Select Artist", list(artist_options.keys()))
        selected_artist_id = artist_options[selected_artist_label]

        with st.form("song_form"):
            title = st.text_input("Song Title*")
            language = st.selectbox("Language", ["Tamil", "Kannada", "Hindi", "Telugu", "English", "Other"])
            lyrics = st.text_area("Lyrics*", height=150, help="Used to generate ownership proof. Not stored as raw text.")
            youtube_url = st.text_input("YouTube URL (optional)")
            production_house = st.text_input("Production House (optional)")
            written_on = st.date_input("Date Written", value=date.today())
            submitted = st.form_submit_button("Register Song")

            if submitted:
                if not title or not lyrics:
                    st.error("Title and Lyrics are required")
                else:
                    payload = {
                        "artist_id": selected_artist_id,
                        "title": title,
                        "language": language,
                        "lyrics": lyrics,
                        "youtube_url": youtube_url or None,
                        "production_house": production_house or None,
                        "written_on": str(written_on),
                    }
                    try:
                        res = requests.post(f"{API_BASE}/songs/", json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"Song registered! Ownership proof hash: {data['lyrics_hash'][:16]}...")
                            st.json(data)
                        elif res.status_code == 409:
                            st.warning(res.json().get('detail'))
                        else:
                            st.error(f"Error: {res.json().get('detail', res.text)}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot reach backend server")
    else:
        st.warning("No artists found. Please register an artist first.")

elif page == "Fraud Dashboard":
    st.title("Fraud Detection Dashboard")
    st.write("ML-powered risk scoring for artist platform profiles")

    try:
        res = requests.get(f"{API_BASE}/profiles/fraud-scores/all")
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json())

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Profiles Scored", len(df))
            col2.metric("High Risk", len(df[df['risk_label'] == 'high_risk']))
            col3.metric("Medium Risk", len(df[df['risk_label'] == 'medium_risk']))
            col4.metric("Low Risk", len(df[df['risk_label'] == 'low_risk']))

            st.subheader("Risk Distribution")
            col_a, col_b = st.columns(2)

            with col_a:
                risk_counts = df['risk_label'].value_counts().reset_index()
                risk_counts.columns = ['risk_label', 'count']
                color_map = {"high_risk": "#e74c3c", "medium_risk": "#f39c12", "low_risk": "#27ae60"}
                fig_pie = px.pie(risk_counts, names='risk_label', values='count',
                                  color='risk_label', color_discrete_map=color_map,
                                  title="Profiles by Risk Level")
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_b:
                fig_scatter = px.scatter(df, x='follower_count', y='monthly_listeners',
                                          color='risk_label', color_discrete_map=color_map,
                                          hover_data=['artist_name', 'claimed_display_name'],
                                          title="Listeners vs Followers (bot-fraud signal)",
                                          log_x=True, log_y=True)
                st.plotly_chart(fig_scatter, use_container_width=True)

            st.subheader("All Scored Profiles")
            display_df = df[['artist_name', 'claimed_display_name', 'platform', 'is_verified_owner',
                              'monthly_listeners', 'follower_count', 'overall_risk_score', 'risk_label']].copy()
            display_df = display_df.sort_values('overall_risk_score', ascending=False)

            def highlight_risk(row):
                if row['risk_label'] == 'high_risk':
                    return ['background-color: #4a1515'] * len(row)
                elif row['risk_label'] == 'medium_risk':
                    return ['background-color: #4a3a15'] * len(row)
                else:
                    return ['background-color: #1a3a1a'] * len(row)

            st.dataframe(display_df.style.apply(highlight_risk, axis=1), use_container_width=True, height=400)

        else:
            st.info("No fraud scores yet. Register some artist profiles first (via the API /docs page).")
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach backend server")
