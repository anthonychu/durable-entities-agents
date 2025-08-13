from durable_entities_agents import run_agent
import azure.durable_functions as df

bp = df.Blueprint()

# Orchestration of multiple agents
# Write a paragraph in English and fan out to translate to French and Spanish
@bp.orchestration_trigger(context_name="context")
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
