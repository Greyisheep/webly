# app/utils.py
from typing import Dict
import urllib.parse
import logging

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def validate_url(url: str) -> str:
    """Validate and clean URL input"""
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Handle sc-domain: format
    if url.startswith("sc-domain:"):
        domain = url.replace("sc-domain:", "").strip()
        return f"https://www.{domain}"
    
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    logging.info(f"Validated and cleaned URL: {url}")
    return urllib.parse.quote(url, safe=':/?=')

def map_sc_domain_to_canonical_url(sc_domain_url: str) -> str:
    """Map sc-domain to canonical URL with better error handling"""
    logging.info(f"Attempting to map sc-domain: {sc_domain_url}")
    
    domain = sc_domain_url.replace("sc-domain:", "").strip()
    canonical_urls = [f"https://www.{domain}", f"https://{domain}"]
    
    for url in canonical_urls:
        try:
            logging.info(f"Trying URL: {url}")
            response = requests.head(url, allow_redirects=True, timeout=5)
            if response.status_code == 200:
                logging.info(f"Successfully resolved to: {url}")
                return url
        except requests.RequestException as e:
            logging.warning(f"Failed to resolve {url}: {str(e)}")
            continue
    
    raise ValueError(f"Could not resolve {sc_domain_url} to a valid URL")

def calculate_performance_score(metrics: Dict[str, float]) -> float:
    """Calculate the weighted performance score based on Lighthouse metrics"""
    weights = {
        'FCP': 0.10,
        'SpeedIndex': 0.10,
        'LCP': 0.25,
        'TBT': 0.30,
        'CLS': 0.25
    }
    
    # Calculate the weighted performance score
    performance_score = (
        weights['FCP'] * metrics['FCP'] +
        weights['SpeedIndex'] * metrics['SpeedIndex'] +
        weights['LCP'] * metrics['LCP'] +
        weights['TBT'] * metrics['TBT'] +
        weights['CLS'] * metrics['CLS']
    )
    
    return round(performance_score * 100, 2)  # Convert to a score out of 100
