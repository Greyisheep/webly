from fastapi import HTTPException
import requests

def get_user_search_console_data(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get the list of sites for this user
    site_list_url = "https://www.googleapis.com/webmasters/v3/sites"
    response = requests.get(site_list_url, headers=headers)
    
    if response.status_code != 200:
        try:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
        except ValueError:
            error_message = response.text
        raise HTTPException(status_code=response.status_code, detail=f"Error fetching Search Console sites: {error_message}")

    sites_data = response.json()
    
    if 'siteEntry' not in sites_data:
        raise HTTPException(status_code=404, detail="No sites found for the user in Search Console. Ensure the user has access to a verified site.")

    site_url = sites_data['siteEntry'][0]['siteUrl'].rstrip('/')
    
    if not (site_url.startswith("sc-domain:") or site_url.startswith("http://") or site_url.startswith("https://")):
        raise HTTPException(status_code=400, detail=f"Invalid Search Console site URL format: {site_url}")
    
    search_console_data_url = f"https://www.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query"
    data = {
        "startDate": "2023-01-01",
        "endDate": "2023-01-30",
        "dimensions": ["query"],
        "rowLimit": 10
    }

    search_console_response = requests.post(search_console_data_url, headers=headers, json=data)
    
    if search_console_response.status_code != 200:
        try:
            error_message = search_console_response.json().get("error", {}).get("message", "Unknown error")
        except ValueError:
            error_message = search_console_response.text
        raise HTTPException(status_code=search_console_response.status_code, detail=f"Error fetching Search Console data: {error_message}")
    
    return search_console_response.json()
