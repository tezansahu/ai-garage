from typing import List, cast

import chainlit as cl
import yaml
from autogen_agentchat.base import TaskResult
from autogen_core.models import ChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, TextMessage, ToolCallRequestEvent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken

from agents import create_agents_for_group_chat



@cl.on_chat_start  # type: ignore
async def start_chat() -> None:
    # For OpenAI/Azure OpenAI models
    with open("model_config.yaml", "r") as f:
        model_config = yaml.safe_load(f)
    model_client = ChatCompletionClient.load_component(model_config)

    group_chat = create_agents_for_group_chat(model_client)

    # Set the assistant agent in the user session.
    cl.user_session.set("prompt_history", "")  # type: ignore
    cl.user_session.set("team", group_chat)  # type: ignore


@cl.set_starters  # type: ignore
async def set_starts() -> List[cl.Starter]:
    return [
        cl.Starter(
            label="Work Week Debate",
            message="Should developed nations implement a four-day work week as standard practice?",
        ),
        cl.Starter(
            label="Social Media Liability Debate",
            message="Should social media companies be legally liable for harmful content on their platforms?",
        ),
        cl.Starter(
            label="Communism Debate",
            message="Is communism an inherently flawed political ideology?",
        ),
        cl.Starter(
            label="Condiment Debate",
            message="Should you put mayo or ketchup on fries?",
        ),
    ]


@cl.on_message  # type: ignore
async def chat(message: cl.Message) -> None:
    # Get the team from the user session.
    team = cast(RoundRobinGroupChat, cl.user_session.get("team"))  # type: ignore
    # Streaming response message.
    streaming_response: cl.Message | None = None
    # Stream the messages from the team.
    async for msg in team.run_stream(
        task=[TextMessage(content=message.content, source="user")],
        cancellation_token=CancellationToken(),
    ):
            
        if isinstance(msg, ModelClientStreamingChunkEvent):
            # Stream the model client response to the user.
            if streaming_response is None:
                # Start a new streaming response.
                streaming_response = cl.Message(content="[" + msg.source + "]\n", author=msg.source)
            await streaming_response.stream_token(msg.content)
        elif streaming_response is not None:
            # Done streaming the model client response.
            # We can skip the current message as it is just the complete message
            # of the streaming response.
            await streaming_response.send()
            # Reset the streaming response so we won't enter this block again
            # until the next streaming response is complete.
            streaming_response = None
        elif isinstance(msg, TaskResult):
            # Send the task termination message.
            final_message = "Task terminated. "
            if msg.stop_reason:
                final_message += msg.stop_reason
            await cl.Message(content=final_message).send()
        elif isinstance(msg, ToolCallRequestEvent):
            # Send the tool call request message.
            await cl.Message(
                content=f"[{msg.source}]\n **Tool calls requested:**\n- " + "\n- ".join(f"{tool.name}: {tool.arguments}" for tool in msg.content),
                author=msg.source,
            ).send()
        else:
            # Skip all other message types.
            pass