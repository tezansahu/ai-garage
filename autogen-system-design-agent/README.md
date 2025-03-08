# System Design Agent (using Autogen)

## Overview

Inspired by [Alex Xu's ByteByteGo edition on "How to ace System Design Interviews"](https://blog.bytebytego.com/p/ep141-how-to-ace-system-design-interviews), this System Design Agent is an advanced multi-agent tool designed to assist software architects and engineers in creating robust, scalable, and efficient design documents for any proposed sopftware system. 

It leverages the **[sequential chat pattern in Autogen](https://microsoft.github.io/autogen/0.2/docs/tutorial/conversation-patterns#sequential-chats)** for a **multi-agent system** to break down complex design tasks into manageable components, ensuring a thorough and well-structured approach to system architecture. The agents collaborate to clarify requirements, estimate capacity, design high-level architecture, choose optimal database types, and design interfaces, among other tasks.

### Agents

The following table describes the various agents that are part of this multi-agent system:

| Agent                        | Description                                                                                           |
|-----------------------------------|-------------------------------------------------------------------------------------------------------|
| `requirement_clarification_agent` | Ensures a complete understanding of system requirements by asking critical questions.                 |
| `capacity_estimation_agent`       | Estimates system resource needs based on requirements using back-of-the-envelope calculations.                                               |
| `high_level_design_agent`         | Designs & visualizes the high-level architecture, breaking it into critical components.                            |
| `database_design_agent`           | Models data and designs efficient data storage systems.                                               |
| `interface_design_agent`          | Designs interfaces between system components, choosing appropriate communication methods.             |
| `scalability_and_performance_agent` | Ensures the system can scale and maintain efficiency under load.                                      |
| `reliability_and_resilience_agent` | Designs fault-tolerant and resilient systems, ensuring high availability and reliability.              |
| `writer_agent`                    | Writes well-structured, formatted, and engaging software design documentation in markdown format.     |


## Features

- **Multi-Agent System**: The project utilizes multiple specialized agents, each focusing on a specific aspect of system design.
- **CLI Interface**: A user-friendly command line interface for interacting with the agents and executing tasks.
- **Human-in-the-loop for Requirement Specification**: Given an initial problem statement, the system design agent confirms your actual requirements & specifications by asking relevant questions, and then proceeds for automated design.
- **Visualization of High-Level ARchitecture & Database Schemas**: Dedicated agents produce PLantUML syntax to visualize teh various components of the high-level architecture, and also the data
- **Design Document produced at the End**: Based on the agentic responses, a detailed, well-formatted design document is produced in Markdown, available in the `sample_systems_designed` folder.


## Setup & Usage Instructions

### Prerequisites

- Python 3.10 or higher
- Poetry [[Installation Instructions]](https://python-poetry.org/docs/#installation)
- Setup your GPT Model on Azure OpenAI [[Reference Video]](https://youtu.be/H_1Ge6wxaaE?si=_mv-I8w2VB7D1PhB)

### Installation
  1. Clone the repository & get into the project directory
     ```sh
     git clone https://github.com/tezansahu/ai-garage.git
     cd ai-garage/diagram-generator
     ```
  2. Install dependencies using Poetry:
     ```sh
     poetry shell
     poetry install #  (installs Autogen & other necessary packages) 
     ```
  3. Set up your environment variables in `.env` file (add the necessary environment variables as specified in `.env.example`)

### Usage

1. **Run the CLI**
    ```sh
    python app.py
    ```
2. **Follow the Prompts**
    - Enter the problem statement when prompted.
    - The system will guide you through the process of designing the system, asking relevant questions and providing detailed outputs.


## Conclusion

The System Design Agent Project is a powerful tool for software architects and engineers, providing a structured and efficient approach to system design. By leveraging a multi-agent system and a user-friendly CLI, this project ensures that all aspects of system design are thoroughly addressed, resulting in robust and scalable architectures.