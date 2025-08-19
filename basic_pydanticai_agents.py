import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPServerStreamableHTTP

client = AsyncAzureOpenAI(
    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
    api_version='2024-07-01-preview',
    azure_ad_token_provider=get_bearer_token_provider(
        DefaultAzureCredential(), 'https://cognitiveservices.azure.com/.default'
    )
)

model = OpenAIModel(
    'gpt-4.1',
    provider=OpenAIProvider(openai_client=client),
)

server = MCPServerStreamableHTTP(url=os.environ['WEATHER_MCP_URL'])

pydanticai_weather_agent = Agent(  
    model,
    system_prompt='Be concise, reply with one sentence.',
    toolsets=[server]
)
