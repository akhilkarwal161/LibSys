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
        fields = ('user', 'book', 'days')

    def validate(self, attrs):
        book = attrs.get('book')
        user = attrs.get('user')
        
        # Calculate availability
        active_issues = Issued.objects.filter(book=book, submit=False).count()
        available = book.quantity - active_issues
        
        if available <= 0:
            raise serializers.ValidationError({"book": "No available copies of this book remain."})
            
        if user and Issued.objects.filter(book=book, user=user, submit=False).exists():
            raise serializers.ValidationError({"non_field_errors": "You have already issued this book and not returned it."})
            
        return attrs

class IssuedListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issued
        fields = '__all__'

