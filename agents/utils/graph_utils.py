from typing import TypedDict, Any
from pathlib import Path
from typing import List, Annotated, Literal
import operator

class State(TypedDict):
    status:str                                          ## Current status of flow
    document_name: Path                                 ## Stores the file name
    raw_content:str                                     ## Store the raw extracted content from extractor agent
    extracted_content: dict[str, Any]                   ## Stores the structured extracted content from extractor agent
    extracted_meta_content: dict[str, Any]              ## Final Meta Data
    translated_content: dict[str, Any]                  ## Translated Content from Translating agent
    translation_confidence: float                       ## Confidence score by LLM for the generated translation
    formatted_content: dict[str, Any]                   ## Final Formatted Data after Validation
    validation_errors: List[str]                        ## Errors in the invoice data found during the validation phase
    corrections_done: List[str]                         ## Corrections made by the Validation agent to ensure compliance with the required structure
    validation_ai_decision: Literal['accept','reject','human_review']                        ## Human input received for HITL triggered by Validation agent
    validation_human_remarks: Annotated[List[str], operator.add]
    validation_human_decision: Literal['accept','reject','human_review'] | None
    business_validation_errors: List[str]
    difference_percentage: dict[str, Any]
    business_validation_ai_decision: Literal['accept','reject','human_review']  
    business_validation_human_remarks: Annotated[List[str], operator.add]
    business_validation_human_decision: Literal['accept','reject','human_review'] | None
    audit_report: dict[str, Any]
