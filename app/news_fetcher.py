import re
import os
import requests
import logging
from urllib.parse import quote

# Add the API Key and CX for Google Custom Search API from environment variables
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# Function to fetch top 5 news using Google Custom Search API with a "news" filter
def get_news_for_site(site_url: str):
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

# Function to fetch social media links and possibly follower counts for a domain
def get_social_media_links_for_site(site_url: str):
    query = f"site:{quote(site_url)} (social media OR facebook OR twitter OR linkedin OR instagram OR youtube)"
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={GOOGLE_SEARCH_CX}&key={GOOGLE_SEARCH_API_KEY}&num=10"
    
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        
        search_results = response.json()
        social_links = []
        
        # Define social media platforms to look for
        social_platforms = ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'X']
        
        if 'items' in search_results:
            for item in search_results.get('items', []):
                link = item.get('link')
                title = item.get('title', '').lower()
                snippet = item.get('snippet', '').lower()
                
                # Check for social media platforms in title, snippet, or link
                if any(platform in link or platform in title or platform in snippet for platform in social_platforms):
                    # Try to extract follower count from the snippet using a regex
                    follower_count_match = re.search(r'(\d[\d,.]*)\s*(followers?|subscribers?)', snippet, re.IGNORECASE)
                    follower_count = follower_count_match.group(1) if follower_count_match else 'N/A'
                    
                    social_links.append({
                        "platform": link,
                        "follower_count": follower_count
                    })
                    
        return social_links
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching social media links for {site_url}: {str(e)}")
        return []  # Return an empty list if the social media fetch fails


# Main function to integrate both news and social media fetching
def get_site_info(site_url: str):
    # Fetch news articles
    news = get_news_for_site(site_url)
    
    # Fetch social media links
    social_links = get_social_media_links_for_site(site_url)
    
    return {
        "news": news,
        "social_media_links": social_links
    }
