import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://delraybeach.wodify.com/OnlineSalesPage/Main?q=Memberships%7CLocationId%3D11090")
    page.get_by_role("link", name="Login").click()
    page.get_by_role("textbox", name="Email*").click()
    page.get_by_role("textbox", name="Email*").fill("ryan@balch.io")
    page.get_by_role("textbox", name="Password*").click()
    page.get_by_role("textbox", name="Password*").fill("")
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("menuitem", name=" Class Calendar").click()
    # page.locator("div").filter(has_text=re.compile(r"^1111/11$")).first.click() # this seems to repeat /## so 11/12 would be 1211/12
    page.locator("div").filter(has_text=re.compile(r".*11/11$")).first.click() # my thought for new regex to essentially just look for the button with the right date
    page.get_by_text("/12").click()
    page.locator("#b4-b5-l2-595_17-button_reservationOpen").click()
    page.get_by_role("button", name="Confirm Booking").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)


def extract_classes(page):
    rows = page.locator("tr, .class-row, .scheduleRow")
    classes = []

    for i in range(rows.count()):
        row = rows.nth(i)
        text = row.inner_text().strip()
        if not text:
            continue

        # crude time parse; adjust to match Wodify format
        m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", text, re.I)
        if not m:
            continue

        hour = int(m.group(1))
        minute = int(m.group(2))
        ampm = (m.group(3) or "").lower()

        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        classes.append({
            "index": i,
            "time_24h": f"{hour:02d}:{minute:02d}",
            "raw_text": text,
        })

    if not classes:
        raise RuntimeError("No classes parsed; update selectors.")

    return classes
