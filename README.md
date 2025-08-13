# Durable Entities Agents

A light-weight SDK for running OpenAI Agents SDK agents on Azure Functions.

## Main goals

- Build agents using the OpenAI Agents SDK
- Run agents on Azure Functions with built-in conversation state management, without extensive knowledge of Azure Functions
- Compose agents into complex workflows with Durable Functions orchestrations

## Features

- **OpenAI Agents SDK** integration: Build agents using the OpenAI Agents SDK and run them on the Azure Functions platform.
- **Stateful AI Agents**: Conversation (sessions) state is automatically maintained. Each conversation (session) with an agent is backed by a durable entity but no knowledge of Durable Functions is needed.
- **RESTful API**: Includes simple HTTP endpoints for interacting with agents.
- **Multi-Agent Orchestration**: Compose multiple stateful agents into complex workflows using Durable Functions orchestrations.
- **MCP Server Integration**: Works with MCP servers. See weather agent for details.
- **Human-in-the-Loop**: See travel planner for an approval workflow.

## Sample Application

A sample Azure Functions application demonstrating AI agents using Azure Durable Entities for state management and session persistence. The project showcases three different agent scenarios:

1. **Basic Agents** - Simple haiku poet and weather information agents
2. **Multilingual Writer** - Orchestrated workflow that writes content in English and translates to French and Spanish
3. **Travel Planner** - Multi-agent travel planning system with human approval workflow

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

## Available Agents

### Basic Agents
- **haiku_agent**: Responds to questions with haiku poems
- **weather_agent**: Provides weather information using MCP server

### Multilingual Writer Agents
- **english_paragraph_writer_agent**: Writes paragraphs in English
- **french_translator_agent**: Translates text to French
- **spanish_translator_agent**: Translates text to Spanish

### Travel Planner Agents
- **destination_expert_agent**: Recommends travel destinations
- **itinerary_planner_agent**: Creates detailed travel itineraries
- **local_recommendations_agent**: Suggests local activities and attractions

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
- **MCP (Model Context Protocol)**: External data integration for agents

## Development

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

### Adding New Agents

1. Define your agent in the appropriate module
2. Register it in `function_app.py`
3. Create test cases in a new `.http` file

## Troubleshooting

### Common Issues

1. **Storage Connection Error**: Ensure Azurite is running on ports 10000-10002
2. **OpenAI Authentication Error**: Verify `AZURE_OPENAI_ENDPOINT` and Azure login
3. **Weather Agent Fails**: Check `WEATHER_MCP_URL` configuration
4. **Timeout Errors**: Increase timeout in orchestrator or use background processing

### Logs

Check function logs for detailed error information:
```bash
func start --verbose
```
