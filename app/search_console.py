from fastapi import HTTPException
import requests

def get_user_search_console_data(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get the list of sites for this user
    site_list_url = "https://www.googleapis.com/webmasters/v3/sites"
    response = requests.get(site_list_url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Error fetching Search Console sites")

    sites_data = response.json()
    
    # Get the first site for simplicity
    site_url = sites_data['siteEntry'][0]['siteUrl']

    # Use this site URL to get the search analytics data
    search_console_data_url = f"https://www.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query"
    data = {
        "startDate": "2023-01-01",
        "endDate": "2023-01-30",
        "dimensions": ["query"]
    }

    search_console_response = requests.post(search_console_data_url, headers=headers, json=data)
    return search_console_response.json()



# def get_search_console_data(token: str):
#     search_console_url = "https://www.googleapis.com/webmasters/v3/sites/dev.to/greyisheepai/searchAnalytics/query"
#     headers = {"Authorization": f"Bearer {token}"}
    
#     body = {
#         "startDate": "2023-01-01",
#         "endDate": "2023-10-01",
#         "dimensions": ["query"],
#         "rowLimit": 10
#     }
    
#     r = requests.post(search_console_url, json=body, headers=headers)
#     return r.json()
