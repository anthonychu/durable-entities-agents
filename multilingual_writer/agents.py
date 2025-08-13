import os
from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider

set_tracing_disabled(disabled=True)

deployment = "gpt-4.1"

credentials = DefaultAzureCredential()

client = AsyncAzureOpenAI(
    api_version="2023-09-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
    azure_ad_token_provider=get_bearer_token_provider(credentials, "https://cognitiveservices.azure.com/.default"),
)

model = OpenAIChatCompletionsModel(
    model=deployment,
    openai_client=client,
)


english_paragraph_writer_agent = Agent(
    name="English Paragraph Writer Agent",
    instructions="You are an expert paragraph writer. Write a detailed paragraph based on the user's input.",
    model=model
)

french_translator_agent = Agent(
    name="French Translator Agent",
    instructions="You are a French translator. Translate the user's input into French.",
    model=model
)

spanish_translator_agent = Agent(
    name="Spanish Translator Agent",
    instructions="You are a Spanish translator. Translate the user's input into Spanish.",
    model=model
)
