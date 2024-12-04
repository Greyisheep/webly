import requests
import time
from typing import Dict, Any
import logging
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def create_session():
    """Create a session with retry strategy"""
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    return session

def check_ssl(domain: str, timeout: int = 60, max_wait_time: int = 300) -> Dict[str, Any]:
    """
    Check SSL configuration of a domain using SSL Labs API.
    Returns DNS resolution results if full SSL check fails.
    """
    base_url = "https://api.ssllabs.com/api/v3"
    headers = {
        'User-Agent': 'SSLChecker/1.0',
        'Accept': 'application/json'
    }
    session = create_session()
    initial_dns_data = None
    
    try:
        # Check API availability
        info_response = session.get(
            f"{base_url}/info", 
            headers=headers, 
            timeout=timeout
        )
        info_response.raise_for_status()
        logging.debug("API Info response: %s", info_response.json())
        
        # Main scan parameters
        params = {
            "host": domain,
            "publish": "off",
            "all": "done",
            "fromCache": "on",
            "ignoreMismatch": "on"
        }
        
        # Initial scan request
        response = session.get(
            f"{base_url}/analyze", 
            params=params, 
            headers=headers, 
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        
        logging.debug("Initial scan response status: %s", response.status_code)
        logging.debug("Response data: %s", data)

        # Store DNS resolution data when we first get it
        if data.get("status") == "DNS":
            initial_dns_data = {
                "status": "DNS_ONLY",
                "domain": domain,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dns_data": {
                    "host": data.get("host"),
                    "port": data.get("port"),
                    "protocol": data.get("protocol"),
                    "status_message": data.get("statusMessage"),
                    "engine_version": data.get("engineVersion"),
                    "criteria_version": data.get("criteriaVersion")
                }
            }

        # Continue with full SSL analysis
        start_time = time.time()
        while data.get("status") in ["DNS", "IN_PROGRESS"]:
            if time.time() - start_time > max_wait_time:
                if initial_dns_data:
                    return initial_dns_data
                return {"error": f"Scan timed out after {max_wait_time} seconds"}
            
            logging.debug(f"Scan in progress: {data.get('status')}. Waiting...")
            time.sleep(min(30, max(10, int((time.time() - start_time) / 10))))  # Dynamic sleep time
            
            response = session.get(
                f"{base_url}/analyze", 
                params={"host": domain, "all": "done"}, 
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "READY":
            if initial_dns_data:
                return initial_dns_data
            return {
                "error": f"Scan failed with status: {data.get('status')}",
                "status_message": data.get("statusMessage", "No status message provided")
            }

        endpoints = data.get("endpoints", [{}])
        if not endpoints:
            if initial_dns_data:
                return initial_dns_data
            return {"error": "No endpoints found in scan results"}

        primary_endpoint = endpoints[0]
        
        results = {
            'basic_info': {
                'host': data.get('host'),
                'ip_address': data['endpoints'][0].get('ipAddress'),
                'grade': data['endpoints'][0].get('grade'),
                'has_warnings': data['endpoints'][0].get('hasWarnings', False),
                'status': data.get('status'),
            },
            'protocols': {
                'supported': [f"{p['name']} {p['version']}" for p in data['endpoints'][0]['details'].get('protocols', [])],
                'preference': data['endpoints'][0]['details']['suites'][0].get('preference', False)
            },
            'certificates': {
                'chains': len(data['endpoints'][0]['details']['certChains']),
                'trust_paths': [],
                'ocsp_stapling': data['endpoints'][0]['details'].get('ocspStapling', False)
            },
            'cipher_suites': {
                'tls12': [suite['name'] for suite in data['endpoints'][0]['details']['suites'][0]['list']],
                'tls13': [suite['name'] for suite in data['endpoints'][0]['details']['suites'][1]['list']] if len(data['endpoints'][0]['details']['suites']) > 1 else [],
                'forward_secrecy': data['endpoints'][0]['details'].get('forwardSecrecy', 0)
            },
            'security_features': {
                'secure_renegotiation': data['endpoints'][0]['details'].get('renegSupport', 0),
                'session_resumption': data['endpoints'][0]['details'].get('sessionResumption', 0),
                'npn_protocols': data['endpoints'][0]['details'].get('npnProtocols', ''),
                'alpn_protocols': data['endpoints'][0]['details'].get('alpnProtocols', ''),
                'session_tickets': data['endpoints'][0]['details'].get('sessionTickets', 0)
            }
        }
        
        # Add trust information
        for chain in data['endpoints'][0]['details']['certChains']:
            for path in chain['trustPaths']:
                results['certificates']['trust_paths'].extend([
                    f"{trust['rootStore']}: {'Trusted' if trust['isTrusted'] else 'Untrusted'}"
                    for trust in path['trust']
                ])
        
        return results

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        if initial_dns_data:
            return initial_dns_data
        return {
            "error": f"Request failed: {str(e)}",
            "details": {
                "status_code": getattr(e.response, 'status_code', None),
                "response_text": getattr(e.response, 'text', None)
            }
        }
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        if initial_dns_data:
            return initial_dns_data
        return {"error": f"Unexpected error: {str(e)}"}

# Configure logging only if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )