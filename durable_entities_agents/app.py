import asyncio
import json
import logging
import uuid
from typing import Any

import azure.functions as func
import azure.durable_functions as df
from azure.durable_functions.models import TaskBase

from agents import Agent, RunResult, Runner
from agents.mcp.server import MCPServer
from .sessions import InMemorySession


_agents:dict[str, Agent] | None = None

def add_agents(app: func.FunctionApp, agents:dict[str, Agent]={}):
    global _agents
    if _agents is not None:
        raise Exception("Agents already initialized")

    _agents = agents

    app.entity_trigger(context_name="context", entity_name="Agent")(agent)
    app.orchestration_trigger(context_name="context", orchestration="agent_run_orchestrator")(agent_run_orchestrator)
    app.route(route="run_agent/{agent_name}/{session_id}", methods=["POST"])(app.durable_client_input(client_name="client")(agent_run_http))


# Durable entity representing a single session of an agent
# Entity key is in the format <agent_name>--<session_id>
def agent(context: df.DurableEntityContext) -> None:
    state = context.get_state(lambda: {})
    operation = context.operation_name
    agent_id = context.entity_key

    agent_name, agent_session_id = agent_id.split("--", 1)

    if not _agents:
        raise Exception("No agents defined")
    
    if operation == "run":
        agent = _agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found.")
        
        session_data = state.get("session_data", [])
        session = InMemorySession(session_data)
        input = context.get_input()

        if not isinstance(input, str):
            input = json.dumps(input)

        result = asyncio.run(_run_agent(agent, input, session=session))
        logging.info(f"Operation result: {result.final_output}")
        context.set_result(result.final_output)
        state["session_data"] = session.get_items_sync()
    
    context.set_state(state)

async def _run_agent(agent: Agent, input: str, session: InMemorySession) -> RunResult:
    connected_servers: list[MCPServer] = []
    for server in agent.mcp_servers:
        try:
            await server.connect()
            connected_servers.append(server)
        except Exception as e:
            logging.warning(f"Failed to connect to MCP server {server}: {e}")

    try:
        result = await Runner.run(agent, input, session=session)
    finally:
        for server in connected_servers:
            await server.cleanup()

    return result

# Orchestrator to call an agent entity and get the result of the run
def agent_run_orchestrator(context: df.DurableOrchestrationContext):
    input = context.get_input() or {}
    agent_name = input.get("agent_name")
    session_id = input.get("session_id")
    operation_input = input.get("operation_input")

    entity_id = df.EntityId("Agent", f"{agent_name}--{session_id}")

    result = yield context.call_entity(entity_id, "run", operation_input)
    return result


# Http triggered function for running an agent
async def agent_run_http(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    agent_name = req.route_params.get('agent_name')
    session_id = req.route_params.get('session_id')
    input_data = req.get_json() or {}

    logging.info(f"Starting agent run for {agent_name} with session ID {session_id} and input: {input_data}")

    instance_id = await client.start_new("agent_run_orchestrator", None, {
        "agent_name": agent_name,
        "session_id": session_id,
        "operation_input": input_data
    })

    result = await client.wait_for_completion_or_create_check_status_response(req, instance_id, timeout_in_milliseconds=180000)
    return result


# Helper function for calling an agent entity's run operation
def run_agent(ctx: df.DurableOrchestrationContext, agent_name: str = '', session_id: str = '', input: Any | None = None) -> TaskBase:
    if not session_id:
        session_id = str(uuid.uuid4())
    entity_id = df.EntityId("Agent", f"{agent_name}--{session_id}")
    return ctx.call_entity(entityId=entity_id, operationName="run", operationInput=input)
