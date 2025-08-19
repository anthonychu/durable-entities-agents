import azure.functions as func
from durable_entities_agents import add_openai_agents, add_pydanticai_agents
from basic_openai_agents import openai_haiku_agent, openai_weather_agent
from basic_pydanticai_agents import pydanticai_weather_agent
from multilingual_writer.agents import english_paragraph_writer_agent, french_translator_agent, spanish_translator_agent
from multilingual_writer.functions import bp as multilingual_writer_functions
from travel_planner.agents import destination_expert_agent, itinerary_planner_agent, local_recommendations_agent
from travel_planner.functions import bp as travel_planner_functions
from multi_sdk_agents.functions import bp as multi_sdk_agents_functions

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# Register agents
# Add Durable Entities and Functions to run the agents
# Add an HTTP function for running agents
add_openai_agents(app, agents={
    "openai_haiku_agent": openai_haiku_agent,
    "openai_weather_agent": openai_weather_agent,

    "english_paragraph_writer_agent": english_paragraph_writer_agent,
    "french_translator_agent": french_translator_agent,
    "spanish_translator_agent": spanish_translator_agent,

    "destination_expert_agent": destination_expert_agent,
    "itinerary_planner_agent": itinerary_planner_agent,
    "local_recommendations_agent": local_recommendations_agent
})

add_pydanticai_agents(app, agents={
    "pydanticai_weather_agent": pydanticai_weather_agent
})

app.register_functions(multilingual_writer_functions)
app.register_functions(travel_planner_functions)
app.register_functions(multi_sdk_agents_functions)
