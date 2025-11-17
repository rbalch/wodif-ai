"""Browser automation service using Playwright"""

import re
import logging
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, Playwright

from app.models import ClassInfo
from app.config import Config


class BrowserService:
    """Handles all Playwright browser automation for Wodify"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def start(self):
        """Start the browser"""
        self.logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=Config.HEADLESS,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )

        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
        )

        self.page = context.new_page()
        self.logger.info("Browser started successfully")

    def close(self):
        """Close the browser and cleanup"""
        if self.browser:
            self.logger.info("Closing browser...")
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def attempt_login(self) -> bool:
        """
        Attempt to login to Wodify

        Returns:
            True if login successful, False otherwise
        """
        # Try primary login selector
        login_link = self.page.get_by_text("Login", exact=False)
        if login_link.count() > 0:
            self.logger.info("Found login link (text selector)")
            login_link.first.click()
            self.page.wait_for_timeout(2000)

            self.page.get_by_role("textbox", name=re.compile("Email", re.I)).fill(Config.WODIFY_EMAIL)
            self.page.get_by_role("textbox", name=re.compile("Password", re.I)).fill(Config.WODIFY_PASSWORD)
            self.page.get_by_role("button", name=re.compile("Sign in", re.I)).click()
            self.page.wait_for_load_state("networkidle")

            self.logger.info("Login successful")
            return True

        # Try alternative login selector
        alt_login = self.page.get_by_role("link", name=re.compile("Login", re.I))
        if alt_login.count() > 0:
            self.logger.info("Found login link (role selector)")
            alt_login.first.click()
            self.page.wait_for_timeout(2000)

            self.page.get_by_role("textbox", name=re.compile("Email", re.I)).fill(Config.WODIFY_EMAIL)
            self.page.get_by_role("textbox", name=re.compile("Password", re.I)).fill(Config.WODIFY_PASSWORD)
            self.page.get_by_role("button", name=re.compile("Sign in", re.I)).click()
            self.page.wait_for_load_state("networkidle")

            self.logger.info("Login successful (alternative method)")
            return True

        self.logger.warning("No login link found")
        return False

    def login(self):
        """Login to Wodify with retry logic"""
        self.logger.info(f"Navigating to {Config.WODIFY_URL}")
        self.page.goto(Config.WODIFY_URL, wait_until="networkidle")
        self.page.wait_for_timeout(3000)

        # First attempt
        if self.attempt_login():
            return

        # Retry with page refresh
        self.logger.warning("Login failed, refreshing page and retrying...")
        self.page.reload(wait_until="networkidle")
        self.page.wait_for_timeout(3000)

        if not self.attempt_login():
            raise Exception("Failed to login after 2 attempts")

    def navigate_to_calendar(self):
        """Navigate to the Class Calendar"""
        self.logger.info("Opening Class Calendar...")
        self.page.get_by_role("menuitem", name=re.compile("Class Calendar", re.I)).click()
        self.page.wait_for_timeout(Config.CALENDAR_LOAD_WAIT)
        self.logger.info("Class Calendar opened")

    def select_date(self, date_str: str):
        """
        Select a specific date in the calendar

        Args:
            date_str: Date string in "M/D" format (e.g., "11/14")
        """
        self.logger.info(f"Selecting date: {date_str}")
        date_pattern = f".*{re.escape(date_str)}$"
        date_elements = self.page.locator("div").filter(has_text=re.compile(date_pattern)).all()

        if date_elements:
            date_elements[0].click()
            self.logger.info(f"Clicked on {date_str}")
            self.page.wait_for_timeout(3000)
        else:
            raise Exception(f"Could not find date element for {date_str}")

    def extract_classes(self) -> list[ClassInfo]:
        """
        Extract class information from the calendar

        Returns:
            List of ClassInfo objects
        """
        self.logger.info("Extracting class information...")
        rows = self.page.locator(".list-item[data-list-item]")
        count = rows.count()

        if count == 0:
            raise Exception("No classes found on calendar")

        classes = []
        for i in range(count):
            row = rows.nth(i)

            # Extract time range
            time_range = ""
            time_left = row.locator(".list-item-content-left").first
            if time_left.count() > 0:
                time_range = time_left.inner_text().split("\n")[0]

            # Extract class name
            class_name = ""
            name_elem = row.locator(".font-size-m span").first
            if name_elem.count() > 0:
                class_name = name_elem.inner_text()

            # Extract coach name
            coach = ""
            coach_elem = row.locator("a[href='#']")
            if coach_elem.count() > 0:
                coach = coach_elem.inner_text()

            # Extract button info
            button = row.locator("button").first
            button_id = None
            button_text = ""
            if button.count() > 0:
                button_id = button.get_attribute("id")
                button_text = button.inner_text()

            class_info = ClassInfo(
                index=i,
                time_range=time_range,
                class_name=class_name,
                coach=coach,
                button_id=button_id,
                button_text=button_text,
            )
            classes.append(class_info)

        self.logger.info(f"Extracted {len(classes)} classes")
        return classes

    def book_class(self, class_info: ClassInfo):
        """
        Book a specific class

        Args:
            class_info: ClassInfo object with button_id to click
        """
        if not class_info.button_id:
            raise Exception(f"No button ID for class: {class_info.class_name}")

        self.logger.info(f"Booking class: {class_info.class_name} at {class_info.time_range}")

        # Click the book button
        self.page.locator(f"#{class_info.button_id}").click()
        self.logger.info("Clicked book button")
        self.page.wait_for_timeout(2000)

        # Click confirm
        try:
            self.page.get_by_role("button", name="Confirm Booking").click()
            self.logger.info("Clicked Confirm Booking")
            self.page.wait_for_timeout(3000)
            self.logger.info("✓ Booking completed successfully")
        except Exception as e:
            raise Exception(f"Failed to confirm booking: {e}")

    def take_screenshot(self, filename: str):
        """Take a screenshot for debugging"""
        Config.SCREENSHOT_DIR.mkdir(exist_ok=True)
        path = Config.SCREENSHOT_DIR / filename
        self.page.screenshot(path=str(path), full_page=True)
        self.logger.debug(f"Screenshot saved: {path}")
