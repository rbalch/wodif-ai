#!/usr/bin/env python3
"""
Demo script to test LLM-based class selection
Uses dummy class data to test the Ollama integration
"""

import sys
import os
import json

try:
    import ollama
except ImportError:
    print("ERROR: ollama package not installed")
    print("Install with: pip install ollama")
    sys.exit(1)


# Configuration
MODEL = "qwen3:8b"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
SYSTEM_PROMPT_FILE = "scripts/system_prompt.txt"

# Create client with custom host
client = ollama.Client(host=OLLAMA_HOST)

# Dummy class data
DUMMY_CLASSES = """00: 5:00 AM - 6:00 AM    | OPEN GYM             | Coach:                 | Button: BOOK (#b4-b5-l2-593_11-button_classNoLimit)
01: 6:00 AM - 7:00 AM    | CrossFit: 6:00 AM    | Coach: Devin Leishman  | Button: BOOK (#b4-b5-l2-593_12-button_reservationOpen)
02: 7:00 AM - 8:00 AM    | CrossFit: 7:00 AM    | Coach: Tyler Johnson Grimes | Button: MANAGE (#b4-b5-l2-593_13-button_reservationOpen)
03: 8:00 AM - 9:00 AM    | CrossFit: 8:00 AM    | Coach: Devin Leishman  | Button: BOOK (#b4-b5-l2-593_14-button_reservationOpen)
04: 9:00 AM - 10:00 AM   | CrossFit: 9:00 AM    | Coach: Devin Leishman  | Button: BOOK (#b4-b5-l2-593_15-button_reservationOpen)
05: 10:00 AM - 12:00 PM  | OPEN GYM             | Coach:                 | Button: BOOK (#b4-b5-l2-593_16-button_classNoLimit)
06: 12:00 PM - 1:00 PM   | CrossFit: 12:00 PM   | Coach: Devin Leishman  | Button: BOOK (#b4-b5-l2-593_17-button_reservationOpen)
07: 1:00 PM - 4:30 PM    | OPEN GYM 1pm-430pm   | Coach:                 | Button: BOOK (#b4-b5-l2-593_18-button_classNoLimit)
08: 4:30 PM - 5:30 PM    | CrossFit: 4:30 PM    | Coach: Devin Leishman  | Button: BOOK (#b4-b5-l2-593_19-button_reservationOpen)
09: 5:30 PM - 6:30 PM    | CrossFit: 5:30 PM    | Coach: Devin Leishman  | Button: BOOK (#b4-b5-l2-593_20-button_reservationOpen)"""


def load_system_prompt():
    """Load the system prompt from file"""
    try:
        with open(SYSTEM_PROMPT_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Could not find {SYSTEM_PROMPT_FILE}")
        sys.exit(1)


def select_class_with_llm(classes_text, system_prompt):
    """
    Use Ollama to select the best class based on preferences
    Returns the parsed JSON response
    """
    print("=" * 60)
    print("SENDING TO LLM:")
    print("=" * 60)
    print(f"System Prompt: {system_prompt[:100]}...")
    print(f"\nClasses Data:\n{classes_text}\n")
    print("=" * 60)
    print("WAITING FOR LLM RESPONSE...")
    print("=" * 60)

    try:
        response = client.chat(
            model=MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': f"Here are the available classes:\n\n{classes_text}\n\nWhich class should I book?"
                }
            ],
            format='json',  # Request JSON output
            options={
                'temperature': 0  # Deterministic output
            }
        )

        assistant_message = response['message']['content']

        print("\n" + "=" * 60)
        print("LLM RESPONSE (raw):")
        print("=" * 60)
        print(assistant_message)
        print("=" * 60)

        # Parse JSON
        result = json.loads(assistant_message)

        print("\n" + "=" * 60)
        print("PARSED RESULT:")
        print("=" * 60)
        print(f"Selected Index: {result['selected_index']}")
        print(f"Reasoning: {result['reasoning']}")
        print(f"Notify User: {result.get('notify_user', 'NOT SET')}")
        print("=" * 60)

        return result

    except json.JSONDecodeError as e:
        print(f"\nERROR: Could not parse JSON response: {e}")
        print(f"Raw response: {assistant_message}")
        return None
    except Exception as e:
        print(f"\nERROR: {e}")
        return None


def main():
    print(f"LLM Class Selection Demo")
    print(f"Model: {MODEL}")
    print(f"Host: {OLLAMA_HOST}\n")

    # Load system prompt
    system_prompt = load_system_prompt()

    # Get LLM selection
    result = select_class_with_llm(DUMMY_CLASSES, system_prompt)

    if result:
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"The LLM selected class #{result['selected_index']}")
        print(f"Reason: {result['reasoning']}")

        notify_user = result.get('notify_user', False)
        if notify_user:
            print(f"\n⚠️  NOTIFICATION TRIGGERED")
            print(f"   This selection is unusual and requires user attention")
            print(f"   Reason: {result['reasoning']}")
        else:
            print(f"\n✓  No notification needed - standard class booking")

        # Show which class was selected
        class_lines = DUMMY_CLASSES.split('\n')
        selected_index = result['selected_index']
        if 0 <= selected_index < len(class_lines):
            print(f"\nSelected class details:")
            print(f"  {class_lines[selected_index]}")
    else:
        print("\n" + "=" * 60)
        print("FAILED to get valid selection from LLM")
        print("=" * 60)


if __name__ == "__main__":
    main()
