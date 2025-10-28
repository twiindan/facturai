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

@pytest.fixture(autouse=True)
def mock_gemini_client_and_configure():
    with patch('google.genai.Client') as mock_client_class:
        with patch('src.invoice_parser.client') as mock_module_client:
            yield mock_client_class, mock_module_client

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
