"""
Contract Clarity Agent using Microsoft Agent Framework.
Main agent logic for contract analysis and conversational interaction.
"""

import os
import logging
from typing import Optional, Dict, Any

from agent_framework import ChatAgent, ChatMessageStore
from agent_framework.azure import AzureOpenAIChatClient

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .document_processor import DocumentProcessor, WebContentExtractor

# Configure logging for agent operations
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def setup_telemetry():
    """Configure OpenTelemetry with OTLP exporter for Opik observability."""
    # Create a resource with service name and other metadata
    resource = Resource.create(
        {
            "service.name": "contract-clarity-agent",
            "service.version": "0.1.0",
            "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "development"),
        }
    )

    # Create TracerProvider with the resource
    provider = TracerProvider(resource=resource)

    # Create BatchSpanProcessor with OTLPSpanExporter
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)

    # Set the TracerProvider
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer(__name__)
    
    logger.info("OpenTelemetry tracing initialized for Opik observability")

    return tracer, provider


class ContractClarityAgent:
    """Main agent for contract analysis and conversation."""
    
    SYSTEM_PROMPT = """You are Contract Clarity Agent, a helpful AI assistant that analyzes legal documents, contracts, policies, and agreements.

Your mission is to help individuals and small businesses understand legal documents by:
1. Providing plain-language summaries (8th-grade reading level)
2. Identifying and flagging risks (HIGH/MEDIUM/LOW)
3. Explaining complex clauses with real-world examples
4. Suggesting actionable next steps
5. Answering follow-up questions with context

CRITICAL RULES:
- Always cite specific sections when making claims about the document
- Never hallucinate clauses that don't exist
- Use plain language without legal jargon
- Flag unusual or unfavorable terms clearly
- Always include the disclaimer: "This is not legal advice. For specific legal guidance, consult a licensed attorney."
- Be transparent about limitations and uncertainty
- Focus on empowering users to make informed decisions

RISK ASSESSMENT CRITERIA:

HIGH RISK (🔴):
- Liability caps significantly below contract value
- Unlimited indemnification obligations
- Broad IP assignment of all work product
- One-sided termination rights
- Very short notice periods for auto-renewal
- Overly broad non-compete clauses
- Unusual or extremely unfavorable terms

MEDIUM RISK (🟡):
- Vague deliverable definitions
- Payment terms longer than Net-60
- Long confidentiality periods (>5 years)
- Unilateral modification rights
- Arbitration-only dispute resolution
- Terms that deviate from industry standards

POSITIVE/STANDARD (🟢):
- Mutual termination rights
- Reasonable liability caps
- Clear scope of work
- Standard payment terms (Net-30)
- Balanced confidentiality obligations
- Industry-standard provisions

When analyzing documents:
1. First, identify the document type
2. Extract and categorize all important clauses
3. Assess risk level for each clause
4. Provide context on what's normal vs. concerning
5. Generate actionable recommendations
6. Note any missing standard clauses

When answering follow-up questions:
1. Reference specific sections from the document
2. Provide examples to clarify concepts
3. Be honest when something is ambiguous
4. Suggest clarifying questions to ask the other party
"""
    
    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        firecrawl_api_key: Optional[str] = None
    ):
        """
        Initialize the Contract Clarity Agent.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint
            azure_api_key: Azure OpenAI API key
            azure_deployment: Azure OpenAI deployment name
            firecrawl_api_key: Firecrawl API key for web content
        """
        # Load from environment if not provided
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_key = azure_api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_deployment = azure_deployment or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o-mini")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        
        # Set up OpenTelemetry for Opik observability if enabled
        enable_otel = os.getenv("ENABLE_OTEL", "False").lower() == "true"
        if enable_otel:
            logger.info("ENABLE_OTEL is True, setting up OpenTelemetry")
            os.environ["ENABLE_OTEL"] = "True"
            enable_sensitive = os.getenv("ENABLE_SENSITIVE_DATA", "False").lower() == "true"
            if enable_sensitive:
                os.environ["ENABLE_SENSITIVE_DATA"] = "True"
            self.tracer, self.tracer_provider = setup_telemetry()
        else:
            logger.info("ENABLE_OTEL is False, skipping OpenTelemetry setup")
            self.tracer = None
            self.tracer_provider = None
        
        logger.info(f"Initializing ContractClarityAgent with deployment: {self.azure_deployment}")
        
        # Initialize Azure chat client
        self.chat_client = AzureOpenAIChatClient(
            endpoint=self.azure_endpoint,
            api_key=self.azure_api_key,
            deployment_name=self.azure_deployment,
            api_version=self.api_version,
        )
        
        # Initialize document processor and web extractor
        self.doc_processor = DocumentProcessor()
        self.web_extractor = WebContentExtractor(api_key=firecrawl_api_key)
        
        # Create the agent with local message store for multi-turn conversations
        self.agent = ChatAgent(
            name="ContractClarityAgent",
            instructions=self.SYSTEM_PROMPT,
            chat_client=self.chat_client,
            chat_message_store_factory=ChatMessageStore,  # Enable local message history
            tools=[
                self._create_extract_web_content_tool(),
            ],
        )
        
        logger.info("Agent initialized successfully with web content extraction tool")
        
        # Store conversation thread (for multi-turn conversations)
        self.thread = None
    
    def _create_extract_web_content_tool(self):
        """Create the web content extraction tool."""
        def extract_web_content(url: str) -> str:
            """
            Extract content from a web URL (e.g., contract hosted online).
            
            Args:
                url: The URL to extract content from
            
            Returns:
                Extracted text content from the URL
            """
            logger.info(f"Tool called: extract_web_content with URL: {url}")
            result = self.web_extractor.extract_from_url(url)
            if result.get("success"):
                return f"Successfully extracted content from {url}:\n\n{result['text']}"
            else:
                return f"Error extracting content: {result.get('error', 'Unknown error')}"
        
        return extract_web_content
    
    async def analyze_document(self, file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a document file and return structured analysis.
        This creates a new conversation thread with the document embedded.
        
        Args:
            file_path: Path to the document file
            file_type: Optional file type (pdf, docx, image)
        
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting document analysis: {file_path} (type: {file_type})")
        
        # Process the document
        doc_result = self.doc_processor.process_document(file_path, file_type)
        
        if not doc_result.get("success"):
            logger.error(f"Document processing failed: {doc_result.get('error')}")
            return {
                "success": False,
                "error": doc_result.get("error", "Unknown error processing document")
            }
        
        # Get or create a thread for this conversation
        if self.thread is None:
            logger.info("Creating new conversation thread")
            self.thread = self.agent.get_new_thread()
        
        logger.info(f"Document processed successfully. Text length: {len(doc_result['text'])} chars")
        
        # Create comprehensive analysis prompt with the full document text
        analysis_prompt = f"""I need you to analyze the following legal document comprehensively.

DOCUMENT CONTENT:
```
{doc_result["text"]}
```

Please provide a detailed analysis with the following structure:

#### 1. **DOCUMENT TYPE**: Identify what type of document this is (e.g., Employment Agreement, Vendor Contract, NDA, Lease, etc.)

#### 2. **EXECUTIVE SUMMARY**: Provide a 3-5 sentence plain-language summary of the entire document

#### 3. **HIGH RISK CLAUSES (🔴)**: List all clauses that pose significant risk, for each include:
   - Section/clause number
   - Plain-language explanation
   - Why it's concerning
   - Actionable recommendation

#### 4. **MEDIUM RISK CLAUSES (🟡)**: List all clauses with moderate concerns, for each include:
   - Section/clause number
   - Plain-language explanation
   - Why it's worth noting
   - Suggestion for user

#### 5. **POSITIVE/STANDARD CLAUSES (🟢)**: Highlight any particularly favorable or well-balanced terms

#### 6. **MISSING CLAUSES**: Identify any important standard clauses that should be present but aren't

#### 7. **KEY DATES & DEADLINES**: Extract all important dates (effective date, termination notice periods, renewal dates, etc.)

#### 8. **KEY TERMS**: Summarize important contract terms (payment terms, contract duration, notice periods, etc.)

-------------------

Remember to:
- Use plain language (8th-grade reading level)
- Cite specific sections for every claim
- Provide real-world examples where helpful
- End with the legal disclaimer

Analyze this document now."""
        
        # Run the agent with the thread to maintain conversation context
        try:
            response = await self.agent.run(analysis_prompt, thread=self.thread)
            
            return {
                "success": True,
                "analysis": response,
                "document_info": {
                    "file_type": doc_result.get("file_type"),
                    "num_pages": doc_result.get("num_pages"),
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error during analysis: {str(e)}"
            }
    
    async def ask_question(self, question: str) -> str:
        """
        Ask a follow-up question about the document.
        Uses the same thread to maintain conversation context from analyze_document().
        
        Args:
            question: The user's question
        
        Returns:
            Response string
        """
        if self.thread is None:
            return "I don't have a document loaded yet. Please upload and analyze a document first."
        
        # Simply pass the question - the thread maintains full conversation history
        # including the original document text from analyze_document()
        try:
            response = await self.agent.run(question, thread=self.thread)
            return response
        except Exception as e:
            return f"Error processing question: {str(e)}"
    
    async def chat(self, message: str, new_thread: bool = False) -> str:
        """
        General chat interface for the agent.
        Uses the current thread if available, otherwise creates a new one.
        
        Args:
            message: User message
            new_thread: If True, creates a new thread (starts fresh conversation)
        
        Returns:
            Agent response
        """
        try:
            # Create new thread if requested or if one doesn't exist
            if new_thread or self.thread is None:
                if new_thread:
                    logger.info("Starting new chat thread (refresh requested)")
                else:
                    logger.info("Creating initial chat thread")
                self.thread = self.agent.get_new_thread()
            
            logger.info(f"Processing chat message: {message[:50]}...")
            response = await self.agent.run(message, thread=self.thread)
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def reset_conversation(self):
        """
        Reset the conversation thread.
        Useful when starting analysis of a new document.
        """
        self.thread = self.agent.get_new_thread()
