import os
import requests
import logging
from urllib.parse import quote

# Add the API Key and CX for Google Custom Search API from environment variables
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# Function to fetch top 5 news using Google Custom Search API with a "news" filter
def get_news_for_site(site_url: str):
    # Use the "site:" filter to limit results to the specific domain, and the "news" filter to get news results
    query = f"site:{quote(site_url)} news"
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={GOOGLE_SEARCH_CX}&key={GOOGLE_SEARCH_API_KEY}&num=5&sort=date"
    
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        
        search_results = response.json()
        news_items = []
        
        # Parse the search results to extract news headlines and links
        if 'items' in search_results:
            for item in search_results['items']:
                news_items.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet")
                })
        
        return news_items
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching news for {site_url}: {str(e)}")
        return []  # Return an empty list if the news fetch fails
