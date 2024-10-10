from fastapi import HTTPException
import requests
from urllib.parse import quote

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
    
    if 'siteEntry' not in sites_data or not sites_data['siteEntry']:
        raise HTTPException(
            status_code=404, 
            detail="No sites found for the user in Search Console. Ensure the user has access to a verified site."
        )
    
    # Initialize a dictionary to store the data for each site
    all_sites_data = {}

    # Iterate over each site in the site list
    for site in sites_data['siteEntry']:
        site_url = site['siteUrl'].rstrip('/')
        
        # Skip if the URL is not in the correct format
        if not (site_url.startswith("sc-domain:") or site_url.startswith("http://") or site_url.startswith("https://")):
            continue  # Skip invalid URLs
        
        # Determine the URL format for the API request
        if site_url.startswith("sc-domain:"):
            # No encoding needed for sc-domain
            search_console_data_url = f"https://www.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query"
        else:
            # URL encode the site URL
            encoded_site_url = quote(site_url, safe='')
            search_console_data_url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site_url}/searchAnalytics/query"
        
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
                error_message = f"Status: {search_console_response.status_code}, Content: {search_console_response.text}"
            raise HTTPException(
                status_code=search_console_response.status_code, 
                detail=f"Error fetching Search Console data for {site_url}: {error_message}"
            )
        
        # Store the response data for each site
        all_sites_data[site_url] = search_console_response.json()

    return all_sites_data
