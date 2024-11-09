# app/domain_whois.py
import whois

def get_whois_data(domain_name: str) -> dict:
    """Fetch and return WHOIS information for a given domain."""
    try:
        # Fetch domain information
        domain = whois.whois(domain_name)
        
        # Organize the WHOIS data into a dictionary
        domain_info = {
            "Domain Name": domain.domain_name,
            "Registrar": domain.registrar,
            "Creation Date": domain.creation_date,
            "Expiration Date": domain.expiration_date,
            "Registrant": domain.registrant_name,
            "Administrative Contact": domain.admin_name,
            "Technical Contact": domain.tech_name,
            "Name Servers": domain.name_servers,
            "Domain Status": domain.status,
            "Registrar Abuse Contact Email": domain.emails,
            "Registrar Abuse Contact Phone": domain.phone,
        }
        
        return domain_info
    except Exception as e:
        # Return an error message if the WHOIS lookup fails
        return {"error": str(e)}
