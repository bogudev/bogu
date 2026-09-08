"""
Bogu Client — POC demo
=======================
Sends a message containing several PII types to an OpenAI-compatible LLM.
The proxy strips PII before the request leaves your machine and puts it
back when the response arrives.

Usage
-----
    export OPENAI_API_KEY=sk-...
    python examples/llm_demo.py

    # Use a different model or base URL (e.g. local Ollama):
    BASE_URL=http://localhost:11434/v1 MODEL=llama3 python examples/llm_demo.py
"""

import os

from openai import OpenAI

from bogu.proxy import BoguClient

# ── Config ────────────────────────────────────────────────────────────────────
MODEL = os.getenv("MODEL", "gpt-4o-mini")
BASE_URL = os.getenv("BASE_URL")  # None → default OpenAI endpoint
API_KEY = os.getenv("OPENAI_API_KEY", "sk-placeholder")

# ── Build the proxy (one line change from a raw OpenAI client) ────────────────
raw_client = OpenAI(api_key=API_KEY, **({"base_url": BASE_URL} if BASE_URL else {}))
client = BoguClient(raw_client, verbose=True)

# ── Demo messages ─────────────────────────────────────────────────────────────
# This simulates a user carelessly including PII in a prompt.
MESSAGES = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant. "
            "Summarise the user's request and confirm the details they provided."
        ),
    },
    {
        "role": "user",
        "content": (
            "Hi, I need help reviewing my insurance claim. "
            "My name details are in the file. "
            "You can reach me at john.doe@example.com or call +1 (415) 555-0182. "
            "My SSN is 123-45-6789 and I paid with card 4111 1111 1111 1111. "
            "The server at 192.168.1.42 has the relevant logs."
        ),
    },
]

# ── Single-turn call ──────────────────────────────────────────────────────────
print("\n" + "═" * 62)
print("  BOGU PROXY — Single-turn demo")
print("═" * 62)

response = client.chat.completions.create(
    model=MODEL,
    messages=MESSAGES,
)

print("\n✅  Final answer delivered to your app:")
print(f"    {response.content}\n")

# ── Multi-turn: same session, new user message ────────────────────────────────
print("═" * 62)
print("  BOGU PROXY — Multi-turn: same session, new PII")
print("═" * 62)

MESSAGES.append({"role": "assistant", "content": response.content})
MESSAGES.append(
    {
        "role": "user",
        "content": (
            "Actually, please also note my backup email is jane.smith@company.org "
            # The repeated value demonstrates stable tokens across turns.
            "and the first email john.doe@example.com is preferred. "
            "My new card ending is 5500 0000 0000 0004."
        ),
    }
)

response2 = client.chat.completions.create(
    model=MODEL,
    messages=MESSAGES,
)

print("\n✅  Final answer (turn 2):")
print(f"    {response2.content}\n")

# ── Show the full session map at the end ─────────────────────────────────────
print("═" * 62)
print("  SESSION MAP (all tokens minted so far)")
print("═" * 62)
for token, original in client.session_map.items():
    print(f"  {token:<22} →  {original}")
print()
