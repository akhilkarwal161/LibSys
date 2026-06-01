import subprocess
import time
import sys
import os
import requests
from playwright.sync_api import sync_playwright

def start_dev_server():
    print("[INIT] Starting local Django development server on port 8000...")
    # Use python -u for unbuffered logs
    process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "8000", "--noreload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Wait for server to boot
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is not None:
        print("[ERROR] Django server failed to start. Stdout / Stderr:")
        stdout, stderr = process.communicate()
        print(stdout)
        print(stderr)
        sys.exit(1)
        
    print("[INIT] Django server successfully started in background.")
    return process

def run_playwright_scenarios():
    print("\n" + "="*50)
    print("   STARTING PLAYWRIGHT FUNCTIONAL VERIFICATION ENGINE")
    print("="*50 + "\n")
    
    base_url = "http://127.0.0.1:8000"
    
    with sync_playwright() as p:
        # Launch Chromium
        print("[BROWSER] Launching Chromium in headless mode...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 1. Load Home Page
            print("[TEST 1] Testing Home Page Connection...")
            page.goto(base_url)
            print(f"-> Loaded Title: '{page.title()}'")
            if "Library Management System" not in page.title():
                raise AssertionError(f"Home Page Title Mismatch! Expected 'Library Management System', got '{page.title()}'")

            print("[TEST 1] -> SUCCESS!\n")

            # 2. Test Invalid Login
            print("[TEST 2] Testing Invalid Credentials Rejection...")
            page.goto(f"{base_url}/login/")
            page.fill("input[name='username']", "nonexistent_caveman")
            page.fill("input[name='password']", "badpassword")
            page.click("input[type='submit']")

            time.sleep(1)
            
            # Verify we are still on the login page (credentials rejected)
            print(f"-> Active URL: {page.url}")
            if "/login" not in page.url:
                raise AssertionError("Invalid login succeeded or did not redirect back correctly!")
            print("[TEST 2] -> SUCCESS (Authentication correctly blocked!)\n")

            # 3. Test API GET Endpoint
            print("[TEST 3] Testing Public REST API Endpoints...")
            page.goto(f"{base_url}/api/books/")
            content = page.content()
            print("-> Successfully reached REST API books endpoint list.")
            if "book_name" not in content and "[]" not in content:
                raise AssertionError(f"Invalid API response: {content[:200]}")
            print("[TEST 3] -> SUCCESS!\n")

            print("[E2E] --- E2E Integration Suite Completed Successfully! ---")

        except Exception as e:
            print(f"\n[FATAL ERROR] Playwright Test Scenario Failed!")
            print(f"[REASON] {str(e)}")
            print("[LOG] Current URL at time of failure: ", page.url)
            browser.close()
            raise e

        browser.close()

if __name__ == "__main__":
    # Ensure database migrations are current locally
    subprocess.run([sys.executable, "manage.py", "migrate"])
    
    server_process = start_dev_server()
    try:
        run_playwright_scenarios()
    finally:
        print("\n[TEARDOWN] Shutting down background Django development server...")
        server_process.terminate()
        server_process.wait()
        print("[TEARDOWN] Server cleanly stopped.")
