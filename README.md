# Financial Extractor Agent (`fin-extractor-agent`)

AI Agent powered by **Microsoft Agent Framework (MAF)** and **Azure AI Foundry** to extract structured financial metrics from PDF documents into validated JSON schemas.

---

## Architecture Overview

```
                                      +-------------------------+
                                      |   Financial PDF Report  |
                                      +------------+------------+
                                                   |
                                                   v
+-------------------------------+     +------------+------------+
|  Structured Output Schema     | <---|  Microsoft Agent        |
|  (Pydantic / JSON Validation) |     |  Framework Agent        |
+-------------------------------+     |  (Azure AI Foundry)     |
                                      +------------+------------+
                                                   ^
                                                   | Tool Invocation
                                      +------------+------------+
                                      |   PDF Extraction Tool   |
                                      |  (PyMuPDF / pdfplumber) |
                                      +-------------------------+
```

1. **PDF Extractor Tool:** An agent-callable tool that parses financial PDFs, extracting high-fidelity text, metadata, and structured tables.
2. **Microsoft Agent Framework Core:** Uses Azure AI Foundry (`agent_framework_foundry.FoundryChatClient`) and `DefaultAzureCredential` to orchestrate multi-step reasoning over financial statements, balance sheets, cash flows, and income statements.
3. **Structured Output Model:** Strictly enforces data types and schemas using Pydantic models ([`FinancialReport`](src/fin_extractor/models/schemas.py)).

> 📘 **Deep Dive:** For the complete technical architecture, Mermaid sequence diagrams, Azure AI Foundry provisioning steps, and MAF code implementation, see [**`docs/ARCHITECTURE.md`**](docs/ARCHITECTURE.md).

---

## Project Structure

```
fin-extractor-agent/
├── .env.example              # Template for Azure AI Foundry credentials
├── .gitignore                # Git ignore rules
├── pyproject.toml            # Project metadata and package definition
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── docs/
│   └── ARCHITECTURE.md       # Detailed technical architecture & MAF/Foundry guide
├── data/
│   ├── postman_collection.json # Pre-configured Postman collection for API testing
│   └── samples/              # Sample financial PDFs for testing and demos
├── src/
│   └── fin_extractor/
│       ├── __init__.py
│       ├── main.py           # Application entrypoint & Uvicorn launcher
│       ├── config.py         # AppSettings for Azure AI Foundry
│       ├── agents/           # Microsoft Agent Framework agent definitions
│       ├── api/              # FastAPI application and REST endpoints
│       ├── models/           # Pydantic structured output models & schemas
│       ├── prompts/          # Domain-tailored system prompts and instructions
│       ├── tools/            # PDF parsing & extraction tools (PyMuPDF)
│       └── utils/            # Logging, formatting, and helper utilities
└── tests/
    ├── __init__.py
    ├── test_agent.py         # Agent orchestrator unit tests
    ├── test_api.py           # FastAPI endpoint unit tests
    ├── test_config.py        # Configuration unit tests
    ├── test_models.py        # Pydantic schema validation tests
    └── test_pdf_extractor.py # PDF parsing tool unit tests
```

---

## Quickstart

### 1. Environment Setup
```bash
# Create virtual environment with Python 3.11+
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies and local package in editable mode
pip install -r requirements.txt
pip install -e .
```

### 2. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your Azure AI Foundry project:
```env
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry-project.services.ai.azure.com
FOUNDRY_MODEL=gpt-4o
LOG_LEVEL=INFO
```

Authenticate via Azure CLI:
```bash
az login
```

---

## Running the API & Testing

### 1. Start the FastAPI Server
```bash
# Run using the python entrypoint:
python -m fin_extractor.main

# Or run using uvicorn directly:
uvicorn fin_extractor.api:app --reload --port 8000
```
The server will start at: `http://localhost:8000`

### 2. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and Azure AI Foundry configuration state |
| `POST` | `/api/v1/extract` | Upload a financial PDF and extract structured `FinancialReport` JSON |

### 3. Interactive Swagger UI (Browser)
Visit **`http://localhost:8000/docs`** in your browser to:
- Test the `GET /health` endpoint.
- Test `POST /api/v1/extract` by dragging and dropping `data/samples/TechNova Q3 2026 Financial Results.pdf`.

### 4. Testing with Postman
Import the pre-configured collection:
1. Open **Postman**.
2. Click **Import** and select `data/postman_collection.json`.
3. Open the request: **Extract Financial Metrics** (`POST http://localhost:8000/api/v1/extract`).
4. In the **Body** tab (`form-data`), click the `file` field and choose your PDF (`data/samples/TechNova Q3 2026 Financial Results.pdf`).
5. Click **Send** to see the extracted structured JSON!

### 5. Testing with cURL
```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/samples/TechNova Q3 2026 Financial Results.pdf"
```

---

## Running Unit Tests

Run the test suite using `pytest`:

```bash
pytest
```

For verbose output with test names:
```bash
pytest -v
```