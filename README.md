# AI Invoice Auditor

AI Invoice Auditor is an **Agentic AI-powered multilingual invoice validation system** that automates invoice extraction, translation, validation, and auditing using LLM-based agents and a Retrieval-Augmented Generation (RAG) pipeline.

The system processes invoices received in different formats and languages, validates them against ERP records, and generates structured discrepancy reports while allowing human review through a dashboard.

---

## Problem Statement

Organizations receive hundreds of invoices daily in various formats (PDF, DOCX, scanned images) and languages. Manual verification is slow, error-prone, and expensive.

AI Invoice Auditor automates the entire workflow:
- Extract invoice data
- Translate multilingual content
- Validate against ERP records
- Generate discrepancy reports
- Allow human feedback and corrections
- Provide AI-powered invoice query capabilities

---

## Key Features

- Automated invoice ingestion
- Multi-format document support (PDF, DOCX, PNG)
- OCR for scanned invoices
- Multilingual translation
- Rule-based invoice validation
- ERP data verification
- Discrepancy report generation
- RAG-based invoice query system
- Human-in-the-loop review dashboard
- Modular agent-based architecture

---

## System Architecture

The system follows an **Agentic AI architecture** where multiple agents collaborate in a workflow.

1. **Invoice Monitor Agent**
   - Detects new invoices in `/data/incoming`

2. **Extractor Agent**
   - Extracts structured data from invoices

3. **Translation Agent**
   - Detects language and translates to English

4. **Invoice Validation Agent**
   - Validates data completeness and structure

5. **Business Validation Agent**
   - Compares invoice data with ERP records

6. **Reporting Agent**
   - Generates validation and discrepancy reports

7. **RAG Agents**
   - Index invoice data
   - Retrieve relevant information
   - Generate answers to user queries

8. **Human Interface**
   - Streamlit dashboard for manual review and corrections

---

## Tech Stack

| Layer | Technology |
|------|-----------|
| Language | Python 3.11 |
| Agent Framework | LangGraph, LangChain |
| Backend | FastAPI |
| Frontend | Streamlit |
| LLM Gateway | LiteLLM |
| OCR | Pytesseract |
| Document Parsing | pdfplumber, python-docx |
| Vector Database | FAISS / Chroma / Qdrant |
| Schema Validation | Pydantic |
| Translation | MarianMT (Helsinki-NLP) |
| LLM Models | AWS Bedrock (Nova Lite, Cohere Command R+) |

---

## Project Structure

```
invoice-auditor/

data/
 ├── incoming/
 └── erp_mock_data/

mock_erp/
 └── app.py

agents/
 ├── monitor_agent.py
 ├── extractor_agent.py
 ├── translation_agent.py
 ├── validation_agent.py
 ├── reporting_agent.py
 └── rag_agents/
     ├── indexing_agent.py
     ├── retrieval_agent.py
     ├── generation_agent.py
     └── reflection_agent.py

configs/
 ├── persona_invoice_agent.yaml
 └── rules.yaml

ui/
 └── streamlit_app.py

langgraph_workflows/
 └── invoice_auditor_workflow.yaml

README.md
```

---

## Workflow

1. Invoice file is added to `/data/incoming`
2. Monitor agent detects the new file
3. Extractor agent parses invoice content
4. Translation agent converts non-English text
5. Validation agents check invoice data
6. ERP API verifies vendor and purchase order data
7. Reporting agent generates validation report
8. Invoice data is indexed for RAG-based querying
9. Human reviewers can validate and correct data via Streamlit UI

---

## Validation Rules

The system uses a configurable `rules.yaml` file to define:

- Required invoice fields
- Data type validation
- Price tolerance limits
- Accepted currencies
- Validation policies
- Reporting configuration

---

## Running the Project

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start Mock ERP API

```bash
uvicorn mock_erp.app:app --reload
```

### Start Streamlit Dashboard

```bash
streamlit run ui/streamlit_app.py
```

### Add Invoice Files

Place invoices inside:

```
/data/incoming
```

The system will automatically process them.

---

## Example Use Cases

- Automated invoice auditing
- Vendor invoice fraud detection
- Multilingual document processing
- Financial document validation
- AI-powered financial query systems

---

## Future Improvements

- Email inbox integration
- Production ERP integration
- Advanced anomaly detection
- Improved UI for invoice analytics
- Scalable batch processing

---

## Author

Nikhil Yadav