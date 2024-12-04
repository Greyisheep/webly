import requests
from bs4 import BeautifulSoup
import re
import json

def clean_url(url):
    """Clean extracted URL by removing unwanted parameters and HTML encoding."""
    url = url.split('&')[0]  # Remove parameters
    url = re.sub(r'(&amp;|")', '', url)  # Remove HTML encoding
    return url

def get_social_media_info(domain: str):
    """
    Scrape social media links and follower counts for a given domain.
    
    Args:
        domain (str): Domain to search for (e.g., 'example.com').
        
    Returns:
        dict: Dictionary containing social media links and follower counts.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    social_patterns = {
        'linkedin': r'linkedin\.com/company/[^/\s]+',
        'twitter': r'twitter\.com/[^/\s]+',
        'instagram': r'instagram\.com/[^/\s]+',
        'facebook': r'facebook\.com/[^/\s]+',
        'youtube': r'youtube\.com/(?:channel|user|c)/[^/\s]+'
    }
    
    results = {
        'links': {},
        'followers': {}
    }
    
    try:
        # Perform search
        search_url = f'https://www.google.com/search?q={domain}+social+media'
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract social media links
        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, response.text)
            if matches:
                results['links'][platform] = f'https://{clean_url(matches[0])}'
                
        # Extract follower counts for supported platforms
        for platform, url in results['links'].items():
            if platform in ['twitter', 'instagram', 'youtube', 'facebook']:
                try:
                    resp = requests.get(url, headers=headers)
                    if platform == 'youtube':
                        subscriber_count = re.search(r'"subscriberCountText":\s*"([^"]+)"', resp.text)
                        if subscriber_count:
                            results['followers'][platform] = subscriber_count.group(1)
                    else:
                        followers = re.search(r'(\d+(?:,\d+)*)\s+[Ff]ollowers', resp.text)
                        if followers:
                            results['followers'][platform] = followers.group(1)
                except Exception as e:
                    print(f"Error scraping {platform}: {e}")
                    
    except Exception as e:
        print(f"Error: {str(e)}")
        
    return results

# # Example usage
# if __name__ == "__main__":
#     domain = "panfinance.net"
#     results = get_social_media_info(domain)
#     print(json.dumps(results, indent=2))
