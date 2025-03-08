from mcp.server.fastmcp import FastMCP
import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("Financial Data Server")

# Define the base URL for the Financial Data API
API_BASE_URL = "https://financialmodelingprep.com/stable"
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")

# Helper function to make API requests
def fetch_data(endpoint, params):
    url = f"{API_BASE_URL}/{endpoint}?apikey={API_KEY}"
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# Define tools for each endpoint

@mcp.tool()
def get_company_profile(symbol: str) -> dict:
    """Get company profile data for a given stock symbol."""
    return fetch_data("profile", {"symbol": symbol})

@mcp.tool()
def get_balance_sheet(symbol: str, limit: int = 3, period: str = "FY") -> list:
    """Get balance sheet data for a given stock symbol."""
    return fetch_data("balance-sheet-statement", {"symbol": symbol, "limit": limit, "period": period})

@mcp.tool()
def get_cash_flow(symbol: str, limit: int = 3, period: str = "FY") -> list:
    """Get cash flow statement data for a given stock symbol."""
    return fetch_data("cash-flow-statement", {"symbol": symbol, "limit": limit, "period": period})

@mcp.tool()
def get_key_metrics(symbol: str, limit: int = 3, period: str = "FY") -> list:
    """Get key financial metrics for a given stock symbol."""
    return fetch_data("key-metrics", {"symbol": symbol, "limit": limit, "period": period})

@mcp.tool()
def get_financial_ratios(symbol: str, limit: int = 3, period: str = "FY") -> list:
    """Get financial ratios for a given stock symbol."""
    return fetch_data("ratios", {"symbol": symbol, "limit": limit, "period": period})

@mcp.tool()
def get_stock_quote(symbol: str) -> list:
    """Get real-time stock quote for a given stock symbol."""
    return fetch_data("quote", {"symbol": symbol})

# Run the server
if __name__ == "__main__":
    mcp.run()