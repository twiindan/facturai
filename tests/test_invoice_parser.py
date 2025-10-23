# ABOUTME: This file contains unit tests for the invoice_parser module.
# ABOUTME: It verifies the basic functionality of PDF text extraction and invoice processing.

import os
import pytest
from unittest.mock import patch, mock_open, call
from src.invoice_parser import process_invoices_from_data_folder, run_cli, CSV_HEADERS
import fitz

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

# Mock PyMuPDF (fitz) API for testing
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

@patch('src.invoice_parser.logging.info')
@patch('os.listdir', return_value=['test_invoice.pdf'])
@patch('src.invoice_parser.extract_invoice_info', return_value=MOCK_GEMINI_RESPONSE)
@patch('builtins.open', new_callable=mock_open)
def test_process_invoices_from_data_folder(mock_file_open, mock_extract_info, mock_listdir, mock_logging_info):
    """
    Tests the end-to-end processing of invoices from a data folder. 
    """
    mock_data_folder = "/mock/data"
    mock_unique_file = "/mock/invoices_unique.csv"
    mock_duplicates_file = "/mock/invoices_duplicates.csv"
    mock_all_file = "/mock/invoices_all.csv"

    # Create separate mock file handles for each CSV file
    mock_all_csv_handle = mock_open()
    mock_unique_csv_handle = mock_open()
    mock_duplicates_csv_handle = mock_open()

    # Configure builtins.open to return these mock handles in the order they are called
    # The order of calls to open is: all_csv, unique_csv, duplicates_csv
    mock_file_open.side_effect = [mock_all_csv_handle.return_value, mock_unique_csv_handle.return_value, mock_duplicates_csv_handle.return_value]
    process_invoices_from_data_folder(mock_data_folder, mock_unique_file, mock_duplicates_file, mock_all_file)

    mock_listdir.assert_called_once_with(mock_data_folder)
    mock_extract_info.assert_called_once_with(os.path.join(mock_data_folder, 'test_invoice.pdf'))

    # Assert that open was called for each file with the correct arguments
    mock_file_open.assert_has_calls([
        call(mock_all_file, 'w', newline='', encoding='utf-8'),
        call(mock_unique_file, 'w', newline='', encoding='utf-8'),
        call(mock_duplicates_file, 'w', newline='', encoding='utf-8')
    ], any_order=True)

    expected_csv_header = ','.join(['filename'] + CSV_HEADERS) + '\r\n'
    expected_csv_data_row = f"test_invoice.pdf,{MOCK_GEMINI_RESPONSE[0]['CIF/ NIF Proveedor']},{MOCK_GEMINI_RESPONSE[0]['Nombre Proveedor']},{MOCK_GEMINI_RESPONSE[0]['CIF/ NIF Cliente']},{MOCK_GEMINI_RESPONSE[0]['Nombre Cliente']},{MOCK_GEMINI_RESPONSE[0]['Numero de Factura']},{MOCK_GEMINI_RESPONSE[0]['Fecha de la factura']},{MOCK_GEMINI_RESPONSE[0]['Base imponible']},{MOCK_GEMINI_RESPONSE[0]['IVA']},{MOCK_GEMINI_RESPONSE[0]['Retencion IRPF']},{MOCK_GEMINI_RESPONSE[0]['TOTAL']},{MOCK_GEMINI_RESPONSE[0]['IBAN']},{MOCK_GEMINI_RESPONSE[0]['Forma de pago']}\r\n"

    # Assert write calls for each mock file handle
    mock_all_csv_handle().write.assert_has_calls([
        call(expected_csv_header),
        call(expected_csv_data_row)
    ])
    mock_unique_csv_handle().write.assert_has_calls([
        call(expected_csv_header),
        call(expected_csv_data_row)
    ])
    mock_duplicates_csv_handle().write.assert_has_calls([
        call(expected_csv_header)
    ]) # No data row for duplicates in this mock scenario

    # Verify logging calls
    expected_logging_calls = [
        call(f"Processing {mock_data_folder}/test_invoice.pdf..."),
        call(f"All 1 invoices (raw) written to {mock_all_file}"),
        call(f"Processed 1 unique invoices. Results written to {mock_unique_file}"),
        call(f"Found 0 duplicate invoices. Results written to {mock_duplicates_file}")
    ]
    mock_logging_info.assert_has_calls(expected_logging_calls, any_order=True)
    assert mock_logging_info.call_count == len(expected_logging_calls)

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