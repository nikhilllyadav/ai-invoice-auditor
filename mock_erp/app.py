from fastapi import FastAPI, HTTPException
from mock_erp.schemas import PODetails, VendorDetails
import json


app = FastAPI(title="ERP Details API")

@app.get("/po/{po_number}")
def get_po_details(po_number: str) -> PODetails:
    """
    Endpoint to get PO Details from the ERP.
    """
    # Load the json file
    erp_po_records = {}
    with open("data/ERP_mockdata/PO Records.json", "r") as f:
        erp_po_records = json.load(f)
    
    # Search for the requested po_number
    po_details = {}
    for po_record in erp_po_records:
        if po_record["po_number"] == po_number:
            po_details = po_record
            break
    
    # Raise an exception if the requested PO is not found
    if not po_details:
        raise HTTPException(
            status_code=404, 
            detail=f"No purchase order found with ID: {po_number}", 
        )
    
    return po_details

@app.get("/vendor/{vendor_id}")
def get_vendor_details(vendor_id: str) -> VendorDetails:
    """
    Endpoint to get Vendor details from the ERP.
    """
    # Load the json file
    erp_vendor_records = {}
    with open("data/ERP_mockdata/vendors.json", "r") as f:
        erp_vendor_records = json.load(f)
    
    # Search for the requested vendor_id
    vendor_details = {}
    for vendor_record in erp_vendor_records:
        if vendor_record["vendor_id"] == vendor_id:
            vendor_details = vendor_record
            break
    
    # Raise an exception if the requested Vendor is not found
    if not vendor_details:
        raise HTTPException(
            status_code=404, 
            detail=f"No vendor found with ID: {vendor_id}", 
        )
    
    return vendor_details