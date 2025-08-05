import os
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential
from azure.identity.aio import get_bearer_token_provider

set_tracing_disabled(disabled=True)

deployment = "gpt-4.1"

credentials = DefaultAzureCredential()

client = AsyncAzureOpenAI(
    api_version="2023-09-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
    azure_ad_token_provider=get_bearer_token_provider(credentials, "https://cognitiveservices.azure.com/.default"),
)

haiku_agent = Agent(
    name="Haiku agent",
    instructions="You are a haiku poet. Respond to the user's question with a haiku.",
    model=OpenAIChatCompletionsModel(
        model=deployment,
        openai_client=client,
    )
)


# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         result = await Runner.run(agent, "What is the capital of France?")
#         print(result.final_output)
#         print(result.to_input_list())
        

    # asyncio.run(main())