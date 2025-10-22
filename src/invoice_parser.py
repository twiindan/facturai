# This is a trivial change to create a new commit for the pull request.
# ABOUTME: This file contains functions for parsing PDF invoices.
# ABOUTME: It extracts text and attempts to identify invoice-related information.

import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from all pages of a PDF file.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def extract_invoice_info(pdf_text: str) -> dict:
    """
    Extracts structured invoice information from raw PDF text.
    This is a placeholder function. In a real scenario, this would use
    regex or other parsing techniques to find specific data points
    like invoice number, date, total amount, line items, etc.
    """
    # For now, just return the raw text as a single item in a dictionary
    return {"raw_text": pdf_text}

def process_invoices_from_data_folder(data_folder: str, output_file: str):
    """
    Processes all PDF files in the specified data_folder, extracts invoice
    information, and writes it to the output_file.
    """
    results = []
    for filename in os.listdir(data_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(data_folder, filename)
            print(f"Processing {pdf_path}...")
            pdf_text = extract_text_from_pdf(pdf_path)
            invoice_info = extract_invoice_info(pdf_text)
            results.append({
                "filename": filename,
                "extracted_data": invoice_info
            })

    with open(output_file, 'w', encoding='utf-8') as f:
        for item in results:
            f.write("--- Invoice from {} ---\n".format(item['filename']))
            for key, value in item['extracted_data'].items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
    print(f"Processed {len(results)} invoices. Results written to {output_file}")

def run_cli():
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) # This will be src
    DATA_FOLDER = os.path.join(os.path.dirname(PROJECT_ROOT), "Data")
    OUTPUT_FILE = os.path.join(os.path.dirname(PROJECT_ROOT), "results.txt")

    # Ensure the Data folder exists
    if not os.path.exists(DATA_FOLDER):
        print(f"Error: Data folder not found at {DATA_FOLDER}")
        print("Please create the 'Data' folder and place your PDF invoices inside.")
    else:
        process_invoices_from_data_folder(DATA_FOLDER, OUTPUT_FILE)

if __name__ == "__main__":
    run_cli()
