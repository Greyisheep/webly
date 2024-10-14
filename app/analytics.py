import requests
from fastapi import HTTPException

def get_ga4_metrics(token: str, property_id: str):
    # Ensure property_id doesn't contain 'properties/' prefix
    if "properties/" in property_id:
        property_id = property_id.split("/")[1]  # Extract the actual ID

    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    headers = {"Authorization": f"Bearer {token}"}
    body = {
        "dimensions": [
            {"name": "sessionSourceMedium"}
        ],
        "metrics": [
            {"name": "activeUsers"},
            {"name": "bounceRate"},
            {"name": "averageSessionDuration"},
            # {"name": "conversionRate"}
        ],
        "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}]
    }

    response = requests.post(url, headers=headers, json=body)

    # Check if the request was successful (status code 200)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Error fetching GA4 metrics: {response.text}")

    # Check if the response body is not empty before parsing
    if not response.content:
        raise HTTPException(status_code=400, detail="Empty response from GA4 API")

    try:
        metrics_data = response.json()
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON response from GA4 API")

    return metrics_data

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