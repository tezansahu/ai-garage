# Structured Output Patterns

## When to Use

- Extracting data from unstructured text into a defined schema.
- Parsing documents, emails, or forms into structured records.
- Generating API-compatible responses from natural language.

---

## OpenAI Structured Outputs

```python
from pydantic import BaseModel
from openai import OpenAI

class Contact(BaseModel):
    name: str
    email: str
    company: str | None = None
    role: str | None = None

client = OpenAI()
response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Extract contact information from the text."},
        {"role": "user", "content": user_text}
    ],
    response_format=Contact
)
contact = response.choices[0].message.parsed
```

## Anthropic Structured Outputs

```python
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="Extract contact info. Respond with valid JSON matching this schema: {name: str, email: str, company: str|null, role: str|null}",
    messages=[{"role": "user", "content": user_text}]
)
# Parse JSON from response.content[0].text
```

---

## Best Practices

1. **Use Pydantic models** to define schemas -- enables validation and IDE support.
2. **Provide examples** in the system prompt for complex schemas.
3. **Handle partial extraction**: Make optional fields nullable rather than making them up.
4. **Validate outputs** programmatically after extraction; retry on validation failures.
5. **Batch processing**: For many items, process in batches of 10-20 to balance cost and reliability.

---

## Common Schemas

### Invoice Extraction
```python
class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

class Invoice(BaseModel):
    invoice_number: str
    date: str
    vendor: str
    line_items: list[LineItem]
    subtotal: float
    tax: float
    total: float
```

### Resume Parsing
```python
class Experience(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: str | None
    highlights: list[str]

class Resume(BaseModel):
    name: str
    email: str
    phone: str | None
    skills: list[str]
    experience: list[Experience]
    education: list[dict]
```
