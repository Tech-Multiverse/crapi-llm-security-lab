# crAPI-LLM Security Lab

> UNDER CONSTRUCTION 🚧
> This project is an active work in progress!

A local, shareable lab for API security, LLM application security, and agentic AI demos.

It combines the OWASP crAPI vulnerable API application with a remote Ollama LLM, a LangGraph-based chatbot/MCP server, and a place for custom agent and WAAP experiments.

## What this is for

This lab is a local, shareable environment for learning and practicing API security, LLM application security, and agentic AI security. It is meant to be:

- **Reproducible**: one `docker compose up` gets crAPI running.
- **Extensible**: add custom agents, a React UI, an API gateway/WAAP, and traffic analysis as phases.
- **Pedagogical**: directly maps to the OWASP API Security Top 10, OWASP LLM / AI security risks, WAAP and runtime security concepts, and agent-to-API/tool interactions.

## What crAPI (develop branch) gives us

The `develop` branch of OWASP crAPI includes:

- The classic OWASP API Security Top 10 challenges (BOLA, BFLA, broken auth, excessive data exposure, mass assignment, rate limiting, SSRF, NoSQL/SQL injection, JWT forgery, unauthenticated access).
- A built-in LLM chatbot (`crapi-chatbot`) that uses LangGraph to call crAPI APIs via an OpenAPI spec.
- An MCP (Model Context Protocol) server on port `5500` that exposes the same API surface as tools.
- LLM-specific challenges 16–18: prompt injection, credential extraction, and action-on-behalf-of-another-user.
- A fake external gateway service (`api.mypremiumdealership.com`) for the SSRF challenge.

## What we have added

- A top-level `docker-compose.yml` that `include`s crAPI's compose and exposes the direct service ports for local testing.
- A root `.env` with all the configuration in one place, including the remote Ollama IP.
- A `crapi-llm` Miniconda environment for Python agent development.
- Node.js (via `nvm`) for the React UI.
- A small patch (`infrastructure/crapi-chatbot-patches/retriever_utils.py`) that makes crAPI's chatbot use `OllamaEmbeddings` for the vector store instead of `OpenAIEmbeddings`, which sends token arrays that Ollama's OpenAI-compatible `/v1/embeddings` endpoint rejects.

## Architecture

```
Host workstation
  ├─ Docker Desktop
  │   └─ crAPI stack
  │       ├─ crapi-identity      :8080
  │       ├─ crapi-community     :8087
  │       ├─ crapi-workshop      :8000
  │       ├─ crapi-chatbot       :5002 (chat) / :5500 (MCP)
  │       ├─ crapi-web           :8888
  │       ├─ postgres            :5432
  │       ├─ mongodb             :27017
  │       ├─ chromadb            :8000
  │       ├─ mailhog             :8025
  │       └─ api.mypremiumdealership.com
  │
  ├─ Conda env `crapi-llm`
  ├─ Node.js / React UI (future)
  └─ agent/ Python demos (future)

Remote GPU machine
  └─ Ollama
      ├─ llama3.1:8b        (chat / tool calling)
      └─ nomic-embed-text:latest (embeddings)
```

## Network layout

`docker-compose.yml` uses the `include` directive to pull in `crapi/deploy/docker/docker-compose.yml` and then override selected ports.

- Docker Compose creates a default bridge network named `crapi-llm_default`.
- Inside that network, services talk to each other by container name (e.g. `crapi-chatbot` calls `http://crapi-identity:8080`).
- The host machine reaches published services on `127.0.0.1`:
  - `http://127.0.0.1:8888`   crAPI web UI
  - `http://127.0.0.1:8080`   identity service
  - `http://127.0.0.1:8087`   community service
  - `http://127.0.0.1:8000`   workshop service
  - `http://127.0.0.1:5002`   chatbot API (`/chatbot/genai/ask`)
  - `http://127.0.0.1:5500`   MCP server
  - `http://127.0.0.1:8025`   MailHog UI
- The `crapi-chatbot` container exits the Docker network through Docker Desktop NAT to reach Ollama on the remote GPU machine.

## Requirements

- macOS or Linux (tested on macOS Intel / `x86_64`)
- Docker Desktop running
- Docker Compose v2.20+ (the root `docker-compose.yml` uses `include`)
- Miniconda (optional, for local Python agent dev)
- Node.js / `nvm` (optional, for React UI dev)
- A separate machine with an NVIDIA GPU running Ollama, reachable from the Mac

## Quick start

1. Clone this repo:

   ```bash
   git clone <your-repo-url> crAPI-LLM
   cd crAPI-LLM
   ```

