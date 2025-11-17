#!/usr/bin/env python3
"""
Simple chat script to test Ollama connection
Usage: python3 scripts/ollama_chat_test.py
"""

import sys
import os

try:
    import ollama
except ImportError:
    print("ERROR: ollama package not installed")
    print("Install with: pip install ollama")
    sys.exit(1)


# Configuration
MODEL = "qwen3:8b"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")

# Create client with custom host
client = ollama.Client(host=OLLAMA_HOST)


def chat():
    """Simple chat loop"""
    print(f"Ollama Chat Test (Model: {MODEL})")
    print(f"Host: {OLLAMA_HOST}")
    print("Type 'quit' or 'exit' to end\n")

    conversation_history = []

    while True:
        # Get user input
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        # Add user message to history
        conversation_history.append({
            'role': 'user',
            'content': user_input
        })

        # Call Ollama using the configured client
        try:
            response = client.chat(
                model=MODEL,
                messages=conversation_history
            )

            assistant_message = response['message']['content']

            # Add assistant response to history
            conversation_history.append({
                'role': 'assistant',
                'content': assistant_message
            })

            # Print response
            print(f"\n{assistant_message}\n")

        except Exception as e:
            print(f"\nERROR: {e}\n")
            print("Make sure Ollama is running and the model is pulled:")
            print(f"  docker exec -it wodify-ollama ollama pull {MODEL}\n")


if __name__ == "__main__":
    chat()
