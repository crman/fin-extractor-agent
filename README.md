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

#### Option A: Using Azure AI Foundry (Recommended)
```env
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry-project.services.ai.azure.com
FOUNDRY_MODEL=gpt-4o
```
Authenticate via Azure CLI:
```bash
az login
```

#### Option B: Using Direct Azure OpenAI Service
```env
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

---

## Development Roadmap & Feature Branches

- [x] **`feat/1-project-scaffolding`**: Project layout, dependencies, Azure AI Foundry & OpenAI config, test suite setup.
- [ ] **`feat/2-pdf-extractor-tool`**: PDF parsing tool (text + tables), chunking, and sample financial PDFs.
- [ ] **`feat/3-structured-models`**: Pydantic schema for financial metrics, income statements, balance sheets.
- [ ] **`feat/4-agent-implementation`**: Microsoft Agent Framework integration with Foundry/Azure OpenAI & tool binding.
- [ ] **`feat/5-cli-and-testing`**: CLI runner, end-to-end integration tests, and output verification.

