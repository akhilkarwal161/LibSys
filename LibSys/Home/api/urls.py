from django.urls import path, include
from . import views
from .views import *


urlpatterns = [
    path("book/create",BookCreate.as_view(), name="Bookcreate"),
    path('book/<int:pk>/', BookDetail.as_view(), name='book_detail'),
    path('books/', BookList.as_view() , name='book_list'),
    path('issue/create', IssuedCreate.as_view(), name='issue_book'),
    path('issue/<int:pk>', IssuedDetail.as_view(), name='issue_detail'),
    path('issued_books/', IssuedList.as_view(), name='issued_books'),

]