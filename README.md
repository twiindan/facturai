# Invoice Parser with Gemini API

This project provides a Python script (`src/pdf_parser.py`) to process PDF invoice files. It extracts relevant information by directly calling the Google Gemini API and then converts the extracted data into a CSV format.

## Features

*   Identifies and lists PDF files in the `Data/` directory.
*   Directly calls the Google Gemini API to parse invoice information from PDF files.
*   Converts the parsed invoice data into a CSV file with a timestamped filename.
*   Supports reading mock Gemini API responses from a JSON file for testing and development purposes, bypassing the actual API call.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd facturai
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Gemini API Key:**
    Obtain a Gemini API key from [https://ai.google.dev/](https://ai.google.dev/).
    Set it as an environment variable named `GEMINI_API_KEY`:
    ```bash
    export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```
    (Replace `YOUR_GEMINI_API_KEY` with your actual key.)

## Usage

1.  **Place your PDF invoice files:** Put your `.pdf` invoice files into the `Data/` directory.

2.  **Run the script:**
    *   **To parse invoices using the Gemini API:**
        ```bash
        python3 src/pdf_parser.py
        ```
    *   **To use mock Gemini API responses from a JSON file (bypassing API call):**
        ```bash
        python3 src/pdf_parser.py --mock-json /path/to/your/mock_responses.json
        ```
        The `mock_responses.json` file should contain a JSON array of invoice objects, matching the expected output format from Gemini.

3.  **Interpret the output:**
    *   The script will print `INFO` and `WARNING` messages to the console.
    *   A CSV file with a timestamped filename (e.g., `parsed_invoices_YYYYMMDD_HHMMSS.csv`) will be generated in the `Output/` directory (created if it doesn't exist). This CSV will contain data from either the Gemini API or your provided mock JSON file.

## Tests

To run the unit tests:

```bash
./.venv/bin/pytest tests/test_pdf_parser.py
```