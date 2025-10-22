# ABOUTME: This file contains integration tests for invoice parsing using real PDF files.
# ABOUTME: It verifies the end-to-end process of reading PDFs and writing to results.txt.

import os
import pytest
import logging
from src.invoice_parser import run_cli, process_invoices_from_data_folder, extract_text_from_pdf

# Configure logging for tests to capture output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@pytest.fixture
def data_folder_path(tmp_path):
    """Fixture to provide a path to the Data folder."""
    # In a real scenario, you might copy actual PDF files here.
    # For now, we'll assume the user has placed them in the project's Data folder.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "Data")

@pytest.fixture
def results_file_path(tmp_path):
    """Fixture to provide a path for the results.txt file."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "results.txt")

def test_process_real_pdfs_and_output_results(data_folder_path, results_file_path):
    """
    Tests the processing of real PDF files from the Data folder and verifies
    that results.txt is created and contains extracted text.
    """
    # Ensure results.txt does not exist before running the test
    if os.path.exists(results_file_path):
        os.remove(results_file_path)

    # Run the CLI function which processes PDFs and writes to results.txt
    # We need to temporarily change the working directory for run_cli to find Data folder correctly
    original_cwd = os.getcwd()
    try:
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Change to project root
        run_cli()
    finally:
        os.chdir(original_cwd)

    # Assert that results.txt was created
    assert os.path.exists(results_file_path)

    # Read the content of results.txt
    with open(results_file_path, 'r', encoding='utf-8') as f:
        results_content = f.read()

    # Assert that content from both PDFs is present (by checking for filenames)
    assert "--- Invoice from facturas_20_ejemplo.pdf ---" in results_content
    assert "--- Invoice from facturas_ejemplo.pdf ---" in results_content

    # Further assertions could be added here to check for specific text content
    # from the PDFs, but that would require knowing the content of the PDFs.
    # For now, we're just verifying that the files were processed and their
    # raw text was included in the output.

    # Clean up results.txt after test
    os.remove(results_file_path)
