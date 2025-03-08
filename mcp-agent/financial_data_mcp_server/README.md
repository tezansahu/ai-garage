# MCP Server Based on [Financial Modeling Prep API](https://site.financialmodelingprep.com/developer/docs/stable)

## What is Financial Modeling Prep?
Financial Modeling Prep (FMP) is a source for reliable and accurate Stock Market API and Financial Data API.

## What is "this" MCP Server?
This is a server built using [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) that exposes the following FMP APIs for use by LLMs using the Model Context Protocol (MCP):

| API Name                  | Description                                           |
|---------------------------|-------------------------------------------------------|
| Company Profile API       | Get company profile data for a given stock symbol.    |
| Balance Sheet API         | Get balance sheet data for a given stock symbol.      |
| Cash Flow Statement API   | Get cash flow statement data for a given stock symbol.|
| Key Metrics API           | Get key financial metrics for a given stock symbol.   |
| Financial Ratios API      | Get financial ratios for a given stock symbol.        |
| Stock Quote API           | Get real-time stock quote for a given stock symbol.   |

## How (easily) was this server built?

This server was spun up in less than 15 minutes using an LLM by following the steps similar to those mentioned in [this tutorial](https://modelcontextprotocol.info/docs/tutorials/building-mcp-with-llms/).

### Steps

1. Used [GitHub to PlainText Converter](https://stephenturner.github.io/repo2txt/) to convert the `docs/` folder of the [MCP documentation repo](https://github.com/modelcontextprotocol/docs/tree/main) into a TXT file & downloaded it
   > This was needed because the `https://modelcontextprotocol.info/llms-full.txt` link mentioned in the tutorial didn't work

2. Downloaded the README file from [MCP Python SDK repo](https://github.com/modelcontextprotocol/python-sdk)

3. Copied the information for the above mentioned APIs from the [FMP API documentation]() to create [this TXT file](./financial-data-api.txt)

4. Uploaded all the 3 files to [Kimi AI](https://kimi.ai/) & prompted it to `Build an MCP server using python SDK that exposes the various endpoints of "Financial Data API" as tools.`
   > [Here is the conversation with Kimi to generate this MCP server](https://kimi.ai/share/cv64g7c06ope1ppcohtg)

The code generated, used as is, works perfectly.

## How to run this server?

### Prerequisites

- Copy the `.env.example` file into `.env`
- Create an account on [FMP](https://site.financialmodelingprep.com/)
- Copy your API Key from your dashboard & paste it against the `FINANCIAL_MODELING_PREP_API_KEY` key in the `.env` file
- Ensure that you have followed the steps mentioned in the [project README]() to install `uv` & `mcp` Python SDK

### Usage

- To **test** the MCP server, run `mcp dev mcp_server.py`
    - MCP Server should start running at `http://localhost:3000`
    - The MCP Inspector should start at `http://localhost:5173` - go here & test your tools

- To **run** the MCP server for deployment, run `python mcp_server.py`