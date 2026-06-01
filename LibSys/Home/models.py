from django.db import models
from django.db import connection
from collections import deque
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
import logging
from typing import Optional

def get_next_bid() -> str:
    return '001'

def get_next_issue_no() -> str:
    return '001'

class Books(models.Model):

    Bid = models.AutoField(primary_key=True)
    book_name = models.CharField(max_length=200, null=False)
    quantity = models.PositiveIntegerField()
    author = models.TextField(default='anonymous', null=False)
    genre = models.TextField(null=True, default='unknown')
    fine = models.PositiveSmallIntegerField(null=False, default=50)
    available_quantity = models.PositiveIntegerField(default=0)
    
    def __str__(self) -> str:
        return self.book_name

    def save(self, *args, **kwargs) -> None:
        if self._state.adding:
            self.available_quantity = self.quantity
        super().save(*args, **kwargs)   
        
    def is_issued_and_not_returned(self, user: User) -> bool:
        return Issued.objects.filter(book=self, user=user, submit=False).exists()

class Issued(models.Model):
    Issue_No = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) 
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    days = models.PositiveIntegerField(default=10)
    submit = models.BooleanField(default=False)
    create = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.book.book_name


    class Meta:
        ordering = ['user']