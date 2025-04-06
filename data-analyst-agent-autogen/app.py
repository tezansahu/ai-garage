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

# Solution for Windows users
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Streamlit app
st.set_page_config(page_title="📊 Data Analyst Agent", layout="wide")

# adding agent object (using a RoundRobinGroupChat, to allow for self looping) to session state to persist across sessions
# streamlit reruns the script on every user interaction
if "agent" not in st.session_state:
    st.session_state["agent"] = get_data_analyst_team()

# initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Ensure the event loop is created only once
if "event_loop" not in st.session_state:
    st.session_state["event_loop"] = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state["event_loop"])

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
st.sidebar.button(
    "New Chat",
    on_click=lambda: asyncio.run(reset_chat()),
    type="secondary",
    use_container_width=True
)

if uploaded_file:
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

        # displying chat history messages
        print("Chat history: " + str(len(st.session_state["messages"])) + " messages")
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