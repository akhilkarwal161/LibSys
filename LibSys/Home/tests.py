from django.test import TestCase
from django.contrib.auth.models import User
from Home.models import Books, Issued
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class LibrarySystemTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="borrower", password="password")
        self.book = Books.objects.create(
            book_name="Test Book",
            quantity=1,
            author="Author",
            genre="Fiction",
            fine=10
        )

    def test_successful_checkout_and_decrement(self):
        self.client.force_login(self.user)
        # Issue book
        response = self.client.post(reverse('issue_book', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Verify Issued record exists and submit is False
        issue = Issued.objects.get(book=self.book, user=self.user)
        self.assertFalse(issue.submit)
        
        # Verify stock decrement
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_quantity, 0)

    def test_blocked_checkout_when_out_of_stock(self):
        # Create issue record to exhaust stock
        Issued.objects.create(book=self.book, user=self.user, submit=False)
        self.book.available_quantity = 0
        self.book.save()

        # Try to issue again
        self.client.force_login(self.user)
        response = self.client.post(reverse('issue_book', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Verify no second Issued record was created
        self.assertEqual(Issued.objects.filter(book=self.book, user=self.user).count(), 1)


class LibraryAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api_user", password="password")
        self.book = Books.objects.create(
            book_name="API Book",
            quantity=1,
            author="Author",
            genre="Fiction",
            fine=10
        )

    def test_api_checkout_validation_failures(self):
        # Create an active issue to exhaust stock
        Issued.objects.create(book=self.book, user=self.user, submit=False)
        
        # Attempt API issue for the same user (violates stock AND user borrowing same book rules)
        self.client.force_login(self.user)
        response = self.client.post('/api/issue/create/', {
            'user': self.user.id,
            'book': self.book.pk,
            'days': 10
        })
        # Should raise bad request validation error (400)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


