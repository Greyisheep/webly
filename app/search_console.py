from http.client import HTTPException
import os
import requests
import logging
from urllib.parse import quote, urlparse
from app.utils import validate_url, map_sc_domain_to_canonical_url
from app.lighthouse_metrics import get_lighthouse_metrics
from app.news_fetcher import fetch_google_rss_news

# Environment variable for API Key
PAGE_SPEED_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")

def extract_domain(url: str) -> str:
    """Extract the main domain from a URL or sc-domain: format"""
    if url.startswith('sc-domain:'):
        return url.replace('sc-domain:', '')
    try:
        parsed = urlparse(url)
        return parsed.netloc or parsed.path
    except Exception:
        return url

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
        raise HTTPException(status_code=response.status_code, 
                          detail=f"Error fetching Search Console sites: {error_message}")

    sites_data = response.json()
    
    if 'siteEntry' not in sites_data or not sites_data['siteEntry']:
        raise HTTPException(
            status_code=404, 
            detail="No sites found for the user in Search Console."
        )
    
    # Initialize dictionaries to store the data
    all_sites_data = {}
    failed_sites = []

    # Iterate over each site
    for site in sites_data['siteEntry']:
        site_url = site['siteUrl'].rstrip('/')
        
        # Skip invalid URLs
        if not (site_url.startswith("sc-domain:") or 
                site_url.startswith("http://") or 
                site_url.startswith("https://")):
            continue
        
        # Extract the domain for news fetching
        domain = extract_domain(site_url)
        
        # Prepare the Search Console URL
        if site_url.startswith("sc-domain:"):
            search_console_data_url = f"https://www.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query"
        else:
            encoded_site_url = quote(site_url, safe='')
            search_console_data_url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site_url}/searchAnalytics/query"
        
        data = {
            "startDate": "2024-01-01",
            "endDate": "2024-09-30",
            "dimensions": ["query"],
            "rowLimit": 10
        }

        try:
            # Fetch Search Console data
            search_console_response = requests.post(
                search_console_data_url, 
                headers=headers, 
                json=data
            )
            search_console_response.raise_for_status()
            search_console_data = search_console_response.json()
            
            # Fetch news data using the extracted domain
            news_data = fetch_google_rss_news(domain)
            lighthouse_data = get_lighthouse_metrics(domain, os.getenv("GOOGLE_SEARCH_API_KEY"))
            
            # Store both sets of data
            all_sites_data[site_url] = {
                "search_console_data": search_console_data.get("rows", []),
                "news_data": news_data if news_data else [],
                "lighthouse_data": lighthouse_data if lighthouse_data else [],
                "domain": domain
            }
            
            # Log successful fetch
            logging.info(f"Successfully fetched data for {domain}")
            logging.debug(f"Found {len(news_data)} news items for {domain}")
            
        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP Error for {domain}: {str(http_err)}"
            logging.error(error_message)
            failed_sites.append({"site": site_url, "error": error_message})
            
        except Exception as e:
            error_message = f"Unexpected error for {domain}: {str(e)}"
            logging.error(error_message)
            failed_sites.append({"site": site_url, "error": error_message})

    if not all_sites_data and failed_sites:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "Failed to fetch data from all sites",
                "failed_sites": failed_sites
            }
        )
    
    return {
        "sites": all_sites_data,
        "failed_sites": failed_sites,
        "total_sites": len(all_sites_data),
        "failed_count": len(failed_sites)
    }