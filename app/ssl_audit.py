import requests
import time

def check_ssl(domain: str):
    url = "https://api.ssllabs.com/api/v3/analyze"
    
    # Start the scan with specific parameters
    params = {
        "host": domain,
        "publish": "off",
        "startNew": "on",
        "all": "done",
        "fromCache": "on"
    }
    response = requests.get(url, params=params)
    
    # Check if initial request was successful
    if response.status_code != 200:
        return {"error": f"Request failed with status code {response.status_code}"}

    data = response.json()

    # Poll the API until the scan completes
    while data.get("status") in ["DNS", "IN_PROGRESS"]:
        time.sleep(10)
        response = requests.get(url, params={"host": domain})
        if response.status_code != 200:
            return {"error": f"Polling request failed with status code {response.status_code}"}
        data = response.json()

    # Check final status after polling
    if data.get("status") != "READY":
        return {"error": f"Scan failed with status: {data.get('status')}"}

    # Extract information with safety checks
    endpoint = data.get("endpoints", [{}])[0]
    results = {
        "domain": domain,
        "grade": endpoint.get("grade"),
        "has_warnings": endpoint.get("hasWarnings"),
        "vulnerabilities": endpoint.get("vulnBeast"),
    }

    return results
