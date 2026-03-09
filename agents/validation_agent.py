from langchain_aws import ChatBedrockConverse
from agents.utils.graph_utils import State
from agents.utils.validation_utils import load_rules
from logs.logger_module import setup_logger
import json
import logging
from agents.personas.persona_utils import load_persona
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

def validation_agent(state: State) -> State:
    """
    This agent validates the invoice data against configured rules.
    """
    # Loading the configured rules
    rules = load_rules()

    # Loading the agent persona
    persona = load_persona(name="validation")

    invoice_data=state.get("formatted_content")
    if not invoice_data:
        invoice_data=state.get("translated_content")

    # Validating invoice data against the configured rules.
    response = llm.invoke(f"""
    - You are an expert Data Validation Agent. 
    - You will be given three things as input: 
        1. python dictionary containing invoice details, 
        2. human review on the invoice details (optional), 
        3. translation confidence
    - Your job is to validate the data against the configured rules and give a decision as ACCEPT / REJECT / HUMAN_REVIEW.
    - If there is a human review then overwrite the invoice details with the information given by the human review, 
        and validate the updated invoice details according to the given rules, while giving the human review as the highest priority.
    - If there is no human feedback, stick to the rules below.

    ### Validation Rules:
    - The data must contain following fields: {rules["required_fields"]["header"] + rules["required_fields"]["line_item"]}.
      in the required field. (For example: `vendor_id` to `vendor_name`)
    - The fields must strictly adhere to these datatypes: {rules["data_types"]}.
    - If the currency symbols are used in input, convert them to their respective string representations as per
      the Currency Symbol Map: {rules["currency_symbol_map"]}.
    - The accepted currencies are: {rules["accepted_currencies"]}.
    - Calculate the total price of each `line_item` using its `qty` and `unit_price` and validate it against 
      the given `total` for that `line_item`.
    - Calculate the sum of `total` from each `line_item`, and validate that against the given `total_amount` for the invoice.
    
    ### Decision Rules:
    - If there are no data discrepencies but if the translation confidence is less than 0.7 => "human_review"
    - If there are minor data discrepencies and if the translation confidence is greater than 0.7 => "accept"
    - If there are any missing fields => "human_review"
    - If there is any currency mismatch or any currency errors => "reject"                                                                                                                                        

    ### Output Format:
    - The output must strictly be in JSON format, containing only three fields: `formatted_content`, `errors` and the decision.
    - If there are any validation errors, populate them into `errors` field as a list of strings, giving your highlights on the error.
    - If there are no errors, the `errors` field must be None.
    - The `formatted_content` field must be populated with the extracted JSON data irrespective of validation error occurs or not. 
    - The "decision" field must be your decision accept/reject/human_review in lower cases without any trailing punctuations.
    - Do not correct any of the errors by yourself.
    - NOTE: The output must strictly not contain any markdown element and without any preamble and explanation(for example: ```json or any other prefix).

    Invoice Data: {invoice_data}
    Translation Confidence: {state["translation_confidence"]}
    Human Feedback : {state.get("validation_human_remarks")}
    Human Decision Override (optional): {state.get("validation_human_decision")}
    """)
    response_content = response.content

    logger.info(f"LLM response in Validation Agent: {response_content}")

    pattern = r"(\{[\s\S]*\})"
    match = re.search(pattern, response_content)
    if match:
        response_content = match.group(1)

    # # For removing markdown syntax (```json) added sometimes.
    # if response_content.startswith("```json"):
    #     response_content = response_content[7:-3]

    parsed_response = json.loads(response_content)
    logger.info(f"LLM response in Validation Agent: {response_content}")

    decision = parsed_response["decision"]
    if state.get("validation_human_decision") in {"accept", "reject", "human_review"}:
        decision = state["validation_human_decision"]

    return {
        "status": "VALIDATED", 
        "formatted_content": parsed_response["formatted_content"], 
        "validation_errors": parsed_response["errors"], 
        "validation_ai_decision": decision, 
    }
