# crAPI-LLM React UI

A minimal demo interface for the crAPI-LLM Security Lab.

## Tabs

- **Home** — overview of the lab.
- **Chatbot** — talk to crAPI's LangGraph + Ollama chatbot.
- **API Explorer** — send requests directly to crAPI endpoints.
- **Scenarios** — one-click replay of attack/defense demos.

## Local development

```bash
npm install
npm run dev
```

The Vite dev server proxies API calls to crAPI, Kong, and the chatbot service.

## Production build

```bash
npm run build
```

The `Dockerfile` builds the app and serves it with Nginx, proxying API routes to the crAPI stack.

## Notes

- The UI expects the same-origin API routes set up in `nginx.conf` and `vite.config.js`.
- No third-party LLM keys are required; everything uses a self-hosted Ollama backend.
