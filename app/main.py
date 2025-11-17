#!/usr/bin/env python3
"""
Wodify Auto-Signup Application
Main entry point for automated class booking
"""

import sys
from app.config import Config
from app.utils.logger import setup_logger
from app.utils.date import get_target_date, format_date_for_wodify, get_human_readable_date
from app.services.browser import BrowserService
from app.services.llm import LLMService
from app.services.notification import NotificationService


def main() -> int:
    """
    Main application workflow

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info("Wodify Auto-Signup Starting")
    logger.info("=" * 60)

    # Validate configuration
    is_valid, errors = Config.validate()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return 1

    # Calculate target date
    target_date = get_target_date(Config.DAYS_AHEAD)
    target_date_str = format_date_for_wodify(target_date)
    human_date = get_human_readable_date(target_date)

    logger.info(f"Target date: {human_date} ({target_date_str})")

    # Initialize services
    notification = NotificationService(logger)
    llm_service = LLMService(logger)

    try:
        # Browser automation
        with BrowserService(logger) as browser:
            # Step 1: Login
            logger.info("Step 1: Logging in to Wodify...")
            browser.login()

            # Step 2: Navigate to calendar
            logger.info("Step 2: Opening Class Calendar...")
            browser.navigate_to_calendar()

            # Step 3: Select target date
            logger.info(f"Step 3: Selecting date {target_date_str}...")
            browser.select_date(target_date_str)

            # Step 4: Extract classes
            logger.info("Step 4: Extracting class list...")
            classes = browser.extract_classes()

            if not classes:
                raise Exception("No classes found for the target date")

            logger.info(f"Found {len(classes)} classes:")
            for cls in classes:
                logger.info(f"  {cls.to_display_string()}")

            # Step 5: LLM selection
            logger.info("Step 5: Consulting LLM for class selection...")
            llm_response = llm_service.select_class(classes)

            selected_class = classes[llm_response.selected_index]
            logger.info(f"Selected: {selected_class.class_name} at {selected_class.time_range}")
            logger.info(f"Reason: {llm_response.reasoning}")

            # Step 6: Book the class
            logger.info("Step 6: Booking selected class...")
            browser.book_class(selected_class)

            # Step 7: Notifications
            logger.info("Step 7: Handling notifications...")
            if llm_response.notify_user:
                logger.info("Sending notification (unusual selection)")
                notification.notify_unusual_selection(
                    class_name=selected_class.class_name,
                    time_range=selected_class.time_range,
                    reasoning=llm_response.reasoning,
                )
            else:
                logger.info("No notification needed (standard booking)")

            logger.info("=" * 60)
            logger.info("✓ SUCCESS: Class booked successfully")
            logger.info("=" * 60)
            return 0

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ERROR: {str(e)}")
        logger.error("=" * 60)

        # Send error notification
        notification.notify_error(str(e))

        return 1


if __name__ == "__main__":
    sys.exit(main())
