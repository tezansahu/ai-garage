import os
import sys
import asyncio

from assistants import get_data_analyst_team
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import streamlit as st
import pandas as pd

async def reset_chat():
    """Clear the chat history."""
    if "messages" in st.session_state:
        st.session_state["messages"] = []
    if "agent" in st.session_state:
        await st.session_state["agent"].reset()

def initialize_data_analyst_agent():
    """Initialize the Data Analyst Agent."""
    # Initialize the agent with the provided GitHub PAT and model selection
    print(f"Creating agent with model {st.session_state['model_selection']}...")
    st.session_state["agent"] = get_data_analyst_team(
        st.session_state["gh_pat"], 
        st.session_state["model_selection"]
    )

# Solution for Windows users
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Streamlit app
st.set_page_config(page_title="📊 Data Analyst Agent", layout="wide")


# initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Ensure the event loop is created only once
if "event_loop" not in st.session_state:
    st.session_state["event_loop"] = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state["event_loop"])

st.title("📊 Data Analyst Agent")
st.markdown(
    """
    A powerful multi-agent system built with AutoGen 0.4 that provides automated data analysis, visualization, and insights generation through an interactive chat interface.

    - **Data Analysis**: Ask questions about your dataset and get insights.
    - **Data Visualization**: Request visualizations to better understand your data.
    - **Interactive Chat**: Engage in a conversation with the agent to refine your queries and get more detailed answers.

    Start by getting a GitHub Personal Access Token (PAT) to access LLMs on GitHub. You can find the steps [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
    """
)

st.sidebar.header("Upload Dataset")
uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV or TSV file", type=["csv", "tsv"]
)

# Add reset button to sidebar
st.sidebar.button(
    "New Chat",
    on_click=lambda: asyncio.run(reset_chat()),
    type="secondary",
    use_container_width=True
)

gh_pat = st.sidebar.text_input(
    "GitHub Personal Access Token (PAT)",
    placeholder="Enter your GitHub PAT here",
    type="password",
    key="gh_pat"
)

if gh_pat:
    st.sidebar.selectbox(
        "Select a model",
        options=["gpt-4o-mini", "gpt-4o", "o1-mini" "o1"],
        index=0,
        key="model_selection",
        on_change=initialize_data_analyst_agent
    )

if uploaded_file:
    try:
        # Create a directory to save the uploaded file
        if not os.path.exists("code_executor"):
            os.makedirs("code_executor")
        # Save the uploaded file to the local directory
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

        # displying chat history messages
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_query = st.chat_input("Ask a query about the data...")

        if not st.session_state["gh_pat"]:
            st.error("Please enter your GitHub Personal Access Token (PAT) to proceed.")
            st.stop()
        
        if not st.session_state["model_selection"]:
            st.error("Please select a model to proceed.")
            st.stop()

        if st.session_state["gh_pat"] and st.session_state["model_selection"]and "agent" not in st.session_state:
            initialize_data_analyst_agent()

        if user_query:
            if user_query.strip() == "":
                st.warning("Please enter a query.")
            else:
                st.session_state["messages"].append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.markdown(user_query)

                user_query += f" (Dataset to be analysed is present at: {uploaded_file.name})"

                # Define an asynchronous function: this is needed to use await
                async def initiate_chat():
                    await st.session_state["agent"].run(
                        task=[TextMessage(content=user_query, source="user")],
                        cancellation_token=CancellationToken(),
                    )
                    st.stop()  # Stop code execution after termination command

                # Run the asynchronous function within the event loop
                st.session_state["event_loop"].run_until_complete(initiate_chat())

    except Exception as e:
        st.error(f"Error processing file: {e}")

# stop app after termination command
st.stop()