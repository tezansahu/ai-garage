import os
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, register_function
from typing import Annotated

load_dotenv()

llm_config = {
    "config_list": [
        # # Local LLM (Llama3.2-1B, inferenced through Ollama, using LiteLLM proxy)
        # {
        #     "model": "NotRequired",  # Loaded with LiteLLM command
        #     "api_key": "NotRequired",  # Not needed
        #     "base_url": "http://0.0.0.0:4000",  # Your LiteLLM URL
        #     "price": [0, 0],  # Put in price per 1K tokens [prompt, response] as free!
        # },

        # Azure OpenAI GPT-4o config
        {
            "api_type": "azure",
            "model": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "base_url": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
        }
    ],
    "cache_seed": None,  # Turns off caching, useful for testing different models
}

#########################
# Define the user proxy #
#########################
user_proxy = UserProxyAgent(
    name="user_proxy",
    system_message="A human admin.",
    human_input_mode="TERMINATE",
    is_termination_msg=lambda x: x.get("content", "") and (x.get("content", "").rstrip().endswith("TERMINATE") or x.get("content", "").rstrip().endswith("TERMINATE.")),
    code_execution_config=False,
)


####################
# Define the tools #
####################
def write_to_markdown_file(
        file_name: Annotated[str, "The name of the markdown file to write the contents to."],
        contents: Annotated[str, "The contents to write to the file."], 
    ) -> Annotated[str, "Confirmation message"]:
    if not file_name.endswith(".md"):
        file_name += ".md"
    file_path = os.path.join("sample_systems_designed", file_name.lower().replace(" ", "-"))
    
    try:
        msg = ""
        if not os.path.exists(file_path):
            msg = f"Created a new markdown file '{file_path}'."
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(contents + "\n")
        return msg + " Content written successfully to it" if msg != "" else f"Content appended successfully to {file_path}"
    except Exception as e:
        return f"An error occurred while writing the file: {str(e)}"


############################################
# Define the agennts for various sub-tasks #
############################################

requirement_clarification_agent = AssistantAgent(
    name="requirement_clarification_agent",
    llm_config=llm_config,
    system_message="You are a thorough system analyst who ensures a complete understanding of system requirements before proceeding with design. You are proficient in asking the right questions to understand the functional & non-functional requirements of a problem, as well as summarize them. You **must** reply 'TERMINATE' at the end of your response."
)

# [TODO] Add knowledge of relevant back-of-the-envelope calculations to this agent
capacity_estimation_agent = AssistantAgent(
    name="capacity_estimation_agent",
    llm_config=llm_config,
    system_message="You are a meticulous capacity planner, proficient in common back-of-the-envelope calculations for software design, who calculates system resource needs based on requirements. Optimize for brevity."
)

hld_agent = AssistantAgent(
    name="high_level_design_agent",
    llm_config=llm_config,
    system_message="You are a skilled software architect who creates robust and scalable high-level system architectures. You have deep knowledge of large-scale systems, focusing on the 'why' behind various design decisions by evaluating tradeoffs effectively. You are also an expert in representing complex system in easy-to-understand diagrams with PlantUML. Optimize for brevity."
)

database_design_agent = AssistantAgent(
    name="database_design_agent",
    llm_config=llm_config,
    system_message="You are an expert database architect who models data and designs efficient data storage systems. You have in-depth understanding & practical insights related to various types of databases, and have a strong graps of various database optimization strategies. You can understand & articulate the various tradeoffs needed to make database design decisions effectively. You are also well-versed with visualizing the database schemas & their interactions using PLantUML diagrams. Optimize for brevity."
)


interface_design_agent = AssistantAgent(
    name="interface_design_gent",
    llm_config=llm_config,
    system_message="You are a communication specialist who designs system interfaces for seamless interaction. You can understand & articulate the various tradeoffs needed to make interface design decisions effectively. Optimize for brevity."
)

scalability_and_performance_agent = AssistantAgent(
    name="acalability_and_performance_agent",
    llm_config=llm_config,
    system_message="You are a performance optimizer who ensures the system can scale and maintain efficiency under load. You have great practical experience with the latest techniques & best-practices to develop highly performant systems that can dynamically scale to any requirements. You can understand & articulate the various tradeoffs needed to ensure desirable level of performance & scale of any small or large system. Optimize for brevity."
)

