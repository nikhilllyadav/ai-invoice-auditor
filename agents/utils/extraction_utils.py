from pathlib import Path
import pdfplumber
import pytesseract
from PIL import Image
from docx import Document
import json


def extract_text_from_pdf(path: Path) -> str:
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def extract_text_from_docx(path: Path) -> str:
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_text_from_image(path: Path) -> str:
    image = Image.open(path)
    return pytesseract.image_to_string(image)

def extract_text_from_json(path: Path) -> str:
    """Extracts text content from a JSON file."""
    try:
        # Open and load the JSON file
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # You can either return the whole JSON or format it into a string. 
        # Here we return it as a pretty-printed string for better readability.
        # return json.dumps(data, indent=4)
        return data
    
    except json.JSONDecodeError as e:
        # Handle errors that happen if the file is not valid JSON
        return f"Error parsing JSON file: {e}"
    except Exception as e:
        # Handle other types of exceptions (e.g., file not found)
        return f"Error reading JSON file: {e}"