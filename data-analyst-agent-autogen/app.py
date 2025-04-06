import os
import re
import sys
from dotenv import load_dotenv
import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.azure import AzureAIChatCompletionClient
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from azure.core.credentials import AzureKeyCredential
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent
from autogen_core import CancellationToken
import streamlit as st
import pandas as pd

def image_files_in_response(response: str) -> list[str]:
    """
    Extracts image file paths from the response string (using regex matching)
    Assumes that image file paths are in the format '<file_name>.png
    """
    
    pattern = r'([a-zA-Z0-9_\-]+\.png)'
    matches = re.findall(pattern, response)
    return matches

def reset_chat():
    """Clear the chat history."""
    if "messages" in st.session_state:
        st.session_state["messages"] = []

async def main():
    load_dotenv()

    # Create the Client
    model_client = AzureAIChatCompletionClient(
        model="gpt-4o-mini",
        endpoint="https://models.inference.ai.azure.com",
        # To authenticate with the model you will need to generate a personal access token (PAT) in your GitHub settings.
        credential=AzureKeyCredential(os.getenv("GITHUB_TOKEN")),
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

    data_analyst_agent = AssistantAgent(
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
        - You must end with the word 'TERMINATE' only at the end of your final response, once you are done with your analysis. **Do NOT use the word 'TERMINATE' if you have NOT received any feedback regarding the code execution.**
        """,
    )

    code_executer_agent = AssistantAgent(
        name="CodeExecutorAgent",
        description="A code executor agent that can execute Python code.",
        tools=[python_code_executor_tool],
        reflect_on_tool_use=True,
        model_client=model_client,
        system_message="""You are a code executor agent. You can execute Python code and return the results.
        
        ## Guidelines
        - You must execute your written Python code whenever possible
        - If the code excution fails, you must debug & provide feedback to fix the error(s)
        - If you try to fix yourself, always write complete code (NOT just incremental snippets)
        """,
    )

    # Terminate the conversation if the tweet scheduler agent mentions "TERMINATE" or if the conversation exceeds 25 messages
    termination_condition = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=15)

    # Streamlit app
    st.set_page_config(page_title="📊 Data Analyst Agent", layout="wide")

    # adding agent object (using a RoundRobinGroupChat, to allow for self looping) to session state to persist across sessions
    # streamlit reruns the script on every user interaction
    if "agent" not in st.session_state:
        st.session_state["agent"] = RoundRobinGroupChat([data_analyst_agent, code_executer_agent], termination_condition)

    # initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    st.title("📊 Data Analyst Agent")
    st.write(
        "This is a data analyst agent (created using AutoGen) that can analyze data, extract insights & create stunning visualizations. "
        "You can upload a CSV or TSV file and ask the agent to analyze it. "
        "The agent will generate Python code to analyze the data, generate visualizations as needed and return the results. "
    )

    st.sidebar.header("Upload Dataset")
    uploaded_file = st.sidebar.file_uploader(
        "Upload a CSV or TSV file", type=["csv", "tsv"]
    )

    # Add reset button to sidebar
    st.sidebar.button("New Chat", on_click=reset_chat, type="secondary", use_container_width=True)

    if uploaded_file:
        reset_chat()
        try:
            local_file_path = os.path.join("code_executor", uploaded_file.name)
            st.write("### Data Preview")
            # Determine file type and read accordingly
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, encoding="utf-8")
                st.dataframe(df)
                df.to_csv(local_file_path, index=False)
            elif uploaded_file.name.endswith(".tsv"):
                df = pd.read_csv(uploaded_file, sep="\t", encoding="utf-8")
                st.dataframe(df)
                df.to_csv(local_file_path, sep="\t", index=False)
            else:
                st.error("Unsupported file format!")
                return

            # displying chat history messages
            for message in st.session_state["messages"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            

            user_query = st.chat_input("Ask a query about the data...")

            if user_query:
                if user_query.strip() == "":
                    st.warning("Please enter a query.")
                else:
                    st.session_state["messages"].append({"role": "user", "content": user_query})
                    with st.chat_message("user"):
                        st.markdown(user_query)

                    user_query += f" (Dataset to be analysed is present at: {uploaded_file.name})"

                    async for msg in st.session_state["agent"].run_stream(
                        task=[TextMessage(content=user_query, source="user")],
                        cancellation_token=CancellationToken(),
                    ):  
                        if isinstance(msg, ToolCallRequestEvent):
                            content = f"**Tool calls requested:** " + ", ".join(f"{tool.name}" for tool in msg.content)
                            st.session_state["messages"].append(
                                {"role": "assistant", "content": content}
                            )
                            with st.chat_message("assistant", avatar="🛠️"):
                                st.markdown(content)
                        
                        elif isinstance(msg, TextMessage) and msg.source != "user":
                            msg_content = msg.content.replace("TERMINATE", "").strip()
                            st.session_state["messages"].append(
                                {"role": "assistant", "content": msg_content}
                            )

                            image_files = image_files_in_response(msg.content)

                            with st.chat_message("assistant"):
                                st.markdown(msg_content)
                                for image_file in image_files:
                                    image_path = os.path.join("code_executor", image_file)
                                    if os.path.exists(image_path):
                                        st.image(image_path, caption=image_file)
                                    # else:
                                        # st.error(f"Image file {image_file} not found.")
                        else:
                            pass
        except Exception as e:
            st.error(f"Error processing file: {e}")

if __name__ == "__main__":
    # Solution for Windows users
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())


# Can you help me understand the trend related to worldwide gross w.r.t languages & country of origins?

