import azure.functions as func
from durable_entities_agents import add_agents
from basic_agents import haiku_agent, weather_agent
from multilingual_writer.agents import english_paragraph_writer_agent, french_translator_agent, spanish_translator_agent
from multilingual_writer.functions import bp as multilingual_writer_functions
from travel_planner.agents import destination_expert_agent, itinerary_planner_agent, local_recommendations_agent
from travel_planner.functions import bp as travel_planner_functions

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# Register agents
# Add Durable Entities and Functions to run the agents
# Add an HTTP function for running agents
add_agents(app, agents={
    "haiku_agent": haiku_agent,
    "weather_agent": weather_agent,

    "english_paragraph_writer_agent": english_paragraph_writer_agent,
    "french_translator_agent": french_translator_agent,
    "spanish_translator_agent": spanish_translator_agent,

    "destination_expert_agent": destination_expert_agent,
    "itinerary_planner_agent": itinerary_planner_agent,
    "local_recommendations_agent": local_recommendations_agent
})


app.register_functions(multilingual_writer_functions)
app.register_functions(travel_planner_functions)
