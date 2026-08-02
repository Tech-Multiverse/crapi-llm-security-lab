# crAPI-LLM Security Lab

> UNDER CONSTRUCTION 🚧
> This project is an active work in progress!

A local, shareable lab for API security, LLM application security, and agentic AI demos.

It combines the OWASP crAPI vulnerable API application with an Ollama LLM (local or remote), a LangGraph-based chatbot/MCP server, a custom Python agent, and an optional API gateway with traffic analysis.

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
- A root `.env` with all the configuration in one place; copy it from `.env.example` and point it at your Ollama instance.
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
  ├─ agent/ Python demos
  ├─ gateway/ Kong + Prometheus + Grafana
  └─ Node.js / React UI (future)

Ollama (local install, remote GPU box, or Docker)
  └─ llama3.1:8b        (chat / tool calling)
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

- macOS, Linux, or Windows with WSL2 / Docker Desktop (tested on macOS Intel / `x86_64`)
- Docker running
- Docker Compose v2.20+ (the root `docker-compose.yml` uses `include`)
- Miniconda (optional, for local Python agent dev)
- Node.js / `nvm` (optional, for React UI dev)
- Ollama reachable from Docker. Options:
  - **Local install** on the same machine running Docker (works with CPU or GPU)
  - **Remote machine** (e.g. Linux box with a GPU) on the same network
  - **Docker with GPU support** (optional, requires `nvidia-container-toolkit`)

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

3. Copy `.env` and point crAPI at your Ollama server:

   ```bash
   cp .env.example .env
   # edit .env and set OLLAMA_HOST_IP to the IP or hostname where Ollama is reachable
   # from the crAPI container (see "Pointing crAPI to Ollama" below for examples).
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

## Pointing crAPI to Ollama

The chatbot and agent use the OpenAI-compatible endpoint that Ollama exposes on port `11434`. Update `.env` so the crAPI container can reach it.

Common setups:

| Where Ollama runs | `OLLAMA_HOST_IP` value | Notes |
|---------------------|-------------------------|-------|
| Same host as Docker Desktop (macOS/Windows) | `host.docker.internal` | Docker Desktop resolves this to the host. |
| Same host, Linux Docker Engine | LAN IP of the host (e.g. `192.168.1.42`) or `172.17.0.1` | `host.docker.internal` is not automatic on Linux Docker Engine. |
| Remote GPU box / another machine | Its IP (e.g. `192.168.1.50`) | Firewall must allow TCP `11434` from the Docker host. |

For example, with a remote GPU machine:

```bash
OLLAMA_HOST_IP=192.168.1.50
CHATBOT_OPENAI_BASE_URL=http://${OLLAMA_HOST_IP}:11434/v1/
```

For a local Ollama on Docker Desktop macOS/Windows:

```bash
OLLAMA_HOST_IP=host.docker.internal
CHATBOT_OPENAI_BASE_URL=http://${OLLAMA_HOST_IP}:11434/v1/
```

For the agent running on the host (not in Docker), you can also export:

```bash
export OLLAMA_BASE_URL=http://${OLLAMA_HOST_IP}:11434/v1
```

After editing `.env`, recreate the chatbot container:

```bash
docker compose up -d
```

## Ollama setup

These instructions work on Linux, macOS, or Windows (with WSL2 / Docker). They assume you want to keep everything self-hosted; no third-party LLM API account is needed.

### 1. Install Ollama

Follow the official guide for your OS:

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: use the installer from https://ollama.com/download/windows
# or run inside WSL2 with the same command as Linux.
```

### 2. Pull the models

Recommended models that fit on an 8 GB GPU or a CPU host:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text:latest
```

### 3. Expose Ollama to the network

By default Ollama only listens on `127.0.0.1:11434`. If you run crAPI in Docker, the container needs to reach it, so bind to all interfaces:

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

On Windows Command Prompt:

```cmd
set OLLAMA_HOST=0.0.0.0
ollama serve
```

On Windows PowerShell:

```powershell
$env:OLLAMA_HOST="0.0.0.0"
ollama serve
```

If Ollama is on a remote machine, make sure the host firewall allows inbound TCP `11434` from the Docker host's subnet.

### 4. Optional: store models on a different drive

On Windows:

```cmd
set OLLAMA_MODELS=D:\OllamaModels
```

On Linux / WSL2:

```bash
export OLLAMA_MODELS=/mnt/d/OllamaModels
```

## Tested configuration

This repo was developed with:

- A Mac host running Docker Desktop
- A separate Linux machine with an NVIDIA GPU running Ollama (`llama3.1:8b` and `nomic-embed-text:latest`)
- The Mac reaching Ollama over the LAN at `http://192.168.4.55:11434/v1`

Any setup where Docker can reach Ollama at the URL you put in `.env` should work the same way.

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
├── agent/                         # custom Python agent demos
├── docs/                          # write-ups and challenge mapping
├── gateway/                       # Kong + Prometheus + Grafana configs
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

# Test Ollama from the Docker host
curl http://${OLLAMA_HOST_IP}:11434/api/tags
```

## License

This project structure and documentation are provided for educational and demo purposes. crAPI itself is licensed under Apache 2.0.
