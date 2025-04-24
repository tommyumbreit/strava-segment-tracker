import requests
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from pytz import timezone
import json
import os  

# --- Google Sheets Authentication ---
def load_google_secrets():
    """
    Loads the Google credentials from environment variables (set in Heroku).
    """
    google_secret = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT"))
    creds_dict = {key: value for key, value in google_secret.items()}
    creds_json = json.dumps(creds_dict)
    return json.loads(creds_json)

# Google Sheets setup
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- Strava API Setup ---
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")  # Use os.getenv() for environment variables
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# --- Refresh Strava Access Token ---
def refresh_strava_token():
    """
    Refreshes the Strava access token.
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
    Fetches the segment data (Effort count and Athlete count) from Strava.
    """
    url = f"https://www.strava.com/api/v3/segments/{segment_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch segment {segment_id}. Status: {response.status_code}")

    try:
        data = response.json()
    except Exception:
        raise Exception("Failed to parse Strava API response as JSON.")

    return {
        "segment_id": data["id"],
        "segment_name": data["name"],
        "effort_count": data["effort_count"],
        "athlete_count": data["athlete_count"],
        "timestamp": datetime.now(timezone("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")  # Berlin time
    }

# --- Update Google Sheets with Segment Data ---
def update_google_sheet(segment_data):
    """
    Updates the Google Sheet with the segment data.
    """
    creds = ServiceAccountCredentials.from_json_keyfile_dict(load_google_secrets(), scope)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(GOOGLE_SHEET_ID)
    worksheet = sheet.sheet1
    worksheet.append_row(list(segment_data.values()))  # Append the data to the sheet

# --- Main Function to Fetch and Update Segment Data ---
def main():
    segment_ids = [
        10515763,    # South Park Line - Nürnberg
        19267099,   # SouthPark (ebike) - Nürnberg
        18513962,    # Bikespielwiese (Pirate) - Nürnberg
        21015289,   # Pirat (ebike) - Nürnberg
        8133978,     # Bucktrail - Nürnberg
        21015374,   # Hard Enduro Zweite Hälfte (ebike Bucktrail) - Nürnberg
        5566759,     # Sketchy Downhill (Kangaroo) - Nürnberg
        10515526,    # Dreierline - Nürnberg
        21125079,    # Prickelpit (alt) - Nürnberg
        36673576,   # Prickel-Pit-Trail  (ebike) - Nürnberg
        29428315,   # Yoli Line eBike - Nürnberg
        29428229,   # Jägertrail eBike (Räubertrail) - Nürnberg
        10828939,    # Wurzeltrail ("Teufelstisch") - Nürnberg
        10516019,     # Snake-Line (Soul Kitchen) - Nürnberg
        23180608,   # E-Schlange 2020 - Nürnberg
        8442428,    # Rothenberg_Höllenritt - Schnaittach
        23690264,   # e_hoellenritt_95percent - Schnaittach
        10874261,   # frängmän_enduro - Schnaittach
        36790585,   # E-Frängmän New line - Schnaittach
        9097172,    # Enzenstein_Höllenritt - Schnaittach
        23689715,   # e_enzenstein_80percent - Schnaittach
        11082443,   # die_birke_enduro - Schnaittach
        35376142    # E-Birke new - Schnaittach
    ]

    # Refresh the Strava token
    access_token = refresh_strava_token()

    # Loop through the segment IDs, fetch stats, and update Google Sheets
    for segment_id in segment_ids:
        stats = get_strava_segment_stats(segment_id, access_token)
        update_google_sheet(stats)

if __name__ == "__main__":
    main()
