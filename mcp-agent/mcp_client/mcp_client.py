import os
import json
import asyncio
import argparse
from typing import Optional, Dict, List, Any
from contextlib import AsyncExitStack
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
import colorama

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import utils
from dotenv import load_dotenv
import litellm

# Initialize colorama for Windows support and create Rich console
colorama.init()
console = Console()

# Load environment variables from .env
load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MCP Client")
    parser.add_argument(
        "--server",
        required=True,
        help="MCP Server from among the available servers (currently only 'financial_data' server)"
    )
    parser.add_argument(
        "--llm-provider",
        default="azure",
        choices=["azure", "openai", "ollama"],
        help="LLM provider to use (default: 'azure')"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model to use (default: 'gpt-4o')"
    )
    return parser.parse_args()


class MCPClient:
    """Client for interacting with MCP servers using LLMs."""

    PROVIDER_ENV_REQUIREMENTS = {
        "openai": ["OPENAI_API_KEY"],
        "azure": [
            "AZURE_API_KEY",
            "AZURE_API_BASE",
            "AZURE_API_VERSION",
        ],
        "ollama": []  # Add required env vars for ollama if any
    }

    SYSTEM_PROMPT = (
        "You are a helpful AI assistant that can answer user's questions & share your insights. "
        "You also have access to a range of tools. Use the relevant tool(s) only when necessary, "
        "based on the user's queries. Whenever asked for recommendations & suggestions, use available "
        "data to form a solid opinion & provide your insights based that. If you don't know the answer "
        "or do not have enough data, refrain from answering."
    )
    
    def __init__(self, llm_provider: str = "azure", model: str = "gpt-4o", use_python_executable_from_venv: bool = True):
        """Initialize MCP client.
        
        Args:
            llm_provider: LLM provider to use (azure, openai, ollama)
            model: Model name to use
            use_python_executable_from_venv: Whether to use Python executable from virtual environment
        """
        self.llm_provider = llm_provider
        self.model = model
        self._validate_provider_config()

        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Set up Python executable path
        venv_path = Path(__file__).parent.parent / ".venv" / "Scripts" / "python.exe"
        self.python_executable = str(venv_path) if use_python_executable_from_venv else "python"

    def _validate_provider_config(self) -> None:
        """Validate that the LLM provider is supported and required env vars are set."""
        if self.llm_provider not in self.PROVIDER_ENV_REQUIREMENTS:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        missing_vars = []
        for var in self.PROVIDER_ENV_REQUIREMENTS[self.llm_provider]:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            raise EnvironmentError(
                f"The following environment variables are required for {self.llm_provider} but not set: "
                f"{', '.join(missing_vars)}"
            )

    def _get_base_url(self) -> Optional[str]:
        """Get base URL for the LLM provider."""
        if self.llm_provider == "ollama":
            return "http://localhost:11434"
        return None
        
    def _format_tool_invocations(self, tool_invocations: List[Dict[str, Any]]) -> str:
        """Format tool invocations for LLM messages."""
        result = []
        for invocation in tool_invocations:
            result.append(f"**Tool {invocation['tool']} called with args {invocation['args']}**")
            result.append(f"Result: {invocation['result'].content}")
            result.append("")  # Empty line for spacing
        return "\n".join(result)
            
    async def connect_to_server(self, server_script_path: str) -> None:
        """Connect to an MCP server and display available tools.
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Connecting to server..."),
                transient=True,
            ) as progress:
                task = progress.add_task("", total=None)
                # Validate script type
                if server_script_path.endswith('.py'):
                    command = self.python_executable
                elif server_script_path.endswith('.js'):
                    command = "node"
                else:
                    raise ValueError("Server script must be a .py or .js file")
                    
                # Setup server connection
                server_params = StdioServerParameters(
                    command=command,
                    args=[server_script_path],
                    env=None
                )
                
                # Initialize connection
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                self.stdio, self.write = stdio_transport
                self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
                await self.session.initialize()

                # Get available tools
                response = await self.session.list_tools()
                tools = response.tools
            
            # Display available tools
            self._display_connection_success(tools)
        except Exception as e:
            console.print(f"[bold red]Connection failed:[/] {str(e)}")
            raise

    def _display_connection_success(self, tools: List[Any]) -> None:
        """Display connection success message and available tools."""
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Available Tools")
        for tool in tools:
            table.add_row(tool.name)
        
        console.print()
        console.print(Panel.fit(
            "🚀 [bold green]Connection Successful![/]", 
            title="MCP Server", 
            border_style="green"
        ))
        console.print(table)

    async def process_query(self, query: str) -> str:
        """Process a query using LLM and available tools.
        
        Args:
            query: User's query string
            
        Returns:
            The final response from the LLM
        """
        if not self.session:
            raise RuntimeError("Not connected to a server. Call connect_to_server() first.")
            
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]

        # Get available tools
        response = await self.session.list_tools()
        available_tools = [utils.convert_mcp_tool_to_litellm_tool(tool) for tool in response.tools]

        # Process the query with tools
        return await self._process_with_tools(messages, available_tools)

    async def _process_with_tools(self, messages: List[Dict[str, Any]], available_tools: List[Dict[str, Any]]) -> str:
        """Process messages with tools until no more tool calls are needed.
        
        Args:
            messages: Conversation history
            available_tools: List of available tools
            
        Returns:
            Final LLM response
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]LLM is thinking..."),
            transient=True,
        ) as progress:
            task = progress.add_task("", total=None)
            # Initial LLM Call
            llm_response = await self._get_llm_response(messages, available_tools)
        response = llm_response.choices[0].message

        # Continue processing as long as there are tool calls
        while response.tool_calls:
            tool_invocations = await self._execute_tool_calls(response.tool_calls)
            
            # Update conversation with results
            if response.content:
                messages.append({"role": "assistant", "content": response.content})
                
            messages.append({
                "role": "user", 
                "content": self._format_tool_invocations(tool_invocations)
            })

            with Progress(
                SpinnerColumn(),
                TextColumn("[bold cyan]LLM is thinking..."),
                transient=True,
            ) as progress:
                task = progress.add_task("", total=None)
                # Get next response from LLM
                llm_response = await self._get_llm_response(messages, available_tools)

            response = llm_response.choices[0].message

        # Return the final response content
        return response.content
    
    async def _get_llm_response(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Any:
        """Get response from LLM.
        
        Args:
            messages: Conversation history
            tools: Available tools
            
        Returns:
            LLM response object
        """
        try:
            # Use asyncio.to_thread to run the synchronous litellm.completion in a separate thread
            return await asyncio.to_thread(
                litellm.completion,
                model=f"{self.llm_provider}/{self.model}",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                api_base=self._get_base_url(),
            )
        except Exception as e:
            console.print(f"[bold red]LLM request failed:[/] {str(e)}")
            raise

    async def _execute_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results.
        
        Args:
            tool_calls: List of tool calls from LLM response
            
        Returns:
            List of tool invocation results
        """
        tool_invocations = []
        
        for tool in tool_calls:
            tool_name = tool.function.name
            tool_args = json.loads(tool.function.arguments)

            # Display tool usage
            console.print(f"[dim cyan]Using tool:[/] [bold yellow]{tool_name}[/] [dim cyan]with args:[/] [bold yellow]{tool_args}[/]")

            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn(f"[cyan]Processing with {tool_name}..."),
                    transient=True,
                ) as progress:
                    task = progress.add_task("", total=None)
                    # Execute tool call without async with Progress
                    result = await self.session.call_tool(tool_name, tool_args)
                tool_invocations.append({"tool": tool_name, "args": tool_args, "result": result})
            except Exception as e:
                console.print(f"[bold red]Tool execution failed:[/] {str(e)}")
                tool_invocations.append({
                    "tool": tool_name, 
                    "args": tool_args, 
                    "result": {"content": f"Error: {str(e)}"}
                })
            
        return tool_invocations
    
    async def chat_loop(self) -> None:
        """Run an interactive chat loop."""
        console.print(Panel.fit(
            "✨ [bold green]MCP Agent Started![/]\n"
            "[cyan]Type your queries or 'quit' to exit.[/]", 
            border_style="magenta"
        ))
        
        while True:
            try:
                console.print()
                query = console.input("[bold blue]You: [/]").strip()
                
                if query.lower() in ('quit', 'exit', 'bye'):
                    console.print("[bold yellow]Goodbye! 👋[/]")
                    break
                
                if not query:
                    continue
                    
                response = await self.process_query(query)
                
                # Format the response as markdown
                md = Markdown(response)
                console.print()
                console.print(Panel(md, title="🤖 Assistant", border_style="green"))
                    
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Interrupted. Exiting...[/]")
                break
            except Exception as e:
                console.print(Panel(f"[bold red]Error:[/] {str(e)}", border_style="red"))

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.exit_stack.aclose()


async def main() -> int:
    """Main entry point for the MCP client.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        args = parse_args()
        server_path = utils.get_server_path_for_available_servers(args.server)

        # Show welcome banner
        console.print()
        console.rule("[bold blue]MCP Agent - AI Garage[/]")
        console.print()

        client = MCPClient(args.llm_provider, args.model)
        try:
            await client.connect_to_server(server_path)
            await client.chat_loop()
        finally:
            await client.cleanup()
            console.print()
            console.rule("[bold blue]Session Ended[/]")
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/] {str(e)}")
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))