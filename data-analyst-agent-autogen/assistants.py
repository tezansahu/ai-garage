from autogen_core import CancellationToken

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Response
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage, TextMessage, ToolCallRequestEvent
from autogen_agentchat.teams import RoundRobinGroupChat

from autogen_ext.models.azure import AzureAIChatCompletionClient
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool

from azure.core.credentials import AzureKeyCredential

from dotenv import load_dotenv
import os
import re
import streamlit as st
from typing import AsyncGenerator, Sequence



class TrackableAssistantAgent(AssistantAgent):
    """
    A specialized assistant agent that tracks and displays responses on Streamlit 
    while processing messages. This class extends the functionality of the 
    `AssistantAgent` by adding methods to handle and visualize responses, including 
    tool call requests, text messages, and responses containing image references.
    Methods:
        on_messages_stream(messages, cancellation_token):
            Asynchronously processes a stream of messages, tracks responses on 
            Streamlit, and yields each message (modified or unmodified).
        _track_response_on_streamlit(msg):
            Tracks and displays the response on Streamlit based on the type of 
            message (e.g., tool call requests, text messages, or responses).
        _handle_text_message(msg):
            Handles text messages by formatting the content, appending it to 
            Streamlit's session state, and displaying it in the chat interface. 
            Also processes image references if the message is from the 
            "DataAnalystAgent".
        _image_files_in_response(response):
            Extracts image file paths from a response string using regex matching. 
            Assumes image file paths are in the format '<file_name>.png'.
    """
    async def on_messages_stream(
        self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[AgentEvent | ChatMessage | Response, None]:
         async for msg in super().on_messages_stream(
            messages=messages,
            cancellation_token=cancellation_token,
         ):
            self._track_response_on_streamlit(msg)
            
            # Yield the item (modified or unmodified)
            yield msg

    def _track_response_on_streamlit(self, msg):
        if isinstance(msg, ToolCallRequestEvent):
            content = f"**[{msg.source}] Tool calls requested:** " + ", ".join(f"{tool.name}" for tool in msg.content)
            st.session_state["messages"].append(
                {"role": "assistant", "content": content}
            )
            with st.chat_message("assistant", avatar="🛠️"):
                st.markdown(content)
        
        elif (isinstance(msg, TextMessage)) and msg.source != "user":
            self._handle_text_message(msg)

        elif isinstance(msg, Response):
            if isinstance(msg.chat_message, TextMessage):
                self._handle_text_message(msg.chat_message)
        else:
            pass

    def _handle_text_message(self, msg: TextMessage) -> None:
        msg_content = f"**[{msg.source}]**\n{msg.content.replace('TERMINATE', '').strip()}"
        st.session_state["messages"].append(
            {"role": "assistant", "content": msg_content}
        )
        if msg.source == "DataAnalystAgent":
            image_files = self._image_files_in_response(msg_content)
            with st.chat_message("assistant"):
                st.markdown(msg_content)
                for image_file in image_files:
                    image_path = os.path.join("code_executor", image_file)
                    if os.path.exists(image_path):
                        st.image(image_path, caption=image_file)
                    # else:
                        # st.error(f"Image file {image_file} not found.")
        else:
            with st.chat_message("assistant"):
                st.markdown(msg_content)


    def _image_files_in_response(self, response: str) -> list[str]:
        """
        Extracts image file paths from the response string (using regex matching)
        Assumes that image file paths are in the format '<file_name>.png
        """
        pattern = r'([a-zA-Z0-9_\-]+\.png)'
        matches = re.findall(pattern, response)
        return list(set(matches))
    
def get_data_analyst_team(gh_pat: str, model: str) -> RoundRobinGroupChat:
    """
    Creates and returns a RoundRobinGroupChat instance consisting of a data analyst agent 
    and a code executor agent, designed to collaboratively analyze datasets, generate insights, 
    create visualizations, and execute Python code.
    
    Steps:
    1. Initializes an AzureAIChatCompletionClient with the specified model, endpoint, and credentials.
    2. Creates a PythonCodeExecutionTool for executing Python code in a local command-line environment.
    3. Configures a `TrackableAssistantAgent` for data analysis (`DataAnalystAgent`) with detailed 
       system instructions for analyzing datasets, generating visualizations, and creating reports.
    4. Configures a `TrackableAssistantAgent` for code execution (`CodeExecutorAgent`) with system 
       instructions for executing Python code and handling errors.
    5. Sets up a termination condition based on either a specific keyword ("TERMINATE") or a maximum 
       number of messages (15).
    6. Combines the agents into a `RoundRobinGroupChat` to enable collaborative interaction.
    
    Args:
        gh_pat (str): GitHub personal access token for authentication.
        model (str): The model name to be used by the AzureAIChatCompletionClient.
    
    Returns:
        RoundRobinGroupChat: A group chat instance with the data analyst agent and code executor agent, 
        along with the defined termination conditions.
    """

    # load_dotenv()
    # Create the Client
    model_client = AzureAIChatCompletionClient(
        # model="gpt-4o-mini",
        model=model,
        endpoint="https://models.inference.ai.azure.com",
        # To authenticate with the model you will need to generate a personal access token (PAT) in your GitHub settings.
        # credential=AzureKeyCredential(os.getenv("GITHUB_TOKEN")),
        credential=AzureKeyCredential(gh_pat),
        model_info={
            "json_output": True,
            "function_calling": True,
            "vision": True,
            "family": "unknown",
        },
    )

    python_code_executor_tool = PythonCodeExecutionTool(
        LocalCommandLineCodeExecutor(work_dir="./code_executor"),
    )

    data_analyst_agent = TrackableAssistantAgent(
        name="DataAnalystAgent",
        description="A data analyst agent that can analyze data, extract insights, create stunning visualizations and generate reports.",
        model_client=model_client,
        system_message="""You are an expert data analyst agent. You can analyze complex datasets, mine interesting insights, create stunning visualizations and generate reports.

        You will be given the path to a dataset to analyse & address the user's query.
        
        ## Guidelines
        - Your first message must be a detailed plan of the steps you will take to analyze the data & address the user's query
        - You must write **correct** & **optimized** Python code to analyze data, extract insights, create visualizations and generate reports
        - Always start your code with all required `import` statements regardless of previous context
        - Always write complete code (NOT just incremental snippets) while iterating on the code
        - Initially, famialiarize yourself with the dataset, its structure & columns 
        - You must visualize the data most appropriatly using the best libraries available
        - Ensure that your visualizations are clear, informative and visually appealing, and **do NOT have any clutter**
        - If you generate any visualizations, you must save them to the local disk strictly in PNG format
        - Given any user query, your first stp must be to plan the steps to be taken to analyze the data
        - In the final response, you must explain the results of your analysis and visualizations in a clear and concise manner
        - Always mention the file names of the generated image files in your response
        - Do **NOT** summarize th findings until you have rceived feedback about correct execution of the code
        - You must end with the word 'TERMINATE' only at the end of your final response, once you are done with your analysis. **Do NOT use the word 'TERMINATE' if you have NOT received any feedback regarding the code execution.**
        """,
    )

    code_executer_agent = TrackableAssistantAgent(
        name="CodeExecutorAgent",
        description="A code executor agent that can execute Python code.",
        tools=[python_code_executor_tool],
        reflect_on_tool_use=True,
        model_client=model_client,
        system_message="""You are a code executor agent. You can execute Python code and return the results.
        
        ## Guidelines
        - You must execute your written Python code whenever possible
        - If the code excution fails, you must debug & provide concise feedback to fix the error(s) in natural language
        - Do NOT use any code snippets in your feedback
        - If things run file, just indicate that the code executed successfully in a concise message with the file name of the generated image files
        """,
    )

    # Terminate the conversation if the tweet scheduler agent mentions "TERMINATE" or if the conversation exceeds 25 messages
    termination_condition = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=15)

    return RoundRobinGroupChat([data_analyst_agent, code_executer_agent], termination_condition)
