import os
import requests
import logging
import time
from urllib.parse import quote
from requests.exceptions import RequestException
from datetime import datetime
import json

# Configuration
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# Enhanced retry decorator with logging
def retry_request(func):
    def wrapper(*args, **kwargs):
        retries = 3
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except RequestException as e:
                logging.error(f"Request failed ({attempt + 1}/{retries}) - {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            except json.JSONDecodeError as e:
                logging.error(f"JSON parsing failed ({attempt + 1}/{retries}) - {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None
    return wrapper

@retry_request
def get_news_for_site(site_url: str):
    """
    Fetch news articles for a given site using Google Custom Search API
    """
    query = f"{quote(site_url)} news"
    params = {
        'q': query,
        'cx': GOOGLE_SEARCH_CX,
        'key': GOOGLE_SEARCH_API_KEY,
        'num': 5,
        'tbm': 'nws',
        'searchType': 'news',
        'sort': 'date'
    }
    
    response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    response.raise_for_status()
    search_results = response.json()

    news_items = []
    if 'items' in search_results:
        for item in search_results['items']:
            # Extract publication date from multiple possible locations
            published_time = (
                item.get('pagemap', {})
                .get('metatags', [{}])[0]
                .get('article:published_time') or
                item.get('pagemap', {})
                .get('newsarticle', [{}])[0]
                .get('datepublished') or
                'N/A'
            )
            
            news_items.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
                "source": item.get("displayLink"),
                "published_time": published_time,
                "publisher": item.get("publisher", {}).get("name", "Unknown")
            })
    
    return news_items

@retry_request
def get_social_media_links_for_site(site_url: str):
    """
    Fetch social media links for a given site
    """
    query = f"{quote(site_url)} (facebook OR twitter OR linkedin OR instagram OR youtube)"
    params = {
        'q': query,
        'cx': GOOGLE_SEARCH_CX,
        'key': GOOGLE_SEARCH_API_KEY,
        'num': 10
    }

    response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    response.raise_for_status()
    search_results = response.json()

    social_links = []
    social_platforms = {
        'facebook.com': 'Facebook',
        'twitter.com': 'Twitter',
        'linkedin.com': 'LinkedIn',
        'instagram.com': 'Instagram',
        'youtube.com': 'YouTube'
    }

    if 'items' in search_results:
        for item in search_results.get('items', []):
            link = item.get('link', '')
            for platform_url, platform_name in social_platforms.items():
                if platform_url in link:
                    social_links.append({
                        "platform": platform_name,
                        "url": link,
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", "")
                    })
                    break

    return social_links

def get_site_info(site_url: str):
    """
    Integrate news and social media fetching with enhanced error handling
    """
    try:
        news = get_news_for_site(site_url) or []
        social_links = get_social_media_links_for_site(site_url) or []

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "site_url": site_url,
            "custom_search_news": news,
            "social_media_links": social_links,
            "total_news_found": len(news),
            "total_social_links_found": len(social_links)
        }
    except Exception as e:
        logging.error(f"Error in get_site_info: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "site_url": site_url,
            "error_message": str(e),
            "custom_search_news": [],
            "social_media_links": []
        }

def print_site_info(info):
    """
    Pretty print the site information
    """
    print(f"\n=== Site Information for {info['site_url']} ===")
    print(f"Status: {info['status']}")
    print(f"Timestamp: {info['timestamp']}")
    
    print("\n=== News Articles ===")
    for i, article in enumerate(info['custom_search_news'], 1):
        print(f"\n--- Article {i} ---")
        print(f"Title: {article['title']}")
        print(f"Source: {article.get('source', 'Unknown')}")
        print(f"Published: {article.get('published_time', 'N/A')}")
        print(f"Link: {article['link']}")
        print(f"Snippet: {article['snippet']}")
    
    print("\n=== Social Media Links ===")
    for link in info['social_media_links']:
        print(f"\nPlatform: {link['platform']}")
        print(f"URL: {link['url']}")
        print(f"Title: {link.get('title', 'N/A')}")