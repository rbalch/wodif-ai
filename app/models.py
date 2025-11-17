"""Data models for the Wodify signup application"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClassInfo:
    """Represents a single class from the Wodify schedule"""

    index: int
    time_range: str
    class_name: str
    coach: str
    button_id: Optional[str]
    button_text: str

    def to_display_string(self) -> str:
        """Format as display string for LLM input"""
        button_info = f"{self.button_text} (#{self.button_id})" if self.button_id else f"{self.button_text} (#None)"
        return f"{self.index:02d}: {self.time_range:20s} | {self.class_name:20s} | Coach: {self.coach:15s} | Button: {button_info}"

    def is_bookable(self) -> bool:
        """Check if this class can be booked"""
        return self.button_id is not None and "BOOK" in self.button_text.upper()


@dataclass
class LLMResponse:
    """Response from the LLM class selection"""

    selected_index: int
    reasoning: str
    notify_user: bool

    @classmethod
    def from_dict(cls, data: dict) -> "LLMResponse":
        """Create from JSON response dictionary"""
        return cls(
            selected_index=data["selected_index"],
            reasoning=data["reasoning"],
            notify_user=data.get("notify_user", False),
        )
