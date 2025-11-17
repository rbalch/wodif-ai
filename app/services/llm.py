"""LLM service using Ollama for intelligent class selection"""

import json
import logging
import ollama

from app.models import ClassInfo, LLMResponse
from app.config import Config


class LLMService:
    """Handles Ollama interactions for class selection"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.client = ollama.Client(host=Config.OLLAMA_HOST)
        self.system_prompt = Config.get_system_prompt()

    def select_class(self, classes: list[ClassInfo]) -> LLMResponse:
        """
        Use LLM to select the best class from available options

        Args:
            classes: List of ClassInfo objects

        Returns:
            LLMResponse with selected_index, reasoning, and notify_user flag
        """
        if not classes:
            raise ValueError("No classes provided for selection")

        # Format classes as display strings
        classes_text = "\n".join([c.to_display_string() for c in classes])

        self.logger.info(f"Sending {len(classes)} classes to LLM for selection")
        self.logger.debug(f"Classes:\n{classes_text}")

        try:
            response = self.client.chat(
                model=Config.OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": f"Here are the available classes:\n\n{classes_text}\n\nWhich class should I book?",
                    },
                ],
                format="json",  # Request structured JSON output
                options={"temperature": 0},  # Deterministic
            )

            response_text = response["message"]["content"]
            self.logger.debug(f"LLM raw response: {response_text}")

            # Parse JSON response
            result_dict = json.loads(response_text)
            llm_response = LLMResponse.from_dict(result_dict)

            self.logger.info(f"LLM selected class #{llm_response.selected_index}")
            self.logger.info(f"Reasoning: {llm_response.reasoning}")
            self.logger.info(f"Notify user: {llm_response.notify_user}")

            # Validate the selection
            if llm_response.selected_index < 0 or llm_response.selected_index >= len(classes):
                raise ValueError(
                    f"LLM selected invalid index {llm_response.selected_index} (valid range: 0-{len(classes) - 1})"
                )

            return llm_response

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON response: {e}")
            self.logger.error(f"Raw response: {response_text}")
            raise Exception(f"LLM returned invalid JSON: {e}")

        except Exception as e:
            self.logger.error(f"Error during LLM selection: {e}")
            raise
