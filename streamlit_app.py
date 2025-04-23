import json
import streamlit as st
import requests
import gspread
import pandas as pd
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
from token_handler import refresh_access_token

# 🔐 Secrets laden
CLIENT_ID = st.secrets["STRAVA_CLIENT_ID"]
CLIENT_SECRET = st.secrets["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["STRAVA_REFRESH_TOKEN"]
SEGMENT_IDS = st.secrets["SEGMENT_IDS"]

# Google Sheets / Drive Zugriff
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Zugriff auf secrets
google_secret = st.secrets["google_service_account"]
creds_dict = {key: value for key, value in google_secret.items()}
creds_json = json.dumps(creds_dict)

# Temporäre Credentials aus secrets erzeugen
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)

# 📊 Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
client = gspread.authorize(creds)
sheet = client.open("strava-segment-tracker").sheet1

def get_segment_stats(segment_id, token):
    url = f"https://www.strava.com/api/v3/segments/{segment_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        name = data['name']
        stats = data['athlete_segment_stats']
        return name, stats['effort_count'], stats['athlete_count']
    else:
        st.warning(f"Fehler bei Segment {segment_id}: {response.status_code}")
        return None, None, None

def log_stats(segment_id, segment_name, effort, athletes):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([segment_id, segment_name, now, effort, athletes])

def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

query_params = st.experimental_get_query_params()
if "run" in query_params and query_params["run"][0] == "auto":
    token = refresh_access_token()
    for seg_id in SEGMENT_IDS.split(","):
        seg_id = seg_id.strip()
        name, effort, athletes = get_segment_stats(seg_id, token)
        if name:
            log_stats(seg_id, name, effort, athletes)
    st.stop()

st.title("📊 Strava Multi-Segment Tracker")

if st.button("🚴‍♂️ Jetzt alle Segmente abfragen & speichern"):
    token = refresh_access_token()
    for seg_id in SEGMENT_IDS.split(","):
        seg_id = seg_id.strip()
        name, effort, athletes = get_segment_stats(seg_id, token)
        if name:
            log_stats(seg_id, name, effort, athletes)
            st.success(f"{name} gespeichert: Efforts={effort}, Athletes={athletes}")

df = load_data()
if not df.empty:
    st.subheader("🔍 Verlauf je Segment")
    selected = st.selectbox("Segment auswählen", df["segment_name"].unique())

    seg_df = df[df["segment_name"] == selected]
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Effort Count**")
        fig1 = px.line(seg_df, x='timestamp', y='effort_count', markers=True)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("**Athlete Count**")
        fig2 = px.line(seg_df, x='timestamp', y='athlete_count', markers=True)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Noch keine Daten vorhanden.")