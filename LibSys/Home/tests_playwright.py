from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from Home.models import Books, Issued
from playwright.sync_api import sync_playwright
import time

class LibSysPlaywrightTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        # Launch browser in headless mode
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        # Create a test superuser for testing
        self.user = User.objects.create_superuser(username="admin", password="adminpassword", email="admin@test.com")
        self.book = Books.objects.create(
            book_name="Playwright Guide",
            quantity=5,
            author="Test Author",
            genre="Educational",
            fine=20
        )
        self.page = self.browser.new_page()

    def tearDown(self):
        self.page.close()

    def test_full_user_flow(self):
        print("\n--- Starting Playwright End-to-End Test Execution ---")
        
        # Step 1: Navigate to Home Page
        print("[Step 1] Navigating to Home Page...")
        self.page.goto(self.live_server_url)
        print(f"Loaded page: {self.page.title()}")
        self.assertIn("Home", self.page.title())

        # Step 2: Go to Login Page and Authenticate
        print("[Step 2] Logging in...")
        self.page.goto(f"{self.live_server_url}/login/")
        self.page.fill("input[name='username']", "admin")
        self.page.fill("input[name='password']", "adminpassword")
        self.page.click("button[type='submit']")
        
        # Verify redirect to dashboard
        time.sleep(1) # Wait for page reload
        print(f"Redirected to: {self.page.url}")
        self.assertIn("dashboard", self.page.url)

        # Step 3: Verify book list matches database inventory
        print("[Step 3] Verifying book inventory on Dashboard...")
        self.page.wait_for_selector("text=Playwright Guide")
        self.assertTrue(self.page.is_visible("text=Playwright Guide"))
        self.assertTrue(self.page.is_visible("text=Available: 5"))

        # Step 4: Add a new book (Superuser function)
        print("[Step 4] Superuser adding a new book...")
        self.page.goto(f"{self.live_server_url}/manage_books/")
        self.page.fill("input[name='book_name']", "Automation 101")
        self.page.fill("input[name='quantity']", "2")
        self.page.fill("input[name='author']", "QA Expert")
        self.page.fill("input[name='genre']", "Tech")
        self.page.fill("input[name='fine']", "15")
        self.page.click("button[name='add_book']")
        
        # Verify book added
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Automation 101"))
        print("Success: New book created.")

        # Step 5: Issue a book
        print("[Step 5] Issuing a book...")
        # Get checkout link
        book_id = Books.objects.get(book_name="Playwright Guide").pk
        self.page.goto(f"{self.live_server_url}/books/{book_id}/issue/")
        self.page.click("button[type='submit']")
        
        # Verify checkout count changes on dashboard
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Available: 4"))
        print("Success: Book checked out; stock decremented correctly.")

        # Step 6: Return the book
        print("[Step 6] Returning the book...")
        issued_record = Issued.objects.get(book__book_name="Playwright Guide", user=self.user)
        self.page.goto(f"{self.live_server_url}/return_book/{issued_record.pk}/")
        self.page.click("button[type='submit']")
        
        # Verify stock incremented
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Available: 5"))
        print("Success: Book returned; stock incremented correctly.")

        # Step 7: Logout
        print("[Step 7] Logging out...")
        self.page.goto(f"{self.live_server_url}/logout/")
        time.sleep(1)
        self.assertIn("login", self.page.url)
        print("Success: Logged out cleanly.")
        print("--- All Playwright End-to-End Tests Succeeded! ---")
