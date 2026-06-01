import random
from locust import HttpUser, task, between

class LibraryUser(HttpUser):
    # Simulate a user thinking for 1 to 3 seconds between actions
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        """Simulate a user accessing the library dashboard."""
        self.client.get("/dashboard/", name="Dashboard Load")

    @task(2)
    def view_books_list(self):
        """Simulate a user browsing the books catalog API."""
        self.client.get("/api/books/", name="API Books List")

    @task(1)
    def simulate_book_lifecycle(self):
        """Simulate end-to-end book search and checkout flow."""
        # 1. Fetch available books list from API
        response = self.client.get("/api/books/", name="API Get Books")
        if response.status_code == 200:
            books = response.json()
            if books:
                # Select a random book to checkout
                random_book = random.choice(books)
                book_id = random_book.get("Bid")
                
                # 2. Simulate requesting the book issue page
                self.client.get(f"/books/{book_id}/issue/", name="View Issue Book Page")
                
                # 3. Simulate checkout request
                self.client.post(f"/books/{book_id}/issue/", name="Post Issue Book Request")
