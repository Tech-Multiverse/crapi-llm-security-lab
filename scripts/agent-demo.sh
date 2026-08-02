#!/usr/bin/env bash
# Demo: run the custom Python agent to sign up, log in, and read the dashboard.
# Requires the crapi-llm Conda environment and OLLAMA_BASE_URL to be set.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! conda info --envs | grep -q '^crapi-llm'; then
  echo "Conda environment 'crapi-llm' not found. Create it with:"
  echo "  conda create -n crapi-llm python=3.11 -y"
  exit 1
fi

conda run -n crapi-llm python agent/simple_agent.py \
  "Sign up a new crAPI user with a unique email and phone number, log them in, fetch the dashboard, then call done with a short summary."
