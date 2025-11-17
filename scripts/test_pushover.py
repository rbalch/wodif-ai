#!/usr/bin/env python3
"""
Test script for Pushover notifications
Usage: python3 scripts/test_pushover.py

Setup:
1. Sign up at https://pushover.net/ ($5 one-time)
2. Create an application to get APP_TOKEN
3. Get your USER_KEY from the dashboard
4. Set environment variables or add to .env:
   PUSHOVER_USER_KEY=your_user_key
   PUSHOVER_APP_TOKEN=your_app_token
"""

import os
import sys
import requests


def send_pushover(message, title="Wodify Signup", priority=0):
    """
    Send a notification via Pushover

    Args:
        message: The notification message
        title: Notification title (default: "Wodify Signup")
        priority: -2 (silent), -1 (quiet), 0 (normal), 1 (high), 2 (emergency)

    Returns:
        True if successful, False otherwise
    """
    user_key = os.environ.get("PUSHOVER_USER_KEY")
    app_token = os.environ.get("PUSHOVER_APP_TOKEN")

    if not user_key or not app_token:
        print("ERROR: Missing Pushover credentials")
        print("Set PUSHOVER_USER_KEY and PUSHOVER_APP_TOKEN environment variables")
        return False

    url = "https://api.pushover.net/1/messages.json"

    data = {
        "token": app_token,
        "user": user_key,
        "message": message,
        "title": title,
        "priority": priority
    }

    try:
        response = requests.post(url, data=data)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == 1:
                print(f"✓ Notification sent successfully!")
                return True
            else:
                print(f"✗ Pushover API returned error: {result}")
                return False
        else:
            print(f"✗ HTTP Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Failed to send notification: {e}")
        return False


def main():
    print("Pushover Notification Test")
    print("=" * 50)

    # Check for credentials
    user_key = os.environ.get("PUSHOVER_USER_KEY")
    app_token = os.environ.get("PUSHOVER_APP_TOKEN")

    if user_key:
        print(f"✓ PUSHOVER_USER_KEY: {user_key[:10]}...{user_key[-4:]}")
    else:
        print("✗ PUSHOVER_USER_KEY: Not set")

    if app_token:
        print(f"✓ PUSHOVER_APP_TOKEN: {app_token[:10]}...{app_token[-4:]}")
    else:
        print("✗ PUSHOVER_APP_TOKEN: Not set")

    print("=" * 50)

    if not user_key or not app_token:
        print("\nSetup instructions:")
        print("1. Sign up at https://pushover.net/")
        print("2. Download the app on your phone ($5 one-time)")
        print("3. Create an application at https://pushover.net/apps/build")
        print("4. Set environment variables:")
        print("   export PUSHOVER_USER_KEY=your_user_key")
        print("   export PUSHOVER_APP_TOKEN=your_app_token")
        print("\nOr add to your .env file")
        sys.exit(1)

    # Send test notification
    print("\nSending test notification...")
    success = send_pushover(
        message="This is a test message from your Wodify signup script! 🏋️",
        title="Wodify Test",
        priority=0
    )

    if success:
        print("\n✓ Success! Check your phone for the notification.")
    else:
        print("\n✗ Failed to send notification. Check your credentials.")
        sys.exit(1)


if __name__ == "__main__":
    main()