2. Clone the crAPI submodule:

   ```bash
   git clone --depth 1 --branch develop https://github.com/OWASP/crAPI.git crapi
   ```

3. Copy `.env` and set your Ollama host IP:

   ```bash
   cp .env.example .env
   # edit .env and update OLLAMA_HOST_IP and CHATBOT_OPENAI_BASE_URL
   ```

4. Make sure Docker Desktop is running, then start the stack:

   ```bash
   docker compose up -d
   ```

5. Verify:

   ```bash
   docker compose ps
   curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8888
   ```

6. Test the chatbot:

   ```bash
   curl -s -X POST http://127.0.0.1:5002/chatbot/genai/ask \
     -H "Content-Type: application/json" \
     -d '{"message":"hello"}'
   ```

## Changing the Ollama IP

If your remote GPU machine gets a new IP, update only `.env`:

```bash
OLLAMA_HOST_IP=<new-ip>
CHATBOT_OPENAI_BASE_URL=http://<new-ip>:11434/v1/
```

Then recreate the chatbot container:

```bash
docker compose up -d
```

## Ollama setup on the GPU machine

Recommended for an RTX 4060 with 8 GB VRAM:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text:latest
```

Expose Ollama to the local network:

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

Make sure the host firewall allows inbound TCP `11434` from the Mac's subnet.

If you want models on a specific drive (e.g. `D:/OllamaModels` on Windows), set:

```bash
set OLLAMA_MODELS=D:\OllamaModels
```

or for WSL2 / Linux:

```bash
export OLLAMA_MODELS=/mnt/d/OllamaModels
```

## Why the `retriever_utils.py` patch?

crAPI's chatbot is hard-coded to use `OpenAIEmbeddings` for the `openai` provider. `OpenAIEmbeddings` tokenizes text with `tiktoken` and sends token-id arrays to `/v1/embeddings`. Ollama's OpenAI-compatible endpoint expects strings, so it returns `invalid input type`.

The patch in `infrastructure/crapi-chatbot-patches/retriever_utils.py` swaps in `OllamaEmbeddings` whenever a non-default `CHATBOT_OPENAI_BASE_URL` is set, and it is mounted over `/app/chatbot/retriever_utils.py` in the `crapi-chatbot` container.

## Roadmap and future additions

For the full phased plan, see `ROADMAP.md`.

crAPI gives us the vulnerable API and a built-in LLM chatbot, but it does **not** cover the full WAAP, runtime-security, and traffic-analysis story. Recommended additions:

1. **API gateway / WAAP layer**  
   Put Kong, Traefik, Envoy, or open-appsec in front of crAPI with rate limiting, JWT validation, WAF rules, and request/response logging. This maps to the WAAP, API gateway, and runtime security requirements.

2. **Traffic analysis and observability**  
   Add `Grafana` + `Loki` + `Prometheus` or `Vector` to collect and visualize API and agent traffic. This is needed for "runtime security" and "traffic analysis."

3. **Custom agent demo**  
   Build a small Python agent (Pydantic AI or LangChain) that calls crAPI endpoints via Ollama. The built-in chatbot is LangGraph; a second, simpler agent is useful for explaining "agent discovery," "agent-to-tool," and "agent-to-API" clearly.

4. **React UI**  
   A Vite + React frontend that shows the agent, the live API calls, and browser DevTools network traffic. This makes demos for non-technical audiences much more compelling.

5. **Write-ups**  
   Map every crAPI challenge to the OWASP API Top 10 2023, the OWASP Top 10 for LLM Applications, and plausible WAAP or API gateway mitigations.

## Project layout

```
crAPI-LLM/
├── .env                           # Docker Compose environment
├── docker-compose.yml             # includes crAPI + port overrides + patch mount
├── README.md                      # this file
├── agent/                         # (future) custom Python agent
├── docs/                          # (future) write-ups and mapping
├── gateway/                       # (future) API gateway / WAAP configs
├── infrastructure/                # support files for the lab
│   └── crapi-chatbot-patches/
│       └── retriever_utils.py     # Ollama embedding fix
├── ui/                            # (future) React UI
└── crapi/                         # cloned OWASP crAPI (develop branch)
```

## Useful commands

```bash
# View all running crAPI services
docker compose ps

# Follow the chatbot logs
docker compose logs -f crapi-chatbot

# Stop everything
docker compose down

# Stop and remove data volumes (destructive)
docker compose down -v

# Test the chatbot directly
curl -s -X POST http://127.0.0.1:5002/chatbot/genai/ask \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'

# Test Ollama from the Mac
curl http://<ollama-ip>:11434/api/tags
```

## License

This project structure and documentation are provided for educational and demo purposes. crAPI itself is licensed under Apache 2.0.
