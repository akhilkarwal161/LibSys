from . import views
from django.urls import path
from . import views
from django.views.generic import RedirectView
from .views import *
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.urls import include

urlpatterns = [
    path('api/', include('Home.api.urls')),
    path('', views.Home, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', CustomlogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.Registerpage.as_view(), name='register'),
    path('dashboard/', views.dashboard, name='dashboard'), 
    path('manage_books/', views.manage_books, name='manage_books'), 
    path('books/<int:pk>/edit/', BookUpdateView.as_view(), name='edit_book'),
    path('books/<int:pk>/issue/', views.BookIssue, name='issue_book'),
    path('dashboard/', views.All_Books, name='All_Books'),
    path('issued_books/', views.issued_books, name='issued_books'),
    path('return_book/<int:pk>/', views.BookReturn, name='return_book'),
    path('Stock/', views.stock, name='books'),
    path('members/', views.members, name='members'),
    path('contacts/', views.contacts, name='contacts'),



]