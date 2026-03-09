# agents/extractor_agent.py
import json
from pathlib import Path
from langchain_aws import ChatBedrockConverse
from agents.utils.graph_utils import State
import logging
from logs.logger_module import setup_logger
from agents.personas.persona_utils import load_persona
import re

# Setup the logger
logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)

from agents.utils.extraction_utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_image,
    extract_text_from_json
)


class InvoiceExtractorAgent:

    def __init__(self):
        self.llm = ChatBedrockConverse(
            model="amazon.nova-lite-v1:0",
            max_tokens=500
        )

    def run(self, state: State) -> State:
        logger.info("Graph Entered Extraction node")
        invoice_path = state["document_name"]
        prefix = invoice_path.stem
        suffix = invoice_path.suffix.lower()

        if suffix == ".pdf":
            raw_text = extract_text_from_pdf(invoice_path)
        elif suffix == ".docx":
            raw_text = extract_text_from_docx(invoice_path)
        elif suffix in {".png", ".jpg", ".jpeg"}:
            raw_text = extract_text_from_image(invoice_path)
        else:
            logger.error(f"Unsupported file type: {suffix}")
            raise ValueError(f"Unsupported file type: {suffix}")
        
        meta_file_path = invoice_path.with_name(prefix + ".meta.json")
    
        if meta_file_path.exists():
            # Extract text from the JSON meta file
            extracted_meta = extract_text_from_json(meta_file_path)
        else:
            extracted_meta = "Meta content not available"  # No meta file found

        extracted = self._extract_features_with_llm(raw_text)

        state["raw_content"] = raw_text
        state["extracted_content"] = extracted
        state["extracted_meta_content"]=extracted_meta
        state["status"] = "EXTRACTED"
        logger.info(f"Extracted Content : {extracted}")
        logger.info(f"Extracted Meta Content : {extracted_meta}")
        return state

    def _extract_features_with_llm(self, raw_text: str) -> dict:
        persona = load_persona(name="extractor")
        prompt = f"""
- You are an expert {persona["agent"]["designation"]}.
- Your job is to {persona["purpose"]["description"]}.
- Return ONLY valid JSON. No explanation.
- If a field is not found, return null. Do not guess.

### Output Schema:
{{
  "invoice_no": null,
  "po_number": null,
  "invoice_date": null,
  "vendor_id": "Vendor name goes here...",
  "currency": null,
  "total_amount": null,
  "line_items": [
    {{
      "item_code": null,
      "description": null,
      "quantity": null,
      "unit_price": null,
      "line_total": null
    }}
  ]
}}

- NOTE: If any of the exact field name is missing, search for its related field in the invoice data and populate its content 
    in the required field. (For example: `vendor_id` to `vendor_name`)

Invoice Text:
\"\"\"
{raw_text}
\"\"\"
"""
        response = self.llm.invoke(prompt)
        content = response.content.strip()

        if not content:
            raise ValueError("LLM returned empty response")

        pattern = r"(\{[\s\S]*\})"
        match = re.search(pattern, content)
        if match:
            content = match.group(1)
        
        # parts = content.split("```")
        # content = parts[1]
        # if content.lower().startswith("json"):
        #     content = content[4:].strip()
        

        return json.loads(content)
