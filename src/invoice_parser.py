# This is a trivial change to create a new commit for the pull request.
# ABOUTME: This file contains functions for parsing PDF invoices.
# ABOUTME: It extracts text and attempts to identify invoice-related information.

import csv
import json
import logging
import os
import re

import google.generativeai as genai

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure Gemini API
# It's recommended to set your API key as an environment variable for security.
# For example: export GOOGLE_API_KEY='your_api_key_here'
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    logging.error("GOOGLE_API_KEY environment variable not set. Please set it to your Gemini API key.")
    # Exit or raise an error, as the model won't work without the API key
    # For now, we'll just log and continue, but model calls will likely fail.
else:
    genai.configure(api_key=API_KEY)

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



def call_gemini_for_extraction(invoice_text: str) -> list[dict]:
    """
    Calls the Gemini model to extract structured information from invoice text.
    The prompt is optimized for deterministic JSON output.
    """
    # Define a maximum context length for the LLM input (configurable)
    # Gemini models have varying context windows. Using a general approach.
    MAX_CONTEXT_LENGTH = 30000 # A common context window for some Gemini models

    original_text_length = len(invoice_text)
    if original_text_length > MAX_CONTEXT_LENGTH:
        logging.warning(f"Invoice text length ({original_text_length}) exceeds MAX_CONTEXT_LENGTH ({MAX_CONTEXT_LENGTH}). Truncating input for Gemini.")
        invoice_text = invoice_text[:MAX_CONTEXT_LENGTH] # Truncate the text

    # Define the prompt for the LLM
    prompt = f"""
    You are an expert invoice parser. Your task is to extract specific fields from the provided invoice text.
    The output MUST be a JSON array of objects, where each object represents an invoice. If only one invoice is found, return an array with a single object.
    Each object MUST have the following keys. If a field is not found, use `null` or an empty string.
    Ensure numerical values are parsed as floats and dates in YYYY-MM-DD format.

    Extract the following fields for EACH invoice:
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

    JSON Output (array of objects):
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash') # Using gemini-pro model
        response = model.generate_content(prompt)
        logging.debug(f"DEBUG: Raw response from Gemini: {response}")

        # Gemini's response structure might vary. We need to extract the text content.
        if not response.candidates:
            logging.error(f"Gemini response has no candidates. Full response: {response}")
            return [{header: None for header in CSV_HEADERS}]

        # Assuming the first candidate's content is the desired output
        json_output = response.candidates[0].content.parts[0].text

        # Extract JSON from Markdown code block if present
        match = re.search(r'```json\n(.*)\n```', json_output, re.DOTALL)
        if match:
            json_string = match.group(1)
        else:
            json_string = json_output # Assume pure JSON if no markdown block

        parsed_data = json.loads(json_string)

        # Normalize to a list of dictionaries if it's a single dictionary
        if isinstance(parsed_data, dict):
            parsed_data = [parsed_data]

        # Validate that all expected headers are present in each extracted data dictionary
        for invoice_data in parsed_data:
            for header in CSV_HEADERS:
                if header not in invoice_data:
                    invoice_data[header] = None # Ensure all fields are present, even if null

        return parsed_data # Return a list of dictionaries
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error from Gemini response: {e}. Response content: {json_output}")
        return [{header: None for header in CSV_HEADERS}]
    except Exception as e:
        logging.error(f"An unexpected error occurred during Gemini call or processing: {e}")
        return [{header: None for header in CSV_HEADERS}]


def deduplicate_invoices(invoices: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Deduplicates a list of invoice dictionaries based on all their fields.
    Returns a tuple of two lists: (unique_invoices, duplicate_invoices).
    """
    seen_hashes = set()
    unique_invoices = []
    duplicate_invoices = []
    
    for invoice in invoices:
        hashable_invoice = tuple(sorted(invoice.items()))
        if hashable_invoice not in seen_hashes:
            seen_hashes.add(hashable_invoice)
            unique_invoices.append(invoice)
        else:
            duplicate_invoices.append(invoice)
    return unique_invoices, duplicate_invoices

def extract_invoice_info(pdf_text: str) -> list[dict]:
    """
    Extracts structured invoice information from raw PDF text using Gemini.
    """
    return call_gemini_for_extraction(pdf_text)


def process_invoices_from_data_folder(data_folder: str, unique_csv_file: str, duplicates_csv_file: str, all_csv_file: str):
    """
    Processes all PDF files in the specified data_folder, extracts structured invoice
    information using Gemini, and writes it to three CSV files:
    - unique_csv_file: contains only unique invoices.
    - duplicates_csv_file: contains only duplicate invoices.
    - all_csv_file: contains all extracted invoices before deduplication.
    """
    all_extracted_data_raw = [] # Store all extracted data before deduplication
    for filename in os.listdir(data_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(data_folder, filename)
            logging.info(f"Processing {pdf_path}...")
            invoices_from_pdf = extract_invoice_info(pdf_path)
            for invoice_info in invoices_from_pdf:
                invoice_info["filename"] = filename # Add filename for reference to each invoice
                all_extracted_data_raw.append(invoice_info)

    # Deduplicate invoices
    unique_invoices, duplicate_invoices = deduplicate_invoices(all_extracted_data_raw)

    # Helper function to write data to CSV
    def write_invoices_to_csv(file_path, invoices_data, fieldnames):
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for data in invoices_data:
                row = {header: data.get(header) for header in fieldnames}
                writer.writerow(row)

    fieldnames = ["filename"] + CSV_HEADERS

    # Write all invoices to CSV
    write_invoices_to_csv(all_csv_file, all_extracted_data_raw, fieldnames)
    logging.info(f"All {len(all_extracted_data_raw)} invoices (raw) written to {all_csv_file}")

    # Write unique invoices to CSV
    write_invoices_to_csv(unique_csv_file, unique_invoices, fieldnames)
    logging.info(f"Processed {len(unique_invoices)} unique invoices. Results written to {unique_csv_file}")

    # Write duplicate invoices to CSV
    write_invoices_to_csv(duplicates_csv_file, duplicate_invoices, fieldnames)
    logging.info(f"Found {len(duplicate_invoices)} duplicate invoices. Results written to {duplicates_csv_file}")


def run_cli():
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.path.join(os.path.dirname(PROJECT_ROOT), "Data")
    UNIQUE_CSV_FILE = os.path.join(os.path.dirname(PROJECT_ROOT), "invoices_unique.csv")
    DUPLICATES_CSV_FILE = os.path.join(os.path.dirname(PROJECT_ROOT), "invoices_duplicates.csv")
    ALL_CSV_FILE = os.path.join(os.path.dirname(PROJECT_ROOT), "invoices_all.csv")

    # Ensure the Data folder exists
    if not os.path.exists(DATA_FOLDER):
        logging.error(f"Error: Data folder not found at {DATA_FOLDER}")
        logging.info("Please create the 'Data' folder and place your PDF invoices inside.")
    else:
        process_invoices_from_data_folder(DATA_FOLDER, UNIQUE_CSV_FILE, DUPLICATES_CSV_FILE, ALL_CSV_FILE)

if __name__ == "__main__":
    run_cli()