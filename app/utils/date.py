"""Date utilities for calculating target booking dates"""

from datetime import datetime, timedelta


def get_target_date(days_ahead: int = 1) -> datetime:
    """
    Get the target date for booking

    Args:
        days_ahead: Number of days in the future (default: 1 for tomorrow)

    Returns:
        datetime object for the target date
    """
    return datetime.now() + timedelta(days=days_ahead)


def format_date_for_wodify(date: datetime) -> str:
    """
    Format date for Wodify calendar selection (M/D format)

    Args:
        date: datetime object

    Returns:
        Date string in "M/D" format (e.g., "11/14")
    """
    # Remove leading zeros: %-m and %-d on Linux, %#m and %#d on Windows
    # Using strftime with no padding, then manual formatting for cross-platform
    month = date.month
    day = date.day
    return f"{month}/{day}"


def get_human_readable_date(date: datetime) -> str:
    """
    Get human-readable date string

    Args:
        date: datetime object

    Returns:
        Date string like "Monday, November 14"
    """
    return date.strftime("%A, %B %d")
