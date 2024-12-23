import rest_framework
from rest_framework import serializers
from Home.models import Books, Issued

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = ('book_name', 'quantity', 'author', 'genre', 'fine') 

class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = '__all__'

class IssuedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issued  
        fields = ('user','book')
class IssuedListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issued
        fields = '__all__'
