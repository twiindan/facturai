# ABOUTME: Unit tests for the invoice parsing script (pdf_parser.py).

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
import re # Added for regex matching of dynamic filenames
from datetime import datetime # Added for datetime mocking

# Add the src directory to the Python path to allow importing pdf_parser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from pdf_parser import (
    get_pdf_files,
    convert_json_to_csv,
    parse_invoices_with_gemini,
    CSV_HEADERS
)

# Patch genai.Client at the module level to prevent API key errors during import
mock_genai_client_instance = MagicMock()
patch('pdf_parser.genai.Client', return_value=mock_genai_client()).start()

# Patch os.getenv at the module level to ensure GEMINI_API_KEY is always set for tests
# This prevents ValueError during genai.Client() initialization at module import time.
patch('pdf_parser.os.getenv', return_value="dummy_api_key").start()

# --- Fixtures ---
@pytest.fixture
def mock_pdf_files(tmp_path):
    # Create a dummy Data directory and some PDF files
    data_dir = tmp_path / "Data"
    data_dir.mkdir()
    (data_dir / "invoice1.pdf").write_text("dummy pdf content 1")
    (data_dir / "invoice2.pdf").write_text("dummy pdf content 2")
    (data_dir / "not_a_pdf.txt").write_text("just a text file")
    return str(data_dir)

@pytest.fixture
def mock_output_dir(tmp_path):
    output_dir = tmp_path / "Output"
    output_dir.mkdir()
    return output_dir # Return as pathlib.Path object

# --- Test get_pdf_files ---
def test_get_pdf_files_finds_pdfs(mock_pdf_files):
    pdf_files = get_pdf_files(mock_pdf_files)
    assert len(pdf_files) == 2
    assert any("invoice1.pdf" in f for f in pdf_files)
    assert any("invoice2.pdf" in f for f in pdf_files)

def test_get_pdf_files_no_pdfs(tmp_path):
    data_dir = tmp_path / "Data"
    data_dir.mkdir()
    (data_dir / "text.txt").write_text("hello")
    pdf_files = get_pdf_files(str(data_dir))
    assert len(pdf_files) == 0

def test_get_pdf_files_non_existent_folder(tmp_path):
    pdf_files = get_pdf_files(str(tmp_path / "non_existent"))
    assert len(pdf_files) == 0

# --- Test parse_invoices_with_gemini ---
def test_parse_invoices_with_gemini_with_mock_json(tmp_path, capsys):
    mock_json_content = [
        {
            "CIF/ NIF Proveedor": "MOCK123",
            "Nombre Proveedor": "Mock Provider",
            "TOTAL": 50.00
        }
    ]
    mock_json_file = tmp_path / "mock_responses.json"
    mock_json_file.write_text(json.dumps(mock_json_content))

    pdf_path = "/fake/path/invoice.pdf"
    parsed_data = parse_invoices_with_gemini(pdf_path, mock_json_path=str(mock_json_file))
    
    assert len(parsed_data) == 1
    assert parsed_data[0]["TOTAL"] == 50.00
    assert parsed_data[0]["Nombre Proveedor"] == "Mock Provider"
    captured = capsys.readouterr()
    assert "INFO: Using mock data from" in captured.out

# --- Test convert_json_to_csv ---
def test_convert_json_to_csv_writes_file(mock_output_dir):
    invoice_data = [
        {
            "CIF/ NIF Proveedor": "B12345678",
            "Nombre Proveedor": "Ejemplo S.L.",
            "CIF/ NIF Cliente": "A87654321",
            "Nombre Cliente": "Cliente Ficticio S.A.",
            "Numero de Factura": "INV-001",
            "Fecha de la factura": "2023-10-26",
            "Base imponible": 100.00,
            "IVA": 21.00,
            "Retencion IRPF": 0.00,
            "TOTAL": 121.00,
            "IBAN": "ES1234567890123456789012",
            "Forma de pago": "Transferencia"
        }
    ]
    output_csv_path = os.path.join(mock_output_dir, "test_output.csv")
    convert_json_to_csv(invoice_data, output_csv_path)

    assert os.path.exists(output_csv_path)
    with open(output_csv_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert ",".join(CSV_HEADERS) in content
        assert "B12345678,Ejemplo S.L.,A87654321,Cliente Ficticio S.A.,INV-001,2023-10-26,100.0,21.0,0.0,121.0,ES1234567890123456789012,Transferencia" in content

def test_convert_json_to_csv_empty_data(mock_output_dir):
    invoice_data = []
    output_csv_path = os.path.join(mock_output_dir, "output.csv")
    convert_json_to_csv(invoice_data, output_csv_path)
    assert not os.path.exists(output_csv_path) # Should not create file if no data