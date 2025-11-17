import re, os
from playwright.sync_api import sync_playwright

EMAIL = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
URL = "https://delraybeach.wodify.com/OnlineSalesPage/Main?q=Memberships%7CLocationId%3D11090"
IMAGE_FILE = "wodify-classlist.png"
DAY_TO_SELECT = "11/14"  # Set to None to stay on today, or "11/12" format for specific date


def delete_image(path: str):
    """Delete the image file at `path` if it exists."""
    try:
        os.remove(path)
        print(f"Deleted {path}")
    except FileNotFoundError:
        print(f"No file found at {path}")
    except PermissionError:
        print(f"Permission denied: {path}")
    except Exception as e:
        print(f"Error deleting {path}: {e}")


def attempt_login(page, email, password):
    """
    Attempt to find and click login, then fill credentials.
    Returns True if login was successful, False if login link not found.
    """
    # Try primary login selector
    login_link = page.get_by_text("Login", exact=False)
    if login_link.count() > 0:
        print("Found login link (text), clicking...")
        login_link.first.click()
        page.wait_for_timeout(2000)

        # Fill login form
        page.get_by_role("textbox", name=re.compile("Email", re.I)).fill(email)
        page.get_by_role("textbox", name=re.compile("Password", re.I)).fill(password)
        page.get_by_role("button", name=re.compile("Sign in", re.I)).click()
        page.wait_for_load_state("networkidle")
        print("Logged in successfully")
        return True

    # Try alternative login selector
    alt_login = page.get_by_role("link", name=re.compile("Login", re.I))
    if alt_login.count() > 0:
        print("Found alternative login link (role), clicking...")
        alt_login.first.click()
        page.wait_for_timeout(2000)

        page.get_by_role("textbox", name=re.compile("Email", re.I)).fill(email)
        page.get_by_role("textbox", name=re.compile("Password", re.I)).fill(password)
        page.get_by_role("button", name=re.compile("Sign in", re.I)).click()
        page.wait_for_load_state("networkidle")
        print("Logged in successfully via alternative method")
        return True

    print("No login link found")
    return False


def list_classes(page):
    """Extract class information from the calendar"""
    # Each class is in a div with class "list-item"
    rows = page.locator(".list-item[data-list-item]")
    count = rows.count()
    print(f"\nFound {count} class rows:")

    classes = []
    for i in range(count):
        row = rows.nth(i)

        # Extract time (e.g., "3:00 PM - 4:30 PM")
        time_elem = row.locator(".list-item-content-left .font-semi-bold").first
        time_text = time_elem.inner_text() if time_elem.count() > 0 else ""

        # Get full time range
        time_range = row.locator(".list-item-content-left").first.inner_text().split('\n')[0] if row.locator(".list-item-content-left").count() > 0 else ""

        # Extract class name (e.g., "ROW CLINIC")
        class_name = row.locator(".font-size-m span").first.inner_text() if row.locator(".font-size-m span").count() > 0 else ""

        # Extract coach name
        coach_elem = row.locator("a[href='#']")
        coach_name = coach_elem.inner_text() if coach_elem.count() > 0 else ""

        # Get button ID for clicking
        button = row.locator("button").first
        button_id = button.get_attribute("id") if button.count() > 0 else None
        button_text = button.inner_text() if button.count() > 0 else ""

        class_info = {
            "index": i,
            "time_range": time_range,
            "class_name": class_name,
            "coach": coach_name,
            "button_id": button_id,
            "button_text": button_text
        }
        classes.append(class_info)

        print(f"{i:02d}: {time_range:20s} | {class_name:20s} | Coach: {coach_name:15s} | Button: {button_text} (#{button_id})")

    return classes


delete_image(IMAGE_FILE)
delete_image('wodify-login.png')
delete_image('wodify-error.png')

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
    )

    page = context.new_page()
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(3000)

    # Login with retry logic
    login_success = attempt_login(page, EMAIL, PASSWORD)

    if not login_success:
        print("First login attempt failed, taking screenshot and refreshing page...")
        page.screenshot(path="wodify-login.png", full_page=True)

        # Refresh and try again
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(3000)

        print("Retrying login after refresh...")
        login_success = attempt_login(page, EMAIL, PASSWORD)

        if not login_success:
            print("ERROR: Could not find login link after 2 attempts. Exiting.")
            page.screenshot(path="wodify-error.png", full_page=True)
            browser.close()
            exit(1)

    # open class calendar
    page.get_by_role("menuitem", name=re.compile("Class Calendar", re.I)).click()

    # Wait for calendar to load
    page.wait_for_timeout(5000)

    # Select specific day if configured
    if DAY_TO_SELECT:
        print(f"\nSelecting date: {DAY_TO_SELECT}")
        # Try to find and click the date
        date_pattern = f".*{DAY_TO_SELECT}$"
        date_elements = page.locator("div").filter(has_text=re.compile(date_pattern)).all()

        if date_elements:
            print(f"Found {len(date_elements)} elements matching date")
            date_elements[0].click()
            print(f"Clicked on {DAY_TO_SELECT}")
            # Wait for the new day's classes to load
            page.wait_for_timeout(3000)
        else:
            print(f"Could not find date element for {DAY_TO_SELECT}")

    # Check what elements are present
    print("\n=== Debugging page content ===")
    print(f"URL: {page.url}")

    # Look for any headings
    headings = page.locator("h1, h2, h3, .heading3, [class*='title']").all()
    print(f"Found {len(headings)} headings:")
    for h in headings[:5]:
        print(f"  - {h.inner_text()[:50]}")

    # Look for anything with "calendar" or "class"
    calendar_elements = page.locator("[class*='calendar'], [id*='calendar'], :text('Calendar')").all()
    print(f"Found {len(calendar_elements)} calendar-related elements")

    # Check if we're in an iframe
    frames = page.frames
    print(f"Number of frames: {len(frames)}")

    classes = list_classes(page)

    page.screenshot(path=IMAGE_FILE, full_page=True)
    print(f"\nSaved screenshot: {IMAGE_FILE}")

    # Interactive class selection
    if classes:
        selection = input("\nEnter the class number to book (or 'q' to quit): ").strip()

        if selection.lower() != 'q' and selection.isdigit():
            index = int(selection)
            if 0 <= index < len(classes):
                selected_class = classes[index]
                button_id = selected_class['button_id']

                if button_id:
                    print(f"\nBooking: {selected_class['time_range']} - {selected_class['class_name']}")

                    # Click the book button
                    page.locator(f"#{button_id}").click()
                    print("Clicked book button, waiting for confirmation dialog...")

                    # Wait for confirmation dialog to appear
                    page.wait_for_timeout(2000)

                    # Click confirm booking
                    try:
                        page.get_by_role("button", name="Confirm Booking").click()
                        print("Clicked Confirm Booking!")

                        # Wait to see result
                        page.wait_for_timeout(3000)

                        # Take final screenshot
                        page.screenshot(path="wodify-booked.png", full_page=True)
                        print("Booking complete! Screenshot saved to wodify-booked.png")
                    except Exception as e:
                        print(f"Error clicking confirm: {e}")
                        page.screenshot(path="wodify-error.png", full_page=True)
                else:
                    print(f"No button ID found for class {index}")
            else:
                print(f"Invalid selection: {index} (must be 0-{len(classes)-1})")
        else:
            print("No booking made")
    else:
        print("No classes found to book")

    browser.close()