# Financial Extractor Agent (`fin-extractor-agent`)

AI Agent powered by **Microsoft Agent Framework (MAF)** and **Azure AI Foundry / Azure OpenAI** to extract structured financial metrics from PDF documents into validated JSON schemas.

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
+-------------------------------+     |  (Azure AI Foundry /    |
                                      |   Azure OpenAI)         |
                                      +------------+------------+
                                                   ^
                                                   | Tool Invocation
                                      +------------+------------+
                                      |   PDF Extraction Tool   |
                                      |  (PyMuPDF / pdfplumber) |
                                      +-------------------------+
```

1. **PDF Extractor Tool:** An agent-callable tool that parses financial PDFs, extracting high-fidelity text, metadata, and structured tables.
2. **Microsoft Agent Framework Core:** Uses Azure AI Foundry (`agent_framework_foundry.FoundryChatClient`) or Azure OpenAI to interpret financial statements, balance sheets, cash flows, and income statements.
3. **Structured Output Model:** Strictly enforces data types and schemas using Pydantic models.

---

## Project Structure

```
fin-extractor-agent/
├── .env.example              # Template for Azure AI Foundry / Azure OpenAI credentials
├── .gitignore                # Git ignore rules
├── pyproject.toml            # Project metadata and package definition
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── data/
│   └── samples/              # Sample financial PDFs for testing and demos
├── src/
│   └── fin_extractor/
│       ├── __init__.py
│       ├── config.py         # AppSettings for Azure AI Foundry & Azure OpenAI
│       ├── agents/           # Microsoft Agent Framework agent definitions
│       ├── models/           # Pydantic structured output models
│       ├── tools/            # PDF parsing & extraction tools
│       └── utils/            # Logging, formatting, and helper utilities
└── tests/
    ├── __init__.py
    └── test_config.py        # Configuration unit tests
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
```

Authenticate via Azure CLI:
```bash
az login
```

---