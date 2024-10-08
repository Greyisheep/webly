from fastapi import HTTPException
import requests

def get_user_analytics_data(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    analytics_accounts_url = "https://analytics.googleapis.com/analytics/v3/management/accounts"
    
    # Fetch Analytics Accounts
    response = requests.get(analytics_accounts_url, headers=headers)
    
    if response.status_code != 200:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        raise HTTPException(status_code=400, detail=f"Error fetching analytics accounts: {error_message}")

    accounts_data = response.json()

    if not accounts_data.get('items'):
        # User has no Google Analytics accounts
        return {"detail": "No Google Analytics accounts found for this user."}

    # Get the first account's ID
    account_id = accounts_data['items'][0]['id']
    property_url = f"https://analytics.googleapis.com/analytics/v3/management/accounts/{account_id}/webproperties"
    
    # Fetch Web Properties
    properties_response = requests.get(property_url, headers=headers)
    
    if properties_response.status_code != 200:
        error_message = properties_response.json().get("error", {}).get("message", "Unknown error")
        raise HTTPException(status_code=400, detail=f"Error fetching web properties: {error_message}")
    
    properties_data = properties_response.json()

    if not properties_data.get('items'):
        # No web properties found for the user
        return {"detail": "No web properties found for this user. Please ensure you have Google Analytics set up."}

    
    # Get the first web property and view
    web_property_id = properties_data['items'][0]['id']
    view_url = f"https://analytics.googleapis.com/analytics/v3/management/accounts/{account_id}/webproperties/{web_property_id}/profiles"
    
    # Fetch Views
    views_response = requests.get(view_url, headers=headers)
    
    if views_response.status_code != 200:
        error_message = views_response.json().get("error", {}).get("message", "Unknown error")
        raise HTTPException(status_code=400, detail=f"Error fetching views: {error_message}")
    
    views_data = views_response.json()

    if not views_data.get('items'):
        return {"detail": "No views found for this user."}

    view_id = views_data['items'][0]['id']
    
    # Fetch Analytics Data using view ID
    analytics_data_url = "https://analytics.googleapis.com/analytics/v4/data/ga"
    params = {
        "ids": f"ga:{view_id}",
        "start-date": "30daysAgo",
        "end-date": "today",
        "metrics": "ga:sessions,ga:bounceRate"
    }

    analytics_response = requests.get(analytics_data_url, headers=headers, params=params)

    if analytics_response.status_code != 200:
        error_message = analytics_response.json().get("error", {}).get("message", "Unknown error")
        raise HTTPException(status_code=400, detail=f"Error fetching analytics data: {error_message}")

    return analytics_response.json()





# def get_analytics_data(token: str):
#     # Define the API endpoint and request body
#     analytics_url = "https://analyticsreporting.googleapis.com/v4/reports:batchGet"
#     headers = {"Authorization": f"Bearer {token}"}
    
#     body = {
#         "reportRequests": [{
#             "viewId": "YOUR_VIEW_ID",  # Replace with your view ID
#             "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
#             "metrics": [{"expression": "ga:users"}, {"expression": "ga:bounceRate"}],
#             "dimensions": [{"name": "ga:sourceMedium"}]
#         }]
#     }
    
#     r = requests.post(analytics_url, json=body, headers=headers)
#     return r.json()
