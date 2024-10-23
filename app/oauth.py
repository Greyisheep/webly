import os
import requests
from fastapi import HTTPException

# Environment variables for Google API credentials
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI") #, "http://localhost:8000/callback")
SCOPE = (
    #"https://www.googleapis.com/auth/analytics"
    "https://www.googleapis.com/auth/analytics.readonly " # check google api documentation for extra permissions
    "https://www.googleapis.com/auth/webmasters.readonly "
    "https://www.googleapis.com/auth/userinfo.profile"
    # "https://www.googleapis.com/auth/cse"
)

# Step 1: Get Google Auth URL (User signs in with Google)
def get_google_auth_url():
    google_auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    scope = SCOPE.replace(" ", "%20")  # URL encode the scope
    auth_url = (
        f"{google_auth_endpoint}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}"
        f"&access_type=offline&prompt=consent"
    )
    return auth_url

# Step 2: Exchange authorization code for access token
def get_google_token(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    try:
        r = requests.post(token_url, data=data)
        r.raise_for_status()  # Raise exception if the token request fails
        token_response = r.json()
        return token_response["access_token"]
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching token: {str(e)}")