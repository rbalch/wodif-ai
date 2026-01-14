"""Configuration management for the Wodify signup application"""

import os
from pathlib import Path


class Config:
    """Application configuration loaded from environment variables"""

    # Paths
    BASE_DIR = Path(__file__).parent
    PROMPTS_DIR = BASE_DIR / "prompts"
    SYSTEM_PROMPT_FILE = PROMPTS_DIR / "system_prompt.txt"

    # Wodify credentials
    WODIFY_EMAIL = os.environ.get("EMAIL", "")
    WODIFY_PASSWORD = os.environ.get("PASSWORD", "")
    WODIFY_URL = "https://app.wodify.com"

    # Scheduling
    DAYS_AHEAD = int(os.environ.get("DAYS_AHEAD", "1"))  # Book for tomorrow by default

    # Ollama configuration
    OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")

    # Pushover configuration
    PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY", "")
    PUSHOVER_APP_TOKEN = os.environ.get("PUSHOVER_APP_TOKEN", "")
    PUSHOVER_ENABLED = bool(PUSHOVER_USER_KEY and PUSHOVER_APP_TOKEN)

    # Browser configuration
    HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
    SCREENSHOT_DIR = BASE_DIR.parent / "screenshots"

    # Timeouts (milliseconds)
    PAGE_LOAD_TIMEOUT = 30000
    ELEMENT_WAIT_TIMEOUT = 10000
    CALENDAR_LOAD_WAIT = 5000

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate configuration
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        if not cls.WODIFY_EMAIL:
            errors.append("EMAIL environment variable not set")

        if not cls.WODIFY_PASSWORD:
            errors.append("PASSWORD environment variable not set")

        if not cls.SYSTEM_PROMPT_FILE.exists():
            errors.append(f"System prompt file not found: {cls.SYSTEM_PROMPT_FILE}")

        if not cls.PUSHOVER_ENABLED:
            errors.append("Pushover credentials not set (notifications disabled)")

        return (len(errors) == 0, errors)

    @classmethod
    def get_system_prompt(cls) -> str:
        """Load system prompt from file"""
        with open(cls.SYSTEM_PROMPT_FILE, "r") as f:
            return f.read()
