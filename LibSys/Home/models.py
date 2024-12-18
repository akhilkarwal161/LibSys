from django.db import models
from django.db import connection
from collections import deque
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
import logging


# Create a queue to store released Bids
released_bids_queue = deque() 
available_issue_nos = set() 

def get_next_bid():
    """
    Generates the next available Bid.
    """
    global released_bids_queue

    if released_bids_queue:
        next_bid = released_bids_queue.popleft() 
    else:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT MAX(Bid) FROM Home_books")
                max_bid = cursor.fetchone()[0]
                if max_bid is None:
                    next_bid = '001'  # Start with '001' by default
                else:
                    next_bid = str(int(max_bid) + 1).zfill(3)
                    if int(next_bid) > 999:
                        next_bid = '001' 
        except Exception as e:
            # Handle potential database errors
            print(f"Error fetching max Bid: {e}")
            next_bid = '001'  # Fallback to '001' in case of errors

    return next_bid

def release_bid(bid):
    """
    Releases a Bid back to the queue.
    """
    global released_bids_queue
    released_bids_queue.append(bid)

def get_next_issue_no():
    global available_issue_nos  # Use a set to store available issue numbers

    if available_issue_nos:
        issue_no = min(available_issue_nos)  # Get the smallest available number
        available_issue_nos.remove(issue_no)
        return str(issue_no).zfill(3)

    last_issue = Issued.objects.order_by('Issue_No').last()
    if last_issue:
        try:
            next_num = int(last_issue.Issue_No) + 1
            if next_num > 999:
                next_num = 1  # Reset to 1 if reached limit
            issue_no = str(next_num).zfill(3)
        except ValueError:
            issue_no = '001'
            logging.warning("Encountered non-numeric Issue_No. Resetting to default.")
    else:
        issue_no = '001'

    return issue_no


class Books(models.Model):
    Bid = models.IntegerField(unique=True,default=get_next_bid,null=False,primary_key=True)
    book_name = models.CharField(max_length=200, null=False)
    quantity = models.PositiveIntegerField()
    author = models.TextField(default='anonymous', null=False)
    genre = models.TextField(null=True, default='unknown')
    fine = models.PositiveSmallIntegerField(null=False, default=50)
    available_quantity = models.PositiveIntegerField(default=0)  # Add available_quantity field
    def __str__(self):
        return self.book_name

    def save(self, *args, **kwargs):
        self.available_quantity = self.quantity  # Set available_quantity to quantity on save
        super().save(*args, **kwargs)   
    def is_issued_and_not_returned(self, user):
        return Issued.objects.filter(book=self, user=user, submit=False).exists()

class Issued(models.Model):
    Issue_No = models.IntegerField(unique=True,primary_key=True,default=get_next_issue_no)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True) 
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    days = models.PositiveIntegerField(default=10)
    submit = models.BooleanField(default=False)
    create = models.DateTimeField(auto_now_add=True)
     # Use AutoField for issued_bid

    def __str__(self):
        return self.book.book_name

    class Meta:
        ordering = ['user']