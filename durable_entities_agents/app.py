import asyncio
import json
import logging
import uuid
from typing import Any

import azure.functions as func
import azure.durable_functions as df
from azure.durable_functions.models import TaskBase

import agents as openai_agents
import pydantic_ai
from pydantic_core import to_jsonable_python
from agents.mcp.server import MCPServer
from .sessions import InMemorySession


_setup_has_run = False
def _setup(app: func.FunctionApp):
    global _setup_has_run
    if _setup_has_run:
        return
    
    app.entity_trigger(context_name="context", entity_name="Agent")(agent)
    app.orchestration_trigger(context_name="context", orchestration="agent_run_orchestrator")(agent_run_orchestrator)
    app.route(route="run_agent/{agent_name}/{session_id}", methods=["POST"])(app.durable_client_input(client_name="client")(agent_run_http))
    _setup_has_run = True


_openai_agents:dict[str, openai_agents.Agent] | None = None
def add_openai_agents(app: func.FunctionApp, agents:dict[str, openai_agents.Agent]={}):
    global _openai_agents
    if _openai_agents is not None:
        raise Exception("Agents already initialized")

    _openai_agents = agents
    _setup(app)


_pydanticai_agents:dict[str, pydantic_ai.Agent] | None = None
def add_pydanticai_agents(app: func.FunctionApp, agents:dict[str, pydantic_ai.Agent]={}):
    global _pydanticai_agents
    if _pydanticai_agents is not None:
        raise Exception("Agents already initialized")

    _pydanticai_agents = agents
    _setup(app)
    

# Durable entity representing a single session of an agent
# Entity key is in the format <agent_name>--<session_id>
def agent(context: df.DurableEntityContext) -> None:
    state = context.get_state(lambda: {})
    operation = context.operation_name
    agent_id = context.entity_key

    agent_name, agent_session_id = agent_id.split("--", 1)

    if not _openai_agents and not _pydanticai_agents:
        raise Exception("No agents defined")
    
    if operation == "run":
        openai_agent = _openai_agents.get(agent_name)
        
        if openai_agent:
            session_data = state.get("session_data", [])
            session = InMemorySession(session_data)
            input = context.get_input()
            if not isinstance(input, str):
                input = json.dumps(input)
            result = asyncio.run(_run_openai_agent(openai_agent, input, session=session))
            logging.info(f"Operation result: {result.final_output}")
            context.set_result(result.final_output)
            state["session_data"] = session.get_items_sync()
            context.set_state(state)
            return

        pydantic_agent = _pydanticai_agents.get(agent_name)
        if pydantic_agent:
            message_history_python = state.get("message_history", [])
            message_history = pydantic_ai.messages.ModelMessagesTypeAdapter.validate_python(message_history_python)
            input = context.get_input()

            if not isinstance(input, str):
                input = json.dumps(input)

            result = asyncio.run(_run_pydanticai_agent(pydantic_agent, input, message_history))
            logging.info(f"Operation result: {result.output}")
            context.set_result(result.output)
            state["message_history"] = to_jsonable_python(result.all_messages())
            context.set_state(state)
            return

        raise ValueError(f"Agent {agent_name} not found.")
    

async def _run_openai_agent(agent: openai_agents.Agent, input: str, session: InMemorySession) -> openai_agents.RunResult:
    connected_servers: list[MCPServer] = []
    for server in agent.mcp_servers:
        try:
            await server.connect()
            connected_servers.append(server)
        except Exception as e:
            logging.warning(f"Failed to connect to MCP server {server}: {e}")

    try:
        result = await openai_agents.Runner.run(agent, input, session=session)
    finally:
        for server in connected_servers:
            await server.cleanup()

    return result


async def _run_pydanticai_agent(agent: pydantic_ai.Agent, input: str, message_history: list[pydantic_ai.messages.ModelMessage]) -> pydantic_ai.agent.AgentRunResult:
    result = await agent.run(user_prompt=input, message_history=message_history)
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
