# ABOUTME: This file contains unit tests for the invoice_parser module.
# ABOUTME: It verifies the basic functionality of PDF text extraction and invoice processing.

import os
import pytest
from unittest.mock import patch, mock_open, call
from src.invoice_parser import extract_text_from_pdf, process_invoices_from_data_folder, run_cli, CSV_HEADERS

# Mock PDF content for testing
MOCK_PDF_TEXT = "This is a mock PDF content for testing purposes."

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

# Mock PdfReader and its methods
class MockPage:
    def extract_text(self):
        return MOCK_PDF_TEXT

class MockPdfReader:
    def __init__(self, file):
        self.pages = [MockPage()]

@patch('builtins.open', new_callable=mock_open)
@patch('src.invoice_parser.PdfReader', return_value=MockPdfReader(None))
def test_extract_text_from_pdf(mock_pdf_reader, mock_file_open):
    """
    Tests that text can be extracted from a mock PDF file.
    """
    dummy_pdf_path = "/path/to/dummy.pdf"
    extracted_text = extract_text_from_pdf(dummy_pdf_path)
    mock_file_open.assert_called_once_with(dummy_pdf_path, 'rb')
    assert extracted_text == MOCK_PDF_TEXT

@patch('src.invoice_parser.logging.info')
@patch('os.listdir', return_value=['test_invoice.pdf'])
@patch('src.invoice_parser.extract_text_from_pdf', return_value=MOCK_PDF_TEXT)
@patch('src.invoice_parser.extract_invoice_info', return_value=MOCK_OLLAMA_RESPONSE)
@patch('builtins.open', new_callable=mock_open)
def test_process_invoices_from_data_folder(mock_file_open, mock_extract_info, mock_extract_text, mock_listdir, mock_logging_info):
    """
    Tests the end-to-end processing of invoices from a data folder. 
    """
    mock_data_folder = "/mock/data"
    mock_output_file = "/mock/invoices_data.csv"
    
    process_invoices_from_data_folder(mock_data_folder, mock_output_file)

    mock_listdir.assert_called_once_with(mock_data_folder)
    mock_extract_text.assert_called_once()
    mock_extract_info.assert_called_once_with(MOCK_PDF_TEXT)
    mock_file_open.assert_called_once_with(mock_output_file, 'w', newline='', encoding='utf-8')

    # Verify content written to the output file (CSV format)
    handle = mock_file_open()
    expected_csv_header = ','.join(['filename'] + CSV_HEADERS) + '\r\n'
    expected_csv_data_row = f"test_invoice.pdf,{MOCK_OLLAMA_RESPONSE['CIF/ NIF Proveedor']},{MOCK_OLLAMA_RESPONSE['Nombre Proveedor']},{MOCK_OLLAMA_RESPONSE['CIF/ NIF Cliente']},{MOCK_OLLAMA_RESPONSE['Nombre Cliente']},{MOCK_OLLAMA_RESPONSE['Numero de Factura']},{MOCK_OLLAMA_RESPONSE['Fecha de la factura']},{MOCK_OLLAMA_RESPONSE['Base imponible']},{MOCK_OLLAMA_RESPONSE['IVA']},{MOCK_OLLAMA_RESPONSE['Retencion IRPF']},{MOCK_OLLAMA_RESPONSE['TOTAL']},{MOCK_OLLAMA_RESPONSE['IBAN']},{MOCK_OLLAMA_RESPONSE['Forma de pago']}\r\n"

    expected_write_calls = [
        call(expected_csv_header),
        call(expected_csv_data_row)
    ]
    handle.write.assert_has_calls(expected_write_calls)
    assert handle.write.call_count == len(expected_write_calls)

    # Verify logging calls
    expected_logging_calls = [
        call(f"Processing {mock_data_folder}/test_invoice.pdf..."),
        call(f"Processed 1 invoices. Results written to {mock_output_file}")
    ]
    mock_logging_info.assert_has_calls(expected_logging_calls)
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
    expected_output_file_path = '/Users/toni.robres/Pycharmprojects/facturai/invoices_data.csv'
    mock_process_invoices.assert_called_once_with(expected_data_folder_path, expected_output_file_path)