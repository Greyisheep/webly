import xml.etree.ElementTree as ET
import requests
import logging
from urllib.parse import quote
from requests.exceptions import RequestException

def fetch_google_rss_news(site_url: str):
    """
    Fetch news articles for a given domain using Google News RSS feed
    
    Args:
        domain (str): The domain to search for news
    
    Returns:
        list: A list of dictionaries containing news article details
    """
    try:
        # Encode the domain to handle special characters
        encoded_domain = quote(site_url)
        
        # Construct the Google News RSS URL
        rss_url = f"https://news.google.com/rss/search?q={encoded_domain}"
        
        # Send GET request to fetch RSS feed
        response = requests.get(rss_url)
        response.raise_for_status()
        
        # Parse the XML response
        root = ET.fromstring(response.content)
        
        # Find the channel element
        channel = root.find('channel')
        
        # List to store news items
        news_items = []
        
        # Iterate through items in the RSS feed
        for item in channel.findall('item'):
            # Extract title
            title = item.find('title').text if item.find('title') is not None else 'N/A'
            
            # Extract link
            link = item.find('link').text if item.find('link') is not None else 'N/A'
            
            # Extract description and source
            description_elem = item.find('description')
            description = 'N/A'
            source = 'N/A'
            
            if description_elem is not None:
                # The description contains an HTML-like structure
                desc_text = description_elem.text
                
                # Try to extract source from the description
                source_start = desc_text.find('<font color="#6f6f6f">') 
                if source_start != -1:
                    source_end = desc_text.find('</font>', source_start)
                    if source_end != -1:
                        source = desc_text[source_start + len('<font color="#6f6f6f">'): source_end]
                
                # Extract the link text
                link_start = desc_text.find('">') 
                link_end = desc_text.find('</a>', link_start)
                if link_start != -1 and link_end != -1:
                    description = desc_text[link_start + 2: link_end]
            
            # Extract publication date
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else 'N/A'
            
            # Create news item dictionary
            news_item = {
                'title': title,
                'link': link,
                'description': description,
                'source': source,
                'pub_date': pub_date
            }
            
            news_items.append(news_item)
        
        return news_items
    
    except RequestException as e:
        logging.error(f"Request failed: {e}")
        return []
    except ET.ParseError as e:
        logging.error(f"XML parsing failed: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return []
