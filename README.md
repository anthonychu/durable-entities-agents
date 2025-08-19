# Durable Entities Agents

A light-weight helper SDK for running distributed, stateful AI Agents (OpenAI Agents SDK and Pydantic AI) on Azure Functions using Durable Entities for session state.

## Main goals

- Build agents using either the OpenAI Agents SDK or Pydantic AI and run them on Azure Functions with built-in serverless scale and conversation (session) state management, without deep knowledge of Durable Functions / Entities.
- Compose agents into complex workflows with Durable Functions orchestrations.

## Features

- **OpenAI Agents SDK integration**: Build agents using the OpenAI Agents SDK.
- **Pydantic AI integration**: Build agents using the Pydantic AI library.
- **Stateful AI Agents**: Conversation (session) state automatically maintained in Durable Entities.
- **Unified RESTful API**: HTTP endpoint `/api/run_agent/{agent_name}/{session_id}` works for both OpenAI and Pydantic AI agents.
- **Multi-Agent Orchestration**: Compose stateful agents in Durable Functions orchestrations.
- **Human-in-the-Loop**: Travel planner scenario shows approval workflow.

## Usage Overview

You can register OpenAI Agents SDK agents, Pydantic AI agents, or both. Each agent gets a durable entity-based session.

### Adding New Agents (OpenAI Agents SDK)

For a single agent, almost no knowledge of Azure Functions is required.

1. Build an agent using the OpenAI Agents SDK

    ```python
    from agents import Agent

    haiku_agent = Agent(
        name="Haiku agent",
        instructions="You are a haiku poet. Respond to the user's question with a haiku.",
        model=model
    )
    ```

2. Register it in `function_app.py`

    ```python
    import azure.functions as func
    from durable_entities_agents import add_openai_agents

    app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

    add_openai_agents(app, agents={
        "haiku_agent": haiku_agent,
    })
    ```

    This will:
    - Register the agent with the function app
    - Add the necessary Durable Functions and Durable Entities behind the scenes.
    - Enable an HTTP endpoint for interacting with the agent

3. Call the agent using the built-in HTTP endpoint. Specify a conversation session ID (creates one implicitly if it does not exist yet):

    ```http
    POST http://localhost:7071/api/run_agent/haiku_agent/session123
    Content-Type: application/json

    "What's the capital of Canada?"
    ```

    Sample response:

    ```
    Ottawa gleams bright,
    Parliament Hill stands so tall,
    Capital's heartbeat.
    ```

4. Make a follow-up request in the same session; it remembers previous context:

    ```http
    POST http://localhost:7071/api/run_agent/haiku_agent/session123
    Content-Type: application/json

    "What about the country to the south?"
    ```

    Sample response:

    ```
    D.C. stands proudly,
    White House beneath cherry blooms,
    Democracy's home.
    ```

### Adding New Agents (Pydantic AI)

1. Define a Pydantic AI agent:

    ```python
    from pydantic_ai import Agent

    haiku_agent = Agent(
        model,
        system_prompt='You are a haiku poet. Reply ONLY with a haiku.'
    )
    ```

2. Register it (can be alongside OpenAI agents):

    ```python
    from durable_entities_agents import add_pydanticai_agents

    add_pydanticai_agents(app, agents={
        "haiku_agent": haiku_agent
    })
    ```

3. Invoke it using the same HTTP pattern:

    ```http
    POST http://localhost:7071/api/run_agent/haiku_agent/session123
    Content-Type: application/json

    "Write one about the ocean."
    ```

Message history for Pydantic AI agents is persisted per conversation automatically.

### Orchestrating Agents

To orchestrate multiple agents, use a standard Durable Functions orchestration with the `run_agent` function.

1. Register agents (OpenAI shown below; works the same with Pydantic AI agent names):

    ```python
    from durable_entities_agents import add_openai_agents
    add_openai_agents(app, agents={
        "english_paragraph_writer_agent": english_paragraph_writer_agent,
        "french_translator_agent": french_translator_agent,
        "spanish_translator_agent": spanish_translator_agent,
    })
    ```

2. Write a durable orchestration function to coordinate the agents:

    ```python
    @app.orchestration_trigger(context_name="context")
    def multilingual_writer_orchestrator(context: df.DurableOrchestrationContext):
        input = context.get_input()
        if not input:
            raise Exception("Input missing")
        
        english = yield run_agent(context, agent_name="english_paragraph_writer_agent", input=input)

        # fan out
        french_task = run_agent(context, agent_name="french_translator_agent", input=english)
        spanish_task = run_agent(context, agent_name="spanish_translator_agent", input=english)

        # fan in
        [french, spanish] = yield context.task_all([french_task, spanish_task])

        return {
            "english": english,
            "french": french,
            "spanish": spanish,
        }
    ```

3. Start an orchestration using the built-in Durable Functions HTTP endpoint:

    ```http
    POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/multilingual_writer_orchestrator
    Content-Type: application/json

    "\"write a paragraph about traveling to seattle\""
    ```

4. Open the status endpoint and poll it to check the progress.

## Sample Application

A sample Azure Functions application demonstrating AI agents using Azure Durable Entities for state management and session persistence. The project showcases three different agent scenarios:

1. **Basic OpenAI Agents**
    - Haiku poet
    - Weather information agent (uses remote weather MCP server)
2. **Basic Pydantic AI Agent**
    - Weather information agent (Pydantic AI flavor)
3. **Multilingual Writer** - Orchestrated workflow that writes content in English and translates to French and Spanish (OpenAI Agents SDK)
4. **Travel Planner** - Multi-agent travel planning system with human approval workflow

