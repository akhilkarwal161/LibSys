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
    on_success_url = reverse_lazy('user:dashboard')
    template_name = 'auth/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

class CustomlogoutView(LogoutView):
    success_url = reverse_lazy('Home:login')


class Registerpage(FormView):
    template_name = 'auth/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user = True
    on_success_url = reverse_lazy('user:dashboard')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(Registerpage, self).form_valid(form)

def dashboard(request):
    books = Books.objects.all()
    issued_books = Issued.objects.all()
    available_books = []
    for book in books:
        issued_count = Issued.objects.filter(book=book).exclude(submit=True).count()
        book.available_quantity = book.quantity - issued_count
        available_books.append(book)
    
    return render(request, 'user/dashboard.html', {'books': books, 'issued_books': issued_books, 'available_books': available_books})


def csrf_failure(request, reason=""):
    return render(request, 'home.html', {'reason': reason})

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def manage_books(request):
    if request.method == 'POST':
        if 'add_book' in request.POST:
            book_name = request.POST.get('book_name')
            quantity = int(request.POST.get('quantity'))
            author = request.POST.get('author')
            genre = request.POST.get('genre')
            fine = int(request.POST.get('fine'))

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
                pk = int(book_id)
                book = Books.objects.get(pk=pk)
                book.delete()
                return redirect('manage_books')
            except Books.DoesNotExist:
                return render(request, 'user/manage_books.html', {'error': 'Book not found.'})

    books = Books.objects.all()
    issued_books = Issued.objects.all()
    available_books = []
    for book in books:
        issued_count = Issued.objects.filter(book=book).exclude(submit=True).count()
        book.available_quantity = book.quantity - issued_count
        available_books.append(book)

    message = request.session.get('message')
    if message:
        del request.session['message'] 

    selected_book = request.GET.get('book', 'all')
    selected_user = request.GET.get('user', 'all')
    issued_books = Issued.objects.all()  # All books initially

    if selected_book != 'all':
        issued_books = issued_books.filter(book=selected_book)

    if selected_user != 'all':
        issued_books = issued_books.filter(user=selected_user)

    return render(request, 'user/manage_books.html', {'books': books, 'issued_books': issued_books, 'available_books': available_books,'issued_books': issued_books, 'all_books': Books.objects.all(), 'all_users': User.objects.all()})

class BookUpdateView(UpdateView):
    model = Books
    fields = ['book_name', 'quantity', 'author', 'genre', 'fine']
    template_name = 'user/edit_book.html'

    def get_success_url(self):
        return reverse('manage_books')

def BookIssue(request, pk):
    book = Books.objects.get(pk=pk)

    if request.method == 'POST':

        issued_count = Issued.objects.filter(book=book).exclude(submit=True).count()
        available_quantity = book.quantity - issued_count
        if book.available_quantity > 0: #check if there are available books
            user = request.user
            
            Issued.objects.create(user=user, book=book)
            book.available_quantity -= 1
            book.save()

            return redirect('dashboard')
        
        else:
            messages.error(request,"Book not available to issue")
            return redirect('dashboard')
        
        

    # Calculate available quantity for this specific book
    issued_count = Issued.objects.filter(book=book).exclude(submit=True).count()
    available_quantity = book.quantity - issued_count

    return render(request, 'user/issue_book.html', {'book': book, 'available_quantity': available_quantity})  

def All_Books(request):
    selected_book = request.GET.get('book', 'all')
    selected_user = request.GET.get('user', 'all')
    issued_books = Issued.objects.all()  # All books initially

    if selected_book != 'all':
        issued_books = issued_books.filter(book=selected_book)

    if selected_user != 'all':
        issued_books = issued_books.filter(user=selected_user)

    context = {'issued_books': issued_books, 'all_books': Books.objects.all(), 'all_users': User.objects.all()}
    return render(request, 'manage_books.html', context) 
@login_required
def issued_books(request):
    issued_books = Issued.objects.filter(user=request.user)
    return render(request, 'user/issued_books.html', {'issued_books': issued_books})    

def BookReturn(request, pk):
  issued_book = Issued.objects.get(pk=pk)  # Get the issued book object

  if request.method == 'POST':
    # Mark the issued book as returned (set submit flag to True)
    issued_book.submit = True
    issued_book.save()

    # Update the book's available quantity
    book = issued_book.book  # Get the actual Book object
    book.available_quantity += 1
    book.save()

    messages.success(request, 'Book returned successfully!')
    return redirect('dashboard')

  # Calculate available quantity for this specific book (optional)
  issued_count = Issued.objects.filter(book=issued_book.book).exclude(submit=True).count()
  available_quantity = issued_book.book.quantity - issued_count 

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



