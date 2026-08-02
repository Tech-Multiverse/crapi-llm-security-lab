# crAPI-LLM Security Lab Roadmap

This is the living plan for the crAPI-LLM security lab. Each phase builds on the previous one. The emphasis is on **validating what is already running before adding new features**.

Legend:

- `✅` Completed
- `🔄` In progress
- `⏳` Not started / planned
- `🔍` Testing / validation

## Phase 0 — Environment baseline

**Goal:** Make the local machine and the remote GPU host ready to run the lab.

| # | Task | Status |
|---|------|--------|
| 0.1 | Docker, Docker Compose, and network checks | `✅` |
| 0.2 | Miniconda `crapi-llm` Python environment | `✅` |
| 0.3 | Node.js (via `nvm`) for the future React UI | `✅` |
| 0.4 | Clone OWASP crAPI `develop` branch | `✅` |
| 0.5 | Create top-level repo layout (`agent/`, `ui/`, `docs/`, `infrastructure/`, `gateway/`) | `✅` |

**Validation gate:** `docker compose ps` shows all crAPI services healthy.

## Phase 1 — crAPI API security walkthrough

**Goal:** Understand the classic OWASP API Security Top 10 challenges built into crAPI (challenges 1–15). Write short notes on the exploit, the vulnerable endpoint, and a defensive mitigation.

| # | Task | Status |
|---|------|--------|
| 1.1 | Deploy crAPI and map services/ports | `✅` |
| 1.2 | Challenge 1–5 walkthrough | `✅` |
| 1.3 | Challenge 6–10 walkthrough | `✅` |
| 1.4 | Challenge 11–15 walkthrough | `⏳` |
| 1.5 | Document each finding in `docs/` with endpoint, payload, and mitigation | `✅` |

**Validation gate:** For each completed block, at least one challenge can be reproduced with `curl` or `httpie`.

## Phase 2 — crAPI + Ollama LLM integration

**Goal:** Run the crAPI chatbot against the remote Ollama server instead of a cloud OpenAI API.

| # | Task | Status |
|---|------|--------|
| 2.1 | Stand up remote Ollama on the GPU host | `✅` |
| 2.2 | Pull `llama3.1:8b` and `nomic-embed-text:latest` | `✅` |
| 2.3 | Configure crAPI chatbot to use the Ollama OpenAI-compatible endpoint | `✅` |
| 2.4 | Patch `retriever_utils.py` so the Ollama embedding step works | `✅` |
| 2.5 | Document IP-change procedure in README | `✅` |

**Validation gate:** `curl -X POST http://127.0.0.1:5002/chatbot/genai/ask -d '{"message":"hello"}'` returns a real assistant message.

## Phase 2.5 — LLM / MCP / tool-calling validation

**Goal:** Confirm that the agentic parts of the chatbot (MCP server, OpenAPI tool calling, Chroma RAG, LangGraph) are healthy before running the LLM security challenges.

| # | Task | Status |
|---|------|--------|
| 2.5.1 | List tools exposed by the MCP server on port `5500` | `✅` |
| 2.5.2 | Verify OpenAPI tool calling works through the chatbot | `✅` |
| 2.5.3 | Test the Chroma / RAG retrieval flow | `✅` |
| 2.5.4 | Document the MCP and chatbot endpoints in `docs/` | `✅` |

**Validation gate:** The MCP server returns a tool list, and the chatbot can be asked to perform an action using a tool.

## Phase 3 — LLM challenges and prompt injection

**Goal:** Run and document crAPI's LLM challenges (16–18) and test common prompt-injection patterns.

| # | Task | Status |
|---|------|--------|
| 3.1 | Challenge 16 — prompt injection | `⏳` |
| 3.2 | Challenge 17 — credential extraction | `⏳` |
| 3.3 | Challenge 18 — action on behalf of another user | `⏳` |
| 3.4 | Additional prompt-injection and jailbreak tests | `⏳` |
| 3.5 | Document mitigations for each class of LLM attack | `⏳` |

**Validation gate:** Each challenge can be reproduced and the prompt / response chain is captured.

## Phase 4 — Custom Python agent

**Goal:** Build a small, self-contained agent that calls crAPI APIs through Ollama, separate from the built-in chatbot. This is useful for demonstrating agent discovery, tool calling, and agent-to-API attacks.

| # | Task | Status |
|---|------|--------|
| 4.1 | Select an agent framework (Pydantic AI, LangChain, or plain OpenAI client) | `⏳` |
| 4.2 | Implement a minimal agent that can sign up, log in, and list vehicles | `⏳` |
| 4.3 | Add tool-calling support so the agent can use crAPI endpoints | `⏳` |
| 4.4 | Demonstrate a prompt-injection or overpermissive tool call | `⏳` |
| 4.5 | Write `agent/README.md` with setup and run instructions | `⏳` |

**Validation gate:** Running one command starts the agent and it successfully makes an authenticated crAPI API call via Ollama.

## Phase 5 — API gateway / WAAP and traffic analysis

**Goal:** Add an open-source API gateway or WAAP in front of crAPI and observe the traffic. This maps to the runtime-security and traffic-analysis parts of the lab.

| # | Task | Status |
|---|------|--------|
| 5.1 | Choose a gateway (Kong, Traefik, Envoy, open-appsec, or Caddy with plugins) | `⏳` |
| 5.2 | Deploy the gateway in front of crAPI | `⏳` |
| 5.3 | Configure rate limiting, JWT validation, or basic WAF rules | `⏳` |
| 5.4 | Capture and replay an attack through the gateway | `⏳` |
| 5.5 | Add traffic analysis (Grafana / Loki / Prometheus or `Vector` + `ClickHouse`) | `⏳` |

**Validation gate:** A known crAPI attack is blocked or logged by the gateway, and the event is visible in the analysis dashboard.

## Phase 6 — React UI and packaging

**Goal:** Make the lab easy to demo and share.

| # | Task | Status |
|---|------|--------|
| 6.1 | Initialize a Vite + React project in `ui/` | `⏳` |
| 6.2 | Build a simple chat / API explorer interface | `⏳` |
| 6.3 | Connect the UI to the chatbot and direct crAPI endpoints | `⏳` |
| 6.4 | Create attack / defense scenario scripts | `⏳` |
| 6.5 | Final `README.md` refresh, demo recording, and release notes | `⏳` |

**Validation gate:** A non-technical user can run `docker compose up` and open `http://127.0.0.1:8888` or the React UI to see the lab in action.

## Current focus

Phase 1 and Phase 3 are the next natural steps. Phase 2.5 is already validated and documented in `docs/phase-2-5-validation.md`.

## Notes

- Phase numbers are not strictly sequential. Gateway and UI work can start in parallel once the API and LLM foundations are validated.
- The `.env` file in the repo is local and should not be committed; see `.env.example` for the template.
- The `crapi/` directory is a cloned third-party repo and should not be committed into this repo.
