# ABOUTME: This script parses PDF invoices from the 'Data' folder by generating prompts
# ABOUTME: for the Gemini API and then converts the extracted (or dummy) information into a CSV file.

import os
import json
import csv
from typing import List, Dict, Any

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

def parse_invoices_with_gemini(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Generates a prompt for the Gemini API to parse a PDF file and returns dummy invoice data.
    
    IMPORTANT NOTE FOR THE USER:
    The 'default_api.web_fetch' tool is an agent-specific tool and cannot be directly
    called from within this Python script when it's executed in a standard Python environment.
    
    To actually send the PDF content to the Gemini API for parsing, you would need to:
    1. Run this script to generate the 'full_prompt' (which includes the PDF path).
    2. Manually copy the 'full_prompt' output.
    3. Execute the 'default_api.web_fetch' tool with the copied prompt.
       Example: print(default_api.web_fetch(prompt="YOUR_COPIED_PROMPT_HERE"))
    4. Take the JSON output from the 'web_fetch' tool and manually feed it back
       into the script (e.g., by replacing the 'dummy_response_content' or
       modifying the script to read from a temporary file).
    
    For demonstration purposes, this script will print the prompt that *would* be sent
    and then proceed with dummy data to show the CSV conversion.

    Args:
        pdf_path (str): The absolute path to the PDF file to parse.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                              an extracted invoice. Returns an empty list if parsing fails.
    """
    print(f"INFO: Parsing invoice: {pdf_path}")
    
    full_prompt = f"{GEMINI_PROMPT}\n\nProcess the following PDF file: file://{pdf_path}"
    
    print(f"--- PROMPT FOR GEMINI API ---")
    print(full_prompt)
    print(f"--- END PROMPT ---")
    print("NOTE: In a real execution, the above prompt would be sent to Gemini via default_api.web_fetch.")
    print("For now, returning dummy data.")

    # Placeholder for actual Gemini API call
    # For testing purposes, let's return a dummy JSON
    dummy_response_content = """
    [
        {
            "CIF/ NIF Proveedor": "B12345678",
            "Nombre Proveedor": "Ejemplo S.L.",
            "CIF/ NIF Cliente": "A87654321",
            "Nombre Cliente": "Cliente Ficticio S.A.",
            "Numero de Factura": "INV-2023-001",
            "Fecha de la factura": "2023-10-26",
            "Base imponible": 100.00,
            "IVA": 21.00,
            "Retencion IRPF": 0.00,
            "TOTAL": 121.00,
            "IBAN": "ES1234567890123456789012",
            "Forma de pago": "Transferencia"
        }
    ]
    """
    
    try:
        parsed_data = json.loads(dummy_response_content) 
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decoding error from dummy response for {pdf_path}: {e}")
        return []
    except Exception as e:
        print(f"ERROR: An unexpected error occurred for {pdf_path}: {e}")
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
        invoices = parse_invoices_with_gemini(pdf_file)
        all_invoices_data.extend(invoices)
    
    if all_invoices_data:
        output_csv_file = os.path.join(output_folder, "parsed_invoices.csv")
        convert_json_to_csv(all_invoices_data, output_csv_file)
    else:
        print("WARNING: No invoice data was extracted from any PDF. No CSV file generated.")

if __name__ == "__main__":
    main()
