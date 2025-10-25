"""
Document processing tools for Contract Clarity Agent.
Handles PDF/DOCX parsing with Docling and web content extraction with Firecrawl.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import io

try:
    from docling.document_converter import DocumentConverter
except ImportError:
    DocumentConverter = None

try:
    from firecrawl import Firecrawl
except ImportError:
    Firecrawl = None

from PIL import Image
import base64


class DocumentProcessor:
    """Handles document parsing and text extraction."""
    
    def __init__(self):
        """Initialize document processor."""
        self.converter = None
        if DocumentConverter:
            try:
                # Initialize Docling converter with default options
                # The converter automatically handles OCR and table structure
                self.converter = DocumentConverter()
            except Exception as e:
                print(f"Warning: Could not initialize Docling converter: {e}")
    
    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Process a PDF file and extract text with structure.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not self.converter:
            return {
                "text": "Error: Docling is not properly installed",
                "error": "Docling dependencies missing"
            }
        
        try:
            # Convert document
            result = self.converter.convert(file_path)
            
            # Extract text with structure preservation
            markdown_text = result.document.export_to_markdown()
            
            return {
                "text": markdown_text,
                "num_pages": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
                "file_type": "pdf",
                "success": True
            }
        except Exception as e:
            return {
                "text": "",
                "error": f"Error processing PDF: {str(e)}",
                "success": False
            }
    
    def process_docx(self, file_path: str) -> Dict[str, Any]:
        """
        Process a DOCX file and extract text.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not self.converter:
            return {
                "text": "Error: Docling is not properly installed",
                "error": "Docling dependencies missing"
            }
        
        try:
            # Convert document
            result = self.converter.convert(file_path)
            
            # Extract text as markdown
            markdown_text = result.document.export_to_markdown()
            
            return {
                "text": markdown_text,
                "file_type": "docx",
                "success": True
            }
        except Exception as e:
            return {
                "text": "",
                "error": f"Error processing DOCX: {str(e)}",
                "success": False
            }
    
    def process_image(self, file_path: str) -> Dict[str, Any]:
        """
        Process an image file (OCR will be handled by the LLM vision capabilities).
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary containing image data for LLM processing
        """
        try:
            # Open and validate image
            img = Image.open(file_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get image info
            return {
                "image_path": file_path,
                "width": img.width,
                "height": img.height,
                "file_type": "image",
                "success": True,
                "text": "[Image will be processed by vision-enabled LLM]"
            }
        except Exception as e:
            return {
                "text": "",
                "error": f"Error processing image: {str(e)}",
                "success": False
            }
    
    def process_document(self, file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a document based on its type.
        
        Args:
            file_path: Path to the document
            file_type: Optional file type hint (pdf, docx, image)
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        # Determine file type if not provided
        if not file_type:
            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.pdf':
                file_type = 'pdf'
            elif file_ext in ['.docx', '.doc']:
                file_type = 'docx'
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                file_type = 'image'
            else:
                return {
                    "text": "",
                    "error": f"Unsupported file type: {file_ext}",
                    "success": False
                }
        
        # Process based on type
        if file_type == 'pdf':
            return self.process_pdf(file_path)
        elif file_type == 'docx':
            return self.process_docx(file_path)
        elif file_type == 'image':
            return self.process_image(file_path)
        else:
            return {
                "text": "",
                "error": f"Unsupported file type: {file_type}",
                "success": False
            }


class WebContentExtractor:
    """Handles web content extraction using Firecrawl."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize web content extractor.
        
        Args:
            api_key: Firecrawl API key (if not provided, will use env var)
        """
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.client = None
        
        if self.api_key and Firecrawl:
            try:
                self.client = Firecrawl(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Firecrawl client: {e}")
    
    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a web URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary containing extracted content
        """
        if not self.client:
            return {
                "text": "",
                "error": "Firecrawl client not initialized. Check API key.",
                "success": False
            }
        
        try:
            # Scrape the URL - returns a Document object (Pydantic model), not a dict
            result = self.client.scrape(url, formats=['markdown', 'html'], remove_base64_images=True)
            
            # Access Document object properties directly
            markdown_content = result.markdown or result.html or ""
            title = result.metadata.title if result.metadata else ""
            
            return {
                "text": markdown_content,
                "url": url,
                "title": title,
                "file_type": "web",
                "success": True
            }
        except Exception as e:
            print(f"Error extracting web content: {e}")
            return {
                "text": "",
                "error": f"Error extracting web content: {str(e)}",
                "success": False
            }