reliability_and_resilience_agent = AssistantAgent(
    name="reliability_and_resilience_agent",
    llm_config=llm_config,
    system_message="You are a reliability engineer who designs fault-tolerant and resilient systems. You have immense experience building small & large scale systems that adhere to tight quality & availability SLAs, and are an expert in identifying anti-patterns, and suggesting fixes for them. Optimize for brevity."
)

writer_agent = AssistantAgent(
    name="writer_agent",
    llm_config=llm_config,
    system_message="You are a technical writer, proficient in writing well-structured, formatted & engaging software design documentation in markdown format. You **must** reply 'TERMINATE' at the end of your response."
)

register_function(
    write_to_markdown_file,
    caller=writer_agent,
    executor=user_proxy,
    name="write_to_markdown_file",
    description="Write the provided contents to a markdown file with the given name.",
)


#################################
# Initiate the System Designing #
#################################

user_input = input("Enter the problem statement (what type of system would you like to design?): ")

task_0 = f"You have been tasked with designing the following system: '{user_input}'."

tasks = [
    f"{task_0}\nTo understand the system to be designed better, ask 3-4 critical questions each for functional and non-functional requirements of a system to clarify all aspects. Once you have the answers, summarize the clarified requirements in a well-structured list.",
    "Estimate the system's capacity needs by analyzing functional and non-functional requirements, focusing on user traffic, storage, memory, compute, and networking. Provide detailed estimates.",
    "Design the high-level architecture for this system, breaking it into all critical components. Provide a detailed design and use PlantUML syntax for block diagrams.",
    "Choose the optimal database type(s) necessary for this system. Using this, provide high-level insights into the model entities, relationships, and attributes in this database. Visualize the database schema and interactions using PlantUML. Also, suggest any optimization strategies.",
    "Design interfaces (e.g., APIs or event models) between system components, choosing communication methods like REST, GraphQL, or gRPC. Provide detailed interface designs.",
    "Address scalability, performance, and latency by suggesting relevant strategies. Provide a detailed scalability and performance plan.",
    "Ensure the system is reliable and resilient by addressing fault tolerance, failover, backups, disaster recovery, and monitoring. Provide a detailed plan for reliability and resilience."
]

is_silent = False

chat_results = user_proxy.initiate_chats(
    [
        {
            "recipient": requirement_clarification_agent,
            "message": tasks[0],
            "clear_history": True,
            "max_turns": 2,
            "summary": "reflection_with_llm",
        },
        {
            "recipient": capacity_estimation_agent,
            "message": tasks[1],
            "clear_history": True,
            "max_turns": 1,
            "silent": is_silent,
            "summary": "reflection_with_llm",
        },
        {
            "recipient": hld_agent,
            "message": tasks[2],
            "clear_history": True,
            "max_turns": 1,
            "silent": is_silent,
            "summary": "reflection_with_llm",
        },
        {
            "recipient": database_design_agent,
            "message": tasks[3],
            "clear_history": True,
            "max_turns": 1,
            "silent": is_silent,
            "summary": "reflection_with_llm",
        },
        {
            "recipient": interface_design_agent,
            "message": tasks[4],
            "clear_history": True,
            "max_turns": 1,
            "silent": is_silent,
            "summary": "reflection_with_llm",
        },
        {
            "recipient": scalability_and_performance_agent,
            "message": tasks[5],
            "clear_history": True,
            "max_turns": 1,
            "silent": is_silent,
            "summary": "reflection_with_llm",
        },
        {
            "recipient": reliability_and_resilience_agent,
            "message": tasks[6],
            "max_turns": 1,
            "clear_history": True,
            "silent": is_silent,
            "summary": "reflection_with_llm",
        },
    ]
)


writer_chat_queue = [
    {
        "recipient": writer_agent,
        "message": f"You need to write a design document for a system '{user_input}'. Suggest an appropriate file name for the markdown document.",
        "clear_history": True,
        "max_turns": 1,
        "summary": "reflection_with_llm",
    },
    *[
        {
            "recipient": writer_agent,
            "message": f"{chat_results[i].summary}",
            "clear_history": True,
            "max_turns": 2,
            "silent": is_silent,
            "summary": "last_msg",
        } for i in range(len(chat_results))
    ]
]

writer_chat_results = user_proxy.initiate_chats(writer_chat_queue)

print("System Design Document has been successfully written. Please check the markdown file for the detailed design.")