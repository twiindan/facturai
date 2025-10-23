# This is a trivial change to create a new commit for the pull request.
# ABOUTME: This file contains functions for parsing PDF invoices.
# ABOUTME: It extracts text and attempts to identify invoice-related information.

import os
import logging
import re
import csv
import json
import ollama
import fitz

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define CSV Headers (and expected fields for extraction)
CSV_HEADERS = [
    "CIF/ NIF Proveedor",
    "Nombre Proveedor",
    "CIF/ NIF Cliente",
    "Nombre Cliente",
    "Numero de Factura",
    "Fecha de la factura",
    "Base imponible",
    "IVA",
    "Retencion IRPF",
    "TOTAL",
    "IBAN",
    "Forma de pago"
]

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from all pages of a PDF file using PyMuPDF (fitz).
    """
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
    except Exception as e:
        logging.error(f"Error reading PDF {pdf_path}: {e}")
    return text

def call_ollama_for_extraction(invoice_text: str) -> dict:
    """
    Calls the Ollama model (Gemma3:4b) to extract structured information from invoice text.
    The prompt is optimized for deterministic JSON output.
    """
    # Define a maximum context length for the LLM input (configurable)
    MAX_CONTEXT_LENGTH = 65536 # User-specified context window

    original_text_length = len(invoice_text)
    if original_text_length > MAX_CONTEXT_LENGTH:
        logging.warning(f"Invoice text length ({original_text_length}) exceeds MAX_CONTEXT_LENGTH ({MAX_CONTEXT_LENGTH}). Truncating input for Ollama.")
        invoice_text = invoice_text[:MAX_CONTEXT_LENGTH] # Truncate the text

    # Define the prompt for the LLM
    prompt = f"""
    You are an expert invoice parser. Your task is to extract specific fields from the provided invoice text.
    The output MUST be a JSON object with the following keys. If a field is not found, use `null` or an empty string.

    Extract the following fields:
    - "CIF/ NIF Proveedor": (string)
    - "Nombre Proveedor": (string)
    - "CIF/ NIF Cliente": (string)
    - "Nombre Cliente": (string)
    - "Numero de Factura": (string)
    - "Fecha de la factura": (YYYY-MM-DD string)
    - "Base imponible": (float)
    - "IVA": (float)
    - "Retencion IRPF": (float)
    - "TOTAL": (float)
    - "IBAN": (string)
    - "Forma de pago": (string)

    Invoice Text:
    ---
    {invoice_text}
    ---

    JSON Output:
    """

    try:
        # Assuming Ollama server is running and Gemma3:4b model is available
        response = ollama.chat(
            model='gemma3:4b', # Specify the model with extended context
            messages=[{'role': 'user', 'content': prompt}],
            options={"temperature": 0.1, 'num_ctx': 65536, 'top_p': 0.5}
        )
        logging.error(f"DEBUG: Raw response from ollama.chat: {response}") # ADD THIS LINE

        message_obj = response.get('message')
        if not message_obj:
            logging.error(f"Ollama response missing 'message' key. Full response: {response}")
            return {header: None for header in CSV_HEADERS}

        json_output = getattr(message_obj, 'content', None)
        if json_output is None:
            logging.error(f"Ollama message object missing 'content' attribute. Full message object: {message_obj}")
            return {header: None for header in CSV_HEADERS}

        # Extract JSON from markdown code block if present
        match = re.search(r'```json\n(.*)\n```', json_output, re.DOTALL)
        if match:
            json_string = match.group(1)
        else:
            json_string = json_output # Assume pure JSON if no markdown block
        extracted_data = json.loads(json_string)

        # Validate that all expected headers are present in the extracted data
        for header in CSV_HEADERS:
            if header not in extracted_data:
                extracted_data[header] = None # Ensure all fields are present, even if null

        return extracted_data
    except ollama.ResponseError as e:
        logging.error(f"Ollama API error: {e}")
        return {header: None for header in CSV_HEADERS} # Return empty dict on error
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from Ollama response: {e}\nResponse content: {json_output}")
        return {header: None for header in CSV_HEADERS} # Return empty dict on error
    except Exception as e:
        logging.error(f"An unexpected error occurred during Ollama call: {e}")
        return {header: None for header in CSV_HEADERS} # Return empty dict on error


def extract_invoice_info(pdf_text: str) -> dict:
    """
    Extracts structured invoice information from raw PDF text using Ollama.
    """
    return call_ollama_for_extraction(pdf_text)


def process_invoices_from_data_folder(data_folder: str, output_csv_file: str):
    """
    Processes all PDF files in the specified data_folder, extracts structured invoice
    information using Ollama, and writes it to a CSV file.
    """
    all_extracted_data = []
    for filename in os.listdir(data_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(data_folder, filename)
            logging.info(f"Processing {pdf_path}...")
            pdf_text = extract_text_from_pdf(pdf_path)
            invoice_info = extract_invoice_info(pdf_text)
            invoice_info["filename"] = filename # Add filename for reference
            all_extracted_data.append(invoice_info)

    # Write to CSV
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["filename"] + CSV_HEADERS # Include filename in CSV
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for data in all_extracted_data:
            # Ensure all fields are present for DictWriter
            row = {header: data.get(header) for header in fieldnames}
            writer.writerow(row)

    logging.info(f"Processed {len(all_extracted_data)} invoices. Results written to {output_csv_file}")


def run_cli():
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.path.join(os.path.dirname(PROJECT_ROOT), "Data")
    OUTPUT_CSV_FILE = os.path.join(os.path.dirname(PROJECT_ROOT), "invoices_data.csv")

    # Ensure the Data folder exists
    if not os.path.exists(DATA_FOLDER):
        logging.error(f"Error: Data folder not found at {DATA_FOLDER}")
        logging.info("Please create the 'Data' folder and place your PDF invoices inside.")
    else:
        process_invoices_from_data_folder(DATA_FOLDER, OUTPUT_CSV_FILE)

if __name__ == "__main__":
    run_cli()