import csv
import json
import logging
import os
from pathlib import Path
import re

import google.genai as genai
from google.genai import types  # Added for multimodal input


# Custom exception for Gemini API extraction errors
class GeminiExtractionError(Exception):
    """Custom exception for errors during Gemini API extraction."""

    pass


# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    logging.error(
        "GOOGLE_API_KEY environment variable not set. Please set it to your Gemini API key."
    )
    # Exit or raise an error, as the model won't work without the API key
    # For now, we'll just log and continue, but model calls will likely fail.
    client = None  # Initialize client as None if API_KEY is missing
else:
    client = genai.Client(api_key=API_KEY)

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
    "Forma de pago",
]


def call_gemini_for_extraction(pdf_path: Path) -> list[dict]:
    """
    Calls the Gemini model to extract structured information from a PDF file.
    The prompt is optimized for deterministic JSON output.
    """

    try:

        with open(pdf_path, "rb") as f:

            pdf_bytes = f.read()

        pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")

        prompt_text = """
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
                        JSON Output (array of objects):
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=[pdf_part, prompt_text]
        )

        logging.debug(f"DEBUG: Raw response from Gemini: {response}")

        if not response or not response.candidates:
            raise GeminiExtractionError("Gemini API returned no candidates.")

        response_text = response.candidates[0].content.parts[0].text

        match = re.search(r"```json\n(.*)\n```", response_text, re.DOTALL)

        if match:

            json_string = match.group(1)

        else:

            json_string = response_text

        parsed_data = json.loads(json_string)

        if isinstance(parsed_data, dict):
            parsed_data = [parsed_data]

        for invoice_data in parsed_data:

            for header in CSV_HEADERS:

                if header not in invoice_data:
                    invoice_data[header] = None

        return parsed_data

    except json.JSONDecodeError as e:

        raise GeminiExtractionError(
            f"Failed to parse Gemini API response as JSON: {e}. Response: {response_text}"
        )

    except Exception as e:

        raise GeminiExtractionError(
            f"An unexpected error occurred during Gemini call or processing: {e}"
        )


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


def extract_invoice_info(pdf_path: Path) -> list[dict]:
    """
    Extracts structured invoice information from a PDF file using the Gemini API.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        A list of dictionaries containing the extracted invoice data.

    Raises:
        GeminiExtractionError: If there's an error during Gemini API extraction.
    """
    try:
        extracted_data = call_gemini_for_extraction(pdf_path)
        return extracted_data
    except GeminiExtractionError as e:
        logging.error(f"Error extracting data from {pdf_path}: {e}")
        raise  # Re-raise the exception as per requirement


from src.models import Invoice, Company  # Import Invoice and Company
from src.validators import CIFConsistencyValidator  # Import CIFConsistencyValidator


def process_invoices_from_data_folder(
        data_folder: str, unique_csv_file: str, duplicates_csv_file: str, all_csv_file: str
):
    """
    Processes all PDF files in the specified data_folder, extracts structured invoice
    information using Gemini, validates CIF consistency, and writes it to three CSV files:
    - unique_csv_file: contains only unique invoices.
    - duplicates_csv_file: contains only duplicate invoices.
    - all_csv_file: contains all extracted invoices before deduplication.
    """
    all_extracted_data_raw = []  # Store all extracted data before deduplication
    cif_validator = CIFConsistencyValidator()
    validation_errors_summary = []

    for filename in os.listdir(data_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = Path(os.path.join(data_folder, filename))
            logging.info(f"Processing {pdf_path}...")

            try:
                invoices_from_pdf_dicts = extract_invoice_info(pdf_path)
                for invoice_data_dict in invoices_from_pdf_dicts:
                    # Add filename for reference to each invoice
                    invoice_data_dict["filename"] = filename
                    all_extracted_data_raw.append(invoice_data_dict)

                    # Map to Pydantic model for CIF validation
                    try:
                        invoice_obj = Invoice(**invoice_data_dict)
                        validation_errors = cif_validator.validate(
                            invoice_obj.to_cif_validation_format()
                        )
                        if validation_errors:
                            for error in validation_errors:
                                validation_errors_summary.append(
                                    f"File {filename}: {error}"
                                )
                                logging.warning(
                                    f"Validation Error in {filename}: {error}"
                                )
                    except Exception as e:
                        validation_errors_summary.append(
                            f"File {filename}: Pydantic mapping/CIF validation error - {e}"
                        )
                        logging.error(
                            f"File {filename}: Pydantic mapping/CIF validation error - {e}"
                        )

            except GeminiExtractionError as e:
                validation_errors_summary.append(
                    f"File {filename}: Extraction Error - {e}"
                )
                logging.error(f"File {filename}: Extraction Error - {e}")
            except Exception as e:
                validation_errors_summary.append(
                    f"File {filename}: Unexpected Error during extraction - {e}"
                )
                logging.error(
                    f"File {filename}: Unexpected Error during extraction - {e}"
                )

    # Deduplicate invoices
    unique_invoices, duplicate_invoices = deduplicate_invoices(all_extracted_data_raw)

    # Helper function to write data to CSV
    def write_invoices_to_csv(file_path, invoices_data, fieldnames):
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for data in invoices_data:
                row = {header: data.get(header) for header in fieldnames}
                writer.writerow(row)

    fieldnames = ["filename"] + CSV_HEADERS

    # Write all invoices to CSV
    write_invoices_to_csv(all_csv_file, all_extracted_data_raw, fieldnames)
    logging.info(
        f"All {len(all_extracted_data_raw)} invoices (raw) written to {all_csv_file}"
    )

    # Write unique invoices to CSV
    write_invoices_to_csv(unique_csv_file, unique_invoices, fieldnames)
    logging.info(
        f"Processed {len(unique_invoices)} unique invoices. Results written to {unique_csv_file}"
    )

    # Write duplicate invoices to CSV
    write_invoices_to_csv(duplicates_csv_file, duplicate_invoices, fieldnames)
    logging.info(
        f"Found {len(duplicate_invoices)} duplicate invoices. Results written to {duplicates_csv_file}"
    )

    if validation_errors_summary:
        logging.warning("--- Summary of Validation Errors ---")
        for error in validation_errors_summary:
            logging.warning(error)
        logging.warning(
            f"Found {len(validation_errors_summary)} validation errors during processing."
        )


def run_cli():
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.path.join(os.path.dirname(PROJECT_ROOT), "Data")
    UNIQUE_CSV_FILE = os.path.join(os.path.dirname(PROJECT_ROOT), "invoices_unique.csv")
    DUPLICATES_CSV_FILE = os.path.join(
        os.path.dirname(PROJECT_ROOT), "invoices_duplicates.csv"
    )
    ALL_CSV_FILE = os.path.join(os.path.dirname(PROJECT_ROOT), "invoices_all.csv")

    # Ensure the Data folder exists
    if not os.path.exists(DATA_FOLDER):
        logging.error(f"Error: Data folder not found at {DATA_FOLDER}")
        logging.info(
            "Please create the 'Data' folder and place your PDF invoices inside."
        )
    else:
        process_invoices_from_data_folder(
            DATA_FOLDER, UNIQUE_CSV_FILE, DUPLICATES_CSV_FILE, ALL_CSV_FILE
        )


if __name__ == "__main__":
    run_cli()
