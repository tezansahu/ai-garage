# Contributing to Contract Clarity Agent

Thank you for your interest in contributing to Contract Clarity Agent! We welcome contributions from the community.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Code of Conduct](#code-of-conduct)

## 🚀 Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/tezansahu/ai-garage.git
cd ai-garage/contract-clarity-agent
```

### 2. Install UV Package Manager

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create Virtual Environment

```bash
# Create venv
uv venv

# Activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
# Install package in editable mode
uv pip install -e . --prerelease=allow

# Install development dependencies
uv pip install black ruff pytest pytest-asyncio
```

### 5. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your test credentials
```

## 🎨 Code Style

We follow strict code quality standards:

### Formatting

**Black** for consistent code formatting:
```bash
black src/ app.py example.py
```

### Linting

**Ruff** for fast linting:
```bash
ruff check src/ app.py example.py
```

### Type Hints

Use type hints for all function signatures:
```python
def process_document(file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
    """Process a document based on its type."""
    pass
```

### Docstrings

Follow Google-style docstrings:
```python
def analyze_document(self, file_path: str) -> Dict[str, Any]:
    """
    Analyze a document file and return structured analysis.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dictionary containing analysis results
        
    Raises:
        ValueError: If file type is not supported
    """
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_agent.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Writing Tests

Create test files in `tests/` directory:

```python
import pytest
from src.agent import ContractClarityAgent

@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initializes correctly."""
    agent = ContractClarityAgent()
    assert agent is not None
    assert agent.agent is not None
```

## 🔨 Making Changes

### Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test Changes**
   ```bash
   black .
   ruff check .
   pytest
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add PDF table extraction support
fix: resolve Firecrawl Document object handling
docs: update architecture diagrams
refactor: simplify document processing pipeline
```

## 🎯 Common Contribution Areas

### Adding New Document Types

1. **Update `src/document_processor.py`:**
   ```python
   def process_new_format(self, file_path: str) -> Dict[str, Any]:
       """Process new document format."""
       # Implementation
       return {"text": extracted_text, "success": True}
   ```

2. **Update `process_document()` method:**
   ```python
   elif file_ext == '.new':
       return self.process_new_format(file_path)
   ```

3. **Update `app.py` file uploader:**
   ```python
   type=["pdf", "docx", "doc", "new"]
   ```

4. **Test thoroughly** with sample documents
5. **Update documentation** in README.md

### Adding Agent Tools

1. **Create tool function in `src/agent.py`:**
   ```python
   def _create_my_tool(self):
       """Create my custom tool."""
       def my_tool(param: str) -> str:
           """Tool description for GPT-4o."""
           # Implementation
           return result
       return my_tool
   ```

2. **Add to agent tools list:**
   ```python
   tools=[
       self._create_extract_web_content_tool(),
       self._create_my_tool(),  # Add here
   ]
   ```

3. **Test tool invocation**

### Improving Risk Assessment

1. **Update `SYSTEM_PROMPT` in `src/agent.py`:**
   ```python
   SYSTEM_PROMPT = """
   ... existing prompt ...
   
   Additional risk factors:
   - New risk type: HIGH RISK if [condition]
   """
   ```

2. **Test with various contracts**

### UI Enhancements

1. **Modify `app.py` Streamlit components**
2. **Update CSS in custom styles**
3. **Test responsiveness**
4. **Update screenshots in README if needed**

## 📝 Documentation

### Required Documentation Updates

When making changes, update relevant documentation:

- **README.md** - User-facing features, setup instructions
- **CONTRIBUTING.md** - Development process changes
- **Code docstrings** - All new functions/classes
- **Type hints** - All function signatures

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams for complex flows (Mermaid syntax)
- Keep examples up-to-date with code

## 🔄 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines (black, ruff)
- [ ] Tests pass (`pytest`)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts with main branch

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Screenshots (if applicable)
```

### Review Process

1. Automated checks run (if configured)
2. Maintainers review code
3. Address feedback
4. Approval and merge

## 🤝 Code of Conduct

### Our Standards

- **Be respectful** - Treat everyone with respect and kindness
- **Be inclusive** - Welcome newcomers and diverse perspectives
- **Be constructive** - Provide helpful, actionable feedback
- **Be collaborative** - Work together towards common goals
- **Be professional** - Keep interactions courteous and on-topic

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal attacks
- Publishing private information
- Other unprofessional conduct

### Enforcement

Violations will be addressed by project maintainers. Serious or repeated violations may result in being banned from the project.

## 🆘 Getting Help

### Questions?

- **General Questions**: Open a [Discussion](https://github.com/your-repo/discussions)
- **Bug Reports**: Open an [Issue](https://github.com/your-repo/issues)
- **Feature Requests**: Open an [Issue](https://github.com/your-repo/issues) with "feature" label

### Resources

- [README.md](README.md) - Project overview and usage
- [references/contract_clarity_prd.md](references/contract_clarity_prd.md) - Product requirements
- [Microsoft Agent Framework docs](https://github.com/microsoft/agent-framework)


**Questions?** Feel free to reach out by opening an issue or discussion.
