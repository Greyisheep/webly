from fastapi import HTTPException
import requests

def get_user_analytics_data(token: str):
    # Get all Analytics accounts for this user
    headers = {"Authorization": f"Bearer {token}"}
    analytics_accounts_url = "https://analytics.googleapis.com/analytics/v3/management/accounts"
    
    response = requests.get(analytics_accounts_url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Error fetching analytics accounts")

    accounts_data = response.json()
        
    if not accounts_data.get('items'):
        return {"detail": "No Google Analytics accounts found for this user."}
    
    return accounts_data  # Return the accounts data

    
    # Get the first account and its view ID for simplicity
    account_id = accounts_data['items'][0]['id']  # Get the user's first account
    property_url = f"https://analytics.googleapis.com/analytics/v3/management/accounts/{account_id}/webproperties"
    
    properties_response = requests.get(property_url, headers=headers)
    properties_data = properties_response.json()
    
    # Get the first web property for simplicity
    web_property_id = properties_data['items'][0]['id']
    view_url = f"https://analytics.googleapis.com/analytics/v3/management/accounts/{account_id}/webproperties/{web_property_id}/profiles"
    
    views_response = requests.get(view_url, headers=headers)
    views_data = views_response.json()

    view_id = views_data['items'][0]['id']  # Get the user's first view ID

    # Now use the view_id to get analytics data
    analytics_data_url = "https://analytics.googleapis.com/v3/data/ga"
    params = {
        "ids": f"ga:{view_id}",  # Use the user's view ID
        "start-date": "30daysAgo",
        "end-date": "today",
        "metrics": "ga:sessions,ga:bounceRate"
    }

    analytics_response = requests.get(analytics_data_url, headers=headers, params=params)
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
