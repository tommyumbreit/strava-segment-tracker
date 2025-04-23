import streamlit as st
import pandas as pd
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

sheet = gc.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
worksheet = sheet.sheet1

# --- Load existing data ---
def load_data():
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        st.warning("⚠️ No 'timestamp' column found in data.")
    return df

# --- Streamlit UI ---

st.cache_data.clear()  # Löscht den Cache von Streamlit Cloud


st.set_page_config(layout="wide")
st.title("📈 Strava Segment Tracker Dashboard")

df = load_data()

if not df.empty:
    with st.expander("📊 Show Time Series", expanded=True):
        segment_options = sorted(df['segment_id'].unique())
        selected_id = st.selectbox("Select Segment", segment_options)
        df_sel = df[df['segment_id'] == selected_id]

        st.subheader(f"Segment: {df_sel['segment_name'].iloc[-1]}")
        st.line_chart(
            df_sel.set_index("timestamp")[["effort_count", "athlete_count"]],
            use_container_width=True
        )
else:
    st.info("No data yet. The background fetch script hasn't populated the sheet.")
