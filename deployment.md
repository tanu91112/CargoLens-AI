# CargoLens AI – Deployment Guide

## 1. Project Overview

CargoLens AI is a document intelligence application that helps users manage shipments, upload shipping documents, extract relevant information, validate document fields, and export shipment data.

### Technology Stack
- Frontend: React, Vite
- Backend: Python, FastAPI
- Database: SQLite
- Authentication: JWT
- Password Hashing: Argon2
- PDF Text Extraction: PyMuPDF

## 2. Prerequisites

Install the following before running the application:

- Python 3.12
- Node.js and npm
- Git (optional)
- A modern web browser

## 3. Project Structure

```text
CargoLens-AI/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── uploads/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── index.html
└── deployment.md
```

## 4. Backend Setup

Open a terminal and navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## 5. Frontend Setup

Open a second terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the frontend in your browser using the URL displayed by Vite, typically:

```text
http://localhost:5173
```

## 6. Database

CargoLens AI uses SQLite for storing user accounts, shipment records, uploaded document information, and audit logs.

The database is initialized by the backend application. Ensure the application has permission to create and write to its database location.

## 7. Application Workflow

1. Register or log in.
2. Create a shipment.
3. Select a shipment and upload PDF documents.
4. Review extracted document information.
5. Check cross-document validation results.
6. View audit history.
7. Export shipment information as a CSV file.

## 8. Notes and Limitations

- PDF text extraction currently uses PyMuPDF and rule-based field extraction.
- Scanned PDFs requiring OCR are not currently processed.
- Extraction results should be reviewed before operational use.
- The project uses SQLite for local development.
- The supplied commands run the application in development mode, not production mode.

## 9. Troubleshooting

- If the backend does not start, verify the Python version and installed dependencies.
- If the frontend does not start, run `npm install` again.
- If the frontend cannot connect to the backend, verify that the backend is running and the API URL is configured correctly.
- If PDF upload fails, verify that the file is a valid PDF and is within the configured size limit.