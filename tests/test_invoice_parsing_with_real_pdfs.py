# ABOUTME: This file contains integration tests for invoice parsing using real PDF files.
# ABOUTME: It verifies the end-to-end process of reading PDFs and writing to results.txt.

import os
import pytest
import logging
import json
import csv
from unittest.mock import patch, MagicMock
from src.invoice_parser import run_cli, process_invoices_from_data_folder, extract_text_from_pdf, CSV_HEADERS

# Configure logging for tests to capture output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mock Ollama response for deterministic testing
MOCK_OLLAMA_RESPONSE = {
    "CIF/ NIF Proveedor": "B12345678",
    "Nombre Proveedor": "Proveedor Mock S.L.",
    "CIF/ NIF Cliente": "A87654321",
    "Nombre Cliente": "Cliente Test S.A.",
    "Numero de Factura": "INV-2025-001",
    "Fecha de la factura": "2025-01-15",
    "Base imponible": 100.00,
    "IVA": 21.00,
    "Retencion IRPF": 0.00,
    "TOTAL": 121.00,
    "IBAN": "ES123456789012345678901234",
    "Forma de pago": "Transferencia"
}

@pytest.fixture
def data_folder_path(tmp_path):
    """Fixture to provide a path to the Data folder."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "Data")

@pytest.fixture
def output_csv_file_path(tmp_path):
    """Fixture to provide a path for the invoices_data.csv file."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "invoices_data.csv")

@patch('src.invoice_parser.ollama.chat')
def test_process_real_pdfs_and_output_csv(mock_ollama_chat, data_folder_path, output_csv_file_path):
    """
    Tests the processing of real PDF files from the Data folder and verifies
    that invoices_data.csv is created and contains extracted data.
    """
    # Configure the mock Ollama chat response
    mock_message = MagicMock()
    mock_message.content = json.dumps(MOCK_OLLAMA_RESPONSE)
    mock_ollama_chat.return_value = {
        'message': mock_message
    }

    # Ensure output_csv_file_path does not exist before running the test
    if os.path.exists(output_csv_file_path):
        os.remove(output_csv_file_path)

    # Run the CLI function which processes PDFs and writes to CSV
    original_cwd = os.getcwd()
    try:
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Change to project root
        run_cli()
    finally:
        os.chdir(original_cwd)

    # Assert that invoices_data.csv was created
    assert os.path.exists(output_csv_file_path)

    # Read the content of invoices_data.csv
    with open(output_csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Assert CSV headers
        expected_headers = ["filename"] + CSV_HEADERS
        assert reader.fieldnames == expected_headers

        rows = list(reader)
        # Assuming two PDF files are in the Data folder
        assert len(rows) == 2

        # Assert content for each row
        for row in rows:
            assert row["filename"] in ["facturas_20_ejemplo.pdf", "facturas_ejemplo.pdf"]
            for key, value in MOCK_OLLAMA_RESPONSE.items():
                # Convert mock values to string for comparison with CSV reader output
                assert row[key] == str(value)

    # Clean up invoices_data.csv after test
    os.remove(output_csv_file_path)