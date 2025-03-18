from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, Swarm
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from tools import *

def create_agents_for_group_chat(model_client: ChatCompletionClient) -> RoundRobinGroupChat:
    # Create the research agent.
    research_agent = AssistantAgent(
        name="ResearchAgent",
        model_client=model_client,
        system_message="You are a resarch agent - methodical, thorough, and objective. You must use the tools available at your disposal for information gathering with academic rigor from the web. Note that you can scrape 2 website URLs at max - so select them wisely. Your job is to gather relevant facts, statistics, and evidence on the debate topic & create a balanced information repository that covers multiple perspectives. Once you have the information, first send your message presenting all the relevant facts, statistics, case studies and evidences in easily digestible bullets and then handoff to the argument agent.",
        handoffs=["ArgumentConstructionAgent"],
        tools=[serper_web_search, scrape_website],
        model_client_stream=True,  # Enable model client streaming.
    )

    # Create an argument construction agent.
    argument_agent = AssistantAgent(
        name="ArgumentConstructionAgent",
        model_client=model_client,
        system_message="You are an argument construction agent - logical, strategic, and persuasive. You have a keen understanding of logical fallacies and rhetorical strategies. You excels at organizing information into compelling narratives. You're analytical and can quickly identify the strongest position to take based on available evidence. Your job is to develop the core thesis and supporting arguments, structure arguments in a logical progression. You must identify the most persuasive pieces of evidence from the research & also create compelling analogies and examples to illustrate points. First, send your message presenting all the arguments and then handoff to the RebuttalAgent.",
        handoffs=["RebuttalAgent"],
        model_client_stream=True,  # Enable model client streaming.
    )

    # Create the rebuttal agent.
    rebuttal_agent = AssistantAgent(
        name="RebuttalAgent",
        model_client=model_client,
        system_message="You are a rebuttal agent - Quick-thinking, critical, and adaptive. You have a sharp eye for logical fallacies and weaknesses in arguments. You are skilled at identifying counterarguments and constructing rebuttals. Your job is to critically analyze the arguments presented by the other agents, identify weaknesses, and construct counterarguments that effectively challenge their positions. First, send your message presenting all the rebuttals and then handoff to the EvaluationAgent.",
        handoffs=["EvaluationAgent"],
        model_client_stream=True,  # Enable model client streaming.
    )

    # Create evaluation agent.
    evaluation_agent = AssistantAgent(
        name="EvaluationAgent",
        model_client=model_client,
        system_message="You are an evaluation agent - analytical, impartial, and detail-oriented. You maintain objectivity and evaluate arguments based on merit rather than personal bias. You have a strong understanding of formal debate criteria and can provide constructive feedback. Your job is to get pre-decided evaluation criteria (using tools), assess the arguments presented by the other agents, identify strengths and weaknesses, and provide scoring based on the criteria along with constructive feedback. Use TERMINATE when you are done evaluating the arguments.",
        tools=[get_eval_criteria],
        model_client_stream=True,  # Enable model client streaming.
    )

    termination = MaxMessageTermination(max_messages=10) | TextMentionTermination("TERMINATE")

    # Chain the agents using RoundRobinGroupChat.
    # group_chat = RoundRobinGroupChat([research_agent, argument_agent, rebuttal_agent, evaluation_agent], termination_condition=termination)
    group_chat = Swarm([research_agent, argument_agent, rebuttal_agent, evaluation_agent], termination_condition=termination)

    return group_chat