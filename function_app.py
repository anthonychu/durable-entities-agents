import azure.functions as func
import azure.durable_functions as df
from durable_entity_agents import run_agent, add_agents
from my_agents import haiku_agent, english_paragraph_writer_agent, french_translator_agent, spanish_translator_agent


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# Register agents
# Add Durable Entities and Functions to run the agents
# Add an HTTP function for running agents
add_agents(app, agents={
    "haiku_agent": haiku_agent,
    "english_paragraph_writer_agent": english_paragraph_writer_agent,
    "french_translator_agent": french_translator_agent,
    "spanish_translator_agent": spanish_translator_agent
})


@app.orchestration_trigger(context_name="context")
def multilingual_writer_orchestrator(context: df.DurableOrchestrationContext):
    input = context.get_input()
    if not input:
        raise Exception("Input missing")
    
    english = yield run_agent(context, agent_name="english_paragraph_writer_agent", input=input)

    french_task = run_agent(context, agent_name="french_translator_agent", input=english)
    spanish_task = run_agent(context, agent_name="spanish_translator_agent", input=english)
    [french, spanish] = yield context.task_all([french_task, spanish_task])

    return {
        "english": english,
        "french": french,
        "spanish": spanish,
    }
