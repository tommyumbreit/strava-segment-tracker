import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import locale

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

# --- Language Toggle (English default) ---
lang = st.radio("Language / Sprache", ["English", "Deutsch"], horizontal=True, index=0)

T = {
    "title": {
        "English": "📈 Strava Segment Tracker Dashboard",
        "Deutsch": "📈 Strava Segment Tracker Dashboard"
    },
    "expander": {
        "English": "📊 Show Time Series",
        "Deutsch": "📊 Zeitreihe anzeigen"
    },
    "selectbox": {
        "English": "Select Segment",
        "Deutsch": "Segment auswählen"
    },
    "effort_title": {
        "English": "📈 Effort Count – How often was the segment ridden?",
        "Deutsch": "📈 Anzahl der Fahrten – Wie oft wurde das Segment gefahren?"
    },
    "athlete_title": {
        "English": "🧍‍♂️ Athlete Count – How many unique athletes completed the segment?",
        "Deutsch": "🧍‍♂️ Anzahl der Athleten – Wie viele verschiedene Personen haben das Segment gefahren?"
    },
    "no_data": {
        "English": "No data yet. The background fetch script hasn't populated the sheet.",
        "Deutsch": "Noch keine Daten vorhanden. Das Hintergrundskript hat das Sheet noch nicht befüllt."
    },
    "segment": lambda name: {
        "English": f"Segment: {name}",
        "Deutsch": f"Segment: {name}"
    },
    "timestamp_axis": {
        "English": "Date & Time",
        "Deutsch": "Datum & Uhrzeit"
    },
    "effort_axis": {
        "English": "Effort Count",
        "Deutsch": "Anzahl der Fahrten"
    },
    "athlete_axis": {
        "English": "Athlete Count",
        "Deutsch": "Anzahl der Athleten"
    },
}

# Dynamisches Achsen-Datumsformat mit Wochentag
if lang == "English":
    date_format = "%a, %b %d, %I:%M %p"  # Tue, Apr 23, 02:30 PM
    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
else:
    date_format = "%a, %d.%m. %H:%M"     # Di, 23.04. 14:30
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")  # Setzt das deutsche Datumsformat

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

        # Manuelle Anpassung für die Wochentage im Deutschen (kurz, wie Mo, Di, Mi...)
        df_sel["formatted_time"] = df_sel["timestamp"].dt.strftime(date_format)
        
        df_sel.sort_values("timestamp", inplace=True)

        st.subheader(T["segment"](df_sel['segment_name'].iloc[-1])[lang])

        # --- Effort Chart ---
        st.markdown(f"### {T['effort_title'][lang]}")

        # Achse auf Basis des neuen Formats setzen (alle 12 Stunden eine Beschriftung)
        chart_effort = alt.Chart(df_sel).mark_line(point=True).encode(
            x=alt.X("timestamp:T", title=T["timestamp_axis"][lang],
                    axis=alt.Axis(format=date_format, labelAngle=0, tickCount="hour", labelLimit=200)),  # Alle 12 Stunden eine Beschriftung
            y=alt.Y("effort_count:Q", title=T["effort_axis"][lang],
                    scale=alt.Scale(domain=[df_sel['effort_count'].min(), df_sel['effort_count'].max()])),
            tooltip=[alt.Tooltip("formatted_time:N", title=T["timestamp_axis"][lang]), "effort_count"]
        ).properties(width="container").interactive()

        st.altair_chart(chart_effort, use_container_width=True)

        # --- Athlete Chart ---
        st.markdown(f"### {T['athlete_title'][lang]}")

        chart_athletes = alt.Chart(df_sel).mark_line(point=True).encode(
            x=alt.X("timestamp:T", title=T["timestamp_axis"][lang],
                    axis=alt.Axis(format=date_format, labelAngle=0, tickCount="hour", labelLimit=200)),  # Alle 12 Stunden eine Beschriftung
            y=alt.Y("athlete_count:Q", title=T["athlete_axis"][lang],
                    scale=alt.Scale(domain=[df_sel['athlete_count'].min(), df_sel['athlete_count'].max()])),
            tooltip=[alt.Tooltip("formatted_time:N", title=T["timestamp_axis"][lang]), "athlete_count"]
        ).properties(width="container").interactive()

        st.altair_chart(chart_athletes, use_container_width=True)
else:
    st.info(T["no_data"][lang])