### Project Structure
```
├── function_app.py                 # Main function app with agent registration
├── basic_openai_agents.py          # Simple OpenAI Agents SDK agents
├── basic_pydanticai_agents.py      # Simple Pydantic AI agent(s)
├── durable_entities_agents/        # Core integration (Durable Entities + helper functions)
│   ├── app.py                      # Registration, HTTP handler, entity/orchestrator
│   └── sessions.py                 # Session abstraction for OpenAI Agents SDK
├── multilingual_writer/            # Multi-agent writing workflow (OpenAI Agents SDK)
│   ├── agents.py                   # Writer and translator agents
│   └── functions.py                # Orchestration functions
├── travel_planner/                 # Travel planning workflow (OpenAI Agents SDK)
│   ├── agents.py                   # Travel-related agents
│   └── functions.py                # Travel orchestration + approval handling
└── test.*.http                     # REST Client test files
```

## Prerequisites

- Python 3.12+
- Azure Functions Core Tools
- Docker (for Azurite storage emulator)
- VS Code with REST Client extension (recommended for testing)
- Azure OpenAI service endpoint (for both OpenAI Agents SDK and Pydantic AI)

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd durable-entities-agents
pip install -r requirements.txt
```

### 2. Start Azurite Storage Emulator

Azurite provides local Azure Storage emulation for development:

```bash
docker run --rm -p 10000:10000 -p 10001:10001 -p 10002:10002 mcr.microsoft.com/azure-storage/azurite
```

Keep this running in a separate terminal throughout development.

### 3. Configure Local Settings

Copy the sample configuration file:

```bash
cp local.settings.sample.json local.settings.json
```

Edit `local.settings.json` and update the following values (add any other environment variables as needed):

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_ENDPOINT": "https://your-openai-instance.openai.azure.com/",
    "WEATHER_MCP_URL": "https://your-weather-mcp-server.azurewebsites.net/mcp"
  }
}
```

**Required Configuration:**
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI service endpoint
- `WEATHER_MCP_URL`: MCP server URL for weather data (required for weather agents)

### 4. Set up Azure Authentication

The application uses Azure DefaultAzureCredential for authentication. Ensure you're logged in:

```bash
az login
```

## Running the Application

### Start the Function App

```bash
func start
```

The application will start on `http://localhost:7071`

### Available Endpoints

- **Individual Agent (OpenAI or Pydantic AI)**: `POST http://localhost:7071/api/run_agent/{agent_name}/{session_id}`
- **Multilingual Writer Orchestration**: `POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/multilingual_writer_orchestrator`
- **Travel Planner Orchestration**: `POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/travel_planner_orchestrator`

## Testing with VS Code REST Client

The repository includes `.http` files for easy testing with the VS Code REST Client extension:

### 1. Install REST Client Extension

In VS Code, install the "REST Client" extension by Huachao Mao.

### 2. Test Basic OpenAI Agents

Open `test.openai_basic.http` and run the requests:

```http
# Test haiku agent
POST http://localhost:7071/api/run_agent/openai_haiku_agent/12345
Content-Type: application/json

"What's the capital of Canada?"

###
# Test weather agent (requires MCP server)
POST http://localhost:7071/api/run_agent/openai_weather_agent/3456789
Content-Type: application/json

"how warm is it in seattle?"
```

### 3. Test Basic Pydantic AI Agent

Open `test.pydanticai_basic.http`:

```http
# Test Pydantic AI weather agent
POST http://localhost:7071/api/run_agent/pydanticai_weather_agent/3456789
Content-Type: application/json

"how warm is it in seattle?"
```

### 4. Test Multilingual Writer

Open `test.multilingual_writer.http`:

```http
# Start orchestration
POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/multilingual_writer_orchestrator
Content-Type: application/json

"\"write a paragraph about traveling to seattle\""
```

This will return a status URL that you can poll to get the final result with English, French, and Spanish versions.

### 5. Test Travel Planner

Open `test.travel_planner.http`:

```http
# Start travel planning orchestration
POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/travel_planner_orchestrator
Content-Type: application/json

"{\"specialRequirements\":\"somewhere warm\"}"
```

For the travel planner, you'll need to:
1. Start the orchestration (get instance ID from response)
2. Wait for it to reach approval status `pending`
3. Send approval using the raise event API with your instance ID

```http
POST http://localhost:7071/runtime/webhooks/durabletask/instances/8f234aea121749d38fde41eb9df5acb5/raiseEvent/approval_event?taskHub=TestHubName&connection=Storage
Content-Type: application/json

"approved"
```

## Session (Conversation State) Management

Each agent maintains conversation state per session ID. A single conversation (session) with an agent is backed by a Durable Entity:

- OpenAI Agents SDK agents: state consists of the session data used by the runner.
- Pydantic AI agents: full message history (model + user + tool messages) is persisted and replayed on each run.

Use the same session ID across requests to maintain context:

```http
# First request
POST http://localhost:7071/api/run_agent/openai_haiku_agent/session123

"What's the capital of Canada?"

# Follow-up request (maintains context)
POST http://localhost:7071/api/run_agent/openai_haiku_agent/session123

"What about the country to the south?"
```

## Limitations

- Durability granularity is a single call to `Runner.run()` (OpenAI Agents) or `agent.run()` (Pydantic AI). Internal LLM/tool calls are not individually checkpointed.
- For OpenAI agents that hand off to others, only the top-level session state is persisted.
