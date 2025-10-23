# ABOUTME: This file contains integration tests for invoice parsing using real PDF files.
# ABOUTME: It verifies the end-to-end process of reading PDFs and writing to results.txt.

import os
import pytest
import logging
import json
import csv
from unittest.mock import patch, MagicMock
from src.invoice_parser import run_cli, process_invoices_from_data_folder, CSV_HEADERS

# Configure logging for tests to capture output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mock Ollama response for deterministic testing
MOCK_GEMINI_RESPONSE = [{
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
}]

@pytest.fixture
def data_folder_path(tmp_path):
    """Fixture to provide a path to the Data folder."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "Data")

@pytest.fixture
def unique_csv_file_path(tmp_path):
    """Fixture to provide a path for the invoices_unique.csv file."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "invoices_unique.csv")

@pytest.fixture
def duplicates_csv_file_path(tmp_path):
    """Fixture to provide a path for the invoices_duplicates.csv file."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "invoices_duplicates.csv")

@pytest.fixture
def all_csv_file_path(tmp_path):
    """Fixture to provide a path for the invoices_all.csv file."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "invoices_all.csv")

@patch('google.generativeai.GenerativeModel')
def test_process_real_pdfs_and_output_csv(mock_generative_model, data_folder_path, unique_csv_file_path, duplicates_csv_file_path, all_csv_file_path):
    """
    Tests the processing of real PDF files from the Data folder and verifies
    that unique, duplicates, and all invoices CSVs are created and contain extracted data.
    """
    # Configure the mock Gemini chat response
    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [MagicMock()]
    mock_response.candidates[0].content.parts[0].text = json.dumps(MOCK_GEMINI_RESPONSE)

    mock_generative_model.return_value.generate_content.return_value = mock_response

    # Ensure output CSV files do not exist before running the test
    for path in [unique_csv_file_path, duplicates_csv_file_path, all_csv_file_path]:
        if os.path.exists(path):
            os.remove(path)

    # Run the CLI function which processes PDFs and writes to CSV
    original_cwd = os.getcwd()
    try:
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Change to project root
        run_cli()
    finally:
        os.chdir(original_cwd)

    # Assert that all three CSV files were created
    assert os.path.exists(unique_csv_file_path)
    assert os.path.exists(duplicates_csv_file_path)
    assert os.path.exists(all_csv_file_path)

    # Read the content of invoices_unique.csv and verify
    with open(unique_csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Assert CSV headers
        expected_headers = ["filename"] + CSV_HEADERS
        assert reader.fieldnames == expected_headers

        rows = list(reader)
        # Assuming two PDF files are in the Data folder and they are unique
        assert len(rows) == 2 # Assuming two unique invoices

        # Assert content for each row (checking against the first item in MOCK_GEMINI_RESPONSE)
        for row in rows:
            assert row["filename"] in ["facturas_20_ejemplo.pdf", "facturas_ejemplo.pdf"]
            for key, value in MOCK_GEMINI_RESPONSE[0].items():
                assert row[key] == str(value)

    # Read the content of invoices_duplicates.csv and verify (assuming no duplicates for now)
    with open(duplicates_csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["filename"] + CSV_HEADERS
        rows = list(reader)
        assert len(rows) == 0 # Assuming no duplicates in the mock data

    # Read the content of invoices_all.csv and verify
    with open(all_csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["filename"] + CSV_HEADERS
        rows = list(reader)
        assert len(rows) == 2 # Assuming two invoices in total

    # Clean up CSV files after test
    for path in [unique_csv_file_path, duplicates_csv_file_path, all_csv_file_path]:
        os.remove(path)