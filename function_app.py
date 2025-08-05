import asyncio
import logging
from agents import Runner
import azure.functions as func
import azure.durable_functions as df
from my_agents import haiku_agent
from entity_agents.sessions import InMemorySession


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

_agents = {
    "haiku_agent": haiku_agent,
}


# Entity function called counter
@app.entity_trigger(context_name="context")
def Agent(context: df.DurableEntityContext) -> None:
    state = context.get_state(lambda: {})
    operation = context.operation_name
    agent_id = context.entity_key

    agent_name, agent_session_id = agent_id.split("--", 1)

    logging.info(f"Entity operation: {operation}, Agent: {agent_name}, Session ID: {agent_session_id}")
    
    if operation == "run":
        agent = _agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found.")
        
        session_data = state.get("session_data", [])
        session = InMemorySession(session_data)
        input = context.get_input() or ""
        
        logging.info(f"Running operation with input: {input}")

        result = asyncio.run(Runner.run(agent, input, session=session))
        logging.info(f"Operation result: {result.final_output}")
        context.set_result(result.final_output)
        state["session_data"] = session.get_items_sync()
    
    context.set_state(state)

    
@app.orchestration_trigger(context_name="context")
def agent_run_orchestrator(context: df.DurableOrchestrationContext):
    input = context.get_input() or {}
    logging.info(f"Orchestration input: {input}")
    agent_name = input.get("agent_name")
    session_id = input.get("session_id")
    operation_input = input.get("operation_input")

    entity_id = df.EntityId("Agent", f"{agent_name}--{session_id}")

    logging.info(f"Starting orchestration for agent: {agent_name}, session ID: {session_id}, input: {operation_input}")

    result = yield context.call_entity(entity_id, "run", operation_input)
    
    return result


@app.route(route="run_agent/{agent_name}/{session_id}", methods=["POST"])
@app.durable_client_input(client_name="client")
async def http_trigger(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    agent_name = req.route_params.get('agent_name')
    session_id = req.route_params.get('session_id')
    input_data = req.get_json() or {}

    logging.info(f"Starting agent run for {agent_name} with session ID {session_id} and input: {input_data}")

    instance_id = await client.start_new("agent_run_orchestrator", None, {
        "agent_name": agent_name,
        "session_id": session_id,
        "operation_input": input_data
    })

    result = await client.wait_for_completion_or_create_check_status_response(req, instance_id, timeout_in_milliseconds=30000)
    return result