# ABOUTME: This file contains unit tests for the invoice_parser module.
# ABOUTME: It verifies the basic functionality of PDF text extraction and invoice processing.

import json  # Added import for json
import os
from pathlib import Path  # Added import for Path
from unittest.mock import patch, mock_open, call, MagicMock

from src.invoice_parser import process_invoices_from_data_folder, run_cli, CSV_HEADERS

# Mock PDF content for testing
MOCK_PDF_TEXT = "This is a mock PDF content for testing purposes."

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

class MockDocument:
    def __init__(self, pages_content):
        self._pages_content = pages_content
        self.page_count = len(pages_content)

    def load_page(self, page_num):
        return MockPage(self._pages_content[page_num])

    def close(self):
        pass

class MockPage:
    def __init__(self, content):
        self._content = content

    def get_text(self):
        return self._content


@patch('os.path.exists', return_value=False)
@patch('src.invoice_parser.logging.error')
@patch('src.invoice_parser.logging.info')
@patch('os.path.abspath', side_effect=lambda x: '/Users/toni.robres/Pycharmprojects/facturai/src/invoice_parser.py' if 'invoice_parser.py' in x else x)
@patch('os.path.dirname', side_effect=lambda x: '/Users/toni.robres/Pycharmprojects/facturai/src' if 'invoice_parser.py' in x else '/Users/toni.robres/Pycharmprojects/facturai')
def test_run_cli_data_folder_not_found(mock_dirname, mock_abspath, mock_logging_info, mock_logging_error, mock_exists):
    """
    Tests that run_cli handles the case where the Data folder is not found.
    """
    run_cli()
    expected_data_folder_path = '/Users/toni.robres/Pycharmprojects/facturai/Data'
    mock_logging_error.assert_any_call(f"Error: Data folder not found at {expected_data_folder_path}")
    mock_logging_info.assert_any_call("Please create the 'Data' folder and place your PDF invoices inside.")

@patch('os.path.exists', return_value=True)
@patch('src.invoice_parser.process_invoices_from_data_folder')
@patch('os.path.abspath', side_effect=lambda x: '/Users/toni.robres/Pycharmprojects/facturai/src/invoice_parser.py' if 'invoice_parser.py' in x else x)
@patch('os.path.dirname', side_effect=lambda x: '/Users/toni.robres/Pycharmprojects/facturai/src' if 'invoice_parser.py' in x else '/Users/toni.robres/Pycharmprojects/facturai')
def test_run_cli_data_folder_found(mock_dirname, mock_abspath, mock_process_invoices, mock_exists):
    """
    Tests that run_cli calls process_invoices_from_data_folder when Data folder exists.
    """
    run_cli()
    expected_data_folder_path = '/Users/toni.robres/Pycharmprojects/facturai/Data'
    expected_unique_csv_file = '/Users/toni.robres/Pycharmprojects/facturai/invoices_unique.csv'
    expected_duplicates_csv_file = '/Users/toni.robres/Pycharmprojects/facturai/invoices_duplicates.csv'
    expected_all_csv_file = '/Users/toni.robres/Pycharmprojects/facturai/invoices_all.csv'
    mock_process_invoices.assert_called_once_with(expected_data_folder_path, expected_unique_csv_file, expected_duplicates_csv_file, expected_all_csv_file)