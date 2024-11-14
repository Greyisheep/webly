import logging
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List, Union
import os
import asyncio
import requests
from urllib.parse import urlparse

import logging.handlers
import json
from datetime import datetime

from app.analytics import get_user_analytics_data
from app.description import get_page_title_and_description
from app.domain_whois import get_whois_data
from app.lighthouse_metrics import get_lighthouse_metrics
from app.news_fetcher import fetch_google_rss_news
from app.oauth import get_google_auth_url, get_google_token
from app.search_console import get_user_search_console_data
from app.ssl_audit import check_ssl
from app.trends import get_keyword_trend, get_rising_queries

# Custom timeout and Google API key
DEFAULT_TIMEOUT = 60  # Timeout in seconds for API requests
PAGE_SPEED_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Utility to clean and validate URL
def clean_url(target: str) -> str:
    """
    Ensure the URL is in the correct format with a scheme and no trailing slashes.
    """
    parsed_url = urlparse(target)
    
    # If no scheme (http/https) is provided, assume 'http://'
    if not parsed_url.scheme:
        target = f"http://{target}"
        parsed_url = urlparse(target)  # Re-parse after adding scheme

    # Clean up any trailing slashes from the path
    cleaned_url = parsed_url.scheme + "://" + parsed_url.netloc
    return cleaned_url


def serialize_data(data: Any) -> Any:
    """
    Recursively serialize data to ensure JSON compatibility
    """
    if data is None:
        return None
    elif isinstance(data, (str, int, float, bool)):
        return data
    elif isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items() if v is not None}
    elif isinstance(data, (list, tuple)):
        return [serialize_data(item) for item in data if item is not None]
    else:
        return str(data)


def is_valid_url(url: str) -> bool:
    """
    Validate if the URL is fully qualified and correctly formatted
    """
    return url.startswith("http://") or url.startswith("https://")

# Enhanced logging configuration
def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler for debug logs
    file_handler = logging.handlers.RotatingFileHandler(
        'debug.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

setup_logging()
logger = logging.getLogger(__name__)

# async def fetch_lighthouse_metrics(site_url: str, api_key: str) -> Dict[str, Any]:
#     """
#     Asynchronously fetch Lighthouse metrics with enhanced error handling and debugging.
#     """
#     request_id = datetime.now().strftime('%Y%m%d_%H%M%S')
#     logger.info(f"[{request_id}] Starting Lighthouse metrics fetch for URL: {site_url}")
    
#     try:
#         # Validate inputs
#         if not site_url:
#             raise ValueError("Empty URL provided")
#         if not api_key:
#             raise ValueError("API key not provided")
            
#         logger.debug(f"[{request_id}] API Key present: {bool(api_key)}, Length: {len(api_key)}")
        
#         # Clean URL
#         clean_target = clean_url(site_url)
#         logger.debug(f"[{request_id}] Cleaned URL: {clean_target}")
        
#         if not is_valid_url(clean_target):
#             raise ValueError(f"Invalid URL after cleaning: {clean_target}")
        
#         # Import and use lighthouse_metrics module
#         from app.lighthouse_metrics import get_lighthouse_metrics
        
#         # Fetch metrics with timeout
#         try:
#             metrics = await asyncio.wait_for(
#                 asyncio.to_thread(get_lighthouse_metrics, clean_target, api_key),
#                 timeout=120  # 2 minute timeout
#             )
            
#             logger.info(f"[{request_id}] Successfully fetched metrics for {clean_target}")
#             logger.debug(f"[{request_id}] Raw metrics: {json.dumps(metrics, indent=2)}")
            
#             return {
#                 "success": True,
#                 "data": serialize_data(metrics),
#                 "error": None,
#                 "request_id": request_id
#             }
            
#         except asyncio.TimeoutError:
#             logger.error(f"[{request_id}] Timeout while fetching metrics for {clean_target}")
#             return {
#                 "success": False,
#                 "data": None,
#                 "error": "Request timed out after 120 seconds",
#                 "request_id": request_id
#             }
            
#     except Exception as e:
#         logger.exception(f"[{request_id}] Error fetching Lighthouse metrics for {site_url}")
#         return {
#             "success": False,
#             "data": None,
#             "error": str(e),
#             "request_id": request_id
#         }


@app.get("/", response_class=HTMLResponse)
async def get_homepage(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})

