# ABOUTME: This script parses PDF invoices from the 'Data' folder using the Gemini API
# ABOUTME: and converts the extracted information into a CSV file.

import os
import json
import csv
import pathlib
import re
import argparse
from typing import List, Dict, Any
from datetime import datetime
from google import genai # Using google-genai as per user's instruction
from google.genai import types # Using google-genai as per user's instruction

# Configure the Gemini API client
# IMPORTANT: Set your Gemini API key as an environment variable named GEMINI_API_KEY.
# You can get one from https://ai.google.dev/
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable not set. Please set it to your Gemini API key.")
    # In a production environment, you might want to sys.exit(1) here.

# Initialize the Gemini client
# Note: The user's example used genai.Client() and client.models.generate_content
# This implies an older version or different usage of the library compared to
# google.generativeai.GenerativeModel. I will follow the user's example.
client = genai.Client()

# Define the prompt for Gemini
GEMINI_PROMPT = """
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
"""

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

def get_pdf_files(data_folder: str) -> List[str]:
    """
    Lists all PDF files in the specified data folder.

    Args:
        data_folder (str): The absolute path to the directory containing PDF files.

    Returns:
        List[str]: A list of absolute paths to PDF files.
    """
    pdf_files = []
    if not os.path.isdir(data_folder):
        print(f"WARNING: Data folder not found: {data_folder}")
        return []
    for root, _, files in os.walk(data_folder):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    print(f"INFO: Found {len(pdf_files)} PDF files in {data_folder}.")
    return pdf_files

def parse_invoices_with_gemini(pdf_path: str, mock_json_path: str = None) -> List[Dict[str, Any]]:
    """
    Sends a PDF file to the Gemini API for parsing and returns invoice data.
    If mock_json_path is provided, it reads mock data from the specified JSON file.
    
    Args:
        pdf_path (str): The absolute path to the PDF file to parse.
        mock_json_path (str, optional): Path to a JSON file containing mock Gemini API responses.
                                        If provided, the function reads from this file instead
                                        of calling the Gemini API.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                              an extracted invoice. Returns an empty list if parsing fails.
    """
    print(f"INFO: Parsing invoice: {pdf_path}")
    
    if mock_json_path:
        try:
            with open(mock_json_path, 'r', encoding='utf-8') as f:
                mock_response_content = f.read()
            parsed_data = json.loads(mock_response_content)
            print(f"INFO: Using mock data from {mock_json_path} for {pdf_path}.")
            return parsed_data
        except FileNotFoundError:
            print(f"ERROR: Mock JSON file not found: {mock_json_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON decoding error from mock file {mock_json_path}: {e}")
            return []
        except Exception as e:
            print(f"ERROR: An unexpected error occurred while reading mock file {mock_json_path}: {e}")
            return []

    try:
        filepath = pathlib.Path(pdf_path)
        
        # The genai.Client() does not have get_default_retriever_config().api_key
        # Instead, the API key is passed during client initialization or configured globally.
        # If api_key is None, the client initialization would likely fail or use default credentials.
        if not api_key: # Check if api_key was loaded from environment
            print("ERROR: Gemini API key is not configured. Skipping API call.")
            return []

        response = client.models.generate_content( # Using client.models.generate_content as per user's example
            model="gemini-2.5-flash", # Model name from user's example
            contents=[
                types.Part.from_bytes(
                    data=filepath.read_bytes(),
                    mime_type='application/pdf',
                ),
                GEMINI_PROMPT
            ]
        )
        
        json_output = response.text
        
        # Attempt to extract JSON from a markdown code block if present
        match = re.search(r'```json\n(.*)\n```', json_output, re.DOTALL)
        if match:
            json_string = match.group(1)
        else:
            json_string = json_output.strip() # Clean up whitespace if not in markdown block

        parsed_data = json.loads(json_string)
        print(f"INFO: Successfully parsed invoice data from {pdf_path} using Gemini API.")
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decoding error from Gemini response for {pdf_path}: {e}. Response text: {json_output}")
        return []
    except Exception as e:
        print(f"ERROR: Error calling Gemini API for {pdf_path}: {e}")
        return []

def convert_json_to_csv(invoice_data: List[Dict[str, Any]], output_csv_path: str):
    """
    Converts a list of invoice dictionaries to a CSV file.

    Args:
        invoice_data (List[Dict[str, Any]]): A list of dictionaries, each representing an invoice.
        output_csv_path (str): The absolute path where the CSV file will be written.
    """
    if not invoice_data:
        print("WARNING: No invoice data to write to CSV.")
        return

    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for invoice in invoice_data:
            row = {header: invoice.get(header, '') for header in CSV_HEADERS}
            writer.writerow(row)
    print(f"INFO: CSV data written to: {output_csv_path}")

def main():
    """
    Main function to orchestrate PDF parsing and CSV conversion.
    """
    parser = argparse.ArgumentParser(description="Parse PDF invoices and convert to CSV.")
    parser.add_argument("--mock-json", type=str, help="Path to a JSON file for mock Gemini API responses.")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_folder = os.path.join(project_root, "Data")
    output_folder = os.path.join(project_root, "Output")

    os.makedirs(output_folder, exist_ok=True)
    print(f"INFO: Ensured output directory exists: {output_folder}")

    pdf_files = get_pdf_files(data_folder)
    
    all_invoices_data = []

    if not pdf_files:
        print(f"INFO: No PDF files found in {data_folder}. Exiting.")
        return

    for pdf_file in pdf_files:
        invoices = parse_invoices_with_gemini(pdf_file, mock_json_path=args.mock_json)
        all_invoices_data.extend(invoices)
    
    if all_invoices_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv_filename = f"parsed_invoices_{timestamp}.csv"
        output_csv_file = os.path.join(output_folder, output_csv_filename)
        convert_json_to_csv(all_invoices_data, output_csv_file)
    else:
        print("WARNING: No invoice data was extracted from any PDF. No CSV file generated.")

if __name__ == "__main__":
    main()
