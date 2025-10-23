# Invoice Parser with Gemini API (Prompt Generation)

This project provides a Python script (`src/pdf_parser.py`) to process PDF invoice files. It extracts relevant information by generating prompts for the Google Gemini API. The script then converts the extracted data (or dummy data for demonstration) into a CSV format.

**Important Note:** This script *generates prompts* for the Gemini API. It does **not** directly call the Gemini API itself. This design choice is due to the constraints of the execution environment, where direct programmatic access to the Gemini API client (`google.generativeai`) is not assumed to be available or is intentionally avoided to adhere to strict dependency requirements.

## Features

*   Identifies and lists PDF files in the `Data/` directory.
*   Constructs a detailed prompt for the Gemini API, including the invoice parsing instructions and the local PDF file path.
*   Prints the generated prompt to the console, which can then be used manually with the `default_api.web_fetch` tool (if available in your environment).
*   Converts the parsed invoice data (or dummy data if the API call is not performed) into a CSV file with a timestamped filename.
*   Supports reading mock Gemini API responses from a JSON file for testing and development purposes.

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

## Usage

1.  **Place your PDF invoice files:** Put your `.pdf` invoice files into the `Data/` directory.

2.  **Run the script:**
    *   **To generate prompts and use dummy data (default):**
        ```bash
        python3 src/pdf_parser.py
        ```
    *   **To use mock Gemini API responses from a JSON file:**
        ```bash
        python3 src/pdf_parser.py --mock-json /path/to/your/mock_responses.json
        ```
        The `mock_responses.json` file should contain a JSON array of invoice objects, matching the expected output format from Gemini.

3.  **Interpret the output:**
    *   The script will print `INFO` and `WARNING` messages to the console.
    *   When not using `--mock-json`, for each PDF file, it will output a block like this:
        ```
        --- PROMPT FOR GEMINI API ---
        You are an expert invoice parser.
        ... (rest of the prompt) ...
        Process the following PDF file: file:///path/to/your/Data/invoice.pdf
        --- END PROMPT ---
        NOTE: In a real execution, the above prompt would be sent to Gemini via default_api.web_fetch.
        For now, returning dummy data.
        ```
    *   A CSV file with a timestamped filename (e.g., `parsed_invoices_YYYYMMDD_HHMMSS.csv`) will be generated in the `Output/` directory (created if it doesn't exist). This CSV will contain data from either the dummy responses or your provided mock JSON file.

## How to use with Gemini API (Manual Step)

To get actual parsed data from the Gemini API, you would perform the following manual steps:

1.  Run `python3 src/pdf_parser.py` (without `--mock-json`).
2.  Copy the `full_prompt` output for a specific PDF file (the text between `--- PROMPT FOR GEMINI API ---` and `--- END PROMPT ---`).
3.  If you have access to a tool that can call `default_api.web_fetch` (like the Gemini CLI agent), execute it with the copied prompt:
    ```python
    print(default_api.web_fetch(prompt="YOUR_COPIED_PROMPT_HERE"))
    ```
    Replace `"YOUR_COPIED_PROMPT_HERE"` with the actual prompt you copied.
4.  The `web_fetch` tool will return a JSON string. You can save this JSON string to a file (e.g., `my_gemini_response.json`) and then run the script with the `--mock-json` option:
    ```bash
    python3 src/pdf_parser.py --mock-json my_gemini_response.json
    ```
    This allows you to process the actual Gemini API response into a CSV.

## Tests

To run the unit tests:

```bash
./.venv/bin/pytest tests/test_pdf_parser.py
```