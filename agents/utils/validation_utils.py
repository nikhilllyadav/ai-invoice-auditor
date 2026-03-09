import yaml
import requests
from typing import Any


ERP_BASE_URL = "http://localhost:8082"

def load_rules() -> dict[str, Any]:
    """
    This is a utility function to load the configured rules from `./config/rules.yaml` file.
    """
    rules = {}
    with open("config/rules.yaml") as f:
        rules = yaml.safe_load(f)
    
    return rules

def fetch_po_details(po_number: str) -> dict[str, Any]:
    """
    This is a utility function to fetch the purchase order detials from the ERP system.
    """
    response = requests.get(f"{ERP_BASE_URL}/po/{po_number}")
    po_details = response.json()
    return po_details

def fetch_vendor_details(vendor_id: str) -> dict[str, Any]:
    """
    This is a utility function to fetch the vendor detials from the ERP system.
    """
    response = requests.get(f"{ERP_BASE_URL}/vendor/{vendor_id}")
    vendor_details = response.json()
    return vendor_details

