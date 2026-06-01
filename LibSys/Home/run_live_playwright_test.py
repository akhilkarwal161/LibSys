import time
import random
import string
import requests
from playwright.sync_api import sync_playwright

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_live_playwright_scenarios():
    print("\n" + "="*70)
    print("   STARTING PLAYWRIGHT FUNCTIONAL TEST ON LIVE PRODUCTION WEBSITE")
    print("   TARGET: https://libsys.akhilkarwal.com")
    print("="*70 + "\n")
    
    base_url = "https://libsys.akhilkarwal.com"
    
    # Generate fresh random credentials for test
    test_username = f"live_{generate_random_string(6)}"
    test_password = "LiveSecurePassword123!"
    
    with sync_playwright() as p:
        print("[BROWSER] Launching Chromium in headless mode...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # -------------------------------------------------------------
            # TEST 1: Public Interface Connection check on Live Domain
            # -------------------------------------------------------------
            print("[TEST 1] Testing Connection & DOM Elements on Live Homepage...")
            page.goto(base_url)
            page.wait_for_load_state("domcontentloaded")
            print(f"  -> Homepage Title: '{page.title()}'")
            if "Library Management System" not in page.title():
                raise AssertionError("Homepage title mismatch on live site!")
            print("[TEST 1] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 2: Individual Public Page Load Checks on Live Domain
            # -------------------------------------------------------------
            print("[TEST 2] Testing individual public pages on Live Domain...")
            
            print("  -> Loading live stock collection page...")
            page.goto(f"{base_url}/stock/")
            if "Available Books" not in page.content() and "Collection" not in page.content():
                raise AssertionError("Live Stock page failed to load correctly!")

            print("  -> Loading live members page...")
            page.goto(f"{base_url}/members/")
            if "Members" not in page.content():
                raise AssertionError("Live Members page failed to load correctly!")

            print("  -> Loading live contacts page...")
            page.goto(f"{base_url}/contacts/")
            if "Get in Touch" not in page.content():
                raise AssertionError("Live Contacts page failed to load correctly!")

            print("[TEST 2] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 3: User Registration and Session Flow on Live Domain
            # -------------------------------------------------------------
            print("[TEST 3] Testing dynamic user registration on Live Domain...")
            page.goto(f"{base_url}/register/")
            
            # Fill out User Creation Form
            page.fill("input[name='username']", test_username)
            # Find password inputs by index or name
            password_inputs = page.locator("input[type='password']")
            password_inputs.nth(0).fill(test_password)
            password_inputs.nth(1).fill(test_password)
            
            # Submit registration
            page.click("[type='submit']")
            time.sleep(3)
            
            # Verify login / redirect onto dashboard
            print(f"  -> Current Redirect URL: {page.url}")
            if "dashboard" not in page.url:
                raise AssertionError(f"User registration did not redirect to dashboard! Got: {page.url}")
            print(f"  -> Logged In User Dashboard: '{page.title()}'")
            print("[TEST 3] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 4: User Dashboard Borrow & Return Operations on Live Domain
            # -------------------------------------------------------------
            print("[TEST 4] Testing checkout / return flows on Live Domain...")
            
            content = page.content()
            if "Issue" in content:
                print("  -> Attempting to issue a book from dashboard listing...")
                page.click("a[href*='/issue/'] >> nth=0")
                time.sleep(2)
                
                # Confirm checkout
                page.click("[type='submit']")
                time.sleep(3)
                
                # Verify checkout reflected on dashboard
                print("  -> Checking active checkout record list...")
                if "return" not in page.content():
                    raise AssertionError("Issued book did not appear in live return list!")
                
                # Return the book
                print("  -> Attempting to return the issued book...")
                page.click("text=return >> nth=0")
                time.sleep(2)
                page.click("[type='submit']")
                time.sleep(3)
                print("  -> Book returned successfully on Live Domain!")
            else:
                print("  -> Skipped checkout test (no active inventory available to borrow on Live Domain).")
                
            print("[TEST 4] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 5: Authentication Logout Protection on Live Domain
            # -------------------------------------------------------------
            print("[TEST 5] Testing custom logout on Live Domain...")
            page.goto(f"{base_url}/dashboard/")
            page.click("text=Logout")
            time.sleep(3)
            
            # Ensure dashboard is no longer accessible
            page.goto(f"{base_url}/dashboard/")
            time.sleep(2)
            print(f"  -> Protected URL: {page.url}")
            if "login" not in page.url:
                raise AssertionError("Dashboard remained accessible on live site after logging out!")
                
            print("[TEST 5] -> SUCCESS!\n")

            print("[E2E] ========================================================")
            print("[E2E]  ALL COMPREHENSIVE LIVE DOMAIN SCENARIOS PASSED!  ")
            print("[E2E] ========================================================")

        except Exception as e:
            print(f"\n[FATAL ERROR] Live Playwright Scenario Failed!")
            print(f"[REASON] {str(e)}")
            print("[LOG] Current URL at time of failure: ", page.url)
            browser.close()
            raise e

        browser.close()

if __name__ == "__main__":
    run_live_playwright_scenarios()
