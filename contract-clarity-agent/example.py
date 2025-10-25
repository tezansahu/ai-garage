"""
Example script for using Contract Clarity Agent programmatically.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from src.agent import ContractClarityAgent

# Load environment variables
load_dotenv()

# Enable logging to see agent's intermediate steps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Main example function."""
    print("🚀 Contract Clarity Agent - Example Usage\n")
    
    # Initialize agent
    print("Initializing agent...")
    agent = ContractClarityAgent()
    
    # Example 1: Analyze a document
    print("\n📄 Example 1: Analyzing a document")
    print("-" * 50)
    
    # Replace with your actual document path
    document_path = "uploads/product_space_contract.pdf"
    
    if os.path.exists(document_path):
        print(f"Analyzing: {document_path}")
        result = await agent.analyze_document(document_path)
        
        if result.get("success"):
            print("\n✅ Analysis Complete!")
            print("\n" + "=" * 50)
            print(result["analysis"])
            print("=" * 50)
            
            # Example 2: Ask follow-up questions
            print("\n💬 Example 2: Asking follow-up questions")
            print("-" * 50)
            
            questions = [
                "What are the payment terms?",
                "Can I terminate this contract early?",
                "What are the confidentiality obligations?"
            ]
            
            for question in questions:
                print(f"\n❓ Question: {question}")
                response = await agent.ask_question(question)
                print(f"💡 Answer: {response}\n")
        else:
            print(f"❌ Error: {result.get('error')}")
    else:
        print(f"⚠️  File not found: {document_path}")
        print("\nTo use this example:")
        print("1. Place a contract PDF in the project directory")
        print("2. Update the 'document_path' variable above")
        print("3. Run: python example.py")
    
    # Example 3: General chat (URL analysis)
    print("\n🌐 Example 3: Analyzing a contract from URL")
    print("-" * 50)
    
    print("\n❓ Request: Please analyze the contract at this URL: https://substack.com/ccpa")
    
    response = await agent.chat(
        "Can you extract and analyze a contract from this URL: https://substack.com/ccpa",
        new_thread=True
    )
    print(f"💡 Response: {response}\n")
    
    # Example 4: General chat
    print("\n💬 Example 4: General chat about contracts")
    print("-" * 50)
    
    print("\n❓ Question: What should I look for in an employment contract?")
    
    response = await agent.chat(
        "What are the most important things to look for in an employment contract?",
        new_thread=True
    )
    print(f"💡 Answer: {response}")


if __name__ == "__main__":
    asyncio.run(main())
