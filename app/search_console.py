from fastapi import HTTPException
import requests
import logging
from urllib.parse import quote

# Import the get_site_info function from news_fetcher.py
# from app.news_fetcher import get_site_info

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
    failed_sites = []  # List to track sites that encountered errors

    # Iterate over each site in the site list
    for site in sites_data['siteEntry']:
        site_url = site['siteUrl'].rstrip('/')
        
        # Skip if the URL is not in the correct format
        if not (site_url.startswith("sc-domain:") or site_url.startswith("http://") or site_url.startswith("https://")):
            continue  # Skip invalid URLs
        
        # Determine the URL format for the API request
        if site_url.startswith("sc-domain:"):
            search_console_data_url = f"https://www.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query"
        else:
            # URL encode the site URL
            encoded_site_url = quote(site_url, safe='')
            search_console_data_url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site_url}/searchAnalytics/query"
        
        data = {
            "startDate": "2024-01-01",
            "endDate": "2024-09-30",
            "dimensions": ["query"],
            "rowLimit": 10
        }

        try:
            search_console_response = requests.post(search_console_data_url, headers=headers, json=data)
            search_console_response.raise_for_status()  # Raises HTTPError for 4xx or 5xx responses
            
            # Store the response data for each site
            search_console_data = search_console_response.json()
            
            # Get the site information (news, social media, and Google News scraping)
            # site_info = get_site_info(site_url)

            all_sites_data[site_url] = {
                "search_console_data": search_console_data,
                # "site_info": site_info
            }
        
        except requests.exceptions.HTTPError as http_err:
            error_message = search_console_response.json().get("error", {}).get("message", str(http_err))
            logging.error(f"Error fetching Search Console data for {site_url}: {error_message}")
            failed_sites.append(site_url)
        
        except Exception as e:
            logging.error(f"Unexpected error fetching data for {site_url}: {str(e)}")
            failed_sites.append(site_url)

    if not all_sites_data and failed_sites:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from all sites: {', '.join(failed_sites)}")
    
    return {
        "success": all_sites_data,
        "failed": failed_sites
    }
