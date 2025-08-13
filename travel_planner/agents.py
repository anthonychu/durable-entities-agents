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


# Agent prompts 
DESTINATION_AGENT_PROMPT = """You are a travel destination expert. Recommend 3 destinations.
Keep responses brief and focused.

For each destination provide:
- Destination name (max 50 chars)
- Brief description (max 150 chars)
- Short reasoning (max 100 chars)  
- Match score (0-100)

Always respond with valid JSON in the following format:
{
    "recommendations": [
        {
            "destination_name": "",
            "description": "",
            "reasoning": "",
            "match_score": 0
        }
    ]
}"""

ITINERARY_AGENT_PROMPT = """Create a concise daily itinerary.

Include:
- Maximum 3 activities per day
- Brief activity descriptions (max 80 chars)
- Simple cost estimates (e.g., "$50", "$100-150")

Always respond with valid JSON in the following format:
{
    "destination_name": "",
    "travel_dates": "",
    "daily_plan": [
        {
            "day": 1,
            "date": "",
            "activities": [
                {
                    "time": "",
                    "activity_name": "",
                    "description": "",
                    "location": "",
                    "estimated_cost": ""
                }
            ]
        }
    ],
    "estimated_total_cost": "",
    "additional_notes": ""
}"""

LOCAL_RECOMMENDATIONS_AGENT_PROMPT = """Provide brief local recommendations.
Include:
- Maximum 3 attractions with short descriptions (max 80 chars each)
- Maximum 3 restaurants with short descriptions (max 80 chars each)
- Brief insider tips (max 150 chars total)
Always respond with valid JSON in the following format:
{
    "attractions": [
        {
            "name": "",
            "category": "",
            "description": "",
            "location": "",
            "visit_duration": "",
            "estimated_cost": "",
            "rating": 4.5
        }
    ],
    "restaurants": [
        {
            "name": "",
            "cuisine": "",
            "description": "",
            "location": "",
            "price_range": "",
            "rating": 4.5
        }
    ],
    "insider_tips": ""
}"""


destination_expert_agent = Agent(
    name="DestinationExpert",
    instructions=DESTINATION_AGENT_PROMPT,
    model=model
)

itinerary_planner_agent = Agent(
    name="ItineraryPlanner",
    instructions=ITINERARY_AGENT_PROMPT,
    model=model
)

local_recommendations_agent = Agent(
    name="LocalRecommendations",
    instructions=LOCAL_RECOMMENDATIONS_AGENT_PROMPT,
    model=model
)
