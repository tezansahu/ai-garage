from langchain_openai import AzureChatOpenAI
from langchain_ollama import ChatOllama
from browser_use import Agent, Controller, ActionResult
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

# llm = AzureChatOpenAI(
#     model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
#     api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
#     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
#     api_key=os.getenv("AZURE_OPENAI_API_KEY")
# )

llm = AzureChatOpenAI(
    model='gpt-4o',
    api_version='2024-10-21',
    azure_endpoint='https://convocapture-az-openai.openai.azure.com/',
    api_key='09d952efb15b4bc3836085745f32280a'
)

llm_ollama = ChatOllama(
    model="qwen2.5:7b",
    num_ctx=32000,
)

# Initialize the controller
controller = Controller()

@controller.action('Ask user for information')
def ask_human(question: str) -> str:
    answer = input(f'\n{question}\nInput: ')
    return ActionResult(extracted_content=answer)

async def main():
    agent = Agent(
        task="""
## ADDITIONAL INSTRUCTIONS:
- Do NOT assume any information not specified in the task.
- If the information related to some input of an action is not available, ask the user.  
- If you do not have some information & need it, ask the user.
        
## TASK
Go to airbnb and find a place to stay in Paris for 2 days
""",
        llm=llm_ollama,
        controller=controller,
    )
    history = await agent.run()
    history.save_to_file('./tmp/history.json')
    print(history.final_result())

asyncio.run(main())