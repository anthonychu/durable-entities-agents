# Durable Entities Agents

A light-weight SDK for running distributed, stateful OpenAI Agents SDK agents on Azure Functions.

## Main goals

- Build agents using the OpenAI Agents SDK and run them on Azure Functions with built-in serverless scale and conversation state management, without extensive knowledge of Azure Functions
- Compose agents into complex workflows with Durable Functions orchestrations

## Features

- **OpenAI Agents SDK** integration: Build agents using the OpenAI Agents SDK.
- **Stateful AI Agents**: Agent conversation (sessions) state is automatically maintained. Each conversation with an agent is backed by a durable entity but no knowledge of Durable Functions is needed.
- **RESTful API**: Includes simple, built-in HTTP endpoints for interacting with agents.
- **Multi-Agent Orchestration**: Compose multiple stateful agents into complex workflows using Durable Functions orchestrations.
- **Human-in-the-Loop**: See travel planner for an approval workflow.

## Usage Overview

### Adding New Agents

For a single agent, almost no knowledge of Azure Functions is needed to make it serverless and stateful.

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
    from durable_entities_agents import add_agents

    app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

    add_agents(app, agents={
        "haiku_agent": haiku_agent,
    })
    ```

    This will:
    - Register the agent with the function app
    - Add the necessary Durable Functions and Durable Entities behind the scenes. Also enables
    - Enable an HTTP endpoint for interacting with the agent

3. Call the agent using the HTTP built-in endpoint. Specify the conversation session ID. If the session doesn't exist, it'll automatically create one:

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

4. Make a follow-up request in the same session, it remembers that we're talking about the capital of Canada and responds with that context:

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

### Orchestrating Agents

To orchestrate multiple agents, use a standard Durable Functions orchestration with the `run_agent` function.

1. Register agents:

    ```python
    add_agents(app, agents={
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

3. Start an orchestration function using the built-in Durable Functions HTTP endpoint:

    ```http
    POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/multilingual_writer_orchestrator
    Content-Type: application/json

    "\"write a paragraph about traveling to seattle\""
    ```

4. Open the status endpoint and poll it to check the progress.

## Sample Application

A sample Azure Functions application demonstrating AI agents using Azure Durable Entities for state management and session persistence. The project showcases three different agent scenarios:

1. **Basic Agents**
    - A simple haiku poet
    - A weather information agent using a remote weather MCP server
2. **Multilingual Writer** - Orchestrated workflow that writes content in English and translates to French and Spanish using 3 agents
3. **Travel Planner** - Multi-agent travel planning system with human approval workflow

### Project Structure
```
├── function_app.py              # Main function app with agent registration
├── basic_agents.py              # Simple agent definitions
├── durable_entities_agents/     # Core agent infrastructure
│   ├── app.py                   # Durable entities and orchestrators
│   └── sessions.py              # Session management
├── multilingual_writer/         # Multi-agent writing workflow
│   ├── agents.py                # Writer and translator agents
│   └── functions.py             # Orchestration functions
├── travel_planner/              # Travel planning workflow
│   ├── agents.py                # Travel-related agents
│   └── functions.py             # Travel orchestration
└── test.*.http                  # REST Client test files
```

## Prerequisites

- Python 3.12+
- Azure Functions Core Tools
- Docker (for Azurite storage emulator)
- VS Code with REST Client extension (recommended for testing)
- Azure OpenAI service endpoint

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

Edit `local.settings.json` and update the following values:

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
- `WEATHER_MCP_URL`: MCP server URL for weather data (required for weather agent)

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

- **Individual Agent**: Interact with a single agent using a built-in HTTP API. A session ID identifies a single conversation. `POST http://localhost:7071/api/run_agent/{agent_name}/{session_id}`
- **Multilingual Writer Orchestration**: Use the built-in Durable Functions API `POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/multilingual_writer_orchestrator`
- **Travel Planner Orchestration**: Use the built-in Durable Functions API `POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/travel_planner_orchestrator`

## Testing with VS Code REST Client

The repository includes `.http` files for easy testing with the VS Code REST Client extension:

### 1. Install REST Client Extension

In VS Code, install the "REST Client" extension by Huachao Mao.

### 2. Test Basic Agents

Open `test.basic.http` and run the requests:

```http
# Test haiku agent
POST http://localhost:7071/api/run_agent/haiku_agent/12345
Content-Type: application/json

"What's the capital of Canada?"
```

```http
# Test weather agent (requires MCP server)
POST http://localhost:7071/api/run_agent/weather_agent/3456789
Content-Type: application/json

"how warm is it in seattle?"
```

### 3. Test Multilingual Writer

Open `test.multilingual_writer.http`:

```http
# Start orchestration
POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/multilingual_writer_orchestrator
Content-Type: application/json

"write a paragraph about traveling to seattle"
```

This will return a status URL that you can poll to get the final result with English, French, and Spanish versions.

### 4. Test Travel Planner

Open `test.travel_planner.http`:

```http
# Start travel planning orchestration
POST http://localhost:7071/runtime/webhooks/durabletask/orchestrators/travel_planner_orchestrator
Content-Type: application/json

{"specialRequirements":"somewhere warm"}
```

For the travel planner, you'll need to:
1. Start the orchestration (get instance ID from response)
2. Wait for it to reach approval status `pending`
3. Send approval using the raise event API with your instance ID

## Session (Conversation State) Management

Each agent maintains conversation state per session ID. A single conversation (session) with an agent is backed by a durable entity. Use the same session ID across requests to maintain context:

```http
# First request
POST http://localhost:7071/api/run_agent/haiku_agent/session123
"What's the capital of Canada?"

# Follow-up request (maintains context)
POST http://localhost:7071/api/run_agent/haiku_agent/session123
"What about the country to the south?"
```

## Architecture

- **Azure Functions**: Serverless compute platform
- **Durable Entities**: Stateful entities for agent session management
- **Durable Orchestrations**: Workflow coordination for multi-agent scenarios
- **OpenAI Agents SDK**: AI agent framework with OpenAI integration

### Logs

Check function logs for detailed error information:
```bash
func start --verbose
```
