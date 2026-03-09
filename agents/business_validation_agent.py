from langchain_aws import ChatBedrockConverse
from agents.utils.validation_utils import load_rules, fetch_po_details, fetch_vendor_details
from agents.utils.graph_utils import State
from logs.logger_module import setup_logger
import logging
import json
import re


# Setup the logger
logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)

# Create LLM instance
llm = ChatBedrockConverse(
    model="cohere.command-r-plus-v1:0", 
    region_name="us-east-1", 
    max_tokens=1500, 
    temperature=0.7
)

def business_validation_agent(state: State) -> State:
    """
    This agent validates the invoice data against the data reflected by ERP.
    """
    # Extracting the latest invoice details from state
    invoice_data = state["formatted_content"]
    extracted_data = state["extracted_content"]

    # Loading the configured rules
    rules = load_rules()

    # Fetching data from the ERP system
    po_suffix = invoice_data.get("invoice_no") or invoice_data.get("header").get("invoice_no")
    # po_number = "PO" + po_suffix[3:]
    po_number=extracted_data.get("po_number")
    # vendor_id = invoice_data.get("vendor_id") or invoice_data.get("header").get("vendor_id")
    po_details = fetch_po_details(po_number=po_number)
    vendor_details = fetch_vendor_details(vendor_id=po_details.get("vendor_id"))

    response = llm.invoke(f"""
    - You are an expert ERP Data Validator. 
    - You will be given the following data as input: 
        1. A python dictionary containing details extracted from an invoice, 
        2. Purchase order details retrieved from the ERP system.
        3. Vendor details retrieved from the ERP system,
        4. Human review on the invoice details (optional), 
    - Your job is to validate the data against the the purchase order and vendor details retrieved from the ERP system, 
        and give a decision as ACCEPT / REJECT / HUMAN_REVIEW.
    - If there is a human review or feedback available, consider it as a highest 
      priority feedback and do the changes as per the human review, 
      while considering the below rules also.
    - If there is no human feedback, stick to the rules below.

    ### Instructions
    - Validate the following properties for each item:
        1. Item Quantity
        2. Currency consistency
        3. Item Unit Price
        4. Item Total Price (i.e. quantity x unit_price)
    - If there is a mismatch in any of these numerical quantities, calculate the following difference percentages:
        1. price_difference_percent
        2. quantity_difference_percent
        3. tax_difference_percent
    - These are the threshold (maximum allowed) deviations when comparing invoice v/s ERP data: {rules["tolerances"]}.

    ### Decision Rules:
    - If there is no data mismatch between ERP and invoice data => "accept"
    - If the mismatch percentages are within the range of given threshold for respective fields => "human_review"
    - If the mismatch percentages exceed the given threshold for respective fields => "reject"

    ### Output Format
    - The output must strictly be in JSON format containing the following fields: `errors`, `difference_percentage` and `decision`.
    - Always populate the `difference_percentage` field with the calculated difference percentages
        as a dictionary containing field names (e.g. price_difference_percentage, quantity_difference_percentage, etc...)
        and their corresponding values.
    - If there are data discrepancies or data mismatch, populate them into `errors` field as a list of strings, giving your highlights on the error.
    - If any difference percentage is above its threshold value, inlude that in the `errors` as well.
    - If there are no errors, the `errors` field must be None.
    - `decision` field must be accept/reject/human_review in lower cases without any trailing punctuations.
    - NOTE: The output must strictly not contain any markdown element (for example: ```json or any other prefix).

    Invoice Data: {invoice_data}
    Purchase Order Details from ERP System: {po_details}
    Vendor Details from ERP System: {vendor_details}
    Human Review: {state.get("business_validation_human_remarks")}
    Human Decision Override (optional): {state.get("business_validation_human_decision")}
    """)
    response_content = response.content
    
    logger.info(f"LLM response in Business Validation Agent: {response_content}")

    pattern = r"(\{[\s\S]*\})"
    match = re.search(pattern, response_content)
    if match:
        response_content = match.group(1)

    # # For removing markdown syntax (```json) added sometimes.
    # if response_content.startswith("```json"):
    #     response_content = response_content[7:-3]

    parsed_response = json.loads(response_content)
    
    logger.info(f"LLM response in Business Validation Agent: {parsed_response}")

    decision = parsed_response["decision"]
    if state.get("business_validation_human_decision") in {"accept", "reject", "human_review"}:
        decision = state["business_validation_human_decision"]

    return {
        "status": "BUSINESS_VALIDATED", 
        "business_validation_errors": parsed_response["errors"], 
        "difference_percentage": parsed_response["difference_percentage"], 
        "business_validation_ai_decision": decision, 
    }
