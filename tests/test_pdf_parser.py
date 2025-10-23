# ABOUTME: Unit tests for the invoice parsing script (pdf_parser.py).

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path to allow importing pdf_parser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from pdf_parser import (
    get_pdf_files,
    convert_json_to_csv,
    CSV_HEADERS
)

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
    return str(output_dir)

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
    output_csv_path = os.path.join(mock_output_dir, "output.csv")
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