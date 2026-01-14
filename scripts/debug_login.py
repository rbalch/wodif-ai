"""Debug script to diagnose login issues with screenshots at each step"""

import re
import os
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

WODIFY_URL = "https://app.wodify.com"
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
SCREENSHOT_DIR = Path("/workspace/screenshots/debug")


def screenshot(page, name: str):
    """Take a screenshot with timestamp"""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    filename = f"{ts}_{name}.png"
    path = SCREENSHOT_DIR / filename
    page.screenshot(path=str(path), full_page=True)
    print(f"  📸 Saved: {path}")


def dump_form_fields(page):
    """Dump all input fields on the page"""
    print("\n  🔍 Form fields found:")
    inputs = page.locator("input").all()
    for i, inp in enumerate(inputs):
        try:
            inp_type = inp.get_attribute("type") or "text"
            inp_name = inp.get_attribute("name") or ""
            inp_id = inp.get_attribute("id") or ""
            inp_placeholder = inp.get_attribute("placeholder") or ""
            aria_label = inp.get_attribute("aria-label") or ""
            visible = inp.is_visible()
            print(f"     [{i}] type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}, aria={aria_label}, visible={visible}")
        except Exception as e:
            print(f"     [{i}] Error reading: {e}")

    print("\n  🔍 Buttons found:")
    buttons = page.locator("button").all()
    for i, btn in enumerate(buttons):
        try:
            btn_text = btn.inner_text().strip()[:30]
            btn_type = btn.get_attribute("type") or ""
            visible = btn.is_visible()
            print(f"     [{i}] text='{btn_text}', type={btn_type}, visible={visible}")
        except Exception as e:
            print(f"     [{i}] Error reading: {e}")


def main():
    print(f"\n{'='*60}")
    print("🔧 Wodify Login Debug Script")
    print(f"{'='*60}\n")

    if not EMAIL or not PASSWORD:
        print("❌ Missing EMAIL or PASSWORD in .env")
        return

    print(f"📧 Email: {EMAIL}")
    print(f"🔐 Password: {'*' * len(PASSWORD)}")

    with sync_playwright() as p:
        # Check for DISPLAY env var to determine headless mode
        headless = os.getenv("DISPLAY") is None
        if headless:
            print("  (No display detected - running headless, check screenshots)")

        browser = p.chromium.launch(
            headless=headless,
            args=["--no-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()

        try:
            # Step 1: Navigate to Wodify
            print("\n[Step 1] Navigating to Wodify...")
            page.goto(WODIFY_URL, wait_until="networkidle")
            page.wait_for_timeout(3000)
            screenshot(page, "01_homepage")

            # Step 2: Check for new flow (email on homepage) vs old flow (login link)
            print("\n[Step 2] Detecting login flow...")

            # New flow: email input directly on homepage
            email_input = page.locator("input[type='email'], input#Input_UserName2")
            if email_input.count() > 0 and email_input.first.is_visible():
                print("  ✓ NEW FLOW DETECTED: Email field on homepage")
                email_input.first.fill(EMAIL)
                screenshot(page, "02_email_filled_homepage")

                # Click CONTINUE
                continue_btn = page.get_by_role("button", name=re.compile("Continue", re.I))
                if continue_btn.count() > 0:
                    print("  ✓ Found CONTINUE button, clicking...")
                    continue_btn.click()
                    page.wait_for_timeout(3000)
                    screenshot(page, "02_after_continue")
                    dump_form_fields(page)
                else:
                    print("  ❌ No CONTINUE button found!")
                    dump_form_fields(page)
                    return
            else:
                # Old flow: click login link first
                print("  Trying old flow (Login link)...")
                login_link = page.get_by_text("Login", exact=False)
                if login_link.count() > 0:
                    print(f"  ✓ Found login link (count: {login_link.count()})")
                    login_link.first.click()
                    page.wait_for_timeout(2000)
                    screenshot(page, "02_after_login_click")
                else:
                    print("  ❌ No login method found!")
                    screenshot(page, "02_no_login_method")
                    dump_form_fields(page)
                    return

                # Step 3: Fill email (old flow)
                print("\n[Step 3] Looking for email field (old flow)...")
                email_field = page.get_by_role("textbox", name=re.compile("Email", re.I))
                if email_field.count() > 0:
                    email_field.fill(EMAIL)
                    screenshot(page, "03_email_filled")
                else:
                    alt_email = page.locator("input[type='email']")
                    if alt_email.count() > 0:
                        alt_email.first.fill(EMAIL)
                        screenshot(page, "03_email_filled_alt")
                    else:
                        print("  ❌ No email field found!")
                        return

            # Step 3: Now we should be on password page (both flows converge here)
            print("\n[Step 3] Looking for password field...")
            pwd_field = page.get_by_role("textbox", name=re.compile("Password", re.I))
            if pwd_field.count() > 0:
                print(f"  ✓ Found password field via role")
                pwd_field.fill(PASSWORD)
                screenshot(page, "05_password_filled")
            else:
                print("  ❌ No password field with role='textbox'")
                # Try input[type='password']
                alt_pwd = page.locator("input[type='password']")
                if alt_pwd.count() > 0:
                    print(f"  ✓ Found password via input[type='password'] (count: {alt_pwd.count()})")
                    alt_pwd.first.fill(PASSWORD)
                    screenshot(page, "05_password_filled_alt")
                else:
                    print("  ❌ No password field found at all!")
                    dump_form_fields(page)
                    screenshot(page, "05_no_password_field")
                    print("\n  💡 The page might need more time to load, or the login flow changed")
                    return

            # Step 6: Click Sign in
            print("\n[Step 4] Clicking Sign in...")
            signin_btn = page.get_by_role("button", name=re.compile("Sign in", re.I))
            if signin_btn.count() > 0:
                signin_btn.click()
                page.wait_for_timeout(5000)
                screenshot(page, "06_after_signin")
                print("  ✓ Clicked sign in")
            else:
                print("  ❌ No sign in button found")
                dump_form_fields(page)

            # Step 7: Check if logged in
            print("\n[Step 5] Checking login status...")
            calendar_link = page.get_by_role("menuitem", name=re.compile("Class Calendar", re.I))
            if calendar_link.count() > 0:
                print("  ✅ LOGIN SUCCESSFUL - Found Class Calendar menu")
                screenshot(page, "07_logged_in")
            else:
                print("  ❌ Login may have failed - no Class Calendar found")
                screenshot(page, "07_login_failed")

                # Check for error messages
                error = page.locator(".error, .alert-danger, [class*='error']")
                if error.count() > 0:
                    print(f"  ⚠️  Error message: {error.first.inner_text()[:100]}")

            print("\n" + "="*60)
            print("Debug complete! Check screenshots in:")
            print(f"  {SCREENSHOT_DIR}")
            print("="*60 + "\n")

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            screenshot(page, "error")
            dump_form_fields(page)

        finally:
            browser.close()


if __name__ == "__main__":
    main()
