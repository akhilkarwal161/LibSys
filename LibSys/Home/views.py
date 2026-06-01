from codecs import lookup
from django.shortcuts import render, redirect
from django.views.generic import FormView, View
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse
from django.views.generic import TemplateView
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse, request
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework import generics
from .api.serializers import *
from rest_framework.response import Response
from rest_framework.views import APIView
import json
available_books = []
issued_books = []
def Home(request):
    return render(request, 'home.html')

class CustomLoginView(LoginView):
    success_url = reverse_lazy('dashboard')
    template_name = 'auth/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

class CustomlogoutView(LogoutView):
    success_url = reverse_lazy('login')


class Registerpage(FormView):
    template_name = 'auth/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(Registerpage, self).form_valid(form)

from django.db import transaction
from django.db.models import Count, Q

def dashboard(request: HttpRequest) -> HttpResponse:
    books = Books.objects.annotate(
        active_issues=Count('issued', filter=Q(issued__submit=False))
    )
    for book in books:
        book.available_quantity = book.quantity - book.active_issues
        
    issued_books = Issued.objects.select_related('book', 'user').all()
    return render(request, 'user/dashboard.html', {'books': books, 'issued_books': issued_books, 'available_books': books})


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    return render(request, 'home.html', {'reason': reason})

def is_superuser(user: User) -> bool:
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def manage_books(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        if 'add_book' in request.POST:
            book_name = request.POST.get('book_name')
            quantity = int(request.POST.get('quantity') or 0)
            author = request.POST.get('author')
            genre = request.POST.get('genre')
            fine = int(request.POST.get('fine') or 0)

            try:
                Books.objects.create(
                    book_name=book_name,
                    quantity=quantity,
                    author=author,
                    genre=genre,
                    fine=fine,
                )
                return redirect('manage_books')
            except Exception as e:
                return render(request, 'user/manage_books.html', {'error': str(e)})

        elif 'remove_book' in request.POST:
            book_id = request.POST.get('book_id')
            try:
                pk = int(book_id or 0)
                book = Books.objects.get(pk=pk)
                book.delete()
                return redirect('manage_books')
            except Books.DoesNotExist:
                return render(request, 'user/manage_books.html', {'error': 'Book not found.'})

    books = Books.objects.annotate(
        active_issues=Count('issued', filter=Q(issued__submit=False))
    )
    for book in books:
        book.available_quantity = book.quantity - book.active_issues

    message = request.session.get('message')
    if message:
        del request.session['message'] 

    selected_book = request.GET.get('book', 'all')
    selected_user = request.GET.get('user', 'all')
    issued_books = Issued.objects.select_related('book', 'user').all()

    if selected_book != 'all':
        issued_books = issued_books.filter(book=selected_book)

    if selected_user != 'all':
        issued_books = issued_books.filter(user=selected_user)

    return render(request, 'user/manage_books.html', {
        'books': books, 
        'issued_books': issued_books, 
        'available_books': books,
        'all_books': Books.objects.all(), 
        'all_users': User.objects.all()
    })

class BookUpdateView(UpdateView):
    model = Books
    fields = ['book_name', 'quantity', 'author', 'genre', 'fine']
    template_name = 'user/edit_book.html'

    def get_success_url(self) -> str:
        return reverse('manage_books')

@login_required
@transaction.atomic
def BookIssue(request: HttpRequest, pk: int) -> HttpResponse:
    book = Books.objects.select_for_update().get(pk=pk)
    active_issues = Issued.objects.filter(book=book, submit=False).count()
    available_quantity = book.quantity - active_issues

    if request.method == 'POST':
        if available_quantity > 0:
            user = request.user
            Issued.objects.create(user=user, book=book)
            book.available_quantity = available_quantity - 1
            book.save()
            return redirect('dashboard')
        else:
            messages.error(request, "Book not available to issue")
            return redirect('dashboard')

    return render(request, 'user/issue_book.html', {'book': book, 'available_quantity': available_quantity})  

def All_Books(request: HttpRequest) -> HttpResponse:
    selected_book = request.GET.get('book', 'all')
    selected_user = request.GET.get('user', 'all')
    issued_books = Issued.objects.select_related('book', 'user').all()

    if selected_book != 'all':
        issued_books = issued_books.filter(book=selected_book)

    if selected_user != 'all':
        issued_books = issued_books.filter(user=selected_user)

    context = {'issued_books': issued_books, 'all_books': Books.objects.all(), 'all_users': User.objects.all()}
    return render(request, 'user/manage_books.html', context) 

@login_required
def issued_books(request: HttpRequest) -> HttpResponse:
    issued_books = Issued.objects.select_related('book').filter(user=request.user)
    return render(request, 'user/issued_books.html', {'issued_books': issued_books})    

@login_required
@transaction.atomic
def BookReturn(request: HttpRequest, pk: int) -> HttpResponse:
    issued_book = Issued.objects.select_for_update().select_related('book').get(pk=pk)

    if request.method == 'POST':
        if not issued_book.submit:
            issued_book.submit = True
            issued_book.save()

            book = Books.objects.select_for_update().get(pk=issued_book.book.pk)
            # Recompute and update
            active_issues = Issued.objects.filter(book=book, submit=False).count()
            book.available_quantity = book.quantity - active_issues
            book.save()

        messages.success(request, 'Book returned successfully!')
        return redirect('dashboard')

    active_issues = Issued.objects.filter(book=issued_book.book, submit=False).count()
    available_quantity = issued_book.book.quantity - active_issues 

    context = {'issued_book': issued_book, 'available_quantity': available_quantity}
    return render(request, 'user/return_book.html', context)

def issued_books_view(request):
    selected_book = request.GET.get('book', 'all')
    selected_user = request.GET.get('user', 'all')

    issued_books = Issued.objects.all()

    if selected_book != 'all':
        issued_books = issued_books.filter(book_id=selected_book)  # Filter by book ID

    if selected_user != 'all':
        issued_books = issued_books.filter(user_id=selected_user)  # Filter by user ID

    context = {
        'issued_books': issued_books,
        'all_books': Books.objects.all(),
        'all_users': User.objects.all(),
    }
    return render(request, 'your_template.html', context)

def stock(request):
    books = Books.objects.all()
    return render(request, 'etc/books.html', {'books': books})

def members(request):
    users = User.objects.all()
    return render(request, 'etc/members.html', {'users': users})

def contacts(request):
    return render(request, 'etc/contacts.html')



