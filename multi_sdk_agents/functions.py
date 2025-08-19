from durable_entities_agents import run_agent
import azure.durable_functions as df

bp = df.Blueprint()

# Orchestration of OpenAI and Pydantic AI agents in the same workflow
@bp.orchestration_trigger(context_name="context")
def multi_sdk_weather_agents_orchestrator(context: df.DurableOrchestrationContext):
    input = context.get_input()
    if not input:
        raise Exception("Input missing")

    city1_weather = run_agent(context, agent_name="openai_weather_agent", input=f"Current weather in {input['city1']}")
    city2_weather = run_agent(context, agent_name="pydanticai_weather_agent", input=f"Current weather in {input['city2']}")
    [city1_weather, city2_weather] = yield context.task_all([city1_weather, city2_weather])

    return {
        "city1_weather": city1_weather,
        "city2_weather": city2_weather,
    }
