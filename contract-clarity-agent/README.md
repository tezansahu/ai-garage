# Contract Clarity Agent

> AI-powered contract analysis assistant that helps individuals and small businesses understand legal documents through plain-language summaries, risk assessments, and conversational guidance.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Microsoft Agent Framework](https://img.shields.io/badge/agent--framework-latest-green.svg)](https://github.com/microsoft/agent-framework)

## ✨ Features

- 📄 **Multi-Format Document Analysis** - PDF, DOCX, and image files supported
- 🎯 **Intelligent Risk Assessment** - Automatic HIGH/MEDIUM/LOW risk flagging
- 💬 **Multi-Turn Conversations** - Ask follow-up questions with full context retention
- 🌐 **URL Analysis** - Extract and analyze contracts from web URLs
- 🔍 **Plain Language Explanations** - Complex legal terms in 8th-grade reading level
- 🔄 **Thread Management** - Start fresh conversations or continue existing ones
- 🔒 **Privacy-First** - Files deleted immediately after analysis
- ⚡ **Powered by GPT-4o-mini** - Uses Microsoft Agent Framework with Azure AI Foundry

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **AI Framework** | Microsoft Agent Framework |
| **LLM** | GPT-4o-mini (Azure AI Foundry) |
| **Frontend** | Streamlit |
| **Document Processing** | Docling 2.0+ |
| **Web Scraping** | Firecrawl |
| **Package Management** | UV |
| **Python Version** | 3.13 |

## 📋 Prerequisites

- **Python**: 3.13 (3.14 not supported due to lxml compatibility)
- **UV Package Manager**: [Installation guide](https://github.com/astral-sh/uv)
- **Azure AI Foundry**: Account with GPT-4o deployment
- **Firecrawl API Key**: (Optional) For web content extraction

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/tezansahu/ai-garage.git
cd ai-garage/contract-clarity-agent
```

### 2. Install UV

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Setup Environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
uv pip install -e . --prerelease=allow
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
```

**Required variables in `.env`:**

```env
# Azure AI Foundry Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Optional: Firecrawl for web content extraction
FIRECRAWL_API_KEY=your-firecrawl-api-key-here
```

### 5. Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 💡 Usage

### Document Analysis Workflow

1. **Upload Document**: Click sidebar "Browse files" → Select PDF/DOCX/image
2. **Analyze**: Click "🔍 Analyze Document"
3. **Review Results**: 
   - Executive summary
   - Document type identification
   - Risk-flagged clauses (🔴 HIGH, 🟡 MEDIUM, 🟢 POSITIVE)
   - Key terms and definitions
   - Actionable recommendations
4. **Ask Questions**: Use chat to ask follow-up questions about specific clauses

### General Chat Mode

- **No Document Required**: Chat works without uploading files
- **Multi-Turn Conversations**: Context maintained across messages
- **URL Analysis**: Ask agent to analyze contracts from URLs
- **Legal Guidance**: Get explanations of contract concepts

### New Chat / Reset

- Click **"🔄 New Chat"** in sidebar to:
  - Clear all messages
  - Delete uploaded files
  - Reset agent memory
  - Start completely fresh conversation

## 📖 Example Use Cases

### Employment Agreement Analysis

```
1. Upload employment contract
2. Agent identifies:
   ✓ IP assignment clauses
   ✓ Non-compete restrictions  
   ✓ Termination terms
   ✓ Severance provisions
3. Ask: "Can I do freelance work on the side?"
4. Ask: "Is this non-compete enforceable in California?"
```

### Vendor Contract Review

```
1. Upload vendor agreement
2. Agent flags:
   ⚠️  Auto-renewal clauses
   ⚠️  Payment terms and penalties
   ⚠️  Liability limitations
3. Ask: "What happens if I want to cancel early?"
4. Ask: "Are these payment terms negotiable?"
```

### URL-Based Analysis

```
1. Chat: "Analyze the contract at https://example.com/terms"
2. Agent extracts web content via Firecrawl
3. Provides same detailed analysis
4. Answer follow-up questions
```

## 🗂️ Project Structure

```
contract-clarity-agent/
├── src/
│   ├── agent.py                    # Main agent with Microsoft Agent Framework
│   └── document_processor.py       # Docling + Firecrawl processors
├── references/
│   └── contract_clarity_prd.md     # Product requirements
├── app.py                          # Streamlit UI
├── example.py                      # Programmatic usage examples
├── pyproject.toml                  # UV project configuration
├── .env.example                    # Environment template
├── .gitignore
├── README.md                       # This file
└──CONTRIBUTING.md                 # Contribution guidelines
```

## 🎯 Risk Assessment Criteria

### 🔴 HIGH RISK
- Unlimited liability or indemnification
- Overly broad IP assignment (includes personal projects)
- Very restrictive non-compete (>2 years, >100 mile radius)
- One-sided termination rights
- Auto-renewal without notice period
- Below-market liability caps

### 🟡 MEDIUM RISK
- Long payment terms (>Net-60)
- Extended confidentiality (>5 years)
- Vague deliverable definitions
- Unilateral modification rights
- Arbitration-only dispute resolution
- Force majeure exclusions

### 🟢 POSITIVE/STANDARD
- Mutual termination rights
- Reasonable liability caps (3x contract value)
- Clear scope of work
- Standard payment terms (Net-30)
- Balanced confidentiality obligations
- Industry-standard clauses

## 🔒 Privacy & Security

### File Handling
- ✅ Files saved temporarily to `uploads/` directory
- ✅ **Deleted immediately** after analysis completes (~30-60 seconds)
- ✅ Only extracted text retained in conversation thread memory
- ✅ "New Chat" button clears all data (files + memory)

### Data Retention
- **During Analysis**: File on disk + text in thread
- **After Analysis**: File deleted, text in thread only
- **After "New Chat"**: Everything cleared, fresh start

### Security
- End-to-end encryption via HTTPS
- No third-party data sharing
- Azure AI Foundry compliance (SOC 2, ISO 27001)
- Local file storage only (no cloud persistence)

## 🔧 Advanced Features

### Logging & Debugging

Enable verbose logging to see agent operations:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Logs include:
- Agent initialization
- Document processing steps
- Tool calls (web extraction)
- Thread creation/reset events
- Chat message processing

### Programmatic Usage

```python
from src.agent import ContractClarityAgent
import asyncio

async def main():
    # Initialize agent
    agent = ContractClarityAgent()
    
    # Analyze document
    result = await agent.analyze_document("contract.pdf")
    print(result["analysis"])
    
    # Ask follow-up
    response = await agent.ask_question("What are the payment terms?")
    print(response)
    
    # General chat
    response = await agent.chat("Explain indemnification")
    print(response)

asyncio.run(main())
```

### Thread Management

```python
# Start fresh conversation
agent.reset_conversation()

# New thread on next message
response = await agent.chat("Hello", new_thread=True)
```

## 🐛 Troubleshooting

### Import Errors

```bash
# Reinstall dependencies
uv pip install -e . --prerelease=allow --force-reinstall
```

### Azure Authentication Issues

- Verify `AZURE_OPENAI_ENDPOINT` format: `https://your-resource.openai.azure.com/`
- Check `AZURE_OPENAI_API_KEY` is valid
- Ensure `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` matches your deployment
- Confirm API version compatibility: `2025-01-01-preview`

### Document Processing Errors

**PDF Issues:**
```bash
# Reinstall Docling
uv pip install docling --force-reinstall
```

**Slow Processing:**
- Large documents (50+ pages) take 30-60 seconds
- Complex PDFs with images/tables take longer
- Check Azure endpoint latency

### Firecrawl Errors

- Verify `FIRECRAWL_API_KEY` is set in `.env`
- Check API quota/rate limits
- URL must be publicly accessible

## 🧪 Development

### Running Examples

```bash
python example.py
```

### Code Quality

```bash
# Install dev dependencies
uv pip install black ruff pytest pytest-asyncio

# Format code
black .

# Lint
ruff check .

# Run tests (when available)
pytest
```

## ⚠️ Limitations

- **Not Legal Advice**: Informational analysis only; consult licensed attorney for legal guidance
- **Accuracy**: May occasionally miss nuances in complex clauses
- **Jurisdiction**: General analysis; doesn't reflect state-specific laws
- **Language**: English documents only
- **File Size**: Best performance with documents <50 pages

## 📚 Documentation

- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Product Requirements**: [references/contract_clarity_prd.md](references/contract_clarity_prd.md)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style and standards
- Pull request process
- Testing requirements
- Documentation updates

---

**⚠️ Legal Disclaimer**: This tool provides informational analysis only and does not constitute legal advice. For specific legal guidance, consult a licensed attorney. Analysis is based on general patterns and may not reflect jurisdiction-specific requirements or recent legal changes.

**Built with ❤️ using Microsoft Agent Framework**
