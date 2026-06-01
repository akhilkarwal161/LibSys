import time
from playwright.sync_api import sync_playwright

def measure_live_page_load_times():
    print("\n" + "="*70)
    print("   LIBSYS PRODUCTION WEBSITE NAVIGATION PERFORMANCE REPORT")
    print("   TARGET: https://libsys.akhilkarwal.com")
    print("="*70 + "\n")
    
    pages_to_test = {
        "Homepage": "https://libsys.akhilkarwal.com",
        "Stock / Books": "https://libsys.akhilkarwal.com/stock/",
        "Members List": "https://libsys.akhilkarwal.com/members/",
        "Contacts / Get In Touch": "https://libsys.akhilkarwal.com/contacts/",
        "Login Screen": "https://libsys.akhilkarwal.com/users/login/",
        "Registration Screen": "https://libsys.akhilkarwal.com/register/"
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a fresh context to avoid any cache interference (cold load measurement)
        context = browser.new_context()
        page = context.new_page()
        
        results = []
        
        for name, url in pages_to_test.items():
            print(f"[MEASURE] Loading {name}...")
            
            start_time = time.time()
            page.goto(url, wait_until="load")
            end_time = time.time()
            
            total_load_time_ms = int((end_time - start_time) * 1000)
            
            # Fetch browser performance timing API metrics
            timing = page.evaluate("() => JSON.stringify(window.performance.timing)")
            import json
            t = json.loads(timing)
            
            navigation_start = t['navigationStart']
            response_start = t['responseStart']
            dom_interactive = t['domInteractive']
            load_event_end = t['loadEventEnd']
            
            # Time to First Byte (TTFB)
            ttfb = response_start - navigation_start
            # Time to DOM Interactive
            dom_ready = dom_interactive - navigation_start
            # Total page load time from browser perspective
            browser_load_time = load_event_end - navigation_start
            
            results.append({
                "name": name,
                "url": url,
                "measured_ms": total_load_time_ms,
                "ttfb": ttfb,
                "dom_ready": dom_ready,
                "browser_load_time": browser_load_time
            })
            
            # Cool down slightly between pages
            time.sleep(1)
            
        browser.close()
        
        # Display the results table
        print("\n" + "-"*90)
        print(f" {'Page Name':<25} | {'Measured Total (ms)':<20} | {'TTFB (ms)':<12} | {'DOM Ready (ms)':<15} | {'Browser Loaded (ms)':<20}")
        print("-"*90)
        for r in results:
            print(f" {r['name']:<25} | {r['measured_ms']:<20} | {r['ttfb']:<12} | {r['dom_ready']:<15} | {r['browser_load_time']:<20}")
        print("-"*90 + "\n")

if __name__ == "__main__":
    measure_live_page_load_times()
