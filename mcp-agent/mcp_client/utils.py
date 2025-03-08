from typing import Dict

def convert_mcp_tool_to_litellm_tool(mcp_tool: Dict):
    """
    Convert an MCP tool to an LiteLLM (OpenAI) tool format.
    
    Args:
        mcp_tool (dict): The Anthropic tool to convert.
        
    Returns:
        dict: The converted OpenAI tool (understood by LiteLLM for any LLM).
    """

    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema,
        }
    }


def get_server_path_for_available_servers(server: str):
    """
    Get the server path for available servers.
    
    Returns:
        List(str): The server path for available servers.
    """
    # Assuming the server path is stored in an environment variable

    available_servers = {
        "financial_data": "../financial_data_mcp_server/mcp_server.py",
    }

    if server in available_servers:
        return available_servers[server]
    else:
        raise ValueError(f"Server {server} not found in available servers.")