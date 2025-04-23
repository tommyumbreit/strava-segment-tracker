import requests
import time
import json
import os

TOKEN_FILE = "strava_tokens.json"

def refresh_access_token():
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    secrets = ctx.session.secrets

    client_id = secrets["STRAVA_CLIENT_ID"]
    client_secret = secrets["STRAVA_CLIENT_SECRET"]
    refresh_token = secrets["STRAVA_REFRESH_TOKEN"]

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            tokens = json.load(f)
    else:
        tokens = {
            "access_token": "",
            "refresh_token": refresh_token,
            "expires_at": 0
        }

    if tokens["expires_at"] > time.time():
        return tokens["access_token"]

    response = requests.post(
        url="https://www.strava.com/api/v3/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"]
        }
    )

    if response.status_code != 200:
        raise Exception(f"Token-Refresh fehlgeschlagen: {response.text}")

    new_tokens = response.json()
    tokens["access_token"] = new_tokens["access_token"]
    tokens["refresh_token"] = new_tokens["refresh_token"]
    tokens["expires_at"] = new_tokens["expires_at"]

    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

    return tokens["access_token"]