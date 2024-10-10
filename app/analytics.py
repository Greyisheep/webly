from fastapi import HTTPException
import requests

def get_user_analytics_data(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    account_info = []
    
    # Fetch Universal Analytics (UA) Accounts
    analytics_accounts_url = "https://analytics.googleapis.com/analytics/v3/management/accounts"
    ua_response = requests.get(analytics_accounts_url, headers=headers)
    
    if ua_response.status_code != 200:
        error_message = ua_response.json().get("error", {}).get("message", "Unknown error")
        raise HTTPException(status_code=400, detail=f"Error fetching Universal Analytics accounts: {error_message}")
    
    ua_accounts_data = ua_response.json()

    if ua_accounts_data.get('items'):
        for account in ua_accounts_data['items']:
            account_id = account['id']
            property_url = f"https://analytics.googleapis.com/analytics/v3/management/accounts/{account_id}/webproperties"
            properties_response = requests.get(property_url, headers=headers)

            if properties_response.status_code == 200:
                properties_data = properties_response.json()
                if properties_data.get('items'):
                    for property in properties_data['items']:
                        account_info.append({
                            "account_id": account_id,
                            "web_property_id": property['id'],
                            "status": "Web properties found"
                        })
                else:
                    account_info.append({
                        "account_id": account_id,
                        "status": "No web properties"
                    })
            else:
                error_message = properties_response.json().get("error", {}).get("message", "Unknown error")
                account_info.append({
                    "account_id": account_id,
                    "status": f"Error fetching web properties: {error_message}"
                })
    else:
        account_info.append({"detail": "No Universal Analytics accounts found for this user."})
    
    # Fetch GA4 Properties
    ga4_properties = get_ga4_properties(token)
    if ga4_properties.get("accountSummaries"):
        for account_summary in ga4_properties['accountSummaries']:
            print(account_summary)  # Debugging print
            
            # Handle GA4 response structure
            account_name = account_summary.get('account', 'Unknown')
            if isinstance(account_name, str):
                account_info.append({
                    "account_id": account_name,
                    "property_id": account_summary.get('propertySummaries', [{}])[0].get('property', 'Unknown'),
                    "status": "GA4 properties found"
                })
            else:
                account_info.append({
                    "account_id": "Unknown",
                    "status": "Unexpected account structure in GA4 response"
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


# from fastapi import HTTPException
# import requests

# def get_user_analytics_data(token: str):
#     headers = {"Authorization": f"Bearer {token}"}
#     analytics_accounts_url = "https://analytics.googleapis.com/analytics/v3/management/accounts"
    
#     # Fetch Analytics Accounts
#     response = requests.get(analytics_accounts_url, headers=headers)
    
#     if response.status_code != 200:
#         error_message = response.json().get("error", {}).get("message", "Unknown error")
#         raise HTTPException(status_code=400, detail=f"Error fetching analytics accounts: {error_message}")

#     accounts_data = response.json()

#     if not accounts_data.get('items'):
#         return {"detail": "No Google Analytics accounts found for this user."}

#     all_analytics_data = []
#     account_info = []  # To track which accounts/properties/views have data

#     # Loop through each account
#     for account in accounts_data['items']:
#         account_id = account['id']
#         property_url = f"https://analytics.googleapis.com/analytics/v3/management/accounts/{account_id}/webproperties"
        
#         # Fetch Web Properties for each account
#         properties_response = requests.get(property_url, headers=headers)
        
#         if properties_response.status_code != 200:
#             error_message = properties_response.json().get("error", {}).get("message", "Unknown error")
#             raise HTTPException(status_code=400, detail=f"Error fetching web properties: {error_message}")
        
#         properties_data = properties_response.json()

#         if not properties_data.get('items'):
#             account_info.append({"account_id": account_id, "status": "No web properties"})
#             continue  # Skip accounts without web properties

#         # Loop through each web property
#         for web_property in properties_data['items']:
#             web_property_id = web_property['id']
#             view_url = f"https://analytics.googleapis.com/analytics/v3/management/accounts/{account_id}/webproperties/{web_property_id}/profiles"
            
#             # Fetch Views for each web property
#             views_response = requests.get(view_url, headers=headers)
            
#             if views_response.status_code != 200:
#                 error_message = views_response.json().get("error", {}).get("message", "Unknown error")
#                 raise HTTPException(status_code=400, detail=f"Error fetching views: {error_message}")
            
#             views_data = views_response.json()

#             if not views_data.get('items'):
#                 account_info.append({"account_id": account_id, "web_property_id": web_property_id, "status": "No views"})
#                 continue  # Skip web properties without views

#             # Loop through each view
#             for view in views_data['items']:
#                 view_id = view['id']
                
#                 # Fetch Analytics Data using view ID
#                 analytics_data_url = "https://analyticsreporting.googleapis.com/v4/reports:batchGet"
#                 body = {
#                     "reportRequests": [{
#                         "viewId": f"ga:{view_id}",
#                         "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}],
#                         "metrics": [{"expression": "ga:sessions"}, {"expression": "ga:bounceRate"}, {"expression": "ga:avgSessionDuration"}],
#                         "dimensions": [{"name": "ga:sourceMedium"}]
#                     }]
#                 }

#                 analytics_response = requests.post(analytics_data_url, json=body, headers=headers)

#                 if analytics_response.status_code != 200:
#                     error_message = analytics_response.json().get("error", {}).get("message", "Unknown error")
#                     raise HTTPException(status_code=400, detail=f"Error fetching analytics data: {error_message}")

#                 analytics_data = analytics_response.json()

#                 if 'reports' in analytics_data and analytics_data['reports']:
#                     all_analytics_data.append(analytics_data)
#                     account_info.append({
#                         "account_id": account_id,
#                         "web_property_id": web_property_id,
#                         "view_id": view_id,
#                         "status": "Data found"
#                     })
#                 else:
#                     account_info.append({
#                         "account_id": account_id,
#                         "web_property_id": web_property_id,
#                         "view_id": view_id,
#                         "status": "No analytics data"
#                     })

#     if not all_analytics_data:
#         return {"detail": "No analytics data found for any account.", "account_info": account_info}

#     return {"analytics_data": all_analytics_data, "account_info": account_info}
