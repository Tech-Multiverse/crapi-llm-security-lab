# Phase 2.5 — LLM / MCP / Tool-Calling Validation

This doc records the validation steps that confirm the agentic parts of the crAPI `develop` branch are wired up to the remote Ollama server.

## Endpoints

| Service | URL | Notes |
|---------|-----|-------|
| crAPI web UI | `http://127.0.0.1:8888` | Sign up / log in here to get a JWT. |
| Chatbot API | `http://127.0.0.1:5002/chatbot/genai/ask` | LangGraph agent that can use MCP tools and RAG. |
| MCP server | `http://127.0.0.1:5500/mcp/` | Streamable HTTP MCP endpoint built from `crapi-openapi-spec.json`. |

## Validation checklist

### 1. Basic chatbot smoke test

```bash
curl -s -X POST http://127.0.0.1:5002/chatbot/genai/ask \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'
```

Expected: a JSON response with an `output` field containing a real assistant message. The first call may take a few seconds while Ollama loads `llama3.1:8b`.

### 2. MCP tool discovery

The MCP server uses FastMCP's `streamable_http` transport and exposes crAPI's OpenAPI operations as tools. The simplest way to list them is from inside the running chatbot container:

```bash
docker exec -it crapi-chatbot python - <<'PY'
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def main():
    async with MultiServerMCPClient({
        "crapi": {
            "transport": "streamable_http",
            "url": "http://localhost:5500/mcp/",
            "headers": {},
        }
    }) as client:
        tools = await client.get_tools()
        for t in tools:
            print(t.name)

asyncio.run(main())
PY
```

Expected: a list of tool names such as `get_all_vehicles`, `get_vehicle_by_vin`, `get_mechanic_reports`, etc. The exact names match the operation IDs in `crapi/services/chatbot/src/resources/crapi-openapi-spec.json`.

### 3. Tool-calling through the chatbot

Sign up in the web UI and copy your JWT. Then ask the chatbot to do something only the API can do, e.g.:

```bash
TOKEN="<your-jwt-here>"

curl -s -X POST http://127.0.0.1:5002/chatbot/genai/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"List all of my vehicles"}'
```

Expected: the assistant returns vehicle data and the response metadata shows it invoked an MCP tool rather than hallucinating.

### 4. RAG / Chroma retrieval flow

Ask a question that is answered by the uploaded crAPI documentation:

```bash
curl -s -X POST http://127.0.0.1:5002/chatbot/genai/ask \
  -H "Content-Type: application/json" \
  -d '{"message":"What does the /workshop/api/me route expose?"}'
```

Expected: the assistant references the retrieved documentation in its answer.

## Common issues

- **`invalid input type` from Ollama embeddings** — the chatbot originally used `OpenAIEmbeddings`, which sends token arrays. The patch in `infrastructure/crapi-chatbot-patches/retriever_utils.py` swaps in `OllamaEmbeddings` when a custom `CHATBOT_OPENAI_BASE_URL` is set.
- **Ollama server stopped or unreachable** — the chatbot will return an error or timeout. Restart Ollama on the GPU host with `OLLAMA_HOST=0.0.0.0 ollama serve` and confirm the Mac can reach `http://<ollama-ip>:11434`.
- **MCP auth failures** — some MCP tools require a valid JWT. Pass `Authorization: Bearer <jwt>` with chatbot requests so the MCP client forwards the token to the identity service.

## Status

All four validation steps above were completed during the initial setup. This document captures the commands so they can be re-run before Phase 3 (LLM challenges) and Phase 4 (custom agent).