@app.post("/process_url", response_class=HTMLResponse)
async def process_url(request: Request, url: str = Form(...)):
    clean_target = clean_url(url)
    try:
        # Call synchronous functions within asyncio.to_thread for compatibility
        news_data = await asyncio.to_thread(fetch_google_rss_news, clean_target)
        whois_data = await asyncio.to_thread(get_whois_data, clean_target)
        lighthouse_data = await asyncio.to_thread(get_lighthouse_metrics, clean_target, PAGE_SPEED_API_KEY)
        page_title_and_description = await asyncio.to_thread(get_page_title_and_description, clean_target)
        ssl_audit = await asyncio.to_thread(check_ssl, clean_target)
        trend_data = await asyncio.to_thread(get_keyword_trend, clean_target)
        trend_data_json = {
            "dates": trend_data.index.strftime('%Y-%m-%d').tolist(),  # Convert dates to strings
            "popularity": trend_data[clean_target].tolist()          # Use the actual keyword name
        }
        rising_queries = await asyncio.to_thread(get_rising_queries, clean_target)
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        raise HTTPException(status_code=400, detail="Error fetching metrics.")
    
    # Render result template with WHOIS and PageSpeed data
    return templates.TemplateResponse("results.html", {
        "request": request,
        "news_data": serialize_data(news_data),
        "whois_data": serialize_data(whois_data),
        "lighthouse_data": serialize_data(lighthouse_data),
        "page_title_and_description": serialize_data(page_title_and_description),
        "ssl_audit": serialize_data(ssl_audit),
        # "trend_data": serialize_data(trend_data_json),
        "rising_queries": serialize_data(rising_queries)
    })


@app.get("/auth")
async def google_login():
    auth_url = get_google_auth_url()
    return RedirectResponse(auth_url)


@app.get("/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request, code: str):
    request_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    logger.info(f"[{request_id}] Starting OAuth callback processing")
    
    try:
        token = get_google_token(code)
        logger.debug(f"[{request_id}] Successfully obtained OAuth token")
        
        analytics_data = {"success": False, "data": None, "error": None}
        search_console_data = {"success": False, "data": None, "error": None}
        # lighthouse_data = []

        # Fetch and log analytics data
        try:
            raw_analytics = await asyncio.to_thread(get_user_analytics_data, token)
            analytics_data = {"success": True, "data": serialize_data(raw_analytics), "error": None}
            logger.debug(f"[{request_id}] Analytics data fetched successfully")
        except Exception as e:
            logger.error(f"[{request_id}] Analytics error: {str(e)}")
            analytics_data["error"] = str(e)

        # Fetch and log search console data
        try:
            raw_search_console = await asyncio.to_thread(get_user_search_console_data, token)
            search_console_data = {"success": True, "data": serialize_data(raw_search_console), "error": None}
            logger.debug(f"[{request_id}] Search Console data fetched successfully")
            
            # Log the structure of search_console_data
            logger.debug(f"[{request_id}] Search Console data structure: {json.dumps(search_console_data, indent=2)}")
        except Exception as e:
            logger.error(f"[{request_id}] Search Console error: {str(e)}")
            search_console_data["error"] = str(e)

        # Extract and validate site URLs
        site_urls = []
        if search_console_data.get("success") and search_console_data.get("data"):
            # Handle both possible data structures
            if isinstance(search_console_data["data"], dict):
                if "success" in search_console_data["data"]:
                    site_urls = list(search_console_data["data"]["success"].keys())
                else:
                    site_urls = list(search_console_data["data"].keys())
            
            logger.info(f"[{request_id}] Extracted site URLs: {site_urls}")
        
        if not site_urls:
            logger.error(f"[{request_id}] No valid site URLs found in Search Console data")
            raise ValueError("No valid sites found in Search Console data")

        template_data = {
            "request_id": request_id,
            "analytics_data": analytics_data,
            "search_console_data": search_console_data,
            # "lighthouse_data": lighthouse_data,
        }
        
        # Log template data structure before rendering
        logger.debug(f"[{request_id}] Template data structure: {json.dumps(template_data, indent=2)}")

        return templates.TemplateResponse("dashboard.html", {"request": request, **template_data})
    
    except Exception as e:
        logger.exception(f"[{request_id}] Unexpected error in callback")
        raise HTTPException(status_code=500, detail=str(e))