from pydantic import BaseModel


class Item(BaseModel):
    item_code: str
    description: str
    currency: str
    qty: int
    unit_price: float

class VendorDetails(BaseModel):
    vendor_id: str
    vendor_name: str
    country: str
    currency: str

class PODetails(BaseModel):
    po_number: str
    vendor_id: str
    line_items: list[Item]
