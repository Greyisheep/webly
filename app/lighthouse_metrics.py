import requests
import logging
from fastapi import HTTPException
from typing import Dict, Any
import urllib.parse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LighthouseMetricsError(Exception):
    """Custom exception for Lighthouse metrics errors"""
    pass

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
    
    # Encode URL properly
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
    
    raise LighthouseMetricsError(f"Could not resolve {sc_domain_url} to a valid URL")

def get_lighthouse_metrics(url: str, api_key: str, retries: int = 3) -> Dict[str, Any]:
    """Fetch Lighthouse metrics with enhanced error handling and logging"""
    if not api_key:
        raise ValueError("API key is required")
    
    try:
        # Validate and clean the URL
        clean_url = validate_url(url)
        logging.info(f"Fetching Lighthouse metrics for: {clean_url}")
        
        # Construct PSI API URL
        psi_api_url = (
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            f"?url={clean_url}"
            f"&key={api_key}"
            f"&strategy=desktop"
            f"&category=performance"
            f"&category=accessibility"
            f"&category=best-practices"
            f"&category=seo"
        )
        
        # Retry logic for the API request
        for attempt in range(retries):
            try:
                # Make the API request
                logging.info(f"Sending request to PageSpeed Insights API (Attempt {attempt + 1}/{retries})")
                response = requests.get(psi_api_url, timeout=60)  # Increased timeout
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                
                # Extract metrics
                lighthouse_result = data.get('lighthouseResult', {})
                
                # Extract key fields
                final_screenshot = lighthouse_result.get('audits', {}).get('final-screenshot', {}).get('details', {}).get('data')
                performance_score = lighthouse_result.get('categories', {}).get('performance', {}).get('score', None)
                seo_score = lighthouse_result.get('categories', {}).get('seo', {}).get('score', None)
                accessibility_score = lighthouse_result.get('categories', {}).get('accessibility', {}).get('score', None)

                metrics = lighthouse_result.get('audits', {})
                performance_metrics = {
                    'FCP': metrics.get('first-contentful-paint', {}).get('numericValue'),
                    'LCP': metrics.get('largest-contentful-paint', {}).get('numericValue'),
                    'SpeedIndex': metrics.get('speed-index', {}).get('numericValue'),
                    'TTI': metrics.get('interactive', {}).get('numericValue'),
                    'TBT': metrics.get('total-blocking-time', {}).get('numericValue'),
                    'CLS': metrics.get('cumulative-layout-shift', {}).get('numericValue'),
                }
                
                # Mobile vs. Desktop Performance
                strategy = data.get('configSettings', {}).get('strategy', 'unknown')
                
                # SEO and Accessibility insights
                seo_metrics = {
                    'viewport': metrics.get('viewport', {}).get('score'),
                    'font_size': metrics.get('font-size', {}).get('score'),
                    'tap_targets': metrics.get('tap-targets', {}).get('score'),
                    'meta_description': metrics.get('meta-description', {}).get('score'),
                    'document_title': metrics.get('document-title', {}).get('score'),
                }
                accessibility_metrics = {
                    'color_contrast': metrics.get('color-contrast', {}).get('score'),
                }
                
                logging.info(f"Lighthouse metrics successfully fetched for {clean_url}")
                
                return {
                    'url': clean_url,
                    'final_screenshot': final_screenshot,
                    'performance_score': round(performance_score * 100, 2) if performance_score is not None else None,
                    'seo_score': round(seo_score * 100, 2) if seo_score is not None else None,
                    'accessibility_score': round(accessibility_score * 100, 2) if accessibility_score is not None else None,
                    'core_web_vitals': performance_metrics,
                    'seo_metrics': seo_metrics,
                    'accessibility_metrics': accessibility_metrics,
                    'strategy': strategy,
                    'optimization_suggestions': metrics.get('opportunities', {}).get('details', {}).get('items', []),
                    'full_report': lighthouse_result
                }
            except requests.exceptions.RequestException as e:
                logging.error(f"Request attempt {attempt + 1} failed for {clean_url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2)  # Small delay between retries
                else:
                    logging.error(f"Failed to fetch Lighthouse metrics after {retries} attempts for {clean_url}: {str(e)}")
                    raise LighthouseMetricsError(f"Failed to fetch Lighthouse metrics after {retries} attempts: {str(e)}")
                
    except (KeyError, ValueError, TypeError) as e:
        logging.error(f"Error parsing response for {url}: {str(e)}")
        raise LighthouseMetricsError(f"Error processing Lighthouse metrics for {url}: {str(e)}")
