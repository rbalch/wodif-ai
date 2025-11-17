"""Notification service using Pushover"""

import logging
import requests

from app.config import Config


class NotificationService:
    """Handles Pushover notifications"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.enabled = Config.PUSHOVER_ENABLED

        if not self.enabled:
            self.logger.warning("Pushover notifications disabled (credentials not configured)")

    def send(self, message: str, title: str = "Wodify Signup", priority: int = 0) -> bool:
        """
        Send a notification via Pushover

        Args:
            message: Notification message
            title: Notification title
            priority: -2 (silent), -1 (quiet), 0 (normal), 1 (high), 2 (emergency)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            self.logger.warning(f"Notification skipped (disabled): {message}")
            return False

        url = "https://api.pushover.net/1/messages.json"

        data = {
            "token": Config.PUSHOVER_APP_TOKEN,
            "user": Config.PUSHOVER_USER_KEY,
            "message": message,
            "title": title,
            "priority": priority,
        }

        try:
            self.logger.info(f"Sending notification: {title}")
            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 1:
                    self.logger.info("✓ Notification sent successfully")
                    return True
                else:
                    self.logger.error(f"Pushover API error: {result}")
                    return False
            else:
                self.logger.error(f"HTTP {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False

    def notify_success(self, class_name: str, time_range: str, reasoning: str):
        """Send a success notification with class details"""
        message = f"Booked: {class_name}\nTime: {time_range}\n\nReason: {reasoning}"
        self.send(message, title="Wodify: Class Booked ✓", priority=0)

    def notify_unusual_selection(self, class_name: str, time_range: str, reasoning: str):
        """Send a notification about an unusual class selection"""
        message = f"⚠️ Unusual selection\n\nBooked: {class_name}\nTime: {time_range}\n\nReason: {reasoning}"
        self.send(message, title="Wodify: Unusual Booking", priority=1)

    def notify_error(self, error_message: str):
        """Send an error notification"""
        message = f"❌ Booking failed\n\n{error_message}"
        self.send(message, title="Wodify: Error", priority=1)
