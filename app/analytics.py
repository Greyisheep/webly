import requests
from fastapi import HTTPException
from typing import List
import asyncio
import aiohttp

async def fetch_metrics_batch(session, url: str, headers: dict, dimensions: List[dict], metrics: List[dict], date_ranges: List[dict]) -> dict:
    body = {
        "dimensions": dimensions,
        "metrics": metrics,
        "dateRanges": date_ranges
    }
    
    async with session.post(url, headers=headers, json=body) as response:
        if response.status != 200:
            text = await response.text()
            raise HTTPException(status_code=response.status, detail=f"Error fetching GA4 metrics: {text}")
        return await response.json()

async def get_ga4_metrics_async(token: str, property_id: str):
    # Ensure property_id doesn't contain 'properties/' prefix
    if "properties/" in property_id:
        property_id = property_id.split("/")[1]

    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Split dimensions into batches of 9 or fewer
    report_batches = [
        {
            "dimensions": [
                {"name": "sessionSourceMedium"},
                {"name": "sourceMedium"},
                {"name": "source"},
                {"name": "medium"},
                {"name": "campaignName"},
                {"name": "campaignId"},
                {"name": "googleAdsCampaignId"},
                {"name": "defaultChannelGroup"},
                {"name": "primaryChannelGroup"},
            ],
            "metrics":[
                {"name": "activeUsers"},
                {"name": "bounceRate"},
                {"name": "totalUsers"},
            ]
        },

        {
            "dimensions": [
                {"name": "sessionSourceMedium"},
                {"name": "country"},
                {"name": "city"},
                {"name": "region"},
                {"name": "pagePath"},
                {"name": "pageReferrer"},
                {"name": "pageTitle"},
                {"name": "percentScrolled"},
            ],
            "metrics":[
                {"name": "keyEvents"},
                {"name": "newUsers"},
                {"name": "averageSessionDuration"},
                {"name": "screenPageViews"},
                {"name": "screenPageViewsPerSession"},
                {"name": "userEngagementDuration"},
                {"name": "eventCount"},
                {"name": "eventCountPerUser"},
            ]
        }
    ]
    date_ranges = [{"startDate": "30daysAgo", "endDate": "today"}]


    try:
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_metrics_batch(
                    session, 
                    url, 
                    headers, 
                    batch["dimensions"], 
                    batch["metrics"], 
                    date_ranges
                )
                for batch in report_batches
            ]
            
            results = await asyncio.gather(*tasks)
            
        # Combine results from all batches
        combined_results = {
            "dimensionHeaders": [],
            "metricHeaders": [],
            "rows": [],
            "totals": [],
            "maximums": [],
            "minimums": [],
            "rowCount": 0
        }
        
        # Track seen dimensions and metrics
        seen_dimension_headers = set()
        seen_metric_headers = set()
        seen_dimension_values = set()
        
        for result in results:
            # Add new dimension headers
            for header in result.get("dimensionHeaders", []):
                header_name = header.get("name")
                if header_name not in seen_dimension_headers:
                    seen_dimension_headers.add(header_name)
                    combined_results["dimensionHeaders"].append(header)
            
            # Add new metric headers
            for header in result.get("metricHeaders", []):
                header_name = header.get("name")
                if header_name not in seen_metric_headers:
                    seen_metric_headers.add(header_name)
                    combined_results["metricHeaders"].append(header)
            
            # Process rows
            for row in result.get("rows", []):
                dimension_values = tuple(dim.get("value") for dim in row.get("dimensionValues", []))
                if dimension_values not in seen_dimension_values:
                    seen_dimension_values.add(dimension_values)
                    combined_results["rows"].append(row)
            
            # Combine other metrics
            if result.get("totals"):
                combined_results["totals"].extend(result["totals"])
            if result.get("maximums"):
                combined_results["maximums"].extend(result["maximums"])
            if result.get("minimums"):
                combined_results["minimums"].extend(result["minimums"])
            combined_results["rowCount"] += result.get("rowCount", 0)
            
        return combined_results

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing GA4 metrics: {str(e)}")

def get_ga4_metrics(token: str, property_id: str):
    """Synchronous wrapper for the async function"""
    return asyncio.run(get_ga4_metrics_async(token, property_id))

def get_user_analytics_data(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    account_info = []

    # Fetch GA4 Properties and their metrics
    ga4_properties = get_ga4_properties(token)
    if ga4_properties.get("accountSummaries"):
        for account_summary in ga4_properties['accountSummaries']:
            account_name = account_summary.get('account', 'Unknown')

            # Loop through all property summaries for the account
            for property_summary in account_summary.get('propertySummaries', []):
                property_id = property_summary.get('property', 'Unknown')

                # Get GA4 metrics
                metrics_data = get_ga4_metrics(token, property_id)

                account_info.append({
                    "account_id": account_name,
                    "property_id": property_id,
                    "metrics": metrics_data,
                    "status": "GA4 properties and metrics found"
                })
    else:
        account_info.append({"detail": "No GA4 accounts found for this user."})

    if len(account_info) == 0:
        return {"analytics_data": {"detail": "No analytics data found for any account."}}

    return {"analytics_data": account_info}

def get_ga4_properties(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    ga4_accounts_url = "https://analyticsadmin.googleapis.com/v1beta/accountSummaries"
    
    response = requests.get(ga4_accounts_url, headers=headers)
    
    if response.status_code != 200:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        raise HTTPException(status_code=400, detail=f"Error fetching GA4 properties: {error_message}")
    
    accounts_data = response.json()
    
    if not accounts_data.get('accountSummaries'):
        return {"detail": "No GA4 accounts found for this user."}
    
    return accounts_data