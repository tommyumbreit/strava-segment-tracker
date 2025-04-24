import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# --- Google Sheets Auth ---
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

google_secret = st.secrets["google_service_account"]
creds_dict = {key: value for key, value in google_secret.items()}
creds_json = json.dumps(creds_dict)
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
gc = gspread.authorize(creds)

sheet = gc.open_by_key(st.secrets["general"]["GOOGLE_SHEET_ID"])
worksheet = sheet.sheet1

# --- Load existing data ---
def load_data():
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    return df

# --- Streamlit UI ---
st.cache_data.clear()
st.set_page_config(layout="wide")

# --- Language Toggle ---
lang = st.radio("Language / Sprache", ["English", "Deutsch"], horizontal=True)

T = {
    "title": {
        "Deutsch": "📈 Strava Segment Tracker Dashboard",
        "English": "📈 Strava Segment Tracker Dashboard"
    },
    "expander": {
        "Deutsch": "📊 Zeitreihe anzeigen",
        "English": "📊 Show Time Series"
    },
    "selectbox": {
        "Deutsch": "Segment auswählen",
        "English": "Select Segment"
    },
    "effort_title": {
        "Deutsch": "📈 Anzahl der Fahrten – Wie oft wurde das Segment gefahren?",
        "English": "📈 Effort Count – How often was the segment ridden?"
    },
    "athlete_title": {
        "Deutsch": "🧍‍♂️ Anzahl der Athleten – Wie viele verschiedene Personen sind das Segment gefahren?",
        "English": "🧍‍♂️ Athlete Count – How many unique athletes completed the segment?"
    },
    "no_data": {
        "Deutsch": "Noch keine Daten vorhanden. Das Hintergrundskript hat das Sheet noch nicht befüllt.",
        "English": "No data yet. The background fetch script hasn't populated the sheet."
    },
    "segment": lambda name: {
        "Deutsch": f"Segment: {name}",
        "English": f"Segment: {name}"
    }
}

st.title(T["title"][lang])
df = load_data()

if not df.empty:
    with st.expander(T["expander"][lang], expanded=True):
        df["segment_label"] = df["segment_id"].astype(str) + " - " + df["segment_name"]
        unique_segments = df[["segment_id", "segment_name", "segment_label"]].drop_duplicates()
        segment_options = unique_segments["segment_label"].tolist()

        selected_label = st.selectbox(T["selectbox"][lang], segment_options)
        selected_id = int(selected_label.split(" - ")[0])
        df_sel = df[df["segment_id"] == selected_id].copy()

        df_sel["timestamp"] = pd.to_datetime(df_sel["timestamp"])
        df_sel.sort_values("timestamp", inplace=True)

        st.subheader(T["segment"](df_sel['segment_name'].iloc[-1])[lang])

        # --- Effort Chart ---
        st.markdown(f"### {T['effort_title'][lang]}")
        chart_effort = alt.Chart(df_sel).mark_line(point=True).encode(
            x=alt.X("timestamp:T", title="Zeitpunkt", axis=alt.Axis(format="%d.%m. %H:%M")),
            y=alt.Y("effort_count:Q", title="Effort Count",
                    scale=alt.Scale(domain=[df_sel['effort_count'].min(), df_sel['effort_count'].max()])),
            tooltip=["timestamp:T", "effort_count"]
        ).properties(width="container").interactive()

        st.altair_chart(chart_effort, use_container_width=True)

        # --- Athlete Chart ---
        st.markdown(f"### {T['athlete_title'][lang]}")
        chart_athletes = alt.Chart(df_sel).mark_line(point=True).encode(
            x=alt.X("timestamp:T", title="Zeitpunkt", axis=alt.Axis(format="%d.%m. %H:%M")),
            y=alt.Y("athlete_count:Q", title="Athlete Count",
                    scale=alt.Scale(domain=[df_sel['athlete_count'].min(), df_sel['athlete_count'].max()])),
            tooltip=["timestamp:T", "athlete_count"]
        ).properties(width="container").interactive()

        st.altair_chart(chart_athletes, use_container_width=True)
else:
    st.info(T["no_data"][lang])
