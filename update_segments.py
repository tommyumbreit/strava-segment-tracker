import requests
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# --- Google Sheets Authentication ---
def load_google_secrets():
    """
    Loads the Google credentials from Streamlit secrets or environment variables.
    """
    google_secret = st.secrets["google_service_account"]
    creds_dict = {key: value for key, value in google_secret.items()}
    creds_json = json.dumps(creds_dict)
    return json.loads(creds_json)

# Google Sheets setup
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- Strava API Setup ---
STRAVA_CLIENT_ID = "your_client_id"
STRAVA_CLIENT_SECRET = "your_client_secret"
STRAVA_REFRESH_TOKEN = "your_refresh_token"
GOOGLE_SHEET_ID = "your_google_sheet_id"

# --- Refresh Strava Access Token ---
def refresh_strava_token():
    """
    Refresh the Strava access token.
    """
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": STRAVA_REFRESH_TOKEN
    }
    response = requests.post(url, data=payload)
    return response.json().get("access_token")

# --- Get Segment Stats from Strava ---
def get_strava_segment_stats(segment_id, access_token):
    """
    Fetch segment stats from Strava API (effort_count and athlete_count).
    """
    url = f"https://www.strava.com/api/v3/segments/{segment_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    return {
        "segment_id": data["id"],
        "segment_name": data["name"],
        "effort_count": data["effort_count"],
        "athlete_count": data["athlete_count"],
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Update Google Sheets with Segment Data ---
def update_google_sheet(segment_data):
    """
    Update the Google Sheet with the segment data.
    """
    creds = ServiceAccountCredentials.from_json_keyfile_dict(load_google_secrets(), scope)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(GOOGLE_SHEET_ID)
    worksheet = sheet.sheet1
    worksheet.append_row(list(segment_data.values()))  # Append the data to the sheet

# --- Main Function to Fetch and Update Segment Data ---
def main():
    segment_ids = [
        1234567,  # Replace with actual segment IDs
        7654321   # Add as many as needed
    ]

    # Refresh the Strava token
    access_token = refresh_strava_token()

    # Loop through the segment IDs, fetch stats, and update Google Sheets
    for segment_id in segment_ids:
        print(f"Fetching stats for segment ID {segment_id}")
        stats = get_strava_segment_stats(segment_id, access_token)
        update_google_sheet(stats)
        print(f"Updated Google Sheet with stats for segment: {stats['segment_name']}")

if __name__ == "__main__":
    main()
