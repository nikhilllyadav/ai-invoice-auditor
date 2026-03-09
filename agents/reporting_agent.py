import json
import logging
from pathlib import Path
from langchain_aws import ChatBedrockConverse
from agents.utils.graph_utils import State
from logs.logger_module import setup_logger
from agents.personas.persona_utils import load_persona

# Setup the logger
logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)

# Create LLM instance
llm = ChatBedrockConverse(
    model="cohere.command-r-plus-v1:0", 
    region_name="us-east-1", 
    max_tokens=1500, 
)

def reporting_agent(state: State) -> State:
    logger.info("Reached Reporting Agent")
    invoice_details = state["formatted_content"]
    translation_confidence = state["translation_confidence"]
    invoice_metadata = state["extracted_meta_content"]

    # Load Persona
    persona = load_persona(name="reporting")

    response = llm.invoke(f"""
    - You are an expert {persona["agent"]["designation"]}.
    - You will be given some details about an invoice audit.
    - Your job is to {persona["purpose"]["description"]}.

    ### Instructions:
    {persona["instructions"]}

    ### Required Fields:
    {persona["fields"]}

    ### Follow these Steps
    1. Data Extraction Phase:{persona["steps"]["data_extraction_phase"]}
    2. Translation Phase:{persona["steps"]["translation_phase"]}
    3. Data Validation Phase:{persona["steps"]["data_validation_phase"]}
    4. Business Validation Phase:{persona["steps"]["business_validation_phase"]}

    ### Invoice Audit Information
    - Invoice Details: {invoice_details}
    - Translation Confidence Score: {translation_confidence}
    - Invoice Metadata: {invoice_metadata}
    - Invoice Data Validation Errors: {state.get("validation_errors")}
    - Errors found during Data Validation Phase: {state.get("validation_errors")}
    - AI Agent decision in data validation phase: {state.get("validation_ai_decision")}
    - Human review (feedback) on the data validation interrupt: {state.get("validation_human_remarks")}
    - Errors found during Business Validation Phase: {state.get("business_validation_errors")}
    - Difference percentages between Invoice and ERP data: {state.get("difference_percentage")}
    - AI Agent decision in business validation phase: {state.get("business_validation_ai_decision")}
    - Human review (feedback) on the business validation interrupt: {state.get("business_validation_human_remarks")}

    ### Output Format
    - Output must contain only the generated invoice audit report.
    """)
    audit_report = response.content
    system_report = {
        "document_name": str(state["document_name"]), 
        "final_verdict": (
            state.get("business_validation_human_decision")
            or state.get("validation_human_decision")
            or state.get("business_validation_ai_decision")
            or state.get("validation_ai_decision")
            or "unknown"
        ), 
        "human_verdict": (
            state.get("business_validation_human_decision")
            or state.get("validation_human_decision")
        ),
        "human_remarks": (
            state.get("business_validation_human_remarks")
            or state.get("validation_human_remarks")
        ),
        "invoice_details": invoice_details, 
        "invoice_metadata": invoice_metadata, 
        "audit_report": audit_report, 
    }

    logger.info(f"Invoice Audit Report Generated: {system_report}")

    # Saving the system report to a JSON file
    system_report_dir = Path("data/reports")
    system_report_dir.mkdir(parents=True, exist_ok=True)
    system_report_file_name = f"{state['document_name'].stem}_audit.json"
    system_report_file_path = system_report_dir / system_report_file_name
    with open(system_report_file_path, "w") as f:
        json.dump(system_report, f, indent=2)
    
    logger.info(f"Invoice Audit Report saved to the file: {system_report_file_name}")
    

    return {
        "status": "REPORT_GENERATED", 
        "audit_report": audit_report, 
    }


