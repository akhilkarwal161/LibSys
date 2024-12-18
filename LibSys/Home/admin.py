from django.contrib import admin
from .models import Issued, Books
# Register your models here.
admin.site.register(Issued)
admin.site.register(Books)
admin.site.site_header = "Library Management System"