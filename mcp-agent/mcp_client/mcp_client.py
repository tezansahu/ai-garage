import os
import json
import asyncio
import argparse
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import utils
from dotenv import load_dotenv
import litellm

def parse_args():
    parser = argparse.ArgumentParser(description="MCP Client")
    parser.add_argument(
        "--server",
        required=True,
        help="MCP Server from among the available servers (currently only 'financial_data' server)"
    )
    parser.add_argument(
        "--llm-provider",
        default="azure",
        help="LLM provider to use (default: 'azure')"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model to use (default: 'gpt-4o')"
    )
    return parser.parse_args()

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self, llm_provider: str = "azure", model: str = "gpt-4o", use_python_executable_from_venv: bool = True):
        
        self.supported_llm_providers_env_vars = {
            "openai": ["OPENAI_API_KEY"],
            "azure": [
                "AZURE_API_KEY",
                "AZURE_API_BASE",
                "AZURE_API_VERSION",
            ],
            "ollama": []  # Add required env vars for ollama if any
        }

        self.llm_provider = llm_provider
        self.model = model
        self.__check_llm_provider_validity()

        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        self.python_executable = os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe") if use_python_executable_from_venv else "python"


    def __check_llm_provider_validity(self):
        if self.llm_provider not in self.supported_llm_providers_env_vars.keys():
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        required_env_vars = self.supported_llm_providers_env_vars[self.llm_provider]
        for var in required_env_vars:
            if not os.getenv(var):
                raise EnvironmentError(f"Environment variable {var} is required for {self.llm_provider} but not set.")

    def __get_base_url(self) -> str:
        if self.llm_provider == "ollama":
            return "http://localhost:11434"
        else:
            return None
        
    def __stringify_tool_invocations(self, tool_invocations):
        result = ""
        for invocation in tool_invocations:
            result += f"**Tool {invocation['tool']} called with args {invocation['args']}**\n"
            result += f"Result: {invocation['result'].content}\n\n"
        return result
            
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = self.python_executable if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using LLM and available tools"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that can answer user's questions & share your insights. You also have access to a range of tools.Use the relevant tool(s) only when necessary, based on the user's queries. Whenever asked for recommendations & suggestions, use available data to form a solid opinion & provide your insights based that. If you don't know the answer or do not have enough data, refrain from answering."
            },
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [utils.convert_mcp_tool_to_litellm_tool(tool) for tool in response.tools]

        # Initial LLM call
        llm_response = litellm.completion(
            model = "{0}/{1}".format(self.llm_provider, self.model),
            messages=messages,
            tools=available_tools,
            tool_choice="auto",
            api_base=self.__get_base_url(),
        )

        response = llm_response.choices[0].message
        while response.tool_calls:
            tool_invocations = []
            for tool in response.tool_calls:
                tool_name = tool.function.name
                tool_args = json.loads(tool.function.arguments)

                # Execute tool call
                print(f"[Internal] Calling tool: {tool_name} with args: {tool_args}")
                result = await self.session.call_tool(tool_name, tool_args)
                tool_invocations.append({"tool": tool_name, "args": tool_args, "result": result})

            # Continue conversation with tool results
            if response.content:
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
            messages.append({
                "role": "user", 
                "content": self.__stringify_tool_invocations(tool_invocations)
            })

            # Get next response from LLM
            llm_response = litellm.completion(
                model = "{0}/{1}".format(self.llm_provider, self.model), 
                messages=messages,
                tools=available_tools,
                tool_choice="auto",
                api_base=self.__get_base_url(),
            )

            response = llm_response.choices[0].message

        # Outside the while loop
        return response.content
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Agent Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    args = parse_args()
    server_path = utils.get_server_path_for_available_servers(args.server)
        
    client = MCPClient(args.llm_provider, args.model)
    try:
        await client.connect_to_server(server_path)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys

    asyncio.run(main())