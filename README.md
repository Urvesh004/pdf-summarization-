# DocSummarize (PDF/DOCX Summarizer)

DocSummarize is a Flask web app that extracts text from **PDF** and **DOCX** documents and generates a **structured AI summary** using Groq’s hosted LLM.

## Features
- Upload **PDF** or **DOCX**
- Extracts readable text (page-by-page for PDFs)
- Generates a structured summary (title + sections)
- Cleaned/normalized output for consistent rendering
- Download the latest summary as a `.txt` file

## Tech Stack
- **Backend:** Flask
- **Frontend:** HTML/Jinja templates + vanilla JS
- **Text extraction:**
  - `pdfplumber` for PDFs
  - `python-docx` for DOCX
- **AI summarization:** Groq Chat Completions API
- **Config:** environment variables via `python-dotenv`

## Project Structure
- `app.py` — Flask routes (`/`, `/summarize`, `/download`)
- `utils/summarizer.py` — extraction helpers, prompt builder, Groq API call, and output cleaning
- `templates/`
  - `index.html` — upload page
  - `loading.html` — loading + fetches `/summarize` and renders result
  - `result.html` — legacy/simple result template
- `static/`
  - `style.css` — styling
  - `script.js` — older client-side helpers (not central to the current flow)
- `summary.txt` — used as the download target for the latest summary

## Requirements
See `requirements.txt`:
- flask
- python-dotenv
- pdfplumber
- requests
- python-docx
- groq

## Setup & Run

### 1) Create a virtual environment
```bash
python -m venv venv
```
Activate it:
- **Windows (cmd):**
  ```bat
  venv\Scripts\activate
  ```
- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure Groq API key
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_key_here
```
Get a key from: https://console.groq.com/keys

### 4) Start the app
```bash
python app.py
```
Then open:
- http://localhost:5000

## How It Works (High Level)
1. You upload a file on `/` (PDF/DOCX).
2. The server stores it temporarily in `uploads/` with a UUID name.
3. The loading page requests `/summarize`.
4. `utils/summarizer.py`:
   - Extracts text from the document
   - Builds a prompt with strict output formatting rules
   - Calls Groq’s Chat Completions API
   - Cleans/normalizes the output for consistent rendering
5. The server deletes the uploaded file after processing.

## Supported Inputs
- **PDF** (`.pdf`)
- **DOCX** (`.docx`)

If the PDF is scanned/image-based and has no extractable text, the app returns an extraction error message.

## Download
Click **Download .txt** on the result page.
- The app writes the most recent summary into `summary.txt` and returns it via `/download`.

## Troubleshooting
- **“Invalid Groq API Key”**: verify `GROQ_API_KEY` in `.env`.
- **“No API Key Found”**: ensure `.env` exists and is loaded (server restarted after changes).
- **Extraction Error**: the document may not contain selectable text (especially scanned PDFs).
- **Rate limits (429)**: try again after a short wait; the code attempts multiple models.

## Notes / Limitations
- Summaries depend on the amount and quality of extracted text.
- Large documents may be truncated before sending to the LLM (prompt builder limits input length).

## License
Add your project license here (e.g., MIT). 

