"""
Streamlit UI for Contract Clarity Agent.
Provides file upload, chat interface, and analysis display.
"""

import streamlit as st
import asyncio
import os
from pathlib import Path
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import agent (will be imported after installation)
try:
    from src.agent import ContractClarityAgent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    st.error("⚠️ Agent framework not installed. Please run: uv pip install -e . --prerelease=allow")


# Page configuration
st.set_page_config(
    page_title="Contract Clarity Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .risk-high {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .risk-medium {
        background-color: #fff8e1;
        border-left: 5px solid #ff9800;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .risk-low {
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .disclaimer {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        padding: 1rem;
        border-radius: 5px;
        margin: 2rem 0;
        font-size: 0.9rem;
        color: #555;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "uploaded_file_path" not in st.session_state:
        st.session_state.uploaded_file_path = None
    if "new_thread_requested" not in st.session_state:
        st.session_state.new_thread_requested = False


def get_agent():
    """Get or create agent instance."""
    if st.session_state.agent is None and AGENT_AVAILABLE:
        try:
            st.session_state.agent = ContractClarityAgent()
        except Exception as e:
            st.error(f"Error initializing agent: {str(e)}")
            st.info("Please check your .env file and ensure all required variables are set.")
    return st.session_state.agent


def display_disclaimer():
    """Display legal disclaimer."""
    st.markdown("""
    <div class="disclaimer">
        <strong>⚠️ Important Disclaimer</strong><br>
        This is not legal advice. The analysis provided by Contract Clarity Agent is for informational purposes only 
        and should not be considered a substitute for professional legal counsel. For specific legal guidance, 
        consult a licensed attorney. Analysis is based on general patterns and may not reflect jurisdiction-specific 
        requirements. Risk assessments are informational only; ultimate decisions rest with you and your advisors.
    </div>
    """, unsafe_allow_html=True)


def display_header():
    """Display page header."""
    st.markdown('<div class="main-header">📄 Contract Clarity Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Understand legal documents with AI-powered analysis</div>',
        unsafe_allow_html=True
    )
    display_disclaimer()


def display_example_use_cases():
    """Display example use cases."""
    st.markdown("### 💡 What can I help you with?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **Employment Agreements**
        - Review job offers
        - Understand IP clauses
        - Evaluate non-compete terms
        """)
    
    with col2:
        st.info("""
        **Vendor Contracts**
        - Assess payment terms
        - Identify liability risks
        - Review termination rights
        """)
    
    with col3:
        st.info("""
        **NDAs & Policies**
        - Understand confidentiality
        - Review compliance docs
        - Clarify obligations
        """)


def save_uploaded_file(uploaded_file) -> str:
    """
    Save uploaded file to temp directory.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
    
    Returns:
        Path to saved file
    """
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Save file
    file_path = upload_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(file_path)


def delete_uploaded_file(file_path: str):
    """
    Delete an uploaded file from the uploads directory.
    
    Args:
        file_path: Path to the file to delete
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")


async def analyze_document_async(agent, file_path: str):
    """Async wrapper for document analysis."""
    result = await agent.analyze_document(file_path)
    
    # Delete the file after processing to maintain privacy
    delete_uploaded_file(file_path)
    
    return result


def display_analysis(analysis_text: str):
    """
    Display analysis results with formatting.
    
    Args:
        analysis_text: The analysis text from the agent
    """
    st.markdown("### 📊 Analysis Results")
    
    # Display the analysis
    # The agent returns formatted text, so we display it directly
    st.markdown(analysis_text)


def main():
    """Main application logic."""
    init_session_state()
    display_header()
    
    if not AGENT_AVAILABLE:
        st.warning("Please install dependencies first. See README.md for setup instructions.")
        return
    
    # Sidebar
    with st.sidebar:
        if st.button("🔄 New Chat", help="Start a fresh conversation (clears chat history and document)"):
            # Delete uploaded file if exists
            if st.session_state.uploaded_file_path:
                delete_uploaded_file(st.session_state.uploaded_file_path)
            
            # Reset agent thread to flush document from memory
            agent = st.session_state.agent
            if agent:
                agent.reset_conversation()
            
            # Clear session state
            st.session_state.messages = []
            st.session_state.analysis_result = None
            st.session_state.uploaded_file_path = None
            st.session_state.new_thread_requested = True
            
            st.success("✅ Chat reset! Starting fresh conversation.")
            st.rerun()
        
        st.markdown("---")

        st.markdown("### 📤 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "doc", "jpg", "jpeg", "png"],
            help="Upload a contract, agreement, or policy document (PDF, DOCX, or image)"
        )
        
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.caption(f"Size: {file_size_mb:.2f} MB")
            
            if st.button("🔍 Analyze Document", type="primary"):
                with st.spinner("Analyzing document... This may take 30-60 seconds."):
                    try:
                        # Save file
                        file_path = save_uploaded_file(uploaded_file)
                        st.session_state.uploaded_file_path = file_path
                        
                        # Get agent
                        agent = get_agent()
                        if agent:
                            # Run analysis
                            result = asyncio.run(analyze_document_async(agent, file_path))
                            
                            if result.get("success"):
                                st.session_state.analysis_result = result["analysis"]
                                st.success("✅ Analysis complete!")
                                st.rerun()
                            else:
                                st.error(f"Error: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error analyzing document: {str(e)}")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption("""
        Contract Clarity Agent helps you understand legal documents by:
        - Providing plain-language summaries
        - Identifying risks and concerns
        - Explaining complex clauses
        - Suggesting actionable next steps
        """)
        
        st.markdown("### 🔒 Privacy")
        st.caption("""
        Your documents are processed securely and deleted immediately after analysis.
        Document content is only retained in the active conversation thread.
        Click "New Chat" to clear all data and start fresh.
        """)
    
    # Main content area
    if st.session_state.analysis_result:
        # Display analysis
        display_analysis(st.session_state.analysis_result)
        
        st.markdown("---")
        st.markdown("### 💬 Ask Follow-up Questions")
        
        # Chat interface
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input for follow-up questions
        if prompt := st.chat_input("Ask a question about the document..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get agent response
            agent = get_agent()
            if agent:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            response = asyncio.run(agent.ask_question(prompt))
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        # No document uploaded - show general chat interface
        st.markdown("### 💬 Chat with Contract Clarity Agent")
        st.write("Ask me anything about contracts, legal documents, or upload a document to analyze!")
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input for general conversation
        if prompt := st.chat_input("Ask about contracts, analyze a URL, or get legal guidance..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get agent response
            agent = get_agent()
            if agent:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            # Check if new thread was requested (refresh)
                            new_thread = st.session_state.get("new_thread_requested", False)
                            
                            # Use general chat method which maintains thread continuity
                            response = asyncio.run(agent.chat(prompt, new_thread=new_thread))
                            
                            # Reset the flag after first message
                            if new_thread:
                                st.session_state.new_thread_requested = False
                            
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Only show landing page content if no messages yet
        if len(st.session_state.messages) == 0:
            st.markdown("---")
            
            # Show example use cases
            display_example_use_cases()
            
            st.markdown("---")
            st.markdown("### 🚀 Get Started")
            st.write("**Option 1:** Upload a document using the sidebar to get a detailed analysis.")
            st.write("**Option 2:** Ask me questions in the chat above about contracts or legal documents.")
            
            # Example scenarios
            with st.expander("📖 Example: Employment Agreement Analysis"):
                st.markdown("""
                **What you'll get:**
                - Executive summary of key terms
                - Risk assessment of IP assignment clauses
                - Evaluation of non-compete restrictions
                - Analysis of termination and severance terms
                - Recommendations for negotiation points
                """)
            
            with st.expander("📖 Example: Vendor Contract Review"):
                st.markdown("""
                **What you'll get:**
                - Assessment of payment terms and penalties
                - Liability and indemnification analysis
                - Termination rights evaluation
                - Identification of auto-renewal clauses
                - Red flags for unfavorable terms
                """)
            
            with st.expander("💬 Example: General Chat Questions"):
                st.markdown("""
                **Try asking:**
                - "What should I look for in an employment contract?"
                - "Can you analyze this URL: [contract-url]?"
                - "What's the difference between an NDA and a non-compete?"
                - "Explain indemnification in simple terms"
                - "What are standard payment terms for vendor contracts?"
                """)


if __name__ == "__main__":
    main()
