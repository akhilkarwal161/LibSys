from re import search
from rest_framework import generics
from rest_framework.response import Response
from .serializers import *
from Home.models import Books, Issued
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class BookCreate(generics.ListCreateAPIView):
    queryset = Books.objects.all()
    serializer_class = BookSerializer

    def delete(self, request, *args, **kwargs):
        Books.objects.filter(pk=kwargs['pk']).delete()
        return self.destroy(request, *args, **kwargs)

class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Books.objects.all()
    serializer_class = BookSerializer
    lookup_field = "pk"

class BookList(generics.ListAPIView):
    queryset = Books.objects.all()
    serializer_class = BookListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'book_name': ['icontains', 'exact'], # Example of multiple lookups
        'author': ['exact'],
        'genre': ['exact'],
    }
    search_fields = ['book_name', 'author']
    ordering_fields = ['book_name', 'author']

class IssuedCreate(generics.ListCreateAPIView):
    queryset = Issued.objects.all()
    serializer_class = IssuedSerializer

    def delete(self, request, *args, **kwargs):
        Issued.objects.filter(pk=kwargs['pk']).delete()
        return self.destroy(request, *args, **kwargs)

class IssuedDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Issued.objects.all()
    serializer_class = IssuedSerializer
    lookup_field = "pk"

class IssuedList(generics.ListAPIView):
    queryset = Issued.objects.all()
    serializer_class = IssuedListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'user': ['exact'],
        'book': ['exact'],
    }
    ordering_fields = ['user', 'book', 'submit', 'create',]
