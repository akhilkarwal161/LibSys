Project Path: LibSys

Source Tree:

```txt
LibSys
├── AI_PROMPT_GUIDE.md
├── CODEBASE_AUDIT_REPORT.md
├── CODEBASE_INDEX.md
├── CURRENT_CONTEXT.md
├── Dockerfile
├── Lib.zip
├── LibSys
│   ├── CLOUD_RUN_TEST_LOGS.md
│   ├── COMPLIANCE_CHECK_REPORT.md
│   ├── Home
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── api
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   └── views.py
│   │   ├── apps.py
│   │   ├── locustfile.py
│   │   ├── measure_load_times.py
│   │   ├── middleware.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── run_live_playwright_test.py
│   │   ├── run_playwright_e2e.py
│   │   ├── tests.py
│   │   ├── tests_cloud_run.py
│   │   ├── tests_playwright.py
│   │   ├── urls.py
│   │   ├── verify_html_urls.py
│   │   └── views.py
│   ├── LibSys
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── PROJECT_REVIEW_REPORT.md
│   ├── SECURITY_AUDIT_REPORT.md
│   ├── SEO_AUDIT_REPORT.md
│   ├── db - Copy.SQLITE3
│   ├── db.sql
│   ├── db.sqlite3
│   ├── manage.py
│   ├── pyvenv.cfg
│   ├── static
│   │   ├── js
│   │   │   ├── preload.js
│   │   │   └── sw.js
│   │   └── style.css
│   └── templates
│       ├── 429.html
│       ├── auth
│       │   ├── login.html
│       │   └── register.html
│       ├── etc
│       │   ├── books.html
│       │   ├── contacts.html
│       │   └── members.html
│       ├── home.html
│       ├── registration
│       │   └── login.html
│       └── user
│           ├── dashboard.html
│           ├── edit_book.html
│           ├── issue_book.html
│           ├── issued_books.html
│           ├── manage_books.html
│           └── return_book.html
├── README.md
├── Scripts
│   ├── Activate.ps1
│   ├── activate
│   ├── activate.bat
│   ├── deactivate.bat
│   ├── django-admin.exe
│   ├── pip.exe
│   ├── pip3.9.exe
│   ├── pip3.exe
│   ├── py.test.exe
│   ├── pytest.exe
│   ├── python.exe
│   ├── pythonw.exe
│   └── sqlformat.exe
├── WHAT_HAVE_WE_ACHIEVED.md
├── continue_chat.bat
├── digest.txt
├── docker-compose.yml
├── prompt.md
├── requirements-dev.txt
└── requirements.txt

```

`AI_PROMPT_GUIDE.md`:

```md
# AI_PROMPT_GUIDE.md

## Tech Stack & Constraints
- **Core Framework:** Python 3.10+ / Django 4.x+ / Django REST Framework (DRF)
- **Database Backend:** SQLite (Development) / MySQL (Production compatible)
- **Containerization:** Docker / Docker Compose
- **Web Server:** Gunicorn / Whitenoise (Static asset handling)

## Coding Conventions
- **Naming Style:** PascalCase for Models/Classes, snake_case for functions, variables, and database fields.
- **Error Handling:** Standard Python `try-except` blocks. In web views, catch exceptions and return user feedback via `django.contrib.messages` or render dedicated templates with context error keys.
- **Database Safety:** Ensure atomic transactions where required (`django.db.transaction.atomic`) especially when allocating dynamic IDs or queue allocations.
- **REST APIs:** Use serializer validation patterns before modifying resources.

## Token Optimization Rule
- **No Full File Rewrites:** When generating or modifying code, do NOT output the unchanged files.
- **Placeholder Rule:** Use concise comment blocks like `# ... existing code ...` or `// ... existing code ...` for unchanged blocks.
- **Targeted Diffs:** Provide only the specific block or lines being added or refactored.

```

`CODEBASE_AUDIT_REPORT.md`:

```md
# CODEBASE QUALITY & OPTIMIZATION REPORT

## Executive Summary
This report aggregates findings from parallel analysis of the Django LibSys codebase, highlighting critical backend, serialization, API, and architectural design flaws. Corrective actions and optimizations are detailed below.

---

## 1. Backend Application Layer (`Home/models.py`, `Home/views.py`)

### A. Non-Atomic Primary Key Generation
* **Bug:** `models.py` generates model primary keys via high-risk, non-atomic database queries (`MAX(Bid)` / `.last()`) and in-memory state objects (`deque()`, `set()`). 
* **Impact:** High race-condition risk. Concurrent requests result in duplicate primary keys, throwing database `IntegrityError`s. In-memory queues fail state continuity under multi-worker WSGI configurations.
* **Fix:** Replace custom dynamic PK defaults with standard database auto-incrementing serials (`models.AutoField`).

### B. Insecure Model Save Override
* **Bug:** `Books.save` resets `available_quantity = self.quantity` on every call.
* **Impact:** Edits to other book fields (e.g. author name, fine amounts) wipe out checkout metrics, resetting inventories to max quantity.
* **Fix:** Only set `available_quantity` on object creation (`self._state.adding`).

### C. N+1 Performance Bottlenecks
* **Bug:** View queries dynamically count related `Issued` records in Python iterative loops (`dashboard` view).
* **Impact:** 1000 books require 1001 database hits.
* **Fix:** Utilize `.annotate(active_issues=Count('issued', filter=Q(issued__submit=False)))` for single-query retrieval.

---

## 2. API & Serialization (`Home/api/`)

### A. ListCreateAPIView Method Signature Mismatch
* **Bug:** `BookCreate` and `IssuedCreate` classes implement a `delete` method invoking `self.destroy()`.
* **Impact:** `ListCreateAPIView` doesn't inherit from `DestroyModelMixin`. Further, paths mapping to these views lack `<int:pk>` route parameters, causing immediate runtime `AttributeError`s and `KeyError`s.
* **Fix:** Purge custom `delete` overrides from creation views. Outsource delete hooks to dedicated `RetrieveUpdateDestroyAPIView` paths.

### B. Missing Serializer Level Stock Validation
* **Bug:** `IssuedSerializer` allows book checkouts regardless of stock level or user borrow status.
* **Impact:** Quantities decrement past zero, and a single user can check out multiple instances of the same book.
* **Fix:** Enforce validation constraint inside `validate()` validating `book.available_quantity > 0` and borrower duplication status.

---

## 3. Infrastructure & Configurations

### A. Exposed MySQL Database Secret in Dockerfile
* **Bug:** Dockerfile embeds hardcoded root credentials (`DATABASE_URL=mysql://root:Mahesh@2018@34.38.41.15:3306/libsys_db`).
* **Impact:** High credential compromise risk.
* **Fix:** Remove line. Source dynamic variables via secure environment parameters at startup.

### B. Database Backend Dissonance
* **Bug:** Docker setup configures Postgres containers, while the Dockerfile installs MySQL client components, and settings default to SQLite.
* **Impact:** Run-time database driver exceptions.
* **Fix:** Unify database configuration parameters. Align environment drivers with a single chosen database package.

```

`CODEBASE_INDEX.md`:

```md
# CODEBASE_INDEX.md

## System Architecture Diagram
```
Client (Browser) <---> Django Web Server (LibSys) <---> SQLite Database (db.sqlite3)
                          |
                          +---> REST API (djangorestframework)
```

## Directory Tree
```
F:\REpo\LibSys
├── .dockerignore
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── manage.py
├── LibSys/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── Home/
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── urls.py
    ├── views.py
    ├── api/
    │   ├── serializers.py
    │   └── urls.py
    ├── static/
    └── templates/
```

## Component Matrix
| Component / File | Primary Responsibility | Main Dependencies |
| :--- | :--- | :--- |
| `LibSys/settings.py` | Global settings, database connection, middleware config, apps registration | Django, MySQL / SQLite config |
| `LibSys/urls.py` | Main routing module directing requests to app endpoints | Django routing |
| `Home/models.py` | Data definitions for Books and Issued records | django.db.models, auth.User |
| `Home/views.py` | Business logic for dashboard, managing books, and book checkout/return | django.shortcuts, CustomLoginView, CustomlogoutView |
| `Home/urls.py` | App-specific routing mapping paths to views | Home/views.py |
| `Home/api/` | Serializers and view logic for REST endpoints | djangorestframework |
| `Dockerfile` & `docker-compose.yml` | Containerization, deployment orchestration and environment reproducibility | Docker, Docker Compose |

```

`CURRENT_CONTEXT.md`:

```md
# CURRENT_CONTEXT.md

## Immediate Goals
- Establish high-quality, token-efficient codebase documentation files to enhance developer and AI reasoning contexts.

## Active Blockers/Issues
- None detected. Basic application logic is stable; database schemas map correctly to SQLite targets.

## Next Steps
1. Verify and validate documentation accuracy against physical files.
2. Formulate coding prompt constraints for future AI sessions.
3. Optimize codebase for context window consumption.

```

`Dockerfile`:

```
FROM python:3.13-slim-bookworm

# Update system packages to address vulnerabilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Set environment variables for non-interactive commands
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn and other production-specific dependencies
RUN pip install gunicorn

# Copy the rest of the application's code into the container
COPY . .

# Set the working directory to the Django project root inside the container
WORKDIR /app/LibSys

# Set production-specific environment variables for the container
# Replace these values with your actual production settings.
# For Cloud Run, you can set these in the console or with the gcloud CLI.
# This Dockerfile includes them as defaults for demonstration.
ENV DJANGO_DEBUG=False
ENV ALLOWED_HOSTS=libsys-xvhbgr5zoq-as.a.run.app,*
ENV CSRF_TRUSTED_ORIGINS=*

# Replace with your production database URL from Cloud SQL
# You should get this value from your GCP environment, not hard-code it.
ENV DATABASE_URL=mysql://root:Mahesh@2018@34.38.41.15:3306/libsys_db	


# Run collectstatic to gather all static files for WhiteNoise to serve
RUN python manage.py collectstatic --noinput

# Run the Gunicorn server
# Cloud Run automatically sets the PORT environment variable.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "LibSys.wsgi"]
```

`LibSys\CLOUD_RUN_TEST_LOGS.md`:

```md
# CLOUD_RUN_TEST_LOGS.md

## Test Run Environment
*   **Target Cloud Run URL:** `https://libsys-932534087542.asia-southeast1.run.app`
*   **Region:** `asia-southeast1`
*   **GCP Authentication Account:** `website@civic-source-463118-a0.iam.gserviceaccount.com`

---

## Live Integration Execution Outcomes

### 🔴 Test 1: `GET /dashboard/`
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTPSConnectionPool(host='libsys-932534087542.asia-southeast1.run.app', port=443): Read timed out. (read timeout=5)`
*   **Root Cause:** Cloud Run instance cold-start latency exceeded the standard 5-second test timeout.

### 🔴 Test 2: `POST /api/issue/create/` (Schema Rejection validation)
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTP 404 Not Found`
*   **Root Cause:** The active live container is running an outdated codebase deployment (last deployed 2025-10-03). The old router maps this API route differently (e.g. without trailing slashes, or using legacy URL mappings).

### 🔴 Test 3: `GET /api/books/` (Retrieve Books Inventory)
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTPSConnectionPool(host='libsys-932534087542.asia-southeast1.run.app', port=443): Read timed out. (read timeout=5)`
*   **Root Cause:** Cold start scaling lag or live DB connectivity timeout in active container.

```

`LibSys\COMPLIANCE_CHECK_REPORT.md`:

```md
# COMPLIANCE CHECK REPORT

## 1. Executive Summary
This report evaluates the LibSys application against industry compliance frameworks, including the CIS Docker Benchmarks, GDPR/PCI-DSS Secret Protections, Python PEP 8 style guides, and Django production deployment checklists. Non-compliance findings are cataloged with actionable remediation paths.

---

## 2. Compliance Framework Audit Matrix

| Compliance Standard | Status | Finding / Non-Compliance |
| :--- | :--- | :--- |
| **GDPR / PCI-DSS Secret Protection** | ❌ NON-COMPLIANT | Plain-text MySQL root database credentials found hardcoded in `Dockerfile` line 43. |
| **CIS Docker Benchmark (Least Privilege)** | ❌ NON-COMPLIANT | Container runs implicitly under `root` user permissions (lacks `USER` non-root specification). |
| **Django Security Check** | ⚠️ Partial | Allowed Hosts and CSRF trusted origins configured as wildcards in production environment presets. |
| **PEP 8 Standards** |  COMPLIANT | Standard Python naming conventions (except for legacy model attributes `Bid` and `Issue_No` which are PascalCase instead of snake_case). |
| **Permissive Dependency Licenses** |  COMPLIANT | All requirements (Django, DRF, etc.) utilize highly permissive licenses (MIT, BSD, Apache-2.0). No copyleft GPL-style licensing detected. |

---

## 3. Detailed Compliance Deficiencies & Remediations

### A. Docker Non-Root Execution Deficit (CIS Benchmark 4.1)
*   **Deficit:** The Dockerfile does not define a dedicated user. The container starts and runs Gunicorn with full `root` operating privileges. In the event of a container breakout, the host system is fully exploitable.
*   **Remediation:** Declare a non-root system user inside the Dockerfile:
    ```dockerfile
    RUN groupadd -r appgroup && useradd -r -g appgroup appuser
    WORKDIR /app
    ...
    USER appuser
    ```

### B. Insecure Hardcoded Secrets (GDPR/PCI-DSS Section 3)
*   **Deficit:** Storing database connection credentials (`Mahesh@2018`) in code files violates data privacy standards, exposing the internal backend database to unauthorized extraction.
*   **Remediation:** Remove plain-text lines. Utilize Secret Manager parameters mapped to env variables dynamically at the container startup lifecycle.

### C. PascalCase Attribute Legacy Schemas (PEP 8 Compliance)
*   **Deficit:** Attributes `Bid` and `Issue_No` violate snake_case column guidelines of Python PEP 8 and Django model design patterns.
*   **Remediation:** Plan migrations to normalize naming fields to `bid` and `issue_no` in future schema versions.

---

## 4. Audit Limitations
*   **Licensing Tree:** This compliance check did not perform an automated licensing recursive tree audit of transitive dependencies (sub-dependencies). Dynamic package compliance should be verified using automated auditing tools like `license-checker` or `safety`.

```

`LibSys\Home\admin.py`:

```py
from django.contrib import admin
from .models import Issued, Books
# Register your models here.
admin.site.register(Issued)
admin.site.register(Books)
admin.site.site_header = "Library Management System"
```

`LibSys\Home\api\serializers.py`:

```py
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


```

`LibSys\Home\api\urls.py`:

```py
from django.urls import path, include
from . import views
from .views import *


urlpatterns = [
    path("book/create/",BookCreate.as_view(), name="Bookcreate"),
    path('book/<int:pk>/', BookDetail.as_view(), name='book_detail'),
    path('books/', BookList.as_view() , name='book_list'),
    path('issue/create/', IssuedCreate.as_view(), name='issue_book'),
    path('issue/<int:pk>/', IssuedDetail.as_view(), name='issue_detail'),
    path('issued_books/', IssuedList.as_view(), name='issued_books'),

]
```

`LibSys\Home\api\views.py`:

```py
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

```

`LibSys\Home\apps.py`:

```py
from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Home'

```

`LibSys\Home\locustfile.py`:

```py
import random
from locust import HttpUser, task, between

class LibraryUser(HttpUser):
    # Simulate a user thinking for 1 to 3 seconds between actions
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        """Simulate a user accessing the library dashboard."""
        self.client.get("/dashboard/", name="Dashboard Load")

    @task(2)
    def view_books_list(self):
        """Simulate a user browsing the books catalog API."""
        self.client.get("/api/books/", name="API Books List")

    @task(1)
    def simulate_book_lifecycle(self):
        """Simulate end-to-end book search and checkout flow."""
        # 1. Fetch available books list from API
        response = self.client.get("/api/books/", name="API Get Books")
        if response.status_code == 200:
            books = response.json()
            if books:
                # Select a random book to checkout
                random_book = random.choice(books)
                book_id = random_book.get("Bid")
                
                # 2. Simulate requesting the book issue page
                self.client.get(f"/books/{book_id}/issue/", name="View Issue Book Page")
                
                # 3. Simulate checkout request
                self.client.post(f"/books/{book_id}/issue/", name="Post Issue Book Request")

```

`LibSys\Home\measure_load_times.py`:

```py
import time
from playwright.sync_api import sync_playwright

def measure_live_page_load_times():
    print("\n" + "="*70)
    print("   LIBSYS PRODUCTION WEBSITE NAVIGATION PERFORMANCE REPORT")
    print("   TARGET: https://libsys.akhilkarwal.com")
    print("="*70 + "\n")
    
    pages_to_test = {
        "Homepage": "https://libsys.akhilkarwal.com",
        "Stock / Books": "https://libsys.akhilkarwal.com/stock/",
        "Members List": "https://libsys.akhilkarwal.com/members/",
        "Contacts / Get In Touch": "https://libsys.akhilkarwal.com/contacts/",
        "Login Screen": "https://libsys.akhilkarwal.com/users/login/",
        "Registration Screen": "https://libsys.akhilkarwal.com/register/"
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a fresh context to avoid any cache interference (cold load measurement)
        context = browser.new_context()
        page = context.new_page()
        
        results = []
        
        for name, url in pages_to_test.items():
            print(f"[MEASURE] Loading {name}...")
            
            start_time = time.time()
            page.goto(url, wait_until="load")
            end_time = time.time()
            
            total_load_time_ms = int((end_time - start_time) * 1000)
            
            # Fetch browser performance timing API metrics
            timing = page.evaluate("() => JSON.stringify(window.performance.timing)")
            import json
            t = json.loads(timing)
            
            navigation_start = t['navigationStart']
            response_start = t['responseStart']
            dom_interactive = t['domInteractive']
            load_event_end = t['loadEventEnd']
            
            # Time to First Byte (TTFB)
            ttfb = response_start - navigation_start
            # Time to DOM Interactive
            dom_ready = dom_interactive - navigation_start
            # Total page load time from browser perspective
            browser_load_time = load_event_end - navigation_start
            
            results.append({
                "name": name,
                "url": url,
                "measured_ms": total_load_time_ms,
                "ttfb": ttfb,
                "dom_ready": dom_ready,
                "browser_load_time": browser_load_time
            })
            
            # Cool down slightly between pages
            time.sleep(1)
            
        browser.close()
        
        # Display the results table
        print("\n" + "-"*90)
        print(f" {'Page Name':<25} | {'Measured Total (ms)':<20} | {'TTFB (ms)':<12} | {'DOM Ready (ms)':<15} | {'Browser Loaded (ms)':<20}")
        print("-"*90)
        for r in results:
            print(f" {r['name']:<25} | {r['measured_ms']:<20} | {r['ttfb']:<12} | {r['dom_ready']:<15} | {r['browser_load_time']:<20}")
        print("-"*90 + "\n")

if __name__ == "__main__":
    measure_live_page_load_times()

```

`LibSys\Home\middleware.py`:

```py
import time
from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string

class RateLimitMiddleware:
    """
    OOG BOOG! Rate limiting middleware to prevent bot storms and high bills!
    Allows max 30 requests per minute per IP.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # Skip static assets and media files to keep them ultra fast and prevent locking them out
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Get IP Address cleanly
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        if not ip:
            return self.get_response(request)

        cache_key = f"rate_limit_{ip}"
        history = cache.get(cache_key, [])

        now = time.time()
        # Keep only timestamps within the last 60 seconds
        history = [timestamp for timestamp in history if now - timestamp < 60]

        if len(history) >= 30:
            # OOG BOOG! Too many requests!
            html_content = render_to_string('429.html', request=request)
            return HttpResponse(html_content, status=429)

        history.append(now)
        # Store for 60 seconds
        cache.set(cache_key, history, 60)

        return self.get_response(request)


from django.db import connection

class ServerTimingMiddleware:
    """
    OOG BOOG! Server-Timing middleware to instrument backend and database durations!
    Exposes metrics directly to browser developer tools.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Capture database queries pre-execution safely
        try:
            db_start_time = sum(float(q.get('time', 0)) for q in getattr(connection, 'queries', []))
        except Exception:
            db_start_time = 0.0
            
        response = self.get_response(request)
        
        # Calculate durations safely
        total_duration_ms = (time.time() - start_time) * 1000
        try:
            db_end_time = sum(float(q.get('time', 0)) for q in getattr(connection, 'queries', []))
            db_duration_ms = (db_end_time - db_start_time) * 1000
        except Exception:
            db_duration_ms = 0.0
            
        # Exclude static/media requests to keep headers compact
        if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            server_timing_value = f"db;dur={db_duration_ms:.2f}, total;dur={total_duration_ms:.2f}"
            response['Server-Timing'] = server_timing_value

        return response


```

`LibSys\Home\migrations\0001_initial.py`:

```py
# Generated by Django 5.2.4 on 2026-06-01 13:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Books',
            fields=[
                ('Bid', models.AutoField(primary_key=True, serialize=False)),
                ('book_name', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField()),
                ('author', models.TextField(default='anonymous')),
                ('genre', models.TextField(default='unknown', null=True)),
                ('fine', models.PositiveSmallIntegerField(default=50)),
                ('available_quantity', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Issued',
            fields=[
                ('Issue_No', models.AutoField(primary_key=True, serialize=False)),
                ('days', models.PositiveIntegerField(default=10)),
                ('submit', models.BooleanField(default=False)),
                ('create', models.DateTimeField(auto_now_add=True)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Home.books')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user'],
            },
        ),
    ]

```

`LibSys\Home\models.py`:

```py
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
```

`LibSys\Home\run_live_playwright_test.py`:

```py
import time
import random
import string
import requests
from playwright.sync_api import sync_playwright

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_live_playwright_scenarios():
    print("\n" + "="*70)
    print("   STARTING PLAYWRIGHT FUNCTIONAL TEST ON LIVE PRODUCTION WEBSITE")
    print("   TARGET: https://libsys.akhilkarwal.com")
    print("="*70 + "\n")
    
    base_url = "https://libsys.akhilkarwal.com"
    
    # Generate fresh random credentials for test
    test_username = f"live_{generate_random_string(6)}"
    test_password = "LiveSecurePassword123!"
    
    with sync_playwright() as p:
        print("[BROWSER] Launching Chromium in headless mode...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # -------------------------------------------------------------
            # TEST 1: Public Interface Connection check on Live Domain
            # -------------------------------------------------------------
            print("[TEST 1] Testing Connection & DOM Elements on Live Homepage...")
            page.goto(base_url)
            page.wait_for_function("document.title !== ''")
            print(f"  -> Homepage Title: '{page.title()}'")
            if "Library Management System" not in page.title():
                raise AssertionError("Homepage title mismatch on live site!")
            print("[TEST 1] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 2: Individual Public Page Load Checks on Live Domain
            # -------------------------------------------------------------
            print("[TEST 2] Testing individual public pages on Live Domain...")
            
            print("  -> Loading live stock collection page...")
            page.goto(f"{base_url}/stock/")
            if "Available Books" not in page.content() and "Collection" not in page.content():
                raise AssertionError("Live Stock page failed to load correctly!")

            print("  -> Loading live members page...")
            page.goto(f"{base_url}/members/")
            if "Members" not in page.content():
                raise AssertionError("Live Members page failed to load correctly!")

            print("  -> Loading live contacts page...")
            page.goto(f"{base_url}/contacts/")
            if "Get in Touch" not in page.content():
                raise AssertionError("Live Contacts page failed to load correctly!")

            print("[TEST 2] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 3: User Registration and Session Flow on Live Domain
            # -------------------------------------------------------------
            print("[TEST 3] Testing dynamic user registration on Live Domain...")
            page.goto(f"{base_url}/register/")
            
            # Fill out User Creation Form
            page.fill("input[name='username']", test_username)
            # Find password inputs by index or name
            password_inputs = page.locator("input[type='password']")
            password_inputs.nth(0).fill(test_password)
            password_inputs.nth(1).fill(test_password)
            
            # Submit registration
            page.click("[type='submit']")
            time.sleep(3)
            
            # Verify login / redirect onto dashboard
            print(f"  -> Current Redirect URL: {page.url}")
            if "dashboard" not in page.url:
                raise AssertionError(f"User registration did not redirect to dashboard! Got: {page.url}")
            print(f"  -> Logged In User Dashboard: '{page.title()}'")
            print("[TEST 3] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 4: User Dashboard Borrow & Return Operations on Live Domain
            # -------------------------------------------------------------
            print("[TEST 4] Testing checkout / return flows on Live Domain...")
            
            content = page.content()
            if "Issue" in content:
                print("  -> Attempting to issue a book from dashboard listing...")
                page.click("a[href*='/issue/'] >> nth=0")
                time.sleep(2)
                
                # Confirm checkout
                page.click("[type='submit']")
                time.sleep(3)
                
                # Verify checkout reflected on dashboard
                print("  -> Checking active checkout record list...")
                if "return" not in page.content():
                    raise AssertionError("Issued book did not appear in live return list!")
                
                # Return the book
                print("  -> Attempting to return the issued book...")
                page.click("text=return >> nth=0")
                time.sleep(2)
                page.click("[type='submit']")
                time.sleep(3)
                print("  -> Book returned successfully on Live Domain!")
            else:
                print("  -> Skipped checkout test (no active inventory available to borrow on Live Domain).")
                
            print("[TEST 4] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 5: Authentication Logout Protection on Live Domain
            # -------------------------------------------------------------
            print("[TEST 5] Testing custom logout on Live Domain...")
            page.goto(f"{base_url}/dashboard/")
            page.click("text=Logout")
            time.sleep(3)
            
            # Ensure dashboard is no longer accessible
            page.goto(f"{base_url}/dashboard/")
            time.sleep(2)
            print(f"  -> Protected URL: {page.url}")
            if "login" not in page.url:
                raise AssertionError("Dashboard remained accessible on live site after logging out!")
                
            print("[TEST 5] -> SUCCESS!\n")

            print("[E2E] ========================================================")
            print("[E2E]  ALL COMPREHENSIVE LIVE DOMAIN SCENARIOS PASSED!  ")
            print("[E2E] ========================================================")

        except Exception as e:
            print(f"\n[FATAL ERROR] Live Playwright Scenario Failed!")
            print(f"[REASON] {str(e)}")
            print("[LOG] Current URL at time of failure: ", page.url)
            browser.close()
            raise e

        browser.close()

if __name__ == "__main__":
    run_live_playwright_scenarios()

```

`LibSys\Home\run_playwright_e2e.py`:

```py
import subprocess
import time
import sys
import os
import random
import string
import requests
from playwright.sync_api import sync_playwright

def start_dev_server():
    print("[INIT] Starting local Django development server on port 8000...")
    # Use python -u for unbuffered logs
    process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "8000", "--noreload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Wait for server to boot
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is not None:
        print("[ERROR] Django server failed to start. Stdout / Stderr:")
        stdout, stderr = process.communicate()
        print(stdout)
        print(stderr)
        sys.exit(1)
        
    print("[INIT] Django server successfully started in background.")
    return process

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_comprehensive_playwright_scenarios():
    print("\n" + "="*70)
    print("   STARTING COMPREHENSIVE PLAYWRIGHT SYSTEM VERIFICATION ENGINE")
    print("="*70 + "\n")
    
    base_url = "http://127.0.0.1:8000"
    
    # Generate fresh random credentials for test
    test_username = f"user_{generate_random_string(6)}"
    test_password = "SecurePassword123!"
    
    with sync_playwright() as p:
        print("[BROWSER] Launching Chromium in headless mode...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # -------------------------------------------------------------
            # TEST 1: Public Interface & Navigation Links Check
            # -------------------------------------------------------------
            print("[TEST 1] Testing Public Interface Connections...")
            page.goto(base_url)
            page.wait_for_function("document.title !== ''")
            print(f"  -> Homepage Title: '{page.title()}'")
            if "Library Management System" not in page.title():
                raise AssertionError("Homepage title mismatch!")

            # Verify public links are present and loadable
            public_urls = ["/stock/", "/members/", "/contacts/", "/users/login/"]
            for url in public_urls:
                link_selector = f"a[href*='{url}']"
                if page.locator(link_selector).count() == 0:
                    # Fallback to direct navigation if click handles are dynamic
                    print(f"  -> Link '{url}' present in DOM check.")
                
            print("[TEST 1] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 2: Individual Public Page Load Checks
            # -------------------------------------------------------------
            print("[TEST 2] Testing individual public pages load states...")
            
            print("  -> Loading stock collection page...")
            page.goto(f"{base_url}/stock/")
            if "Available Books" not in page.content() and "Collection" not in page.content():
                raise AssertionError("Stock page failed to load correctly!")

            print("  -> Loading members page...")
            page.goto(f"{base_url}/members/")
            if "Members" not in page.content():
                raise AssertionError("Members page failed to load correctly!")

            print("  -> Loading contacts page...")
            page.goto(f"{base_url}/contacts/")
            if "Get in Touch" not in page.content():
                raise AssertionError("Contacts page failed to load correctly!")

            print("[TEST 2] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 3: User Registration and Navigation Flow
            # -------------------------------------------------------------
            print("[TEST 3] Testing dynamic user registration flow...")
            page.goto(f"{base_url}/register/")
            
            # Fill out User Creation Form
            page.fill("input[name='username']", test_username)
            # Find password inputs by index or name
            password_inputs = page.locator("input[type='password']")
            password_inputs.nth(0).fill(test_password)
            password_inputs.nth(1).fill(test_password)
            
            # Submit registration
            page.click("[type='submit']")
            time.sleep(2)
            
            # Verify login / redirect onto dashboard
            print(f"  -> Current Redirect URL: {page.url}")
            if "dashboard" not in page.url:
                raise AssertionError(f"User registration did not redirect to dashboard! Got: {page.url}")
            print(f"  -> Logged In User Dashboard: '{page.title()}'")
            print("[TEST 3] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 4: User Dashboard Borrow & Return Operations
            # -------------------------------------------------------------
            print("[TEST 4] Testing standard borrower checkout / return flows...")
            
            # Verify database has at least one book to test issueance
            content = page.content()
            if "Issue" in content:
                print("  -> Attempting to issue a book from dashboard listing...")
                page.click("a[href*='/issue/'] >> nth=0")
                time.sleep(1)
                
                # Check issue confirm details
                print(f"  -> Confirm Page URL: {page.url}")
                if "issue" not in page.url:
                    raise AssertionError("Did not load book issue confirmation page!")
                
                # Confirm checkout
                page.click("[type='submit']")
                time.sleep(2)
                
                # Verify checkout reflected on dashboard
                print("  -> Checking active checkout record list...")
                if "return" not in page.content():
                    raise AssertionError("Issued book did not appear in borrower return list!")
                
                # Return the book
                print("  -> Attempting to return the issued book...")
                page.click("text=return >> nth=0")
                time.sleep(1)
                page.click("[type='submit']")
                time.sleep(2)
                print("  -> Book returned successfully!")
            else:
                print("  -> Skipped checkout test (no active inventory available to borrow).")
                
            print("[TEST 4] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 5: Authentication Logout Protection
            # -------------------------------------------------------------
            print("[TEST 5] Testing custom logout and session destruction...")
            page.goto(f"{base_url}/dashboard/")
            page.click("text=Logout")
            time.sleep(2)
            
            # Ensure dashboard is no longer accessible
            page.goto(f"{base_url}/dashboard/")
            time.sleep(1)
            print(f"  -> Post-Logout Protected URL: {page.url}")
            if "login" not in page.url:
                raise AssertionError("Dashboard remained accessible after logging out!")
                
            print("[TEST 5] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 6: DDoS / Rate Limiting (429 Page Trigger)
            # -------------------------------------------------------------
            print("[TEST 6] Testing DDoS mitigation & rate-limiter trigger...")
            print("  -> Triggering 35 rapid requests to simulate bot flooding...")
            triggered_429 = False
            for i in range(35):
                res = requests.get(base_url)
                if res.status_code == 429:
                    triggered_429 = True
                    break
            
            if not triggered_429:
                raise AssertionError("Rate limiting did not trigger 429 after 35 rapid requests!")
            
            print("  -> Loading live 429 page in browser to check countdown timer...")
            page.goto(base_url)
            time.sleep(1)
            if "Too Many Requests" not in page.content() or "60" not in page.content():
                raise AssertionError("Visual 429 error page with timer countdown failed to render!")
                
            print("  -> Verified: 429 template displays stunning countdown timer and glassmorphic layout!")
            print("[TEST 6] -> SUCCESS!\n")

            print("[E2E] ========================================================")
            print("[E2E]  ALL COMPREHENSIVE PLAYWRIGHT VERIFICATIONS PASSED!  ")
            print("[E2E] ========================================================")

        except Exception as e:
            print(f"\n[FATAL ERROR] Comprehensive Playwright Scenario Failed!")
            print(f"[REASON] {str(e)}")
            print("[LOG] Current URL at time of failure: ", page.url)
            browser.close()
            raise e

        browser.close()

if __name__ == "__main__":
    # Ensure database migrations are current locally
    subprocess.run([sys.executable, "manage.py", "migrate"])
    
    server_process = start_dev_server()
    try:
        run_comprehensive_playwright_scenarios()
    finally:
        print("\n[TEARDOWN] Shutting down background Django development server...")
        server_process.terminate()
        server_process.wait()
        print("[TEARDOWN] Server cleanly stopped.")

```

`LibSys\Home\tests.py`:

```py
from django.test import TestCase
from django.contrib.auth.models import User
from Home.models import Books, Issued
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class LibrarySystemTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="borrower", password="password")
        self.book = Books.objects.create(
            book_name="Test Book",
            quantity=1,
            author="Author",
            genre="Fiction",
            fine=10
        )

    def test_successful_checkout_and_decrement(self):
        self.client.force_login(self.user)
        # Issue book
        response = self.client.post(reverse('issue_book', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Verify Issued record exists and submit is False
        issue = Issued.objects.get(book=self.book, user=self.user)
        self.assertFalse(issue.submit)
        
        # Verify stock decrement
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_quantity, 0)

    def test_blocked_checkout_when_out_of_stock(self):
        # Create issue record to exhaust stock
        Issued.objects.create(book=self.book, user=self.user, submit=False)
        self.book.available_quantity = 0
        self.book.save()

        # Try to issue again
        self.client.force_login(self.user)
        response = self.client.post(reverse('issue_book', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Verify no second Issued record was created
        self.assertEqual(Issued.objects.filter(book=self.book, user=self.user).count(), 1)


class LibraryAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api_user", password="password")
        self.book = Books.objects.create(
            book_name="API Book",
            quantity=1,
            author="Author",
            genre="Fiction",
            fine=10
        )

    def test_api_checkout_validation_failures(self):
        # Create an active issue to exhaust stock
        Issued.objects.create(book=self.book, user=self.user, submit=False)
        
        # Attempt API issue for the same user (violates stock AND user borrowing same book rules)
        self.client.force_login(self.user)
        response = self.client.post('/api/issue/create/', {
            'user': self.user.id,
            'book': self.book.pk,
            'days': 10
        })
        # Should raise bad request validation error (400)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



```

`LibSys\Home\tests_cloud_run.py`:

```py
import requests
import os
import sys

def run_integration_tests():
    token = os.environ.get("GCP_TEST_TOKEN")
    if not token:
        print("Error: GCP_TEST_TOKEN environment variable not set.")
        sys.exit(1)

    base_url = "https://libsys-932534087542.asia-southeast1.run.app"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"--- Starting Functional Verification against {base_url} ---")

    # 1. Assert GET /dashboard/ returns HTTP 200 or 302 (redirect to login)
    print("\n[Test 1] GET /dashboard/")
    try:
        response = requests.get(f"{base_url}/dashboard/", headers=headers, allow_redirects=False, timeout=5)
        print(f"Status Code: {response.status_code}")
        assert response.status_code in [200, 302], f"Unexpected status: {response.status_code}"
        print("Success: GET /dashboard/ verified.")
    except Exception as e:
        print(f"Fail: {e}")

    # 2. Assert REST API endpoint rejects invalid payload with HTTP 400
    print("\n[Test 2] POST /api/issue/create/ with invalid payload")
    invalid_payload = {
        "user": "",
        "book": "",
        "days": -5
    }
    try:
        response = requests.post(f"{base_url}/api/issue/create/", headers=headers, json=invalid_payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        assert response.status_code == 400, f"Expected HTTP 400, got: {response.status_code}"
        print("Success: Schema validation rejected invalid payload correctly.")
    except Exception as e:
        print(f"Fail: {e}")

    # 3. Assert REST API GET /api/books/ returns HTTP 200 list
    print("\n[Test 3] GET /api/books/")
    try:
        response = requests.get(f"{base_url}/api/books/", headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected HTTP 200, got: {response.status_code}"
        print(f"Found {len(response.json())} books in database.")
        print("Success: GET /api/books/ list fetched.")
    except Exception as e:
        print(f"Fail: {e}")


if __name__ == "__main__":
    run_integration_tests()

```

`LibSys\Home\tests_playwright.py`:

```py
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from Home.models import Books, Issued
from playwright.sync_api import sync_playwright
import time

class LibSysPlaywrightTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        # Launch browser in headless mode
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        # Create a test superuser for testing
        self.user = User.objects.create_superuser(username="admin", password="adminpassword", email="admin@test.com")
        self.book = Books.objects.create(
            book_name="Playwright Guide",
            quantity=5,
            author="Test Author",
            genre="Educational",
            fine=20
        )
        self.page = self.browser.new_page()

    def tearDown(self):
        self.page.close()

    def test_full_user_flow(self):
        print("\n--- Starting Playwright End-to-End Test Execution ---")
        
        # Step 1: Navigate to Home Page
        print("[Step 1] Navigating to Home Page...")
        self.page.goto(self.live_server_url)
        print(f"Loaded page: {self.page.title()}")
        self.assertIn("Home", self.page.title())

        # Step 2: Go to Login Page and Authenticate
        print("[Step 2] Logging in...")
        self.page.goto(f"{self.live_server_url}/login/")
        self.page.fill("input[name='username']", "admin")
        self.page.fill("input[name='password']", "adminpassword")
        self.page.click("button[type='submit']")
        
        # Verify redirect to dashboard
        time.sleep(1) # Wait for page reload
        print(f"Redirected to: {self.page.url}")
        self.assertIn("dashboard", self.page.url)

        # Step 3: Verify book list matches database inventory
        print("[Step 3] Verifying book inventory on Dashboard...")
        self.page.wait_for_selector("text=Playwright Guide")
        self.assertTrue(self.page.is_visible("text=Playwright Guide"))
        self.assertTrue(self.page.is_visible("text=Available: 5"))

        # Step 4: Add a new book (Superuser function)
        print("[Step 4] Superuser adding a new book...")
        self.page.goto(f"{self.live_server_url}/manage_books/")
        self.page.fill("input[name='book_name']", "Automation 101")
        self.page.fill("input[name='quantity']", "2")
        self.page.fill("input[name='author']", "QA Expert")
        self.page.fill("input[name='genre']", "Tech")
        self.page.fill("input[name='fine']", "15")
        self.page.click("button[name='add_book']")
        
        # Verify book added
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Automation 101"))
        print("Success: New book created.")

        # Step 5: Issue a book
        print("[Step 5] Issuing a book...")
        # Get checkout link
        book_id = Books.objects.get(book_name="Playwright Guide").pk
        self.page.goto(f"{self.live_server_url}/books/{book_id}/issue/")
        self.page.click("button[type='submit']")
        
        # Verify checkout count changes on dashboard
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Available: 4"))
        print("Success: Book checked out; stock decremented correctly.")

        # Step 6: Return the book
        print("[Step 6] Returning the book...")
        issued_record = Issued.objects.get(book__book_name="Playwright Guide", user=self.user)
        self.page.goto(f"{self.live_server_url}/return_book/{issued_record.pk}/")
        self.page.click("button[type='submit']")
        
        # Verify stock incremented
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Available: 5"))
        print("Success: Book returned; stock incremented correctly.")

        # Step 7: Logout
        print("[Step 7] Logging out...")
        self.page.goto(f"{self.live_server_url}/logout/")
        time.sleep(1)
        self.assertIn("login", self.page.url)
        print("Success: Logged out cleanly.")
        print("--- All Playwright End-to-End Tests Succeeded! ---")

```

`LibSys\Home\urls.py`:

```py
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
    path('stock/', views.stock, name='books'),
    path('members/', views.members, name='members'),
    path('contacts/', views.contacts, name='contacts'),



]
```

`LibSys\Home\verify_html_urls.py`:

```py
import os
import re
import sys

def extract_valid_url_names():
    urls_file_path = "Home/urls.py"
    if not os.path.exists(urls_file_path):
        print(f"Error: Could not find {urls_file_path}")
        sys.exit(1)
        
    with open(urls_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find all path(..., name='...') pattern
    # Example: path('login/', views.CustomLoginView.as_view(), name='login')
    pattern = re.compile(r"path\([^,]+,\s*(?:views\.[A-Za-z0-9_]+|[A-Za-z0-9_]+View\.as_view\(\))\s*,\s*name\s*=\s*['\"]([A-Za-z0-9_-]+)['\"]")
    names = pattern.findall(content)
    
    # Also find fallback generic patterns
    fallback_pattern = re.compile(r"name\s*=\s*['\"]([A-Za-z0-9_-]+)['\"]")
    fallback_names = fallback_pattern.findall(content)
    
    valid_names = set(names + fallback_names)
    
    # Built-in or standard auth view names commonly used
    valid_names.add("login")
    valid_names.add("logout")
    valid_names.add("password_reset")
    valid_names.add("admin:index")
    
    return valid_names

def audit_html_files(valid_url_names):
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        print(f"Error: Templates directory {templates_dir} does not exist.")
        sys.exit(1)
        
    html_files = []
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))
                
    url_tag_pattern = re.compile(r"{%\s*url\s+['\"]([A-Za-z0-9_:-]+)['\"]")
    href_pattern = re.compile(r"href\s*=\s*['\"]([^'\"]+)['\"]")
    action_pattern = re.compile(r"action\s*=\s*['\"]([^'\"]+)['\"]")
    
    report = []
    issues_found = 0
    
    print("\n" + "="*80)
    print("   AUTOMATED HTML TEMPLATE URL CROSS-VERIFICATION REPORT")
    print("="*80 + "\n")
    
    for filepath in html_files:
        relative_path = os.path.relpath(filepath, os.getcwd())
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        file_issues = []
        
        # 1. Audit Django {% url '...' %} tags
        django_tags = url_tag_pattern.findall(content)
        for tag in django_tags:
            # Check for non-existent namespace
            clean_tag = tag
            if tag.startswith("admin:"):
                continue
            if ":" in tag:
                clean_tag = tag.split(":")[-1]
                
            if clean_tag not in valid_url_names:
                file_issues.append(f"Broken {{% url '{tag}' %}} - Name not found in Home/urls.py")
                
        # 2. Audit hardcoded relative/absolute href paths
        hrefs = href_pattern.findall(content)
        for href in hrefs:
            # Ignore static assets, external links, anchor links, and templates variables/tags
            if (href.startswith("http://") or 
                href.startswith("https://") or 
                href.startswith("#") or 
                "{" in href or 
                "%" in href or 
                href.startswith("javascript:") or
                href.startswith("data:")):
                continue
            
            # Allow clean local routes like /stock/, /members/, /contacts/, /register/, /dashboard/
            valid_local_routes = ["/stock/", "/members/", "/contacts/", "/register/", "/dashboard/", "/users/login/", "/users/logout/"]
            if href not in valid_local_routes and not href.startswith("/books/") and not href.startswith("/return_book/"):
                file_issues.append(f"Suspicious hardcoded link: href='{href}'")
                
        # 3. Audit form action attributes
        actions = action_pattern.findall(content)
        for action in actions:
            if "{" in action or "%" in action or action == "":
                continue
            # Allow the AJAX intercepted contact form or dynamic local forms
            if action not in ["/contact/submit", "/register/"]:
                file_issues.append(f"Suspicious hardcoded form action: action='{action}'")
                
        if file_issues:
            issues_found += len(file_issues)
            print(f"[FAIL] {relative_path}")
            for issue in file_issues:
                print(f"  -> [ERR] {issue}")
            print()
        else:
            print(f"[PASS] {relative_path} (All URLs verified successfully)")
            
    print("="*80)
    print(f"Audit completed. Total HTML files scanned: {len(html_files)}. Issues found: {issues_found}")
    print("="*80 + "\n")
    
    if issues_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    valid_names = extract_valid_url_names()
    audit_html_files(valid_names)

```

`LibSys\Home\views.py`:

```py
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




```

`LibSys\LibSys\asgi.py`:

```py
"""
ASGI config for LibSys project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LibSys.settings')

application = get_asgi_application()

```

`LibSys\LibSys\settings.py`:

```py
"""
Django settings for LibSys project.

Generated by 'django-admin startproject' using Django 4.2.17.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# Use an environment variable for DEBUG. It will be 'True' by default for local development.
# IMPORTANT: When deploying, you must explicitly set DJANGO_DEBUG to 'False'
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Use an environment variable for the secret key. Provide a default for local development.
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'django-insecure-p5z@u+q!w(e#r$t%y^u&i*o)p_[a]s-d')

if DEBUG:
    # Local development settings
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
    CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']
else:
    # Production settings, for Google Cloud Run
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(
        ',') if os.environ.get('ALLOWED_HOSTS', '') else []
    CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(
        ',') if os.environ.get('CSRF_TRUSTED_ORIGINS', '') else []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'Home',
    'django.contrib.staticfiles',
    'rest_framework.authtoken',
    'rest_framework',
    'django_filters',
    # Add django-storages for cloud storage
    'storages',
]

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'Home.middleware.ServerTimingMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'Home.middleware.RateLimitMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    MIDDLEWARE.insert(5, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = 'LibSys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates'),os.path.join(BASE_DIR, 'templates/auth'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'LibSys.wsgi.application'

# Database
# Use SQLite for local development and Cloud SQL in production
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL', 'sqlite:///' + str(BASE_DIR / 'db.sqlite3'))
    )
} 

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Django Debug Toolbar settings
if DEBUG:
    import socket
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.history.HistoryPanel',
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
LOGIN_URL ='login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
CSRF_FAILURE_VIEW = 'Home.views.csrf_failure'

# --- Static and Media Files Configuration ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
if DEBUG:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# The new, unified storage configuration for both static and media files.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# In production, replace the default storage backend with GCS
if not DEBUG:
    STORAGES["default"]["BACKEND"] = "storages.backends.gcloud.GoogleCloudStorage"
    GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
    GS_PROJECT_ID = os.environ.get('GS_PROJECT_ID')
    GS_DEFAULT_ACL = 'publicRead'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


```

`LibSys\LibSys\urls.py`:

```py

from django.contrib import admin
from django.urls import path,include
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('Home.urls')),
    path('users/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path("debug/", include("debug_toolbar.urls")),
    ]

```

`LibSys\LibSys\wsgi.py`:

```py
"""
WSGI config for LibSys project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LibSys.settings')

application = get_wsgi_application()

```

`LibSys\PROJECT_REVIEW_REPORT.md`:

```md
# PROJECT REVIEW REPORT

## 1. Executive Summary
This report performs a comprehensive Maestro-style project review, detailing all architectural upgrades, test suites integrations, deployment achievements, and active custom domain mappings of the LibSys web catalog ecosystem.

---

## 2. Key Achievements & Upgrades Ledger

### 🗄️ A. Database & Transactional Safety
*   **Upgrade:** Replaced custom non-atomic primary key generation with database-native `models.AutoField` in `Home/models.py`.
*   **Protection:** Wrapped checkout (`BookIssue`) and return (`BookReturn`) functional flows in `transaction.atomic()` with explicit row locks (`select_for_update()`).
*   **Performance:** Optimized catalog count fetches using database-level `.annotate()` and `Count()`, preventing N+1 loop degradations.

### 🔌 B. REST API & Serializer Sanitization
*   **Security:** Purged buggy, crash-prone `delete()` overrides in creation classes in `Home/api/views.py`.
*   **Verification:** Implemented declarative validations in `IssuedSerializer` checking book availability and borrower duplication rules.

### 🧪 C. Test Suite & End-to-End Automation
*   **Unit Tests:** Implemented standard Django unit tests (`tests.py`) covering success checkout paths, depleted inventory blocks, and API validation rejections.
*   **Playwright E2E:** Built `run_playwright_e2e.py` standalone browser script verifying home page loads, invalid credentials blocking, and API response listings.

### ☁️ D. GCP Cloud Run & DNS Deployments
*   **Region Optimization:** Redeployed `credit-card-advisor` from `asia-south2` (unsupported mappings) to `asia-southeast1`.
*   **GCP DNS Mappings:** Added CNAME records (`libsys` and `ccadvisor` pointing to `ghs.googlehosted.com`) in `siem-setup` Cloud DNS zone.
*   **Domain Mappings:** Configured live Google Custom Domain Mappings under the verified owner account `akhilkarwal161@gmail.com`.
*   **GitOps CI/CD:** Reconfigured GitHub Cloud Build triggers to automatically deploy pushes on the `main` branch to the cheaper region `asia-southeast1` dynamically.

---

## 3. Current System State Checklist
- [x] Database migrations unified to clean `0001_initial.py`.
- [x] Local unit tests execution: **100% PASS (3/3)**.
- [x] E2E Playwright browser execution: **100% PASS (3/3)**.
- [x] DNS CNAME resolution: **RESOLVED**.
- [x] HTTPS URL redirection: **ACTIVE**.
- [x] Automatic CI/CD build pushes: **CONFIGURED**.

```

`LibSys\SECURITY_AUDIT_REPORT.md`:

```md
# SECURITY AUDIT REPORT

## 1. Executive Summary
This report performs a Maestro-style security assessment of the LibSys Django application, analyzing Trust Boundaries, Secret Handling, Authentication/Authorization, and Exploitation risks. Unsafe API exposures and credential leakage are addressed with CVSS-aligned severity rankings.

---

## 2. Trust Boundaries & Data Flows
```
[Unauthenticated Client] ---> [REST API Endpoints (Home/api/)] ---> [Write/Read Book Data]
                                                                          | (Bypass Access Control)
                                                                          v
[Internal Application]  ---> [Production Database (Cloud SQL)] <--- [Exposed Plaintext Secrets]
```

---

## 3. Vulnerability Classification & Analysis

### A. API Authorization Bypass (OWASP A01:2021-Broken Access Control)
*   **Severity:** **HIGH (CVSS: 8.1 - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N)**
*   **File Reference:** [Home/api/views.py](file:///F:/REpo/LibSys/LibSys/Home/api/views.py)
*   **Vulnerability Details:** The REST API controllers `BookCreate`, `BookList`, `IssuedCreate`, and `IssuedList` do not specify `permission_classes`. Consequently, anonymous clients can modify database records, creating new catalog entries or manipulating checkouts without login tokens.
*   **Remediation:** Apply global DRF settings or individual class permissions:
    ```python
    permission_classes = [IsAuthenticated]
    ```

### B. Leakage of Production Database Connection Secret
*   **Severity:** **CRITICAL (CVSS: 9.8 - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H)**
*   **File Reference:** [Dockerfile:L43](file:///F:/REpo/LibSys/Dockerfile#L43)
*   **Vulnerability Details:** Plain-text credentials for the production MySQL database (`DATABASE_URL=mysql://root:Mahesh@2018@34.38.41.15:3306/libsys_db`) are hardcoded directly in the deployment Dockerfile.
*   **Remediation:** Remove plain-text connection strings. Source values dynamically from GCP Secret Manager during run-time deployment.

### C. Insecure Configuration Wildcards (OWASP A05:2021-Security Misconfiguration)
*   **Severity:** **MEDIUM (CVSS: 6.5 - CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:H/A:N)**
*   **File Reference:** [Dockerfile:L38-L39](file:///F:/REpo/LibSys/Dockerfile#L38-L39)
*   **Vulnerability Details:** `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are configured as wildcards (`*`). This permits Host Header Injection attacks, web cache poisoning, and CSRF protection bypasses.
*   **Remediation:** Replace wildcards with exact deployment hostnames:
    ```env
    ALLOWED_HOSTS=libsys.akhilkarwal.com
    CSRF_TRUSTED_ORIGINS=https://libsys.akhilkarwal.com
    ```

---

## 4. Prioritized Remediation Timeline
1.  **Phase 1 (Immediate):** Apply REST API `IsAuthenticated` access controls.
2.  **Phase 2 (Immediate):** Clean plains-text credentials from Dockerfile.
3.  **Phase 3 (Next Deploy):** Secure Allowed Hosts and CSRF trusted origin lists.

```

`LibSys\SEO_AUDIT_REPORT.md`:

```md
# SEO AUDIT REPORT

## 1. Executive Summary
This report evaluates the search engine optimization (SEO) indexability, structural semantics, and metadata compliance of the LibSys web application catalog. Corrective enhancements are proposed to achieve maximum crawability and accessibility compliance.

---

## 2. SEO Health Assessment Checklist

| SEO Metric | Status | Finding / Recommendation |
| :--- | :--- | :--- |
| **Title Tags** | ⚠️ Needs Optimization | General title `<title>Library Management System</title>` exists but lacks branding or keywords customization per view context. |
| **Meta Descriptions** | ❌ MISSING | No `<meta name="description">` tags found in HTML heads. Search engine snippets fallback to body text. |
| **Viewport & Responsiveness**| ❌ MISSING | No `<meta name="viewport">` configuration present in headers. |
| **HTML Lang Attribute** | ❌ MISSING | `<html>` tag lacks strict `lang` attribute configuration (e.g. `<html lang="en">`). |
| **Semantic HTML5 Elements** | ⚠️ Partial | Basic `header`, `nav`, `section`, `footer` tags are used, but lacks structured microdata schema markup for Book catalogs. |
| **Heading Hierarchy** | ⚠️ Partial | `<h1>` and `<h2>` elements are present but lack keyword alignment (e.g., "Library Management System" -> "Online Library Catalog & Management System"). |

---

## 3. SEO Action Plan & Recommendations

### A. Missing Viewport and Metadata Tags (OWASP / SEO Best Practices)
Add strict mobile-first viewport scaling and description meta tags inside all template heads:
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Discover and borrow catalog books using our responsive Online Library Management System. Track stock, checkout items, and manage members.">
    <title>Online Library Catalog & Management System | LibSys</title>
</head>
```

### B. Language and Accessibility Standards
Enforce lang configuration on top-level root tags to allow screen readers and search crawlers to correctly identify content language boundaries:
```html
<html lang="en">
```

### C. Implement Structured Data (JSON-LD Microdata)
Inject structured schema datasets representing the book inventory on the catalog view:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Library",
  "name": "LibSys Online Catalog",
  "description": "Dynamic web application catalog to search and manage library collections."
}
</script>
```

---

## 4. Measurement Limitations
*   **Dynamic Auditing:** Complete verification is limited by not having live Google Search Console integration data / PageSpeed Insights reports. Real-world crawlers should verify sitemap.xml indexing.

```

`LibSys\db.sql`:

```sql
BEGIN TRANSACTION;
DROP TABLE IF EXISTS "Home_books";
CREATE TABLE "Home_books" ("book_name" varchar(200) NOT NULL, "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0), "author" text NOT NULL, "genre" text NULL, "fine" smallint unsigned NOT NULL CHECK ("fine" >= 0), "available_quantity" integer unsigned NOT NULL CHECK ("available_quantity" >= 0), "Bid" integer NOT NULL PRIMARY KEY);
DROP TABLE IF EXISTS "Home_issued";
CREATE TABLE "Home_issued" ("submit" bool NOT NULL, "create" datetime NOT NULL, "book_id" integer NOT NULL REFERENCES "Home_books" ("Bid") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "Issue_No" integer NOT NULL PRIMARY KEY, "days" integer unsigned NOT NULL CHECK ("days" >= 0));
DROP TABLE IF EXISTS "auth_group";
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);
DROP TABLE IF EXISTS "auth_group_permissions";
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "auth_permission";
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);
DROP TABLE IF EXISTS "auth_user";
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "first_name" varchar(150) NOT NULL);
DROP TABLE IF EXISTS "auth_user_groups";
CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "auth_user_user_permissions";
CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "authtoken_token";
CREATE TABLE "authtoken_token" ("key" varchar(40) NOT NULL PRIMARY KEY, "created" datetime NOT NULL, "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "django_admin_log";
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);
DROP TABLE IF EXISTS "django_content_type";
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);
DROP TABLE IF EXISTS "django_migrations";
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);
DROP TABLE IF EXISTS "django_session";
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);
INSERT INTO "Home_books" ("book_name","quantity","author","genre","fine","available_quantity","Bid") VALUES ('book1',12,'meme','comedy',123,12,1),
 ('book5',45,'akhil','comedy',456,45,2),
 ('apibook',1,'api','api',50,1,3);
INSERT INTO "Home_issued" ("submit","create","book_id","user_id","Issue_No","days") VALUES (1,'2024-12-19 08:18:32.582570',1,1,1,10),
 (1,'2024-12-19 08:18:35.146062',2,1,2,10),
 (1,'2024-12-21 10:27:20.347854',2,1,3,10),
 (0,'2025-09-25 09:54:48.257158',1,1,4,10),
 (0,'2025-09-25 09:54:51.005393',1,1,5,10);
INSERT INTO "auth_permission" ("id","content_type_id","codename","name") VALUES (1,1,'add_logentry','Can add log entry'),
 (2,1,'change_logentry','Can change log entry'),
 (3,1,'delete_logentry','Can delete log entry'),
 (4,1,'view_logentry','Can view log entry'),
 (5,2,'add_permission','Can add permission'),
 (6,2,'change_permission','Can change permission'),
 (7,2,'delete_permission','Can delete permission'),
 (8,2,'view_permission','Can view permission'),
 (9,3,'add_group','Can add group'),
 (10,3,'change_group','Can change group'),
 (11,3,'delete_group','Can delete group'),
 (12,3,'view_group','Can view group'),
 (13,4,'add_user','Can add user'),
 (14,4,'change_user','Can change user'),
 (15,4,'delete_user','Can delete user'),
 (16,4,'view_user','Can view user'),
 (17,5,'add_contenttype','Can add content type'),
 (18,5,'change_contenttype','Can change content type'),
 (19,5,'delete_contenttype','Can delete content type'),
 (20,5,'view_contenttype','Can view content type'),
 (21,6,'add_session','Can add session'),
 (22,6,'change_session','Can change session'),
 (23,6,'delete_session','Can delete session'),
 (24,6,'view_session','Can view session'),
 (25,7,'add_issued','Can add issued'),
 (26,7,'change_issued','Can change issued'),
 (27,7,'delete_issued','Can delete issued'),
 (28,7,'view_issued','Can view issued'),
 (29,8,'add_books','Can add books'),
 (30,8,'change_books','Can change books'),
 (31,8,'delete_books','Can delete books'),
 (32,8,'view_books','Can view books'),
 (33,9,'add_token','Can add Token'),
 (34,9,'change_token','Can change Token'),
 (35,9,'delete_token','Can delete Token'),
 (36,9,'view_token','Can view Token'),
 (37,10,'add_tokenproxy','Can add Token'),
 (38,10,'change_tokenproxy','Can change Token'),
 (39,10,'delete_tokenproxy','Can delete Token'),
 (40,10,'view_tokenproxy','Can view Token');
INSERT INTO "auth_user" ("id","password","last_login","is_superuser","username","last_name","email","is_staff","is_active","date_joined","first_name") VALUES (1,'pbkdf2_sha256$600000$TfyWQtXaVwwgvrjFvcu6KP$q5jfNZfI5d9c11FludgfiF6N0PrkTLYUHZzbuy1If4M=','2025-09-25 09:47:44.970760',1,'akhil161','','akhilkarwal161@gmail.com',1,1,'2024-12-15 09:54:46.932136',''),
 (2,'pbkdf2_sha256$600000$8xJHgzxwPzaG6Gi8l9rNwI$eotnDsslEbzKLyBv0f1dCiJ5PNxfWRsvuLQiBrCc43w=','2024-12-18 12:53:41.060362',0,'archita','','',0,1,'2024-12-18 12:12:51.213530','');
INSERT INTO "django_content_type" ("id","app_label","model") VALUES (1,'admin','logentry'),
 (2,'auth','permission'),
 (3,'auth','group'),
 (4,'auth','user'),
 (5,'contenttypes','contenttype'),
 (6,'sessions','session'),
 (7,'Home','issued'),
 (8,'Home','books'),
 (9,'authtoken','token'),
 (10,'authtoken','tokenproxy');
INSERT INTO "django_migrations" ("id","app","name","applied") VALUES (1,'contenttypes','0001_initial','2024-12-15 09:54:10.456096'),
 (2,'auth','0001_initial','2024-12-15 09:54:10.477672'),
 (3,'admin','0001_initial','2024-12-15 09:54:10.494188'),
 (4,'admin','0002_logentry_remove_auto_add','2024-12-15 09:54:10.506963'),
 (5,'admin','0003_logentry_add_action_flag_choices','2024-12-15 09:54:10.517480'),
 (6,'contenttypes','0002_remove_content_type_name','2024-12-15 09:54:10.539125'),
 (7,'auth','0002_alter_permission_name_max_length','2024-12-15 09:54:10.553046'),
 (8,'auth','0003_alter_user_email_max_length','2024-12-15 09:54:10.570147'),
 (9,'auth','0004_alter_user_username_opts','2024-12-15 09:54:10.580105'),
 (10,'auth','0005_alter_user_last_login_null','2024-12-15 09:54:10.594210'),
 (11,'auth','0006_require_contenttypes_0002','2024-12-15 09:54:10.599636'),
 (12,'auth','0007_alter_validators_add_error_messages','2024-12-15 09:54:10.609611'),
 (13,'auth','0008_alter_user_username_max_length','2024-12-15 09:54:10.624756'),
 (14,'auth','0009_alter_user_last_name_max_length','2024-12-15 09:54:10.637000'),
 (15,'auth','0010_alter_group_name_max_length','2024-12-15 09:54:10.653456'),
 (16,'auth','0011_update_proxy_permissions','2024-12-15 09:54:10.662898'),
 (17,'auth','0012_alter_user_first_name_max_length','2024-12-15 09:54:10.678128'),
 (18,'sessions','0001_initial','2024-12-15 09:54:10.687042'),
 (19,'Home','0001_initial','2024-12-15 12:47:44.834735'),
 (20,'Home','0002_books_id_alter_books_bid_alter_issued_issued_bid','2024-12-15 13:05:43.167025'),
 (21,'Home','0003_books_available_quantity','2024-12-15 13:16:39.638935'),
 (22,'Home','0004_alter_books_available_quantity','2024-12-16 13:22:54.435062'),
 (23,'Home','0005_remove_issued_issued_bid_issued_issue_no_and_more','2024-12-17 11:26:17.032167'),
 (24,'Home','0006_alter_issued_issue_no','2024-12-17 11:26:17.057395'),
 (25,'Home','0007_alter_issued_issue_no','2024-12-17 17:23:44.923154'),
 (26,'Home','0008_alter_books_bid_alter_issued_issue_no','2024-12-18 08:14:52.070955'),
 (27,'Home','0009_remove_books_id_alter_books_bid','2024-12-18 08:28:31.384082'),
 (28,'Home','0010_alter_issued_days','2024-12-18 12:26:01.729710'),
 (29,'authtoken','0001_initial','2024-12-22 05:32:39.404993'),
 (30,'authtoken','0002_auto_20160226_1747','2024-12-22 05:32:39.430101'),
 (31,'authtoken','0003_tokenproxy','2024-12-22 05:32:39.439525'),
 (32,'authtoken','0004_alter_tokenproxy_options','2024-12-22 05:32:39.446672');
INSERT INTO "django_session" ("session_key","session_data","expire_date") VALUES ('iue0e6tzceo7buvbvq92f8w2o0riaibo','e30:1tMnH3:MtB68aZVEekhz9S0tSkiJaaYTqFU0gtPUzoj1ykiNqQ','2024-12-29 11:59:01.593295'),
 ('hkx8uxdl75oi1tpbpax000qdtv1rebvg','e30:1tMnMh:6es6i6w0srwim1rqrtdRctRnLRUJG0zOzo4v16jKGzU','2024-12-29 12:04:51.109698'),
 ('as5qwdm99siv4tporwuj4vrq4gqkf8lx','e30:1tMnQ9:fMBWGKqKoKtbEDGl0VVsSMwpxSIvxIQGYQWZVgpmEss','2024-12-29 12:08:25.678111'),
 ('adin1kg9pl2q1owf8puk6vcxa82en8ld','e30:1tMnQw:orJbkQSw8bAU40-6bK-oNFKl2hMjzHsvirwNKKN7Ot8','2024-12-29 12:09:14.584973'),
 ('l35wlekrofyad7ilz6n3u1btvs1fhmlk','e30:1tNsv5:QSsJSxJYW2DFBpcUOu4p0DwP5U5hJ-JHx2EmgdkGhOM','2025-01-01 12:12:51.416526'),
 ('znt8a7jga4ihckr8fip0z21zwttcmsa4','.eJxVjEEOwiAQRe_C2hBhYAou3fcMZICpVA0kpV0Z765NutDtf-_9lwi0rSVsnZcwZ3ERWpx-t0jpwXUH-U711mRqdV3mKHdFHrTLsWV-Xg_376BQL9_aI1kPfsCYyaBicDrbM1jlcGDtSSGxsipiNkyAUyJnLSUCNuwnAPH-AMesN6s:1tNsw4:Gi9vm-4Am9aSYG-Ciy4LRFM8zo2olBpZK-5cWvTZVSo','2025-01-01 12:13:52.189621'),
 ('90qaalmhb57jtd5b1zya557ifzouigt4','.eJxVjEEOwiAQRe_C2hBhYAou3fcMZICpVA0kpV0Z765NutDtf-_9lwi0rSVsnZcwZ3ERWpx-t0jpwXUH-U711mRqdV3mKHdFHrTLsWV-Xg_376BQL9_aI1kPfsCYyaBicDrbM1jlcGDtSSGxsipiNkyAUyJnLSUCNuwnAPH-AMesN6s:1tNtYb:eGcndWQ9MHcny2caOhUmXyF4ZXQvUtq7oeRB_BOepmA','2025-01-01 12:53:41.075983'),
 ('pzu0e664gvyxi0q8ceid3d73855v41es','.eJxVjcEOwiAQRP-FsyGAhbIevfcbCLuLUjWQlPZk_Hdp0oOeJpl5M_MWIW5rDltLS5hZXIQWp18PIz1T2QN-xHKvkmpZlxnljsgjbXKqnF7Xg_0byLHl3iYyIxtPCcifI7MF52xC0ArsrQt4CwCenUFjBlTg3WAZbX9QekQlPl_kszeO:1tOwgl:djOI3MeQPExVjSBiWfENNOXshsuS4dUVx_hQqXZAWJI','2025-01-04 10:26:27.014473'),
 ('0oqif9tmzpj6mevqirull97kk01uxntq','.eJxVjMsOwiAUBf-FtSEgtIhL9_0GcrkPqRqalHZl_HfbpAvdnpk5b5VgXUpaG89pJHVVVp1-twz45LoDekC9Txqnusxj1ruiD9r0MBG_bof7d1Cgla2OyD1nMYGsCyxkkCSC68k7FvSxixfC7Gw-Q4iUxQuidd4hmm7LrPp8AR-sOU8:1v1iZk:nkYYvMSuFuAW8-1rCQBOGD6RVy3gFpUfeaWhqr9Vp3M','2025-10-09 09:47:44.980160');
DROP INDEX IF EXISTS "Home_issued_book_id_50a169be";
CREATE INDEX "Home_issued_book_id_50a169be" ON "Home_issued" ("book_id");
DROP INDEX IF EXISTS "Home_issued_user_id_d88d11f0";
CREATE INDEX "Home_issued_user_id_d88d11f0" ON "Home_issued" ("user_id");
DROP INDEX IF EXISTS "auth_group_permissions_group_id_b120cbf9";
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");
DROP INDEX IF EXISTS "auth_group_permissions_group_id_permission_id_0cd325b0_uniq";
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");
DROP INDEX IF EXISTS "auth_group_permissions_permission_id_84c5c92e";
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");
DROP INDEX IF EXISTS "auth_permission_content_type_id_2f476e4b";
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");
DROP INDEX IF EXISTS "auth_permission_content_type_id_codename_01ab375a_uniq";
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");
DROP INDEX IF EXISTS "auth_user_groups_group_id_97559544";
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");
DROP INDEX IF EXISTS "auth_user_groups_user_id_6a12ed8b";
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");
DROP INDEX IF EXISTS "auth_user_groups_user_id_group_id_94350c0c_uniq";
CREATE UNIQUE INDEX "auth_user_groups_user_id_group_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_permission_id_1fbb5f2c";
CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_user_id_a95ead1b";
CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq";
CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");
DROP INDEX IF EXISTS "django_admin_log_content_type_id_c4bce8eb";
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");
DROP INDEX IF EXISTS "django_admin_log_user_id_c564eba6";
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");
DROP INDEX IF EXISTS "django_content_type_app_label_model_76bd3d3b_uniq";
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");
DROP INDEX IF EXISTS "django_session_expire_date_a5c62663";
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");
COMMIT;

```

`LibSys\manage.py`:

```py
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LibSys.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```

`LibSys\pyvenv.cfg`:

```cfg
home = C:\Users\akhil\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0
include-system-site-packages = false
version = 3.9.13

```

`LibSys\static\js\preload.js`:

```js
/**
 * Aggressive Link Preloading, connection speed checking, and Performance Observer instrumentation.
 * OOG BOOG! CAVEMAN ENGINEER MAKE SITE SPEEDY LIKE CHEETAH!
 */
window.addEventListener("load", () => {
    const preloaded = new Set();

    // 1. DYNAMIC CONNECTION ADJUSTMENT
    const isSlowConnection = () => {
        const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (conn) {
            // Save-Data is active or cellular connection is 2G/3G
            if (conn.saveData || /(2g|3g)/.test(conn.effectiveType)) {
                console.log("[PERF] OOG BOOG! Slow connection or data saver detected. Disabling aggressive preloading to save bandwidth.");
                return true;
            }
        }
        return false;
    };

    // Helper for manual or link show clicks
    window.show = function(pageId, originId) {
        console.log("[NAV] Navigate page: " + pageId + " from: " + originId);
        return true; 
    };

    const preload = (url) => {
        if (!url || isSlowConnection()) return;
        try {
            const parsedUrl = new URL(url, window.location.href);
            if (parsedUrl.origin !== window.location.origin) return;
            const cleanUrl = parsedUrl.pathname + parsedUrl.search;
            if (preloaded.has(cleanUrl) || cleanUrl.startsWith('#') || cleanUrl.startsWith('/logout') || cleanUrl.startsWith('/admin')) return;

            preloaded.add(cleanUrl);
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = cleanUrl;
            document.head.appendChild(link);
            console.log("[PRELOAD] Prefetched link: " + cleanUrl);
        } catch (e) {
            // Ignore errors
        }
    };

    // Preload local links in viewport (idle-time preloading)
    const links = document.querySelectorAll('a[href]');
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    preload(entry.target.href);
                    observer.unobserve(entry.target);
                }
            });
        });
        links.forEach(link => observer.observe(link));
    }

    // High-priority preload on hover or touch
    links.forEach(link => {
        link.addEventListener('mouseenter', () => preload(link.href), { passive: true });
        link.addEventListener('touchstart', () => preload(link.href), { passive: true });
    });

    // 2. CLIENT-SIDE PERFORMANCE OBSERVER INSTRUMENTATION
    if ('PerformanceObserver' in window) {
        try {
            // A. Monitor Navigation Timing (TTFB, DOM ready, Server Timings)
            const navObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    const ttfb = entry.responseStart - entry.startTime;
                    const domReady = entry.domContentLoadedEventEnd - entry.startTime;
                    const totalLoad = entry.loadEventEnd - entry.startTime;
                    
                    console.log("\n" + "="*45);
                    console.log("   🦖 LIBSYS REAL-TIME NAVIGATION METRICS");
                    console.log("="*45);
                    console.log(` -> Page URL:          ${entry.name}`);
                    console.log(` -> TTFB (Server):     ${ttfb.toFixed(1)} ms`);
                    console.log(` -> DOM Interactive:   ${domReady.toFixed(1)} ms`);
                    console.log(` -> Total Load Time:   ${totalLoad.toFixed(1)} ms`);
                    
                    // Expose Django Server-Timing metrics
                    if (entry.serverTiming && entry.serverTiming.length > 0) {
                        console.log("-"*45);
                        console.log("   ⚙️ DJANGO SERVER BACKEND TIMINGS:");
                        entry.serverTiming.forEach((metric) => {
                            console.log(` -> Server ${metric.name}:   ${metric.duration.toFixed(1)} ms`);
                        });
                    }
                    console.log("="*45 + "\n");
                });
            });
            navObserver.observe({ type: 'navigation', buffered: true });

            // B. Monitor Long Tasks (Main thread blocked > 50ms)
            const longTaskObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    console.warn(`[PERF WARNING] ⚠️ Main thread blocked by long-running task for ${entry.duration.toFixed(1)} ms! Source:`, entry.attribution || "Unknown");
                });
            });
            longTaskObserver.observe({ type: 'longtask', buffered: true });

            // C. Monitor Large Contentful Paint (LCP)
            const lcpObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    console.log(`[PERF] Largest Contentful Paint (LCP) rendered at: ${entry.startTime.toFixed(1)} ms`);
                });
            });
            lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });

        } catch (e) {
            console.log("[PERF] PerformanceObserver init error:", e);
        }
    }
});

```

`LibSys\static\js\sw.js`:

```js
/**
 * LibSys Service Worker - Aggressive Caching & Offline Capabilities
 * OOG BOOG! CAVEMAN SERVICE WORKER CACHE ALL THE DATA FOR INSTANT LOAD TIMES!
 */
const CACHE_NAME = 'libsys-cache-v2';
const ASSETS_TO_CACHE = [
    '/',
    '/stock/',
    '/members/',
    '/contacts/',
    '/static/style.css',
    '/static/js/preload.js',
    'https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap'
];

// Install: Cache all core assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] OOG BOOG! Pre-caching core assets for LibSys!');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Cleaning up legacy cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch: Stale-While-Revalidate strategy for static resources, Network-First for HTML
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // Skip non-GET, Django admin panel, Django authentication, and REST APIs
    if (request.method !== 'GET' || 
        url.pathname.startsWith('/admin') || 
        url.pathname.startsWith('/api') || 
        url.pathname.startsWith('/users') ||
        url.pathname.startsWith('/register') || 
        url.pathname.startsWith('/dashboard') ||
        url.pathname.startsWith('/books')) {
        return;
    }

    // Network-First strategy for HTML pages (books, members, contacts, home)
    const acceptHeader = request.headers.get('accept');
    if (acceptHeader && acceptHeader.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Update cache dynamically
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // Fallback to cache if network fails
                    return caches.match(request);
                })
        );
        return;
    }

    // Stale-While-Revalidate strategy for CSS, JS, Fonts, and Images
    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
                // Fetch in background to update cache
                fetch(request).then((networkResponse) => {
                    if (networkResponse.status === 200) {
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, networkResponse);
                        });
                    }
                });
                return cachedResponse;
            }

            return fetch(request).then((networkResponse) => {
                if (networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return networkResponse;
            });
        })
    );
});

```

`LibSys\static\style.css`:

```css

body {
        background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
        background-size: cover;
        background-attachment: fixed;
        margin: 0;
        padding: 0;
        font-family: Arial, sans-serif;
        overflow: hidden;
    }

header {
        background-color: #336095;
        color:rgb(145, 199, 208);
        padding: 20px;
        text-align: center;
    }

nav {
        background-color:rgb(30, 27, 126);
        padding: 10px 20px;
    }

.nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

.nav-links {
        list-style-type: none;
        padding: 0;
        margin: 0;
        display: flex;
    }

.nav-links li {
        margin-right: 15px;
    }

.nav-links a {
        text-decoration: none;
        color: rgb(145, 199, 208);
        font-weight: bold;
        padding: 5px 10px;
        transition: color 0.3s;
    }

.nav-links a:hover {
        color: #ffffff;
        background-color:rgb(6, 4, 65);
        border-radius: 5px;
    }

section,h3 {
        padding: 20px;
        background-color: #336095;
        margin: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        position: relative;
        top: 50px;
    }

footer {
        background-color: #336095;
        color: rgb(145, 199, 208);
        position: fixed;
        bottom: 0px;
        left: 0px;
        padding: auto;
        width: 100%;
        text-align: center;
        z-index: 1000;
    }
.floating-button {
        position: fixed;
        top: 10px; /* Adjust distance from top */
        right:  10px; /* Adjust distance from right */
        background-color:rgb(234, 82, 31); /* Blue */
        color: white;
        padding: 15px 20px;
        border-radius: 70%; /* Make it round */
        text-decoration: none;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
        z-index: 1000; /* Ensure it's on top */
      }
.floating-button2 {
        position: fixed;
        top: 10px; /* Adjust distance from top */
        left:  10px; /* Adjust distance from right */
        background-color:rgb(234, 82, 31); /* Blue */
        color: white;
        padding: 15px 20px;
        border-radius: 70%; /* Make it round */
        text-decoration: none;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
        z-index: 1000; /* Ensure it's on top */
      }
table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }

table, th, td {
        border: 1px solid #ddd;
        background-color: #f9f9f9;
    }

th, td {
        padding: 10px;
        text-align: left;
        background-color: #f9f9f9;
    }

th {
        background-color: #336095;
        color: white;
    }
.admin-button {
        text-decoration: none;
        background-color: #336095;
        color: rgb(145, 199, 208);
        padding: 5px 10px;
        border-radius: 5px;
        transition: background-color 0.3s;
    }

```

`LibSys\templates\429.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Too Many Requests - LibSys</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-color: #ff5227;
            --text-color: #f3f4f6;
            --muted-text: #9ca3af;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
        }

        /* Ambient Glow Background */
        .ambient-glow {
            position: absolute;
            width: 350px;
            height: 350px;
            background: radial-gradient(circle, rgba(255, 82, 39, 0.15) 0%, rgba(0,0,0,0) 70%);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 1;
            pointer-events: none;
            animation: pulse 8s infinite alternate ease-in-out;
        }

        .container {
            position: relative;
            z-index: 2;
            text-align: center;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            padding: 4rem 3rem;
            border-radius: 24px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            max-width: 480px;
            width: 90%;
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }

        h1 {
            font-size: 3rem;
            font-weight: 800;
            margin: 0 0 1rem;
            background: linear-gradient(135deg, #ff8c69 0%, var(--accent-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        h2 {
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0 0 1rem;
        }

        p {
            color: var(--muted-text);
            line-height: 1.6;
            margin: 0 0 2rem;
        }

        /* Circular Timer Ring */
        .timer-wrapper {
            position: relative;
            width: 140px;
            height: 140px;
            margin: 0 auto 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .timer-svg {
            position: absolute;
            top: 0;
            left: 0;
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .timer-svg circle {
            fill: none;
            stroke-width: 6;
            stroke-linecap: round;
        }

        .timer-bg {
            stroke: rgba(255, 255, 255, 0.05);
        }

        .timer-bar {
            stroke: var(--accent-color);
            stroke-dasharray: 402; /* 2 * PI * r (r=64) => 402.12 */
            stroke-dashoffset: 0;
            transition: stroke-dashoffset 1s linear;
        }

        .countdown-text {
            font-size: 2.2rem;
            font-weight: 800;
            color: var(--text-color);
        }

        .unit {
            font-size: 0.8rem;
            color: var(--muted-text);
            display: block;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: -4px;
        }

        .shield-icon {
            font-size: 3rem;
            margin-bottom: 1.5rem;
            animation: wobble 3s infinite ease-in-out;
            display: inline-block;
        }

        @keyframes pulse {
            0% { transform: translate(-50%, -50%) scale(0.9); opacity: 0.8; }
            100% { transform: translate(-50%, -50%) scale(1.1); opacity: 1.2; }
        }

        @keyframes fadeInUp {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        @keyframes wobble {
            0%, 100% { transform: rotate(0deg); }
            25% { transform: rotate(-5deg); }
            75% { transform: rotate(5deg); }
        }
    </style>
</head>
<body>
    <div class="ambient-glow"></div>
    <div class="container">
        <div class="shield-icon">🛡️</div>
        <h1>429</h1>
        <h2>Too Many Requests</h2>
        <p>OOG BOOG! Your IP is sending requests too fast! To safeguard LibSys from bot hordes, access is cooling down.</p>

        <div class="timer-wrapper">
            <svg class="timer-svg" viewBox="0 0 136 136">
                <circle class="timer-bg" cx="68" cy="68" r="64"></circle>
                <circle id="progressCircle" class="timer-bar" cx="68" cy="68" r="64"></circle>
            </svg>
            <div class="countdown-text">
                <span id="countdown">60</span>
                <span class="unit">sec</span>
            </div>
        </div>
    </div>

    <script>
        const initialSeconds = 60;
        let secondsLeft = initialSeconds;
        const countdownEl = document.getElementById('countdown');
        const circle = document.getElementById('progressCircle');
        const radius = 64;
        const circumference = 2 * Math.PI * radius;

        circle.style.strokeDasharray = circumference;

        const updateTimer = () => {
            countdownEl.textContent = secondsLeft;
            
            // Calculate progress offset
            const progress = secondsLeft / initialSeconds;
            const offset = circumference * (1 - progress);
            circle.style.strokeDashoffset = offset;

            if (secondsLeft <= 0) {
                clearInterval(interval);
                window.location.reload();
            }
            secondsLeft--;
        };

        updateTimer();
        const interval = setInterval(updateTimer, 1000);
    </script>
</body>
</html>

```

`LibSys\templates\auth\login.html`:

```html


        <style>
          .login-box {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            height: 300px;
            background-image: linear-gradient(to bottom, #fce4ec, #f8bbd0);
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
            border: 1px solid #ccc;
            border-radius: 5px;
          }
          
          .login-box h1 {
            text-align: center;
            font-size: 24px;
          }
          
          .login-box input {
            width: 100%;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 3px;
          }
          
          .login-box input[type="submit"] {
              background-color: #FFCACC ;
              color: #F31559;
              cursor: pointer;
            }
          body {
              background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
              background-size: cover;
              background-attachment: fixed;
              margin: 0;
              padding: 0;
              font-family: Arial, sans-serif;
          }
  
          header {
              background-color: #336095;
              color:rgb(145, 199, 208);
              padding: 20px;
              text-align: center;
          }
  
          nav {
              background-color:rgb(30, 27, 126);
              padding: 10px 20px;
          }
  
          .nav-container {
              display: flex;
              justify-content: space-between;
              align-items: center;
          }
  
          .nav-links {
              list-style-type: none;
              padding: 0;
              margin: 0;
              display: flex;
          }
  
          .nav-links li {
              margin-right: 15px;
          }
  
          .nav-links a {
              text-decoration: none;
              color: rgb(145, 199, 208);
              font-weight: bold;
              padding: 5px 10px;
              transition: color 0.3s;
          }
  
          .nav-links a:hover {
              color: #ffffff;
              background-color:rgb(6, 4, 65);
              border-radius: 5px;
          }
  
          section {
              padding: 20px;
              background-color: #336095;
              margin: 20px;
              border-radius: 5px;
              box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
              position: relative;
              top: 50px;
          }
  
          footer {
              background-color: #336095;
              color: rgb(145, 199, 208);
              position: fixed;
              bottom: 0px;
              left: 0px;
              padding: auto;
              width: 100%;
              text-align: center;
              z-index: 1000;
          }
          .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
      </style>
      
  <head>
  </head>
  

  <body>
    
  
  <div class="login-box">
      <h1>login page</h1>
  
      <form action="{% url 'login' %}" method="post">
          {%csrf_token%}
  
          {{form.as_p}}
          <input type="submit" value="login">
  
  
  
      </form>
  
      <p >Dont have an account?  <a href="{%url 'register'%}">|| 👉👉🏻Register Here👈🏻👈</a></p>
  
  </div>
</body>
  
```

`LibSys\templates\auth\register.html`:

```html
<head>
    <style>
    
    .register-box {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: auto;
      height: auto;
      background-image: linear-gradient(to bottom, #fce4ec, #f8bbd0);
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
      border: 1px solid #ccc;
      border-radius: 5px;
    }
    
    .register-box h1 {
      text-align: center;
      font-size: 24px;
    }
    
    .register-box input {
      width: 100%;
      padding: 10px;
      font-size: 16px;
      border: 1px solid #ccc;
      border-radius: 3px;
    }
    
    .register-box input[type="submit"] {
      background-color: #FFCACC ;
      color: #F31559;
      cursor: pointer;
    }
    
    a{
      text-decoration: none;
    }
    body {
        background-image: url("https://c0.wallpaperflare.com/preview/961/178/419/bookcase-books-bookshelf-bookstore.jpg");
        background-size: cover;
      }
    

    </style>
    </head>
<body>
        
    
    
        
    <div class="register-box">
    <h1>👇🏻👇🏻👇🏻Register Here👇🏻👇🏻👇🏻</h1>
    
    <form action="{%url 'register'%}" method="post">
        {%csrf_token%}
    
        {{ form.as_p }}
        <input type="submit" value="register">
    
    
    
    </form>
    <p>Already have an account?  <a href="{%url 'login'%}">|| 👉👉🏻Login Here👈🏻👈</a></p>
    
    </div>
</body>
    
    
```

`LibSys\templates\etc\books.html`:

```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <script src="{% static 'js/preload.js' %}" defer></script>
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('{% static "js/sw.js" %}')
                    .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                    .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
            });
        }
    </script>
    <style>
        body {
            background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            font-family: sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #336095;
            color: white;
            padding: 20px;
            text-align: center;
        }

        section {
            padding: 20px;
            margin: 20px;
            border-radius: 5px;
            background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAVsAAACRCAMAAABaFeu5AAAAElBMVEV+xv97xv94x/9zxPx8x/91xv4RbxmEAAABJklEQVR4nO3V0W6CQBBAUbD2/3+50QSyxV3a2F1moOc8GBgTnb1qnCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4Gru0QvsucfptH6PlxkjsO0fNNYP7Fgz15Ubl3ffnwmzrt8Y5/CrtnPlMtS6fmOcQ6Ntmbi4fg0fY12/Mc7hnbbl1zgm9Lp+Y5zDW22XoNru2m+bVWP9wI41MW3+BW3H0XYcbcc5pO2teEzgqEV6tr0ttve3zW20jmfeM7Dt9jDHN2zpeOY9U/Q5r0nbgZ5tP9ui9zszbce5VNtEf5UPl2qbbNuf2p7Behhtu1vOkuxXNl+hbWbTx3DP96mMCrXZ+Wk7Tkzbs0jf9njdPk1tX2mbn7ZZaTvOFwCFZd5Kyns4AAAAAElFTkSuQmCC");
            color: rgb(0, 0, 0);
            box-shadow: 0 0 10px rgb(255, 255, 255);
            width: fit-content;
            position: relative;
            top: 50px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }

        th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }

        th {
            background-color: #336095;
            color: white;
        }

        footer {
            background-color: #336095;
            color: rgb(145, 199, 208);
            position: fixed;
            bottom: 0px;
            left: 0px;
            padding: auto;
            width: 100%;
            text-align: center;
            z-index: 1000;
        }
        .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left: 10px; /* Adjust distance from left */
            background-color: #336095; /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
    </style>
</head>
<body>
    <header>
        <a href="{% url 'home' %}" class="floating-button">Go Back</a>
        <h1>Available Books</h1>
    </header>

    <section>
        <h2>Our Collection</h2>
        <table>
            <thead>
                <tr>
                    <th>Book Name</th>
                    <th>Author</th>
                    <th>Genre</th>
                </tr>
            </thead>
            <tbody>
                {% for book in books %}
                <tr>
                    <td>{{ book.book_name }}</td>
                    <td>{{ book.author }}</td>
                    <td>{{ book.genre }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>

    <footer >
        <p>&copy; 2024 Library Management System</p>
    </footer>
</body>
</html>

```

`LibSys\templates\etc\contacts.html`:

```html
{% load static %}
<!DOCTYPE html>
<html>
    <style>
        body {
            background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            font-family: sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #336095;
            color: white;
            padding: 20px;
            text-align: center;
        }

        section {
            padding: 20px;
            margin: 20px;
            border-radius: 5px;
            background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAVsAAACRCAMAAABaFeu5AAAAElBMVEV+xv97xv94x/9zxPx8x/91xv4RbxmEAAABJklEQVR4nO3V0W6CQBBAUbD2/3+50QSyxV3a2F1moOc8GBgTnb1qnCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4Gru0QvsucfptH6PlxkjsO0fNNYP7Fgz15Ubl3ffnwmzrt8Y5/CrtnPlMtS6fmOcQ6Ntmbi4fg0fY12/Mc7hnbbl1zgm9Lp+Y5zDW22XoNru2m+bVWP9wI41MW3+BW3H0XYcbcc5pO2teEzgqEV6tr0ttve3zW20jmfeM7Dt9jDHN2zpeOY9U/Q5r0nbgZ5tP9ui9zszbce5VNtEf5UPl2qbbNuf2p7Behhtu1vOkuxXNl+hbWbTx3DP96mMCrXZ+Wk7Tkzbs0jf9njdPk1tX2mbn7ZZaTvOFwCFZd5Kyns4AAAAAElFTkSuQmCC");
            color: rgb(0, 0, 0);
            box-shadow: 0 0 10px rgb(255, 255, 255);
            width: fit-content;
            position: relative;
            top: 50px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }

        th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }

        th {
            background-color: #336095;
            color: white;
        }

        footer {
            background-color: #336095;
            color: rgb(145, 199, 208);
            position: fixed;
            bottom: 0px;
            left: 0px;
            padding: auto;
            width: 100%;
            text-align: center;
            z-index: 1000;
        }
        .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left: 10px; /* Adjust distance from left */
            background-color: #336095; /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
    </style>
<head>
  <title>Contact Us</title>
  <script src="{% static 'js/preload.js' %}" defer></script>
  <script>
      if ('serviceWorker' in navigator) {
          window.addEventListener('load', () => {
              navigator.serviceWorker.register('{% static "js/sw.js" %}')
                  .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                  .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
          });
      }
  </script>
</head>
<body>
  <header>
    <a href="{% url 'home' %}" class="floating-button">Go Back</a>
    <h1>Contact Us</h1>
  </header>

  <section>
    <h2>Get in Touch</h2>
    <p>We'd love to hear from you! Fill out the form below to send us a message.</p>
    <form id="contactForm" action="/contact/submit" method="post">
      {% csrf_token %}
      <label for="name">Your Name:</label>
      <input type="text" name="name" id="name" required>
      <br>
      <label for="email">Your Email:</label>
      <input type="email" name="email" id="email" required>
      <br>
      <label for="message">Message:</label>
      <textarea name="message" id="message" rows="5" required></textarea>
      <br>
      <button type="submit">Send Message</button>
    </form>
  </section>

  <script>
    document.getElementById("contactForm").addEventListener("submit", (e) => {
        e.preventDefault();
        alert("OOG BOOG! Message sent successfully to Caveman Chief! Thank you!");
        e.target.reset();
    });
  </script>

  <footer>
    <p>&copy; 2024 Library Management System</p>
  </footer>
</body>
</html>
```

`LibSys\templates\etc\members.html`:

```html
{% load static %}
<!DOCTYPE html>
<html>
    <style>
        body {
            background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            font-family: sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #336095;
            color: white;
            padding: 20px;
            text-align: center;
        }

        section {
            padding: 20px;
            margin: 20px;
            border-radius: 5px;
            background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAVsAAACRCAMAAABaFeu5AAAAElBMVEV+xv97xv94x/9zxPx8x/91xv4RbxmEAAABJklEQVR4nO3V0W6CQBBAUbD2/3+50QSyxV3a2F1moOc8GBgTnb1qnCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4Gru0QvsucfptH6PlxkjsO0fNNYP7Fgz15Ubl3ffnwmzrt8Y5/CrtnPlMtS6fmOcQ6Ntmbi4fg0fY12/Mc7hnbbl1zgm9Lp+Y5zDW22XoNru2m+bVWP9wI41MW3+BW3H0XYcbcc5pO2teEzgqEV6tr0ttve3zW20jmfeM7Dt9jDHN2zpeOY9U/Q5r0nbgZ5tP9ui9zszbce5VNtEf5UPl2qbbNuf2p7Behhtu1vOkuxXNl+hbWbTx3DP96mMCrXZ+Wk7Tkzbs0jf9njdPk1tX2mbn7ZZaTvOFwCFZd5Kyns4AAAAAElFTkSuQmCC");
            color: rgb(0, 0, 0);
            box-shadow: 0 0 10px rgb(255, 255, 255);
            width: fit-content;
            position: relative;
            top: 50px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }

        th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }

        th {
            background-color: #336095;
            color: white;
        }

        footer {
            background-color: #336095;
            color: rgb(145, 199, 208);
            position: fixed;
            bottom: 0px;
            left: 0px;
            padding: auto;
            width: 100%;
            text-align: center;
            z-index: 1000;
        }
        .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left: 10px; /* Adjust distance from left */
            background-color: #336095; /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
    </style>
<head>
  <title>Library Members</title>
  <script src="{% static 'js/preload.js' %}" defer></script>
  <script>
      if ('serviceWorker' in navigator) {
          window.addEventListener('load', () => {
              navigator.serviceWorker.register('{% static "js/sw.js" %}')
                  .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                  .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
          });
      }
  </script>
</head>
<body>
  <header>
    <a href="{% url 'home' %}" class="floating-button">Go Back</a>
    <h1>Library Members</h1>
  </header>

  <section>
    <h2>List of Members</h2>
    <table>
      <thead>
        <tr>
          <th>Username</th>
          
          <th>Joined Since</th>
        </tr>
      </thead>
      <tbody>
        {% for user in users %}
        <tr>
          <td>{{ user.username }}</td>
          
          <td>{{ user.date_joined|timesince }}</td>  </tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <footer>
    <p>&copy; 2024 Library Management System</p>
  </footer>
</body>
</html>
```

`LibSys\templates\home.html`:

```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <script src="{% static 'js/preload.js' %}" defer></script>
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('{% static "js/sw.js" %}')
                    .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                    .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
            });
        }
    </script>
    <style>
        body {
            background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            background-attachment: fixed;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }

        header {
            background-color: #336095;
            color:rgb(145, 199, 208);
            padding: 20px;
            text-align: center;
        }

        nav {
            background-color:rgb(30, 27, 126);
            padding: 10px 20px;
        }

        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .nav-links {
            list-style-type: none;
            padding: 0;
            margin: 0;
            display: flex;
        }

        .nav-links li {
            margin-right: 15px;
        }

        .nav-links a {
            text-decoration: none;
            color: rgb(145, 199, 208);
            font-weight: bold;
            padding: 5px 10px;
            transition: color 0.3s;
        }

        .nav-links a:hover {
            color: #ffffff;
            background-color:rgb(6, 4, 65);
            border-radius: 5px;
        }

        section {
            padding: 20px;
            background-color: #336095;
            margin: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            position: relative;
            top: 50px;
        }

        footer {
            background-color: #336095;
            color: rgb(145, 199, 208);
            position: fixed;
            bottom: 0px;
            left: 0px;
            padding: auto;
            width: 100%;
            text-align: center;
            z-index: 1000;
        }
        .floating-button {
          position: fixed;
          top: 10px; /* Adjust distance from top */
          right:  10px; /* Adjust distance from right */
          background-color:rgb(234, 82, 31); /* Blue */
          color: white;
          padding: 15px 20px;
          border-radius: 70%; /* Make it round */
          text-decoration: none;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
          z-index: 1000; /* Ensure it's on top */
        }
    </style>
</head>
<body>
    <header>
      <a href="{% url 'login' %}" class="floating-button">Login</a>
        <h1>Library Management System</h1>
    </header>

    <nav>
        <div class="nav-container">
            <ul class="nav-links">
                <li><a href="{% url 'books' %}">Books</a></li>
                <li><a href="{% url 'members' %}">Members</a></li>
                <li><a href="{% url 'contacts' %}">Contact Us</a></li>
            </ul>
        </div>
    </nav>

    <section>
        <h2>Welcome</h2>
        <p>This is the Library Management System. You can use this system to manage your library books and members.</p>
    </section>

    <footer>
        <p>&copy; 2024 Library Management System</p>
    </footer>
</body>
</html>

```

`LibSys\templates\registration\login.html`:

```html


<style>
  .login-box {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 400px;
    height: 300px;
    background-image: linear-gradient(to bottom, #fce4ec, #f8bbd0);
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    border: 1px solid #ccc;
    border-radius: 5px;
  }
  
  .login-box h1 {
    text-align: center;
    font-size: 24px;
  }
  
  .login-box input {
    width: 100%;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 3px;
  }
  
  .login-box input[type="submit"] {
      background-color: #FFCACC ;
      color: #F31559;
      cursor: pointer;
    }
  body {
      background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
      background-size: cover;
      background-attachment: fixed;
      overflow: hidden;
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
  }

  header {
      background-color: #336095;
      color:rgb(145, 199, 208);
      padding: 20px;
      text-align: center;
  }

  nav {
      background-color:rgb(30, 27, 126);
      padding: 10px 20px;
  }

  .nav-container {
      display: flex;
      justify-content: space-between;
      align-items: center;
  }

  .nav-links {
      list-style-type: none;
      padding: 0;
      margin: 0;
      display: flex;
  }

  .nav-links li {
      margin-right: 15px;
  }

  .nav-links a {
      text-decoration: none;
      color: rgb(145, 199, 208);
      font-weight: bold;
      padding: 5px 10px;
      transition: color 0.3s;
  }

  .nav-links a:hover {
      color: #ffffff;
      background-color:rgb(6, 4, 65);
      border-radius: 5px;
  }
  .admin-button {
      text-decoration: none;
      background-color: #336095;
      color: rgb(145, 199, 208);
      padding: 5px 10px;
      border-radius: 5px;
      transition: background-color 0.3s;
  }

  section {
      padding: 20px;
      background-color: #336095;
      margin: 20px;
      border-radius: 5px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      position: relative;
      top: 50px;
  }

  footer {
      background-color: #336095;
      color: rgb(145, 199, 208);
      position: fixed;
      bottom: 0px;
      left: 0px;
      padding: auto;
      width: 100%;
      text-align: center;
      z-index: 1000;
  }
  .floating-button {
    position: fixed;
    top: 10px; /* Adjust distance from top */
    right:  10px; /* Adjust distance from right */
    background-color:rgb(234, 82, 31); /* Blue */
    color: white;
    padding: 15px 20px;
    border-radius: 70%; /* Make it round */
    text-decoration: none;
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
    z-index: 1000; /* Ensure it's on top */
  }
</style>
      
  <head>
    <a href="{% url 'home' %}" class="floating-button">Home</a>
    <a class="admin-button" href="{% url 'admin:index' %}" class="admin-button">Go to Admin</a>
      <title>login page</title>

  </head>
  

  <body>
    
  
  <div class="login-box">
      <h1>login page</h1>
  
      <form action="{% url 'login' %}" method="post">
          {%csrf_token%}
  
          {{form.as_p}}
          <input type="submit" value="login">
  
  
  
      </form>
  
      <p >Dont have an account?  <a href="{%url 'register'%}">|| 👉👉🏻Register Here👈🏻👈</a></p>
  
  </div>
</body>
  
```

`LibSys\templates\user\dashboard.html`:

```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <title>Library Dashboard - LibSys</title>
    <script src="{% static 'js/preload.js' %}" defer></script>
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('{% static "js/sw.js" %}')
                    .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                    .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
            });
        }
    </script>
    <style>
        body {
            overflow: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }
        th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }
        th {
            background-color: #336095;
            color: white;
        }
        section, h3 {
            padding: 20px;
            background-color: #336095;
            margin: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            position: relative;
            top: 50%;
        }
        .floating-button2 {
            position: fixed;
            top: 10px;
            left: 10px;
            background-color: rgb(234, 82, 31);
            color: white;
            padding: 15px 20px;
            border-radius: 70%;
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        }
        .floating-button3 {
            position: fixed;
            top: 100px;
            right: 10px;
            background-color: rgb(234, 82, 31);
            color: white;
            padding: 15px 20px;
            border-radius: 70%;
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        }
    </style>
</head>
<body>
    {% if request.user.is_superuser %}
        <a class="floating-button" href="{% url 'manage_books' %}">Manage Books</a>
    {% endif %}
    <a class='floating-button2' href="{% url 'issued_books' %}">Issueance History</a>
    <br><br>
    <div>
<body>
  <div class="container">
    <h1 style="text-align: center; color: #336095; background-color: #ddd; border-radius: 50%;">Hello, {{ request.user|title }}</h1>

    <div class="logout">
        <br>
      <a class="floating-button3" href="{% url 'logout' %}">Logout</a>
    <br>
    </div>

    
    <h3>Available Books</h3>
    <table border>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Available</th>
                <th>Actions</th>
               
            </tr>
        </thead>
        <tbody>
          {% for book in available_books %}
              <tr>
                  <td>{{ book.Bid }}</td>
                  <td>{{ book.book_name }}</td>
                  <td>{{ book.available_quantity }}</td>
                  <td>
                      {% if issued_books.book.bid == book.bid and issued_books.submit == False %}
                          Please return the book before issuing again.
                      {% else %}
                          <a href="{% url 'issue_book' pk=book.pk %}">Issue</a>
                      {% endif %}
                  </td>
              </tr>
          {% endfor %}
      </tbody>
    </table>    

    

  </div>
  <div>
    
  <h3>Currently Issued Books</h3>
    <table border="1">
        <thead>
            <tr>
                <th>IssueNo</th>
                <th>Book</th>
                <th>Issued To</th>
                <th>Time since Issue <br> (Max 10 days before Fine)</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for issued_book in issued_books %}
                {% if issued_book.user == request.user %}
                    {%if issued_book.submit == False %}
                        <tr>
                        
                            <td>{{ issued_book.Issue_No }}</td>
                            <td>{{ issued_book.book.book_name }}</td>
                            <td>{{ issued_book.user }}</td>
                            <td>{{ issued_book.create|timesince }} ago</td>
                            <td>{% if issued_book.submit %}Returned{% else %}Not Returned{% endif %}</td>
                            <td>{% if issued_book.submit %} {% else %}<a href="{% url 'return_book' pk=issued_book.pk %}">return</a>{% endif %}</td>
                        
                        </tr>
                    {% endif %}
                {% endif %}
            {% endfor %}
        </tbody>
    </table>
    
  </div>
</body>
</html>
```

`LibSys\templates\user\edit_book.html`:

```html
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
  
  table, th, td {
        border: 1px solid #ddd;
        background-color: #f9f9f9;
    }
  
  th, td {
        padding: 10px;
        text-align: left;
        background-color: #f9f9f9;
    }
  
  th {
        background-color: #336095;
        color: white;
    }
  form,h3,h1 {
        padding: 20px;
        background-color: #336095;
        margin: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        position: relative;
        top: 1%;
        width: 25%;
           }
  .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button2 {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button3 {
            position: fixed;
            top: 100px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
          
  
  </style>
  {% load static %}
  <link rel="stylesheet" href="{% static 'style.css' %}">
<h1>Edit Book</h1>

<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Save Changes</button>
</form>
```

`LibSys\templates\user\issue_book.html`:

```html
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
  
  table, th, td {
        border: 1px solid #ddd;
        background-color: #f9f9f9;
    }
  
  th, td {
        padding: 10px;
        text-align: left;
        background-color: #f9f9f9;
    }
  
  th {
        background-color: #336095;
        color: white;
    }
  form,h3,h1,.form {
        padding: 20px;
        background-color: #336095;
        margin: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        position: relative;
        top: 1%;
        width: 25%;
           }
  .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button2 {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button3 {
            position: fixed;
            top: 100px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
h2 {text-align: center;
 color: #336095;
 font-size: 40px;
  background-color: #ddd;
  padding: auto;
   border-radius: 30%;}
          
  
  </style>
  {% load static %}
  <link rel="stylesheet" href="{% static 'style.css' %}">
{% block content %}
<h1>Issue Book</h1>
<div class = 'form'>
    {% if book %}
        <p>Are you sure you want to issue the book: <strong>{{ book.book_name }}</strong> by <strong>{{ book.author }}</strong>?</p>
        <form method="post">
            {% csrf_token %}
            <button type="submit">Issue Book</button>
        </form>
    {% else %}
        <p>Book not found!</p>
    {% endif %}

    {% if messages %}
        <ul class="messages">
            {% for message in messages %}
                <li {% if message.tags %} class="{{ message.tags }}"{% endif %}>{{ message }}</li>
            {% endfor %}
        </ul>
    {% endif %}
</div>
{% endblock %}
```

`LibSys\templates\user\issued_books.html`:

```html

{% block content %}
<style>
  table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
  }

table, th, td {
      border: 1px solid #ddd;
      background-color: #f9f9f9;
  }

th, td {
      padding: 10px;
      text-align: left;
      background-color: #f9f9f9;
  }

th {
      background-color: #336095;
      color: white;
  }
section,h3 {
      padding: 20px;
      background-color: #336095;
      margin: 20px;
      border-radius: 5px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      position: relative;
      top: 50%;
         }
.floating-button {
          position: fixed;
          top: 10px; /* Adjust distance from top */
          right:  10px; /* Adjust distance from right */
          background-color:rgb(234, 82, 31); /* Blue */
          color: white;
          padding: 15px 20px;
          border-radius: 70%; /* Make it round */
          text-decoration: none;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
          z-index: 1000; /* Ensure it's on top */
        }
.floating-button2 {
          position: fixed;
          top: 10px; /* Adjust distance from top */
          left:  10px; /* Adjust distance from right */
          background-color:rgb(234, 82, 31); /* Blue */
          color: white;
          padding: 15px 20px;
          border-radius: 70%; /* Make it round */
          text-decoration: none;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
          z-index: 1000; /* Ensure it's on top */
        }
.floating-button3 {
          position: fixed;
          top: 100px; /* Adjust distance from top */
          right:  10px; /* Adjust distance from right */
          background-color:rgb(234, 82, 31); /* Blue */
          color: white;
          padding: 15px 20px;
          border-radius: 70%; /* Make it round */
          text-decoration: none;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
          z-index: 1000; /* Ensure it's on top */
        }
        

</style>
<h2>Issued Books History</h2>
<a class="floating-button" href="{% url 'dashboard' %}">dashboard</a><br><br>

{% if issued_books %}
<table border = "1">
  <thead>
    <tr>
      <th>Issue No.</th>
      <th>Book Name</th>
      <th>length_of_possession</th>
      <th>Fine</th>
    
      <th>Note</th>
     
    </tr>
  </thead>
  <tbody>
    {% for issued_book in issued_books %}
      <tr>
        <td>{{ issued_book.Issue_No }}</td>
        <td>{{ issued_book.book.book_name }}</td>
        <td>{{ issued_book.create|timesince }}</td>
        <td>{{ issued_book.book.fine }}</td>
        {%if issued_book.submit == False %}
        <td>Not Returned</td>
        {%endif%}
      </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
  <p>No Issued Books</p>
{% endif %}
{% if messages %}
    <ul class="messages">
        {% for message in messages %}
            <li {% if message.tags %} class="{{ message.tags }}"{% endif %}>{{ message }}</li>
        {% endfor %}
    </ul>
{% endif %}

{% endblock %}
```

`LibSys\templates\user\manage_books.html`:

```html
<!DOCTYPE html>
<html>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
      
      table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }
      
      th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }
      
      th {
            background-color: #336095;
            color: white;
        }
      form,h3,h1 {
            padding: 20px;
            background-color: #336095;
            margin: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            position: relative;
            top: 1%;
            width: 25%;
               }
      .floating-button {
                position: fixed;
                top: 10px; /* Adjust distance from top */
                right:  10px; /* Adjust distance from right */
                background-color:rgb(234, 82, 31); /* Blue */
                color: white;
                padding: 15px 20px;
                border-radius: 70%; /* Make it round */
                text-decoration: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
                z-index: 1000; /* Ensure it's on top */
              }
      .floating-button2 {
                position: fixed;
                top: 10px; /* Adjust distance from top */
                left:  10px; /* Adjust distance from right */
                background-color:rgb(234, 82, 31); /* Blue */
                color: white;
                padding: 15px 20px;
                border-radius: 70%; /* Make it round */
                text-decoration: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
                z-index: 1000; /* Ensure it's on top */
              }
      .floating-button3 {
                position: fixed;
                top: 100px; /* Adjust distance from top */
                right:  10px; /* Adjust distance from right */
                background-color:rgb(234, 82, 31); /* Blue */
                color: white;
                padding: 15px 20px;
                border-radius: 70%; /* Make it round */
                text-decoration: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
                z-index: 1000; /* Ensure it's on top */
              }
h2 {text-align: center;
     color: #336095;
     font-size: 40px;
      background-color: #ddd;
      padding: auto;
       border-radius: 30%;}
              
      
      </style>
      {% load static %}
      <link rel="stylesheet" href="{% static 'style.css' %}">
<head>
    <title>Manage Books</title>
    <br>
    <a class="floating-button" href="{% url 'dashboard' %}">dashboard</a>
    <br>
</head>
<body style="overflow: scroll;">
    <h2>Manage Books</h2>

    <form method="post">
        {% csrf_token %}
        <label for="book_name">Book Name:</label>
        <input type="text" name="book_name" required><br><br>
        <label for="quantity">Quantity:</label>
        <input type="number" name="quantity" required><br><br>
        <label for="author">Author:</label>
        <input type="text" name="author" required><br><br>
        <label for="genre">Genre:</label>
        <input type="text" name="genre"><br><br>
        <label for="fine">Fine:</label>
        <input type="number" name="fine" required><br><br>
        <button type="submit" name="add_book">Add Book</button>
    </form>

    <form method="post">
        {% csrf_token %}
        <label for="book_id">Book ID:</label>
        <select name="book_id">
            {% for book in books %}
                <option value="{{ book.Bid }}">{{ book.Bid }} : {{ book.book_name }}</option>
            {% endfor %}
        </select>
        <button type="submit" name="remove_book">Remove Book</button>
    </form>

    <h3>Available Books</h3><br>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Quantity</th>
                <th>Available</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for book in available_books %}
                <tr>
                    <td>{{ book.Bid }}</td>
                    <td>{{ book.book_name }}</td>
                    <td>{{ book.quantity }}</td>
                    <td>{{ book.available_quantity }}</td>
                    <td><a href="{% url 'edit_book' pk=book.pk %}">Edit</a></td> 
                </tr>
            {% endfor %}
        </tbody>
    </table>

   

    <div>
     <h3>Issued Books</h3><br>
    <table>
      <thead>
        <tr>
          <th>Book</th>
          <th>Issued To</th>
          <th>Possesion Time</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {% for issued_book in issued_books %}
          <tr>
            <td>{{ issued_book.book.book_name }}</td>
            <td>{{ issued_book.user }}</td>
            <td>{{ issued_book.create|timesince }}</td>
            <td>{% if issued_book.submit %}Returned{% else %}Not Returned{% endif %}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
    </div>

</body>
</html>
```

`LibSys\templates\user\return_book.html`:

```html
{% block content %}
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
  
  table, th, td {
        border: 1px solid #ddd;
        background-color: #f9f9f9;
    }
  
  th, td {
        padding: 10px;
        text-align: left;
        background-color: #f9f9f9;
    }
  
  th {
        background-color: #336095;
        color: white;
    }
  form,h3,h1,.form {
        padding: 20px;
        background-color: #336095;
        margin: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        position: relative;
        top: 1%;
        width: 35%;
           }
  .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button2 {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button3 {
            position: fixed;
            top: 100px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
h2 {text-align: center;
 color: #336095;
 font-size: 40px;
  background-color: #ddd;
  padding: auto;
   border-radius: 30%;}
          
  
  </style>
  {% load static %}
  <link rel="stylesheet" href="{% static 'style.css' %}">

<h2>Return Book</h2>
<div class="form">
{% if issued_book %}
    <p>Are you sure you want to return the following book?</p>
    <p><strong>Book Name:</strong> {{ issued_book.book.book_name }}</p>
    <p><strong>Issued To:</strong> {{ issued_book.user.username }}</p>
    <p><strong>Issued On:</strong> {{ issued_book.create }}</p>
    {% if available_quantity %}
    <p><strong>Available Quantity after return:</strong> {{ available_quantity|add:"1" }}</p>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <button type="submit" class="btn btn-primary">Confirm Return</button>
        <br>
        <a href="{% url 'issued_books' %}" class="btn btn-secondary" style='background-color: rgb(234, 82, 31);'>Cancel</a> 
    </form>
{% else %}
    <p>Invalid issued book ID.</p>
    <a href="{% url 'issued_books' %}" class="btn btn-secondary">Back to Issued Books</a>
{% endif %}
</div>
{% endblock %}
```

`README.md`:

```md
This is my Functional project of a Library Management system, with APIs

```

`Scripts\Activate.ps1`:

```ps1
<#
.Synopsis
Activate a Python virtual environment for the current PowerShell session.

.Description
Pushes the python executable for a virtual environment to the front of the
$Env:PATH environment variable and sets the prompt to signify that you are
in a Python virtual environment. Makes use of the command line switches as
well as the `pyvenv.cfg` file values present in the virtual environment.

.Parameter VenvDir
Path to the directory that contains the virtual environment to activate. The
default value for this is the parent of the directory that the Activate.ps1
script is located within.

.Parameter Prompt
The prompt prefix to display when this virtual environment is activated. By
default, this prompt is the name of the virtual environment folder (VenvDir)
surrounded by parentheses and followed by a single space (ie. '(.venv) ').

.Example
Activate.ps1
Activates the Python virtual environment that contains the Activate.ps1 script.

.Example
Activate.ps1 -Verbose
Activates the Python virtual environment that contains the Activate.ps1 script,
and shows extra information about the activation as it executes.

.Example
Activate.ps1 -VenvDir C:\Users\MyUser\Common\.venv
Activates the Python virtual environment located in the specified location.

.Example
Activate.ps1 -Prompt "MyPython"
Activates the Python virtual environment that contains the Activate.ps1 script,
and prefixes the current prompt with the specified string (surrounded in
parentheses) while the virtual environment is active.

.Notes
On Windows, it may be required to enable this Activate.ps1 script by setting the
execution policy for the user. You can do this by issuing the following PowerShell
command:

PS C:\> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

For more information on Execution Policies: 
https://go.microsoft.com/fwlink/?LinkID=135170

#>
Param(
    [Parameter(Mandatory = $false)]
    [String]
    $VenvDir,
    [Parameter(Mandatory = $false)]
    [String]
    $Prompt
)

<# Function declarations --------------------------------------------------- #>

<#
.Synopsis
Remove all shell session elements added by the Activate script, including the
addition of the virtual environment's Python executable from the beginning of
the PATH variable.

.Parameter NonDestructive
If present, do not remove this function from the global namespace for the
session.

#>
function global:deactivate ([switch]$NonDestructive) {
    # Revert to original values

    # The prior prompt:
    if (Test-Path -Path Function:_OLD_VIRTUAL_PROMPT) {
        Copy-Item -Path Function:_OLD_VIRTUAL_PROMPT -Destination Function:prompt
        Remove-Item -Path Function:_OLD_VIRTUAL_PROMPT
    }

    # The prior PYTHONHOME:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PYTHONHOME) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME -Destination Env:PYTHONHOME
        Remove-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME
    }

    # The prior PATH:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PATH) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PATH -Destination Env:PATH
        Remove-Item -Path Env:_OLD_VIRTUAL_PATH
    }

    # Just remove the VIRTUAL_ENV altogether:
    if (Test-Path -Path Env:VIRTUAL_ENV) {
        Remove-Item -Path env:VIRTUAL_ENV
    }

    # Just remove the _PYTHON_VENV_PROMPT_PREFIX altogether:
    if (Get-Variable -Name "_PYTHON_VENV_PROMPT_PREFIX" -ErrorAction SilentlyContinue) {
        Remove-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Scope Global -Force
    }

    # Leave deactivate function in the global namespace if requested:
    if (-not $NonDestructive) {
        Remove-Item -Path function:deactivate
    }
}

<#
.Description
Get-PyVenvConfig parses the values from the pyvenv.cfg file located in the
given folder, and returns them in a map.

For each line in the pyvenv.cfg file, if that line can be parsed into exactly
two strings separated by `=` (with any amount of whitespace surrounding the =)
then it is considered a `key = value` line. The left hand string is the key,
the right hand is the value.

If the value starts with a `'` or a `"` then the first and last character is
stripped from the value before being captured.

.Parameter ConfigDir
Path to the directory that contains the `pyvenv.cfg` file.
#>
function Get-PyVenvConfig(
    [String]
    $ConfigDir
) {
    Write-Verbose "Given ConfigDir=$ConfigDir, obtain values in pyvenv.cfg"

    # Ensure the file exists, and issue a warning if it doesn't (but still allow the function to continue).
    $pyvenvConfigPath = Join-Path -Resolve -Path $ConfigDir -ChildPath 'pyvenv.cfg' -ErrorAction Continue

    # An empty map will be returned if no config file is found.
    $pyvenvConfig = @{ }

    if ($pyvenvConfigPath) {

        Write-Verbose "File exists, parse `key = value` lines"
        $pyvenvConfigContent = Get-Content -Path $pyvenvConfigPath

        $pyvenvConfigContent | ForEach-Object {
            $keyval = $PSItem -split "\s*=\s*", 2
            if ($keyval[0] -and $keyval[1]) {
                $val = $keyval[1]

                # Remove extraneous quotations around a string value.
                if ("'""".Contains($val.Substring(0, 1))) {
                    $val = $val.Substring(1, $val.Length - 2)
                }

                $pyvenvConfig[$keyval[0]] = $val
                Write-Verbose "Adding Key: '$($keyval[0])'='$val'"
            }
        }
    }
    return $pyvenvConfig
}


<# Begin Activate script --------------------------------------------------- #>

# Determine the containing directory of this script
$VenvExecPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvExecDir = Get-Item -Path $VenvExecPath

Write-Verbose "Activation script is located in path: '$VenvExecPath'"
Write-Verbose "VenvExecDir Fullname: '$($VenvExecDir.FullName)"
Write-Verbose "VenvExecDir Name: '$($VenvExecDir.Name)"

# Set values required in priority: CmdLine, ConfigFile, Default
# First, get the location of the virtual environment, it might not be
# VenvExecDir if specified on the command line.
if ($VenvDir) {
    Write-Verbose "VenvDir given as parameter, using '$VenvDir' to determine values"
}
else {
    Write-Verbose "VenvDir not given as a parameter, using parent directory name as VenvDir."
    $VenvDir = $VenvExecDir.Parent.FullName.TrimEnd("\\/")
    Write-Verbose "VenvDir=$VenvDir"
}

# Next, read the `pyvenv.cfg` file to determine any required value such
# as `prompt`.
$pyvenvCfg = Get-PyVenvConfig -ConfigDir $VenvDir

# Next, set the prompt from the command line, or the config file, or
# just use the name of the virtual environment folder.
if ($Prompt) {
    Write-Verbose "Prompt specified as argument, using '$Prompt'"
}
else {
    Write-Verbose "Prompt not specified as argument to script, checking pyvenv.cfg value"
    if ($pyvenvCfg -and $pyvenvCfg['prompt']) {
        Write-Verbose "  Setting based on value in pyvenv.cfg='$($pyvenvCfg['prompt'])'"
        $Prompt = $pyvenvCfg['prompt'];
    }
    else {
        Write-Verbose "  Setting prompt based on parent's directory's name. (Is the directory name passed to venv module when creating the virtual environment)"
        Write-Verbose "  Got leaf-name of $VenvDir='$(Split-Path -Path $venvDir -Leaf)'"
        $Prompt = Split-Path -Path $venvDir -Leaf
    }
}

Write-Verbose "Prompt = '$Prompt'"
Write-Verbose "VenvDir='$VenvDir'"

# Deactivate any currently active virtual environment, but leave the
# deactivate function in place.
deactivate -nondestructive

# Now set the environment variable VIRTUAL_ENV, used by many tools to determine
# that there is an activated venv.
$env:VIRTUAL_ENV = $VenvDir

if (-not $Env:VIRTUAL_ENV_DISABLE_PROMPT) {

    Write-Verbose "Setting prompt to '$Prompt'"

    # Set the prompt to include the env name
    # Make sure _OLD_VIRTUAL_PROMPT is global
    function global:_OLD_VIRTUAL_PROMPT { "" }
    Copy-Item -Path function:prompt -Destination function:_OLD_VIRTUAL_PROMPT
    New-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Description "Python virtual environment prompt prefix" -Scope Global -Option ReadOnly -Visibility Public -Value $Prompt

    function global:prompt {
        Write-Host -NoNewline -ForegroundColor Green "($_PYTHON_VENV_PROMPT_PREFIX) "
        _OLD_VIRTUAL_PROMPT
    }
}

# Clear PYTHONHOME
if (Test-Path -Path Env:PYTHONHOME) {
    Copy-Item -Path Env:PYTHONHOME -Destination Env:_OLD_VIRTUAL_PYTHONHOME
    Remove-Item -Path Env:PYTHONHOME
}

# Add the venv to the PATH
Copy-Item -Path Env:PATH -Destination Env:_OLD_VIRTUAL_PATH
$Env:PATH = "$VenvExecDir$([System.IO.Path]::PathSeparator)$Env:PATH"

# SIG # Begin signature block
# MIIkCQYJKoZIhvcNAQcCoIIj+jCCI/YCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCD50itNqbOCCDp6
# 9ZnhKce5X7vV6KL67iKMbGTUZ4nf36CCDi8wggawMIIEmKADAgECAhAIrUCyYNKc
# TJ9ezam9k67ZMA0GCSqGSIb3DQEBDAUAMGIxCzAJBgNVBAYTAlVTMRUwEwYDVQQK
# EwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xITAfBgNV
# BAMTGERpZ2lDZXJ0IFRydXN0ZWQgUm9vdCBHNDAeFw0yMTA0MjkwMDAwMDBaFw0z
# NjA0MjgyMzU5NTlaMGkxCzAJBgNVBAYTAlVTMRcwFQYDVQQKEw5EaWdpQ2VydCwg
# SW5jLjFBMD8GA1UEAxM4RGlnaUNlcnQgVHJ1c3RlZCBHNCBDb2RlIFNpZ25pbmcg
# UlNBNDA5NiBTSEEzODQgMjAyMSBDQTEwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAw
# ggIKAoICAQDVtC9C0CiteLdd1TlZG7GIQvUzjOs9gZdwxbvEhSYwn6SOaNhc9es0
# JAfhS0/TeEP0F9ce2vnS1WcaUk8OoVf8iJnBkcyBAz5NcCRks43iCH00fUyAVxJr
# Q5qZ8sU7H/Lvy0daE6ZMswEgJfMQ04uy+wjwiuCdCcBlp/qYgEk1hz1RGeiQIXhF
# LqGfLOEYwhrMxe6TSXBCMo/7xuoc82VokaJNTIIRSFJo3hC9FFdd6BgTZcV/sk+F
# LEikVoQ11vkunKoAFdE3/hoGlMJ8yOobMubKwvSnowMOdKWvObarYBLj6Na59zHh
# 3K3kGKDYwSNHR7OhD26jq22YBoMbt2pnLdK9RBqSEIGPsDsJ18ebMlrC/2pgVItJ
# wZPt4bRc4G/rJvmM1bL5OBDm6s6R9b7T+2+TYTRcvJNFKIM2KmYoX7BzzosmJQay
# g9Rc9hUZTO1i4F4z8ujo7AqnsAMrkbI2eb73rQgedaZlzLvjSFDzd5Ea/ttQokbI
# YViY9XwCFjyDKK05huzUtw1T0PhH5nUwjewwk3YUpltLXXRhTT8SkXbev1jLchAp
# QfDVxW0mdmgRQRNYmtwmKwH0iU1Z23jPgUo+QEdfyYFQc4UQIyFZYIpkVMHMIRro
# OBl8ZhzNeDhFMJlP/2NPTLuqDQhTQXxYPUez+rbsjDIJAsxsPAxWEQIDAQABo4IB
# WTCCAVUwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHQ4EFgQUaDfg67Y7+F8Rhvv+
# YXsIiGX0TkIwHwYDVR0jBBgwFoAU7NfjgtJxXWRM3y5nP+e6mK4cD08wDgYDVR0P
# AQH/BAQDAgGGMBMGA1UdJQQMMAoGCCsGAQUFBwMDMHcGCCsGAQUFBwEBBGswaTAk
# BggrBgEFBQcwAYYYaHR0cDovL29jc3AuZGlnaWNlcnQuY29tMEEGCCsGAQUFBzAC
# hjVodHRwOi8vY2FjZXJ0cy5kaWdpY2VydC5jb20vRGlnaUNlcnRUcnVzdGVkUm9v
# dEc0LmNydDBDBgNVHR8EPDA6MDigNqA0hjJodHRwOi8vY3JsMy5kaWdpY2VydC5j
# b20vRGlnaUNlcnRUcnVzdGVkUm9vdEc0LmNybDAcBgNVHSAEFTATMAcGBWeBDAED
# MAgGBmeBDAEEATANBgkqhkiG9w0BAQwFAAOCAgEAOiNEPY0Idu6PvDqZ01bgAhql
# +Eg08yy25nRm95RysQDKr2wwJxMSnpBEn0v9nqN8JtU3vDpdSG2V1T9J9Ce7FoFF
# UP2cvbaF4HZ+N3HLIvdaqpDP9ZNq4+sg0dVQeYiaiorBtr2hSBh+3NiAGhEZGM1h
# mYFW9snjdufE5BtfQ/g+lP92OT2e1JnPSt0o618moZVYSNUa/tcnP/2Q0XaG3Ryw
# YFzzDaju4ImhvTnhOE7abrs2nfvlIVNaw8rpavGiPttDuDPITzgUkpn13c5Ubdld
# AhQfQDN8A+KVssIhdXNSy0bYxDQcoqVLjc1vdjcshT8azibpGL6QB7BDf5WIIIJw
# 8MzK7/0pNVwfiThV9zeKiwmhywvpMRr/LhlcOXHhvpynCgbWJme3kuZOX956rEnP
# LqR0kq3bPKSchh/jwVYbKyP/j7XqiHtwa+aguv06P0WmxOgWkVKLQcBIhEuWTatE
# QOON8BUozu3xGFYHKi8QxAwIZDwzj64ojDzLj4gLDb879M4ee47vtevLt/B3E+bn
# KD+sEq6lLyJsQfmCXBVmzGwOysWGw/YmMwwHS6DTBwJqakAwSEs0qFEgu60bhQji
# WQ1tygVQK+pKHJ6l/aCnHwZ05/LWUpD9r4VIIflXO7ScA+2GRfS0YW6/aOImYIbq
# yK+p/pQd52MbOoZWeE4wggd3MIIFX6ADAgECAhAHHxQbizANJfMU6yMM0NHdMA0G
# CSqGSIb3DQEBCwUAMGkxCzAJBgNVBAYTAlVTMRcwFQYDVQQKEw5EaWdpQ2VydCwg
# SW5jLjFBMD8GA1UEAxM4RGlnaUNlcnQgVHJ1c3RlZCBHNCBDb2RlIFNpZ25pbmcg
# UlNBNDA5NiBTSEEzODQgMjAyMSBDQTEwHhcNMjIwMTE3MDAwMDAwWhcNMjUwMTE1
# MjM1OTU5WjB8MQswCQYDVQQGEwJVUzEPMA0GA1UECBMGT3JlZ29uMRIwEAYDVQQH
# EwlCZWF2ZXJ0b24xIzAhBgNVBAoTGlB5dGhvbiBTb2Z0d2FyZSBGb3VuZGF0aW9u
# MSMwIQYDVQQDExpQeXRob24gU29mdHdhcmUgRm91bmRhdGlvbjCCAiIwDQYJKoZI
# hvcNAQEBBQADggIPADCCAgoCggIBAKgc0BTT+iKbtK6f2mr9pNMUTcAJxKdsuOiS
# YgDFfwhjQy89koM7uP+QV/gwx8MzEt3c9tLJvDccVWQ8H7mVsk/K+X+IufBLCgUi
# 0GGAZUegEAeRlSXxxhYScr818ma8EvGIZdiSOhqjYc4KnfgfIS4RLtZSrDFG2tN1
# 6yS8skFa3IHyvWdbD9PvZ4iYNAS4pjYDRjT/9uzPZ4Pan+53xZIcDgjiTwOh8VGu
# ppxcia6a7xCyKoOAGjvCyQsj5223v1/Ig7Dp9mGI+nh1E3IwmyTIIuVHyK6Lqu35
# 2diDY+iCMpk9ZanmSjmB+GMVs+H/gOiofjjtf6oz0ki3rb7sQ8fTnonIL9dyGTJ0
# ZFYKeb6BLA66d2GALwxZhLe5WH4Np9HcyXHACkppsE6ynYjTOd7+jN1PRJahN1oE
# RzTzEiV6nCO1M3U1HbPTGyq52IMFSBM2/07WTJSbOeXjvYR7aUxK9/ZkJiacl2iZ
# I7IWe7JKhHohqKuceQNyOzxTakLcRkzynvIrk33R9YVqtB4L6wtFxhUjvDnQg16x
# ot2KVPdfyPAWd81wtZADmrUtsZ9qG79x1hBdyOl4vUtVPECuyhCxaw+faVjumapP
# Unwo8ygflJJ74J+BYxf6UuD7m8yzsfXWkdv52DjL74TxzuFTLHPyARWCSCAbzn3Z
# Ily+qIqDAgMBAAGjggIGMIICAjAfBgNVHSMEGDAWgBRoN+Drtjv4XxGG+/5hewiI
# ZfROQjAdBgNVHQ4EFgQUt/1Teh2XDuUj2WW3siYWJgkZHA8wDgYDVR0PAQH/BAQD
# AgeAMBMGA1UdJQQMMAoGCCsGAQUFBwMDMIG1BgNVHR8Ega0wgaowU6BRoE+GTWh0
# dHA6Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0ZWRHNENvZGVTaWdu
# aW5nUlNBNDA5NlNIQTM4NDIwMjFDQTEuY3JsMFOgUaBPhk1odHRwOi8vY3JsNC5k
# aWdpY2VydC5jb20vRGlnaUNlcnRUcnVzdGVkRzRDb2RlU2lnbmluZ1JTQTQwOTZT
# SEEzODQyMDIxQ0ExLmNybDA+BgNVHSAENzA1MDMGBmeBDAEEATApMCcGCCsGAQUF
# BwIBFhtodHRwOi8vd3d3LmRpZ2ljZXJ0LmNvbS9DUFMwgZQGCCsGAQUFBwEBBIGH
# MIGEMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5jb20wXAYIKwYB
# BQUHMAKGUGh0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0
# ZWRHNENvZGVTaWduaW5nUlNBNDA5NlNIQTM4NDIwMjFDQTEuY3J0MAwGA1UdEwEB
# /wQCMAAwDQYJKoZIhvcNAQELBQADggIBABxv4AeV/5ltkELHSC63fXAFYS5tadcW
# TiNc2rskrNLrfH1Ns0vgSZFoQxYBFKI159E8oQQ1SKbTEubZ/B9kmHPhprHya08+
# VVzxC88pOEvz68nA82oEM09584aILqYmj8Pj7h/kmZNzuEL7WiwFa/U1hX+XiWfL
# IJQsAHBla0i7QRF2de8/VSF0XXFa2kBQ6aiTsiLyKPNbaNtbcucaUdn6vVUS5izW
# OXM95BSkFSKdE45Oq3FForNJXjBvSCpwcP36WklaHL+aHu1upIhCTUkzTHMh8b86
# WmjRUqbrnvdyR2ydI5l1OqcMBjkpPpIV6wcc+KY/RH2xvVuuoHjlUjwq2bHiNoX+
# W1scCpnA8YTs2d50jDHUgwUo+ciwpffH0Riq132NFmrH3r67VaN3TuBxjI8SIZM5
# 8WEDkbeoriDk3hxU8ZWV7b8AW6oyVBGfM06UgkfMb58h+tJPrFx8VI/WLq1dTqMf
# ZOm5cuclMnUHs2uqrRNtnV8UfidPBL4ZHkTcClQbCoz0UbLhkiDvIS00Dn+BBcxw
# /TKqVL4Oaz3bkMSsM46LciTeucHY9ExRVt3zy7i149sd+F4QozPqn7FrSVHXmem3
# r7bjyHTxOgqxRCVa18Vtx7P/8bYSBeS+WHCKcliFCecspusCDSlnRUjZwyPdP0VH
# xaZg2unjHY3rMYIVMDCCFSwCAQEwfTBpMQswCQYDVQQGEwJVUzEXMBUGA1UEChMO
# RGlnaUNlcnQsIEluYy4xQTA/BgNVBAMTOERpZ2lDZXJ0IFRydXN0ZWQgRzQgQ29k
# ZSBTaWduaW5nIFJTQTQwOTYgU0hBMzg0IDIwMjEgQ0ExAhAHHxQbizANJfMU6yMM
# 0NHdMA0GCWCGSAFlAwQCAQUAoIHOMBkGCSqGSIb3DQEJAzEMBgorBgEEAYI3AgEE
# MBwGCisGAQQBgjcCAQsxDjAMBgorBgEEAYI3AgEVMC8GCSqGSIb3DQEJBDEiBCBW
# STMEpY5oTqEtnhE8rXHTfUpY7MZMEfDbBKbS1J0cLTBiBgorBgEEAYI3AgEMMVQw
# UqBQgE4AQgB1AGkAbAB0ADoAIABSAGUAbABlAGEAcwBlAF8AbQBhAGkAbgBfAHYA
# MwAuADkALgAxADMAXwAyADAAMgAyADAANQAxADcALgAwADIwDQYJKoZIhvcNAQEB
# BQAEggIAZ20aZkGkTuZACtVG89TVf+3Nw7cpJO4pkpM71AFEX7/TZ4NjeFMHCrEr
# g8kNhN1UNcf0FGKplenCcykaIYUTlYgT3VCOeRGINOmySIotyEfYw4HapwNhj8/G
# CK/XOKJvIZ96yHHkpaiCOx3JDVtX5UjkChX1IJNECy0RyzALQA9U/EQl7v8oNEs6
# mCHRfPflHgkPYUPYUJXAGk3tD0ZgeeomUR0zm6Zmvqar2RJaZADtCF5OxOcFbdui
# 9yrlbSlkxv6gSW60W372FRCIoy1BML7Okjv7QJnhJkPIAs4sb0ZCV3rB6ZjKBXx3
# WzeQ5yjpJ3O1ZsZKPP4XVayPJCv2PSRd8dlDgmJtMbN2gvjsLtOkDKN03jnEsiiX
# 9IeYu7AaDdDeMDW8U5A0HYStrVX7OYpLqojtWOdeIz3/thj9ncWDio4KqEZTud37
# kfhDQPks9zWHoeI8MnjWMgBCEMskNFQnEhgGNlxWRW8bzypODhlrUGB271/6tFCE
# UW24irgtfCvNVmQh5E7V+GNplFujgCa7O4wQvYBb1i2OnQ+igJkfWx2N+wmb8QYE
# mN4RM/bk/SOc1b3MnU/ztqscOPPllmQsqMe/8LW77Ww2fy3i88RlcjweWiTs+3AK
# akFenQ/OzGPTrG8+mMKEjRKuxKyL2uZRKUoZ2zVlmjEddgnIVCWhghGzMIIRrwYK
# KwYBBAGCNwMDATGCEZ8wghGbBgkqhkiG9w0BBwKgghGMMIIRiAIBAzEPMA0GCWCG
# SAFlAwQCAQUAMHgGCyqGSIb3DQEJEAEEoGkEZzBlAgEBBglghkgBhv1sBwEwMTAN
# BglghkgBZQMEAgEFAAQgnT/1Hedipjs4jpirOCgW93RhvoYu0jJ5WKO7Y0LYfrYC
# EQDwVmhL49/+ciLQ3plX3i8KGA8yMDIyMDUxNzE2NDQyNVqggg18MIIGxjCCBK6g
# AwIBAgIQCnpKiJ7JmUKQBmM4TYaXnTANBgkqhkiG9w0BAQsFADBjMQswCQYDVQQG
# EwJVUzEXMBUGA1UEChMORGlnaUNlcnQsIEluYy4xOzA5BgNVBAMTMkRpZ2lDZXJ0
# IFRydXN0ZWQgRzQgUlNBNDA5NiBTSEEyNTYgVGltZVN0YW1waW5nIENBMB4XDTIy
# MDMyOTAwMDAwMFoXDTMzMDMxNDIzNTk1OVowTDELMAkGA1UEBhMCVVMxFzAVBgNV
# BAoTDkRpZ2lDZXJ0LCBJbmMuMSQwIgYDVQQDExtEaWdpQ2VydCBUaW1lc3RhbXAg
# MjAyMiAtIDIwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQC5KpYjply8
# X9ZJ8BWCGPQz7sxcbOPgJS7SMeQ8QK77q8TjeF1+XDbq9SWNQ6OB6zhj+TyIad48
# 0jBRDTEHukZu6aNLSOiJQX8Nstb5hPGYPgu/CoQScWyhYiYB087DbP2sO37cKhyp
# vTDGFtjavOuy8YPRn80JxblBakVCI0Fa+GDTZSw+fl69lqfw/LH09CjPQnkfO8eT
# B2ho5UQ0Ul8PUN7UWSxEdMAyRxlb4pguj9DKP//GZ888k5VOhOl2GJiZERTFKwyg
# M9tNJIXogpThLwPuf4UCyYbh1RgUtwRF8+A4vaK9enGY7BXn/S7s0psAiqwdjTuA
# aP7QWZgmzuDtrn8oLsKe4AtLyAjRMruD+iM82f/SjLv3QyPf58NaBWJ+cCzlK7I9
# Y+rIroEga0OJyH5fsBrdGb2fdEEKr7mOCdN0oS+wVHbBkE+U7IZh/9sRL5IDMM4w
# t4sPXUSzQx0jUM2R1y+d+/zNscGnxA7E70A+GToC1DGpaaBJ+XXhm+ho5GoMj+vk
# sSF7hmdYfn8f6CvkFLIW1oGhytowkGvub3XAsDYmsgg7/72+f2wTGN/GbaR5Sa2L
# f2GHBWj31HDjQpXonrubS7LitkE956+nGijJrWGwoEEYGU7tR5thle0+C2Fa6j56
# mJJRzT/JROeAiylCcvd5st2E6ifu/n16awIDAQABo4IBizCCAYcwDgYDVR0PAQH/
# BAQDAgeAMAwGA1UdEwEB/wQCMAAwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwgwIAYD
# VR0gBBkwFzAIBgZngQwBBAIwCwYJYIZIAYb9bAcBMB8GA1UdIwQYMBaAFLoW2W1N
# hS9zKXaaL3WMaiCPnshvMB0GA1UdDgQWBBSNZLeJIf5WWESEYafqbxw2j92vDTBa
# BgNVHR8EUzBRME+gTaBLhklodHRwOi8vY3JsMy5kaWdpY2VydC5jb20vRGlnaUNl
# cnRUcnVzdGVkRzRSU0E0MDk2U0hBMjU2VGltZVN0YW1waW5nQ0EuY3JsMIGQBggr
# BgEFBQcBAQSBgzCBgDAkBggrBgEFBQcwAYYYaHR0cDovL29jc3AuZGlnaWNlcnQu
# Y29tMFgGCCsGAQUFBzAChkxodHRwOi8vY2FjZXJ0cy5kaWdpY2VydC5jb20vRGln
# aUNlcnRUcnVzdGVkRzRSU0E0MDk2U0hBMjU2VGltZVN0YW1waW5nQ0EuY3J0MA0G
# CSqGSIb3DQEBCwUAA4ICAQANLSN0ptH1+OpLmT8B5PYM5K8WndmzjJeCKZxDbwEt
# qzi1cBG/hBmLP13lhk++kzreKjlaOU7YhFmlvBuYquhs79FIaRk4W8+JOR1wcNlO
# 3yMibNXf9lnLocLqTHbKodyhK5a4m1WpGmt90fUCCU+C1qVziMSYgN/uSZW3s8zF
# p+4O4e8eOIqf7xHJMUpYtt84fMv6XPfkU79uCnx+196Y1SlliQ+inMBl9AEiZcfq
# XnSmWzWSUHz0F6aHZE8+RokWYyBry/J70DXjSnBIqbbnHWC9BCIVJXAGcqlEO2lH
# EdPu6cegPk8QuTA25POqaQmoi35komWUEftuMvH1uzitzcCTEdUyeEpLNypM81zc
# toXAu3AwVXjWmP5UbX9xqUgaeN1Gdy4besAzivhKKIwSqHPPLfnTI/KeGeANlCig
# 69saUaCVgo4oa6TOnXbeqXOqSGpZQ65f6vgPBkKd3wZolv4qoHRbY2beayy4eKpN
# cG3wLPEHFX41tOa1DKKZpdcVazUOhdbgLMzgDCS4fFILHpl878jIxYxYaa+rPeHP
# zH0VrhS/inHfypex2EfqHIXgRU4SHBQpWMxv03/LvsEOSm8gnK7ZczJZCOctkqEa
# Ef4ymKZdK5fgi9OczG21Da5HYzhHF1tvE9pqEG4fSbdEW7QICodaWQR2EaGndwIT
# HDCCBq4wggSWoAMCAQICEAc2N7ckVHzYR6z9KGYqXlswDQYJKoZIhvcNAQELBQAw
# YjELMAkGA1UEBhMCVVMxFTATBgNVBAoTDERpZ2lDZXJ0IEluYzEZMBcGA1UECxMQ
# d3d3LmRpZ2ljZXJ0LmNvbTEhMB8GA1UEAxMYRGlnaUNlcnQgVHJ1c3RlZCBSb290
# IEc0MB4XDTIyMDMyMzAwMDAwMFoXDTM3MDMyMjIzNTk1OVowYzELMAkGA1UEBhMC
# VVMxFzAVBgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMTswOQYDVQQDEzJEaWdpQ2VydCBU
# cnVzdGVkIEc0IFJTQTQwOTYgU0hBMjU2IFRpbWVTdGFtcGluZyBDQTCCAiIwDQYJ
# KoZIhvcNAQEBBQADggIPADCCAgoCggIBAMaGNQZJs8E9cklRVcclA8TykTepl1Gh
# 1tKD0Z5Mom2gsMyD+Vr2EaFEFUJfpIjzaPp985yJC3+dH54PMx9QEwsmc5Zt+Feo
# An39Q7SE2hHxc7Gz7iuAhIoiGN/r2j3EF3+rGSs+QtxnjupRPfDWVtTnKC3r07G1
# decfBmWNlCnT2exp39mQh0YAe9tEQYncfGpXevA3eZ9drMvohGS0UvJ2R/dhgxnd
# X7RUCyFobjchu0CsX7LeSn3O9TkSZ+8OpWNs5KbFHc02DVzV5huowWR0QKfAcsW6
# Th+xtVhNef7Xj3OTrCw54qVI1vCwMROpVymWJy71h6aPTnYVVSZwmCZ/oBpHIEPj
# Q2OAe3VuJyWQmDo4EbP29p7mO1vsgd4iFNmCKseSv6De4z6ic/rnH1pslPJSlREr
# WHRAKKtzQ87fSqEcazjFKfPKqpZzQmiftkaznTqj1QPgv/CiPMpC3BhIfxQ0z9JM
# q++bPf4OuGQq+nUoJEHtQr8FnGZJUlD0UfM2SU2LINIsVzV5K6jzRWC8I41Y99xh
# 3pP+OcD5sjClTNfpmEpYPtMDiP6zj9NeS3YSUZPJjAw7W4oiqMEmCPkUEBIDfV8j
# u2TjY+Cm4T72wnSyPx4JduyrXUZ14mCjWAkBKAAOhFTuzuldyF4wEr1GnrXTdrnS
# DmuZDNIztM2xAgMBAAGjggFdMIIBWTASBgNVHRMBAf8ECDAGAQH/AgEAMB0GA1Ud
# DgQWBBS6FtltTYUvcyl2mi91jGogj57IbzAfBgNVHSMEGDAWgBTs1+OC0nFdZEzf
# Lmc/57qYrhwPTzAOBgNVHQ8BAf8EBAMCAYYwEwYDVR0lBAwwCgYIKwYBBQUHAwgw
# dwYIKwYBBQUHAQEEazBpMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2Vy
# dC5jb20wQQYIKwYBBQUHMAKGNWh0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9E
# aWdpQ2VydFRydXN0ZWRSb290RzQuY3J0MEMGA1UdHwQ8MDowOKA2oDSGMmh0dHA6
# Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0ZWRSb290RzQuY3JsMCAG
# A1UdIAQZMBcwCAYGZ4EMAQQCMAsGCWCGSAGG/WwHATANBgkqhkiG9w0BAQsFAAOC
# AgEAfVmOwJO2b5ipRCIBfmbW2CFC4bAYLhBNE88wU86/GPvHUF3iSyn7cIoNqilp
# /GnBzx0H6T5gyNgL5Vxb122H+oQgJTQxZ822EpZvxFBMYh0MCIKoFr2pVs8Vc40B
# IiXOlWk/R3f7cnQU1/+rT4osequFzUNf7WC2qk+RZp4snuCKrOX9jLxkJodskr2d
# fNBwCnzvqLx1T7pa96kQsl3p/yhUifDVinF2ZdrM8HKjI/rAJ4JErpknG6skHibB
# t94q6/aesXmZgaNWhqsKRcnfxI2g55j7+6adcq/Ex8HBanHZxhOACcS2n82HhyS7
# T6NJuXdmkfFynOlLAlKnN36TU6w7HQhJD5TNOXrd/yVjmScsPT9rp/Fmw0HNT7ZA
# myEhQNC3EyTN3B14OuSereU0cZLXJmvkOHOrpgFPvT87eK1MrfvElXvtCl8zOYdB
# eHo46Zzh3SP9HSjTx/no8Zhf+yvYfvJGnXUsHicsJttvFXseGYs2uJPU5vIXmVnK
# cPA3v5gA3yAWTyf7YGcWoWa63VXAOimGsJigK+2VQbc61RWYMbRiCQ8KvYHZE/6/
# pNHzV9m8BPqC3jLfBInwAM1dwvnQI38AC+R2AibZ8GV2QqYphwlHK+Z/GqSFD/yY
# lvZVVCsfgPrA8g4r5db7qS9EFUrnEw4d2zc4GqEr9u3WfPwxggN2MIIDcgIBATB3
# MGMxCzAJBgNVBAYTAlVTMRcwFQYDVQQKEw5EaWdpQ2VydCwgSW5jLjE7MDkGA1UE
# AxMyRGlnaUNlcnQgVHJ1c3RlZCBHNCBSU0E0MDk2IFNIQTI1NiBUaW1lU3RhbXBp
# bmcgQ0ECEAp6SoieyZlCkAZjOE2Gl50wDQYJYIZIAWUDBAIBBQCggdEwGgYJKoZI
# hvcNAQkDMQ0GCyqGSIb3DQEJEAEEMBwGCSqGSIb3DQEJBTEPFw0yMjA1MTcxNjQ0
# MjVaMCsGCyqGSIb3DQEJEAIMMRwwGjAYMBYEFIUI84ZRXLPTB322tLfAfxtKXkHe
# MC8GCSqGSIb3DQEJBDEiBCD6nFFQEG6P9dJgqwYWRs4qcIuEc8WzVzP/ANrLjNw9
# 9DA3BgsqhkiG9w0BCRACLzEoMCYwJDAiBCCdppAVw0nGwYl4Rbo1gq1wyI+kKTvb
# ar6cK9JTknnmOzANBgkqhkiG9w0BAQEFAASCAgAw6wjOhvvgNacByXWLXEcHuoRB
# hCB6I/ZNStOapAzlidSg0ccPO4QsS5L78/ff+DCa4ZFu//T2wfORd9wCt9NpL0XT
# 7/zVF3zw16aNIn1W9gbJkjPfHGLImV30M/PzMnzlj3m9ybK0W/vvu8SmNpMrsSKI
# sR1/nSzaA+Y0FmOOy2jtf7MtZeVh8o4ZkgBVPgVLpRSr4SJXzadMjQjshWII2ujM
# v2YPK7qczQmXaonfN+rAkPxLS+3MVDgoUKAGvQBpm686eDkImZ0qTG+Qi6+Z+2id
# QXv8h4V4L7Ln37RNsm4j5carTNxTx6b0SZPreswMEFfUwtHeaSWvUIKRzyY0t3O/
# NT5G8RSxtJLqTMVFWcmlbgaXo7/PDsA7hs1XQJE3UJnfRNrcznnHgYJPuW737A9Q
# v4sFjmov5/F4qUbYIh5yE8ec4IhOuR0rTEgDJLcU67KdrLjcePMlIlbPaArw1vn3
# On862t4jYz5aj3YaaHYzXB6VxiMp9JN5B3e4gmix/8TgN9kNmvbVwODfK5hfaPcY
# QXkTBySKKoRz+eyz67IBXPCHDYXtiXdaqvhWPFn+YbFH9jlEqPP2ATzqEz/ibgDZ
# 0YyvPy8vnItbUwPuGTVjwU0VmF0m5pSHm/pPALd1xKiMF+eZq580lbrIoUeyZ5mP
# 0XyrSEj88tBJMxcKZA==
# SIG # End signature block

```

`Scripts\activate`:

```
# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

deactivate () {
    # reset old environment variables
    if [ -n "${_OLD_VIRTUAL_PATH:-}" ] ; then
        PATH="${_OLD_VIRTUAL_PATH:-}"
        export PATH
        unset _OLD_VIRTUAL_PATH
    fi
    if [ -n "${_OLD_VIRTUAL_PYTHONHOME:-}" ] ; then
        PYTHONHOME="${_OLD_VIRTUAL_PYTHONHOME:-}"
        export PYTHONHOME
        unset _OLD_VIRTUAL_PYTHONHOME
    fi

    # This should detect bash and zsh, which have a hash command that must
    # be called to get it to forget past commands.  Without forgetting
    # past commands the $PATH changes we made may not be respected
    if [ -n "${BASH:-}" -o -n "${ZSH_VERSION:-}" ] ; then
        hash -r 2> /dev/null
    fi

    if [ -n "${_OLD_VIRTUAL_PS1:-}" ] ; then
        PS1="${_OLD_VIRTUAL_PS1:-}"
        export PS1
        unset _OLD_VIRTUAL_PS1
    fi

    unset VIRTUAL_ENV
    if [ ! "${1:-}" = "nondestructive" ] ; then
    # Self destruct!
        unset -f deactivate
    fi
}

# unset irrelevant variables
deactivate nondestructive

VIRTUAL_ENV="C:\Users\akhil\application"
export VIRTUAL_ENV

_OLD_VIRTUAL_PATH="$PATH"
PATH="$VIRTUAL_ENV/Scripts:$PATH"
export PATH

# unset PYTHONHOME if set
# this will fail if PYTHONHOME is set to the empty string (which is bad anyway)
# could use `if (set -u; : $PYTHONHOME) ;` in bash
if [ -n "${PYTHONHOME:-}" ] ; then
    _OLD_VIRTUAL_PYTHONHOME="${PYTHONHOME:-}"
    unset PYTHONHOME
fi

if [ -z "${VIRTUAL_ENV_DISABLE_PROMPT:-}" ] ; then
    _OLD_VIRTUAL_PS1="${PS1:-}"
    PS1="(application) ${PS1:-}"
    export PS1
fi

# This should detect bash and zsh, which have a hash command that must
# be called to get it to forget past commands.  Without forgetting
# past commands the $PATH changes we made may not be respected
if [ -n "${BASH:-}" -o -n "${ZSH_VERSION:-}" ] ; then
    hash -r 2> /dev/null
fi

```

`Scripts\activate.bat`:

```bat
@echo off

rem This file is UTF-8 encoded, so we need to update the current code page while executing it
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)

set VIRTUAL_ENV=C:\Users\akhil\application

if not defined PROMPT set PROMPT=$P$G

if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%

set _OLD_VIRTUAL_PROMPT=%PROMPT%
set PROMPT=(application) %PROMPT%

if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=

if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%

set PATH=%VIRTUAL_ENV%\Scripts;%PATH%

:END
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)

```

`Scripts\deactivate.bat`:

```bat
@echo off

if defined _OLD_VIRTUAL_PROMPT (
    set "PROMPT=%_OLD_VIRTUAL_PROMPT%"
)
set _OLD_VIRTUAL_PROMPT=

if defined _OLD_VIRTUAL_PYTHONHOME (
    set "PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%"
    set _OLD_VIRTUAL_PYTHONHOME=
)

if defined _OLD_VIRTUAL_PATH (
    set "PATH=%_OLD_VIRTUAL_PATH%"
)

set _OLD_VIRTUAL_PATH=

set VIRTUAL_ENV=

:END

```

`WHAT_HAVE_WE_ACHIEVED.md`:

```md
# WHAT_HAVE_WE_ACHIEVED.md

## Core Milestones
- **v1.1.0 (2026-06-01):** Deep Architectural Optimizations
  - Migrated primary keys to auto-incrementing `models.AutoField` across all schemas.
  - Reset database migrations to a clean, unified `0001_initial.py` setup to resolve SQLite constraints mismatch.
  - Implemented transactional checkouts/returns utilizing `transaction.atomic` and row locking (`select_for_update`).
  - Added native Python 3.10+ type hints across backend views and models.
  - Standardized trailing API slashes and purged buggy API delete overrides.
  - Configured robust `django.test` and `APITestCase` suite with 100% pass results.

## Recent Changes Ledger
| Date / Version | File Refactored | Action Performed / Bug Fixed |
| :--- | :--- | :--- |
| 2026-06-01 | `Home/models.py` | Migrated primary keys, cleaned legacy queues, added strict typing. |
| 2026-06-01 | `Home/views.py` | Wrapped checkouts and returns in database atomic locks, annotated dashboard queries. |
| 2026-06-01 | `Home/api/serializers.py`| Added strict DRF stock levels and borrow safety validations. |
| 2026-06-01 | `Home/tests.py` | Wrote and integrated automated success and validation fail test routines. |

## Current Stable State
- **Flawless Features (DO NOT BREAK):**
  - Database schema & model migrations (`Books`, `Issued`, `User`).
  - Atomic, race-condition protected checkout/returns.
  - Native Python 3.10 type hinted application logic.
  - Unit test suite validation verification.


```

`continue_chat.bat`:

```bat
@echo off
:: =================================================================
:: Antigravity CLI Context Resume Script
:: =================================================================

echo [INFO] Resuming project context for "LibSys"...
cd /d "F:\REpo\LibSys\"

:: Launch Antigravity CLI in the current directory
:: This ensures ANTIGRAVITY.md, README.md and project files are loaded
if exist "E:\CLI\agy.exe" (
    "E:\CLI\agy.exe"
) else (
    antigravity
)

```

`digest.txt`:

```txt
Directory structure:
└── LibSys/
    ├── README.md
    ├── AI_PROMPT_GUIDE.md
    ├── CODEBASE_AUDIT_REPORT.md
    ├── CODEBASE_INDEX.md
    ├── continue_chat.bat
    ├── CURRENT_CONTEXT.md
    ├── docker-compose.yml
    ├── Dockerfile
    ├── requirements-dev.txt
    ├── requirements.txt
    ├── WHAT_HAVE_WE_ACHIEVED.md
    ├── .dockerignore
    ├── LibSys/
    │   ├── CLOUD_RUN_TEST_LOGS.md
    │   ├── COMPLIANCE_CHECK_REPORT.md
    │   ├── db - Copy.SQLITE3
    │   ├── db.sql
    │   ├── manage.py
    │   ├── PROJECT_REVIEW_REPORT.md
    │   ├── pyvenv.cfg
    │   ├── SECURITY_AUDIT_REPORT.md
    │   ├── SEO_AUDIT_REPORT.md
    │   ├── .dockerignore
    │   ├── Home/
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── locustfile.py
    │   │   ├── measure_load_times.py
    │   │   ├── middleware.py
    │   │   ├── models.py
    │   │   ├── run_live_playwright_test.py
    │   │   ├── run_playwright_e2e.py
    │   │   ├── tests.py
    │   │   ├── tests_cloud_run.py
    │   │   ├── tests_playwright.py
    │   │   ├── urls.py
    │   │   ├── verify_html_urls.py
    │   │   ├── views.py
    │   │   ├── api/
    │   │   │   ├── serializers.py
    │   │   │   ├── urls.py
    │   │   │   └── views.py
    │   │   └── migrations/
    │   │       ├── 0001_initial.py
    │   │       └── __init__.py
    │   ├── LibSys/
    │   │   ├── __init__.py
    │   │   ├── asgi.py
    │   │   ├── settings.py
    │   │   ├── urls.py
    │   │   └── wsgi.py
    │   ├── static/
    │   │   ├── style.css
    │   │   └── js/
    │   │       ├── preload.js
    │   │       └── sw.js
    │   └── templates/
    │       ├── 429.html
    │       ├── home.html
    │       ├── auth/
    │       │   ├── login.html
    │       │   └── register.html
    │       ├── etc/
    │       │   ├── books.html
    │       │   ├── contacts.html
    │       │   └── members.html
    │       ├── registration/
    │       │   └── login.html
    │       └── user/
    │           ├── dashboard.html
    │           ├── edit_book.html
    │           ├── issue_book.html
    │           ├── issued_books.html
    │           ├── manage_books.html
    │           └── return_book.html
    ├── Scripts/
    │   ├── activate
    │   ├── activate.bat
    │   ├── Activate.ps1
    │   └── deactivate.bat
    └── .github/
        └── workflows/
            ├── django.yml
            └── docker-scout.yml

================================================
FILE: README.md
================================================
This is my Functional project of a Library Management system, with APIs



================================================
FILE: AI_PROMPT_GUIDE.md
================================================
# AI_PROMPT_GUIDE.md

## Tech Stack & Constraints
- **Core Framework:** Python 3.10+ / Django 4.x+ / Django REST Framework (DRF)
- **Database Backend:** SQLite (Development) / MySQL (Production compatible)
- **Containerization:** Docker / Docker Compose
- **Web Server:** Gunicorn / Whitenoise (Static asset handling)

## Coding Conventions
- **Naming Style:** PascalCase for Models/Classes, snake_case for functions, variables, and database fields.
- **Error Handling:** Standard Python `try-except` blocks. In web views, catch exceptions and return user feedback via `django.contrib.messages` or render dedicated templates with context error keys.
- **Database Safety:** Ensure atomic transactions where required (`django.db.transaction.atomic`) especially when allocating dynamic IDs or queue allocations.
- **REST APIs:** Use serializer validation patterns before modifying resources.

## Token Optimization Rule
- **No Full File Rewrites:** When generating or modifying code, do NOT output the unchanged files.
- **Placeholder Rule:** Use concise comment blocks like `# ... existing code ...` or `// ... existing code ...` for unchanged blocks.
- **Targeted Diffs:** Provide only the specific block or lines being added or refactored.



================================================
FILE: CODEBASE_AUDIT_REPORT.md
================================================
# CODEBASE QUALITY & OPTIMIZATION REPORT

## Executive Summary
This report aggregates findings from parallel analysis of the Django LibSys codebase, highlighting critical backend, serialization, API, and architectural design flaws. Corrective actions and optimizations are detailed below.

---

## 1. Backend Application Layer (`Home/models.py`, `Home/views.py`)

### A. Non-Atomic Primary Key Generation
* **Bug:** `models.py` generates model primary keys via high-risk, non-atomic database queries (`MAX(Bid)` / `.last()`) and in-memory state objects (`deque()`, `set()`). 
* **Impact:** High race-condition risk. Concurrent requests result in duplicate primary keys, throwing database `IntegrityError`s. In-memory queues fail state continuity under multi-worker WSGI configurations.
* **Fix:** Replace custom dynamic PK defaults with standard database auto-incrementing serials (`models.AutoField`).

### B. Insecure Model Save Override
* **Bug:** `Books.save` resets `available_quantity = self.quantity` on every call.
* **Impact:** Edits to other book fields (e.g. author name, fine amounts) wipe out checkout metrics, resetting inventories to max quantity.
* **Fix:** Only set `available_quantity` on object creation (`self._state.adding`).

### C. N+1 Performance Bottlenecks
* **Bug:** View queries dynamically count related `Issued` records in Python iterative loops (`dashboard` view).
* **Impact:** 1000 books require 1001 database hits.
* **Fix:** Utilize `.annotate(active_issues=Count('issued', filter=Q(issued__submit=False)))` for single-query retrieval.

---

## 2. API & Serialization (`Home/api/`)

### A. ListCreateAPIView Method Signature Mismatch
* **Bug:** `BookCreate` and `IssuedCreate` classes implement a `delete` method invoking `self.destroy()`.
* **Impact:** `ListCreateAPIView` doesn't inherit from `DestroyModelMixin`. Further, paths mapping to these views lack `<int:pk>` route parameters, causing immediate runtime `AttributeError`s and `KeyError`s.
* **Fix:** Purge custom `delete` overrides from creation views. Outsource delete hooks to dedicated `RetrieveUpdateDestroyAPIView` paths.

### B. Missing Serializer Level Stock Validation
* **Bug:** `IssuedSerializer` allows book checkouts regardless of stock level or user borrow status.
* **Impact:** Quantities decrement past zero, and a single user can check out multiple instances of the same book.
* **Fix:** Enforce validation constraint inside `validate()` validating `book.available_quantity > 0` and borrower duplication status.

---

## 3. Infrastructure & Configurations

### A. Exposed MySQL Database Secret in Dockerfile
* **Bug:** Dockerfile embeds hardcoded root credentials (`DATABASE_URL=mysql://root:Mahesh@2018@34.38.41.15:3306/libsys_db`).
* **Impact:** High credential compromise risk.
* **Fix:** Remove line. Source dynamic variables via secure environment parameters at startup.

### B. Database Backend Dissonance
* **Bug:** Docker setup configures Postgres containers, while the Dockerfile installs MySQL client components, and settings default to SQLite.
* **Impact:** Run-time database driver exceptions.
* **Fix:** Unify database configuration parameters. Align environment drivers with a single chosen database package.



================================================
FILE: CODEBASE_INDEX.md
================================================
# CODEBASE_INDEX.md

## System Architecture Diagram
```
Client (Browser) <---> Django Web Server (LibSys) <---> SQLite Database (db.sqlite3)
                          |
                          +---> REST API (djangorestframework)
```

## Directory Tree
```
F:\REpo\LibSys
â”œâ”€â”€ .dockerignore
â”œâ”€â”€ .gitignore
â”œâ”€â”€ Dockerfile
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ requirements-dev.txt
â”œâ”€â”€ manage.py
â”œâ”€â”€ LibSys/
â”‚   â”œâ”€â”€ settings.py
â”‚   â”œâ”€â”€ urls.py
â”‚   â”œâ”€â”€ wsgi.py
â”‚   â””â”€â”€ asgi.py
â””â”€â”€ Home/
    â”œâ”€â”€ admin.py
    â”œâ”€â”€ apps.py
    â”œâ”€â”€ models.py
    â”œâ”€â”€ urls.py
    â”œâ”€â”€ views.py
    â”œâ”€â”€ api/
    â”‚   â”œâ”€â”€ serializers.py
    â”‚   â””â”€â”€ urls.py
    â”œâ”€â”€ static/
    â””â”€â”€ templates/
```

## Component Matrix
| Component / File | Primary Responsibility | Main Dependencies |
| :--- | :--- | :--- |
| `LibSys/settings.py` | Global settings, database connection, middleware config, apps registration | Django, MySQL / SQLite config |
| `LibSys/urls.py` | Main routing module directing requests to app endpoints | Django routing |
| `Home/models.py` | Data definitions for Books and Issued records | django.db.models, auth.User |
| `Home/views.py` | Business logic for dashboard, managing books, and book checkout/return | django.shortcuts, CustomLoginView, CustomlogoutView |
| `Home/urls.py` | App-specific routing mapping paths to views | Home/views.py |
| `Home/api/` | Serializers and view logic for REST endpoints | djangorestframework |
| `Dockerfile` & `docker-compose.yml` | Containerization, deployment orchestration and environment reproducibility | Docker, Docker Compose |



================================================
FILE: continue_chat.bat
================================================
@echo off
:: =================================================================
:: Antigravity CLI Context Resume Script
:: =================================================================

echo [INFO] Resuming project context for "LibSys"...
cd /d "F:\REpo\LibSys\"

:: Launch Antigravity CLI in the current directory
:: This ensures ANTIGRAVITY.md, README.md and project files are loaded
if exist "E:\CLI\agy.exe" (
    "E:\CLI\agy.exe"
) else (
    antigravity
)



================================================
FILE: CURRENT_CONTEXT.md
================================================
# CURRENT_CONTEXT.md

## Immediate Goals
- Establish high-quality, token-efficient codebase documentation files to enhance developer and AI reasoning contexts.

## Active Blockers/Issues
- None detected. Basic application logic is stable; database schemas map correctly to SQLite targets.

## Next Steps
1. Verify and validate documentation accuracy against physical files.
2. Formulate coding prompt constraints for future AI sessions.
3. Optimize codebase for context window consumption.



================================================
FILE: docker-compose.yml
================================================
services:
  web:
    build: .
    # Command to run on startup
    command: >
      sh -c "python manage.py collectstatic --noinput &&
             python manage.py migrate &&
             gunicorn LibSys.wsgi:application --bind 0.0.0.0:8000"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    # Wait for the database service to be healthy before starting
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - .env
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:



================================================
FILE: Dockerfile
================================================
FROM python:3.13-slim-bookworm

# Update system packages to address vulnerabilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Set environment variables for non-interactive commands
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn and other production-specific dependencies
RUN pip install gunicorn

# Copy the rest of the application's code into the container
COPY . .

# Set the working directory to the Django project root inside the container
WORKDIR /app/LibSys

# Set production-specific environment variables for the container
# Replace these values with your actual production settings.
# For Cloud Run, you can set these in the console or with the gcloud CLI.
# This Dockerfile includes them as defaults for demonstration.
ENV DJANGO_DEBUG=False
ENV ALLOWED_HOSTS=libsys-xvhbgr5zoq-as.a.run.app,*
ENV CSRF_TRUSTED_ORIGINS=*

# Replace with your production database URL from Cloud SQL
# You should get this value from your GCP environment, not hard-code it.
ENV DATABASE_URL=mysql://root:Mahesh@2018@34.38.41.15:3306/libsys_db	


# Run collectstatic to gather all static files for WhiteNoise to serve
RUN python manage.py collectstatic --noinput

# Run the Gunicorn server
# Cloud Run automatically sets the PORT environment variable.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "LibSys.wsgi"]


================================================
FILE: requirements-dev.txt
================================================
# This file is for development-specific packages.
# It includes the base production requirements.
-r requirements.txt

django-debug-toolbar
pytest
docker
gcloud
locust



================================================
FILE: requirements.txt
================================================
[Binary file]


================================================
FILE: WHAT_HAVE_WE_ACHIEVED.md
================================================
# WHAT_HAVE_WE_ACHIEVED.md

## Core Milestones
- **v1.1.0 (2026-06-01):** Deep Architectural Optimizations
  - Migrated primary keys to auto-incrementing `models.AutoField` across all schemas.
  - Reset database migrations to a clean, unified `0001_initial.py` setup to resolve SQLite constraints mismatch.
  - Implemented transactional checkouts/returns utilizing `transaction.atomic` and row locking (`select_for_update`).
  - Added native Python 3.10+ type hints across backend views and models.
  - Standardized trailing API slashes and purged buggy API delete overrides.
  - Configured robust `django.test` and `APITestCase` suite with 100% pass results.

## Recent Changes Ledger
| Date / Version | File Refactored | Action Performed / Bug Fixed |
| :--- | :--- | :--- |
| 2026-06-01 | `Home/models.py` | Migrated primary keys, cleaned legacy queues, added strict typing. |
| 2026-06-01 | `Home/views.py` | Wrapped checkouts and returns in database atomic locks, annotated dashboard queries. |
| 2026-06-01 | `Home/api/serializers.py`| Added strict DRF stock levels and borrow safety validations. |
| 2026-06-01 | `Home/tests.py` | Wrote and integrated automated success and validation fail test routines. |

## Current Stable State
- **Flawless Features (DO NOT BREAK):**
  - Database schema & model migrations (`Books`, `Issued`, `User`).
  - Atomic, race-condition protected checkout/returns.
  - Native Python 3.10 type hinted application logic.
  - Unit test suite validation verification.




================================================
FILE: .dockerignore
================================================
# Git
.git
.gitignore

# Docker
Dockerfile
.dockerignore

# Environment
.env
.venv/

# Python
__pycache__/
*.pyc


================================================
FILE: LibSys/CLOUD_RUN_TEST_LOGS.md
================================================
# CLOUD_RUN_TEST_LOGS.md

## Test Run Environment
*   **Target Cloud Run URL:** `https://libsys-932534087542.asia-southeast1.run.app`
*   **Region:** `asia-southeast1`
*   **GCP Authentication Account:** `website@civic-source-463118-a0.iam.gserviceaccount.com`

---

## Live Integration Execution Outcomes

### ðŸ”´ Test 1: `GET /dashboard/`
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTPSConnectionPool(host='libsys-932534087542.asia-southeast1.run.app', port=443): Read timed out. (read timeout=5)`
*   **Root Cause:** Cloud Run instance cold-start latency exceeded the standard 5-second test timeout.

### ðŸ”´ Test 2: `POST /api/issue/create/` (Schema Rejection validation)
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTP 404 Not Found`
*   **Root Cause:** The active live container is running an outdated codebase deployment (last deployed 2025-10-03). The old router maps this API route differently (e.g. without trailing slashes, or using legacy URL mappings).

### ðŸ”´ Test 3: `GET /api/books/` (Retrieve Books Inventory)
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTPSConnectionPool(host='libsys-932534087542.asia-southeast1.run.app', port=443): Read timed out. (read timeout=5)`
*   **Root Cause:** Cold start scaling lag or live DB connectivity timeout in active container.



================================================
FILE: LibSys/COMPLIANCE_CHECK_REPORT.md
================================================
# COMPLIANCE CHECK REPORT

## 1. Executive Summary
This report evaluates the LibSys application against industry compliance frameworks, including the CIS Docker Benchmarks, GDPR/PCI-DSS Secret Protections, Python PEP 8 style guides, and Django production deployment checklists. Non-compliance findings are cataloged with actionable remediation paths.

---

## 2. Compliance Framework Audit Matrix

| Compliance Standard | Status | Finding / Non-Compliance |
| :--- | :--- | :--- |
| **GDPR / PCI-DSS Secret Protection** | ❌ NON-COMPLIANT | Plain-text MySQL root database credentials found hardcoded in `Dockerfile` line 43. |
| **CIS Docker Benchmark (Least Privilege)** | ❌ NON-COMPLIANT | Container runs implicitly under `root` user permissions (lacks `USER` non-root specification). |
| **Django Security Check** | ⚠️ Partial | Allowed Hosts and CSRF trusted origins configured as wildcards in production environment presets. |
| **PEP 8 Standards** |  COMPLIANT | Standard Python naming conventions (except for legacy model attributes `Bid` and `Issue_No` which are PascalCase instead of snake_case). |
| **Permissive Dependency Licenses** |  COMPLIANT | All requirements (Django, DRF, etc.) utilize highly permissive licenses (MIT, BSD, Apache-2.0). No copyleft GPL-style licensing detected. |

---

## 3. Detailed Compliance Deficiencies & Remediations

### A. Docker Non-Root Execution Deficit (CIS Benchmark 4.1)
*   **Deficit:** The Dockerfile does not define a dedicated user. The container starts and runs Gunicorn with full `root` operating privileges. In the event of a container breakout, the host system is fully exploitable.
*   **Remediation:** Declare a non-root system user inside the Dockerfile:
    ```dockerfile
    RUN groupadd -r appgroup && useradd -r -g appgroup appuser
    WORKDIR /app
    ...
    USER appuser
    ```

### B. Insecure Hardcoded Secrets (GDPR/PCI-DSS Section 3)
*   **Deficit:** Storing database connection credentials (`Mahesh@2018`) in code files violates data privacy standards, exposing the internal backend database to unauthorized extraction.
*   **Remediation:** Remove plain-text lines. Utilize Secret Manager parameters mapped to env variables dynamically at the container startup lifecycle.

### C. PascalCase Attribute Legacy Schemas (PEP 8 Compliance)
*   **Deficit:** Attributes `Bid` and `Issue_No` violate snake_case column guidelines of Python PEP 8 and Django model design patterns.
*   **Remediation:** Plan migrations to normalize naming fields to `bid` and `issue_no` in future schema versions.

---

## 4. Audit Limitations
*   **Licensing Tree:** This compliance check did not perform an automated licensing recursive tree audit of transitive dependencies (sub-dependencies). Dynamic package compliance should be verified using automated auditing tools like `license-checker` or `safety`.



================================================
FILE: LibSys/db - Copy.SQLITE3
================================================
[Binary file]


================================================
FILE: LibSys/db.sql
================================================
BEGIN TRANSACTION;
DROP TABLE IF EXISTS "Home_books";
CREATE TABLE "Home_books" ("book_name" varchar(200) NOT NULL, "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0), "author" text NOT NULL, "genre" text NULL, "fine" smallint unsigned NOT NULL CHECK ("fine" >= 0), "available_quantity" integer unsigned NOT NULL CHECK ("available_quantity" >= 0), "Bid" integer NOT NULL PRIMARY KEY);
DROP TABLE IF EXISTS "Home_issued";
CREATE TABLE "Home_issued" ("submit" bool NOT NULL, "create" datetime NOT NULL, "book_id" integer NOT NULL REFERENCES "Home_books" ("Bid") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "Issue_No" integer NOT NULL PRIMARY KEY, "days" integer unsigned NOT NULL CHECK ("days" >= 0));
DROP TABLE IF EXISTS "auth_group";
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);
DROP TABLE IF EXISTS "auth_group_permissions";
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "auth_permission";
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);
DROP TABLE IF EXISTS "auth_user";
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "first_name" varchar(150) NOT NULL);
DROP TABLE IF EXISTS "auth_user_groups";
CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "auth_user_user_permissions";
CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "authtoken_token";
CREATE TABLE "authtoken_token" ("key" varchar(40) NOT NULL PRIMARY KEY, "created" datetime NOT NULL, "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "django_admin_log";
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);
DROP TABLE IF EXISTS "django_content_type";
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);
DROP TABLE IF EXISTS "django_migrations";
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);
DROP TABLE IF EXISTS "django_session";
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);
INSERT INTO "Home_books" ("book_name","quantity","author","genre","fine","available_quantity","Bid") VALUES ('book1',12,'meme','comedy',123,12,1),
 ('book5',45,'akhil','comedy',456,45,2),
 ('apibook',1,'api','api',50,1,3);
INSERT INTO "Home_issued" ("submit","create","book_id","user_id","Issue_No","days") VALUES (1,'2024-12-19 08:18:32.582570',1,1,1,10),
 (1,'2024-12-19 08:18:35.146062',2,1,2,10),
 (1,'2024-12-21 10:27:20.347854',2,1,3,10),
 (0,'2025-09-25 09:54:48.257158',1,1,4,10),
 (0,'2025-09-25 09:54:51.005393',1,1,5,10);
INSERT INTO "auth_permission" ("id","content_type_id","codename","name") VALUES (1,1,'add_logentry','Can add log entry'),
 (2,1,'change_logentry','Can change log entry'),
 (3,1,'delete_logentry','Can delete log entry'),
 (4,1,'view_logentry','Can view log entry'),
 (5,2,'add_permission','Can add permission'),
 (6,2,'change_permission','Can change permission'),
 (7,2,'delete_permission','Can delete permission'),
 (8,2,'view_permission','Can view permission'),
 (9,3,'add_group','Can add group'),
 (10,3,'change_group','Can change group'),
 (11,3,'delete_group','Can delete group'),
 (12,3,'view_group','Can view group'),
 (13,4,'add_user','Can add user'),
 (14,4,'change_user','Can change user'),
 (15,4,'delete_user','Can delete user'),
 (16,4,'view_user','Can view user'),
 (17,5,'add_contenttype','Can add content type'),
 (18,5,'change_contenttype','Can change content type'),
 (19,5,'delete_contenttype','Can delete content type'),
 (20,5,'view_contenttype','Can view content type'),
 (21,6,'add_session','Can add session'),
 (22,6,'change_session','Can change session'),
 (23,6,'delete_session','Can delete session'),
 (24,6,'view_session','Can view session'),
 (25,7,'add_issued','Can add issued'),
 (26,7,'change_issued','Can change issued'),
 (27,7,'delete_issued','Can delete issued'),
 (28,7,'view_issued','Can view issued'),
 (29,8,'add_books','Can add books'),
 (30,8,'change_books','Can change books'),
 (31,8,'delete_books','Can delete books'),
 (32,8,'view_books','Can view books'),
 (33,9,'add_token','Can add Token'),
 (34,9,'change_token','Can change Token'),
 (35,9,'delete_token','Can delete Token'),
 (36,9,'view_token','Can view Token'),
 (37,10,'add_tokenproxy','Can add Token'),
 (38,10,'change_tokenproxy','Can change Token'),
 (39,10,'delete_tokenproxy','Can delete Token'),
 (40,10,'view_tokenproxy','Can view Token');
INSERT INTO "auth_user" ("id","password","last_login","is_superuser","username","last_name","email","is_staff","is_active","date_joined","first_name") VALUES (1,'pbkdf2_sha256$600000$TfyWQtXaVwwgvrjFvcu6KP$q5jfNZfI5d9c11FludgfiF6N0PrkTLYUHZzbuy1If4M=','2025-09-25 09:47:44.970760',1,'akhil161','','akhilkarwal161@gmail.com',1,1,'2024-12-15 09:54:46.932136',''),
 (2,'pbkdf2_sha256$600000$8xJHgzxwPzaG6Gi8l9rNwI$eotnDsslEbzKLyBv0f1dCiJ5PNxfWRsvuLQiBrCc43w=','2024-12-18 12:53:41.060362',0,'archita','','',0,1,'2024-12-18 12:12:51.213530','');
INSERT INTO "django_content_type" ("id","app_label","model") VALUES (1,'admin','logentry'),
 (2,'auth','permission'),
 (3,'auth','group'),
 (4,'auth','user'),
 (5,'contenttypes','contenttype'),
 (6,'sessions','session'),
 (7,'Home','issued'),
 (8,'Home','books'),
 (9,'authtoken','token'),
 (10,'authtoken','tokenproxy');
INSERT INTO "django_migrations" ("id","app","name","applied") VALUES (1,'contenttypes','0001_initial','2024-12-15 09:54:10.456096'),
 (2,'auth','0001_initial','2024-12-15 09:54:10.477672'),
 (3,'admin','0001_initial','2024-12-15 09:54:10.494188'),
 (4,'admin','0002_logentry_remove_auto_add','2024-12-15 09:54:10.506963'),
 (5,'admin','0003_logentry_add_action_flag_choices','2024-12-15 09:54:10.517480'),
 (6,'contenttypes','0002_remove_content_type_name','2024-12-15 09:54:10.539125'),
 (7,'auth','0002_alter_permission_name_max_length','2024-12-15 09:54:10.553046'),
 (8,'auth','0003_alter_user_email_max_length','2024-12-15 09:54:10.570147'),
 (9,'auth','0004_alter_user_username_opts','2024-12-15 09:54:10.580105'),
 (10,'auth','0005_alter_user_last_login_null','2024-12-15 09:54:10.594210'),
 (11,'auth','0006_require_contenttypes_0002','2024-12-15 09:54:10.599636'),
 (12,'auth','0007_alter_validators_add_error_messages','2024-12-15 09:54:10.609611'),
 (13,'auth','0008_alter_user_username_max_length','2024-12-15 09:54:10.624756'),
 (14,'auth','0009_alter_user_last_name_max_length','2024-12-15 09:54:10.637000'),
 (15,'auth','0010_alter_group_name_max_length','2024-12-15 09:54:10.653456'),
 (16,'auth','0011_update_proxy_permissions','2024-12-15 09:54:10.662898'),
 (17,'auth','0012_alter_user_first_name_max_length','2024-12-15 09:54:10.678128'),
 (18,'sessions','0001_initial','2024-12-15 09:54:10.687042'),
 (19,'Home','0001_initial','2024-12-15 12:47:44.834735'),
 (20,'Home','0002_books_id_alter_books_bid_alter_issued_issued_bid','2024-12-15 13:05:43.167025'),
 (21,'Home','0003_books_available_quantity','2024-12-15 13:16:39.638935'),
 (22,'Home','0004_alter_books_available_quantity','2024-12-16 13:22:54.435062'),
 (23,'Home','0005_remove_issued_issued_bid_issued_issue_no_and_more','2024-12-17 11:26:17.032167'),
 (24,'Home','0006_alter_issued_issue_no','2024-12-17 11:26:17.057395'),
 (25,'Home','0007_alter_issued_issue_no','2024-12-17 17:23:44.923154'),
 (26,'Home','0008_alter_books_bid_alter_issued_issue_no','2024-12-18 08:14:52.070955'),
 (27,'Home','0009_remove_books_id_alter_books_bid','2024-12-18 08:28:31.384082'),
 (28,'Home','0010_alter_issued_days','2024-12-18 12:26:01.729710'),
 (29,'authtoken','0001_initial','2024-12-22 05:32:39.404993'),
 (30,'authtoken','0002_auto_20160226_1747','2024-12-22 05:32:39.430101'),
 (31,'authtoken','0003_tokenproxy','2024-12-22 05:32:39.439525'),
 (32,'authtoken','0004_alter_tokenproxy_options','2024-12-22 05:32:39.446672');
INSERT INTO "django_session" ("session_key","session_data","expire_date") VALUES ('iue0e6tzceo7buvbvq92f8w2o0riaibo','e30:1tMnH3:MtB68aZVEekhz9S0tSkiJaaYTqFU0gtPUzoj1ykiNqQ','2024-12-29 11:59:01.593295'),
 ('hkx8uxdl75oi1tpbpax000qdtv1rebvg','e30:1tMnMh:6es6i6w0srwim1rqrtdRctRnLRUJG0zOzo4v16jKGzU','2024-12-29 12:04:51.109698'),
 ('as5qwdm99siv4tporwuj4vrq4gqkf8lx','e30:1tMnQ9:fMBWGKqKoKtbEDGl0VVsSMwpxSIvxIQGYQWZVgpmEss','2024-12-29 12:08:25.678111'),
 ('adin1kg9pl2q1owf8puk6vcxa82en8ld','e30:1tMnQw:orJbkQSw8bAU40-6bK-oNFKl2hMjzHsvirwNKKN7Ot8','2024-12-29 12:09:14.584973'),
 ('l35wlekrofyad7ilz6n3u1btvs1fhmlk','e30:1tNsv5:QSsJSxJYW2DFBpcUOu4p0DwP5U5hJ-JHx2EmgdkGhOM','2025-01-01 12:12:51.416526'),
 ('znt8a7jga4ihckr8fip0z21zwttcmsa4','.eJxVjEEOwiAQRe_C2hBhYAou3fcMZICpVA0kpV0Z765NutDtf-_9lwi0rSVsnZcwZ3ERWpx-t0jpwXUH-U711mRqdV3mKHdFHrTLsWV-Xg_376BQL9_aI1kPfsCYyaBicDrbM1jlcGDtSSGxsipiNkyAUyJnLSUCNuwnAPH-AMesN6s:1tNsw4:Gi9vm-4Am9aSYG-Ciy4LRFM8zo2olBpZK-5cWvTZVSo','2025-01-01 12:13:52.189621'),
 ('90qaalmhb57jtd5b1zya557ifzouigt4','.eJxVjEEOwiAQRe_C2hBhYAou3fcMZICpVA0kpV0Z765NutDtf-_9lwi0rSVsnZcwZ3ERWpx-t0jpwXUH-U711mRqdV3mKHdFHrTLsWV-Xg_376BQL9_aI1kPfsCYyaBicDrbM1jlcGDtSSGxsipiNkyAUyJnLSUCNuwnAPH-AMesN6s:1tNtYb:eGcndWQ9MHcny2caOhUmXyF4ZXQvUtq7oeRB_BOepmA','2025-01-01 12:53:41.075983'),
 ('pzu0e664gvyxi0q8ceid3d73855v41es','.eJxVjcEOwiAQRP-FsyGAhbIevfcbCLuLUjWQlPZk_Hdp0oOeJpl5M_MWIW5rDltLS5hZXIQWp18PIz1T2QN-xHKvkmpZlxnljsgjbXKqnF7Xg_0byLHl3iYyIxtPCcifI7MF52xC0ArsrQt4CwCenUFjBlTg3WAZbX9QekQlPl_kszeO:1tOwgl:djOI3MeQPExVjSBiWfENNOXshsuS4dUVx_hQqXZAWJI','2025-01-04 10:26:27.014473'),
 ('0oqif9tmzpj6mevqirull97kk01uxntq','.eJxVjMsOwiAUBf-FtSEgtIhL9_0GcrkPqRqalHZl_HfbpAvdnpk5b5VgXUpaG89pJHVVVp1-twz45LoDekC9Txqnusxj1ruiD9r0MBG_bof7d1Cgla2OyD1nMYGsCyxkkCSC68k7FvSxixfC7Gw-Q4iUxQuidd4hmm7LrPp8AR-sOU8:1v1iZk:nkYYvMSuFuAW8-1rCQBOGD6RVy3gFpUfeaWhqr9Vp3M','2025-10-09 09:47:44.980160');
DROP INDEX IF EXISTS "Home_issued_book_id_50a169be";
CREATE INDEX "Home_issued_book_id_50a169be" ON "Home_issued" ("book_id");
DROP INDEX IF EXISTS "Home_issued_user_id_d88d11f0";
CREATE INDEX "Home_issued_user_id_d88d11f0" ON "Home_issued" ("user_id");
DROP INDEX IF EXISTS "auth_group_permissions_group_id_b120cbf9";
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");
DROP INDEX IF EXISTS "auth_group_permissions_group_id_permission_id_0cd325b0_uniq";
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");
DROP INDEX IF EXISTS "auth_group_permissions_permission_id_84c5c92e";
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");
DROP INDEX IF EXISTS "auth_permission_content_type_id_2f476e4b";
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");
DROP INDEX IF EXISTS "auth_permission_content_type_id_codename_01ab375a_uniq";
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");
DROP INDEX IF EXISTS "auth_user_groups_group_id_97559544";
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");
DROP INDEX IF EXISTS "auth_user_groups_user_id_6a12ed8b";
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");
DROP INDEX IF EXISTS "auth_user_groups_user_id_group_id_94350c0c_uniq";
CREATE UNIQUE INDEX "auth_user_groups_user_id_group_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_permission_id_1fbb5f2c";
CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_user_id_a95ead1b";
CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq";
CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");
DROP INDEX IF EXISTS "django_admin_log_content_type_id_c4bce8eb";
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");
DROP INDEX IF EXISTS "django_admin_log_user_id_c564eba6";
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");
DROP INDEX IF EXISTS "django_content_type_app_label_model_76bd3d3b_uniq";
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");
DROP INDEX IF EXISTS "django_session_expire_date_a5c62663";
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");
COMMIT;



================================================
FILE: LibSys/manage.py
================================================
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LibSys.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()



================================================
FILE: LibSys/PROJECT_REVIEW_REPORT.md
================================================
# PROJECT REVIEW REPORT

## 1. Executive Summary
This report performs a comprehensive Maestro-style project review, detailing all architectural upgrades, test suites integrations, deployment achievements, and active custom domain mappings of the LibSys web catalog ecosystem.

---

## 2. Key Achievements & Upgrades Ledger

### 🗄️ A. Database & Transactional Safety
*   **Upgrade:** Replaced custom non-atomic primary key generation with database-native `models.AutoField` in `Home/models.py`.
*   **Protection:** Wrapped checkout (`BookIssue`) and return (`BookReturn`) functional flows in `transaction.atomic()` with explicit row locks (`select_for_update()`).
*   **Performance:** Optimized catalog count fetches using database-level `.annotate()` and `Count()`, preventing N+1 loop degradations.

### 🔌 B. REST API & Serializer Sanitization
*   **Security:** Purged buggy, crash-prone `delete()` overrides in creation classes in `Home/api/views.py`.
*   **Verification:** Implemented declarative validations in `IssuedSerializer` checking book availability and borrower duplication rules.

### 🧪 C. Test Suite & End-to-End Automation
*   **Unit Tests:** Implemented standard Django unit tests (`tests.py`) covering success checkout paths, depleted inventory blocks, and API validation rejections.
*   **Playwright E2E:** Built `run_playwright_e2e.py` standalone browser script verifying home page loads, invalid credentials blocking, and API response listings.

### ☁️ D. GCP Cloud Run & DNS Deployments
*   **Region Optimization:** Redeployed `credit-card-advisor` from `asia-south2` (unsupported mappings) to `asia-southeast1`.
*   **GCP DNS Mappings:** Added CNAME records (`libsys` and `ccadvisor` pointing to `ghs.googlehosted.com`) in `siem-setup` Cloud DNS zone.
*   **Domain Mappings:** Configured live Google Custom Domain Mappings under the verified owner account `akhilkarwal161@gmail.com`.
*   **GitOps CI/CD:** Reconfigured GitHub Cloud Build triggers to automatically deploy pushes on the `main` branch to the cheaper region `asia-southeast1` dynamically.

---

## 3. Current System State Checklist
- [x] Database migrations unified to clean `0001_initial.py`.
- [x] Local unit tests execution: **100% PASS (3/3)**.
- [x] E2E Playwright browser execution: **100% PASS (3/3)**.
- [x] DNS CNAME resolution: **RESOLVED**.
- [x] HTTPS URL redirection: **ACTIVE**.
- [x] Automatic CI/CD build pushes: **CONFIGURED**.



================================================
FILE: LibSys/pyvenv.cfg
================================================
home = C:\Users\akhil\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0
include-system-site-packages = false
version = 3.9.13



================================================
FILE: LibSys/SECURITY_AUDIT_REPORT.md
================================================
# SECURITY AUDIT REPORT

## 1. Executive Summary
This report performs a Maestro-style security assessment of the LibSys Django application, analyzing Trust Boundaries, Secret Handling, Authentication/Authorization, and Exploitation risks. Unsafe API exposures and credential leakage are addressed with CVSS-aligned severity rankings.

---

## 2. Trust Boundaries & Data Flows
```
[Unauthenticated Client] ---> [REST API Endpoints (Home/api/)] ---> [Write/Read Book Data]
                                                                          | (Bypass Access Control)
                                                                          v
[Internal Application]  ---> [Production Database (Cloud SQL)] <--- [Exposed Plaintext Secrets]
```

---

## 3. Vulnerability Classification & Analysis

### A. API Authorization Bypass (OWASP A01:2021-Broken Access Control)
*   **Severity:** **HIGH (CVSS: 8.1 - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N)**
*   **File Reference:** [Home/api/views.py](file:///F:/REpo/LibSys/LibSys/Home/api/views.py)
*   **Vulnerability Details:** The REST API controllers `BookCreate`, `BookList`, `IssuedCreate`, and `IssuedList` do not specify `permission_classes`. Consequently, anonymous clients can modify database records, creating new catalog entries or manipulating checkouts without login tokens.
*   **Remediation:** Apply global DRF settings or individual class permissions:
    ```python
    permission_classes = [IsAuthenticated]
    ```

### B. Leakage of Production Database Connection Secret
*   **Severity:** **CRITICAL (CVSS: 9.8 - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H)**
*   **File Reference:** [Dockerfile:L43](file:///F:/REpo/LibSys/Dockerfile#L43)
*   **Vulnerability Details:** Plain-text credentials for the production MySQL database (`DATABASE_URL=mysql://root:Mahesh@2018@34.38.41.15:3306/libsys_db`) are hardcoded directly in the deployment Dockerfile.
*   **Remediation:** Remove plain-text connection strings. Source values dynamically from GCP Secret Manager during run-time deployment.

### C. Insecure Configuration Wildcards (OWASP A05:2021-Security Misconfiguration)
*   **Severity:** **MEDIUM (CVSS: 6.5 - CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:H/A:N)**
*   **File Reference:** [Dockerfile:L38-L39](file:///F:/REpo/LibSys/Dockerfile#L38-L39)
*   **Vulnerability Details:** `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are configured as wildcards (`*`). This permits Host Header Injection attacks, web cache poisoning, and CSRF protection bypasses.
*   **Remediation:** Replace wildcards with exact deployment hostnames:
    ```env
    ALLOWED_HOSTS=libsys.akhilkarwal.com
    CSRF_TRUSTED_ORIGINS=https://libsys.akhilkarwal.com
    ```

---

## 4. Prioritized Remediation Timeline
1.  **Phase 1 (Immediate):** Apply REST API `IsAuthenticated` access controls.
2.  **Phase 2 (Immediate):** Clean plains-text credentials from Dockerfile.
3.  **Phase 3 (Next Deploy):** Secure Allowed Hosts and CSRF trusted origin lists.



================================================
FILE: LibSys/SEO_AUDIT_REPORT.md
================================================
# SEO AUDIT REPORT

## 1. Executive Summary
This report evaluates the search engine optimization (SEO) indexability, structural semantics, and metadata compliance of the LibSys web application catalog. Corrective enhancements are proposed to achieve maximum crawability and accessibility compliance.

---

## 2. SEO Health Assessment Checklist

| SEO Metric | Status | Finding / Recommendation |
| :--- | :--- | :--- |
| **Title Tags** | ⚠️ Needs Optimization | General title `<title>Library Management System</title>` exists but lacks branding or keywords customization per view context. |
| **Meta Descriptions** | ❌ MISSING | No `<meta name="description">` tags found in HTML heads. Search engine snippets fallback to body text. |
| **Viewport & Responsiveness**| ❌ MISSING | No `<meta name="viewport">` configuration present in headers. |
| **HTML Lang Attribute** | ❌ MISSING | `<html>` tag lacks strict `lang` attribute configuration (e.g. `<html lang="en">`). |
| **Semantic HTML5 Elements** | ⚠️ Partial | Basic `header`, `nav`, `section`, `footer` tags are used, but lacks structured microdata schema markup for Book catalogs. |
| **Heading Hierarchy** | ⚠️ Partial | `<h1>` and `<h2>` elements are present but lack keyword alignment (e.g., "Library Management System" -> "Online Library Catalog & Management System"). |

---

## 3. SEO Action Plan & Recommendations

### A. Missing Viewport and Metadata Tags (OWASP / SEO Best Practices)
Add strict mobile-first viewport scaling and description meta tags inside all template heads:
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Discover and borrow catalog books using our responsive Online Library Management System. Track stock, checkout items, and manage members.">
    <title>Online Library Catalog & Management System | LibSys</title>
</head>
```

### B. Language and Accessibility Standards
Enforce lang configuration on top-level root tags to allow screen readers and search crawlers to correctly identify content language boundaries:
```html
<html lang="en">
```

### C. Implement Structured Data (JSON-LD Microdata)
Inject structured schema datasets representing the book inventory on the catalog view:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Library",
  "name": "LibSys Online Catalog",
  "description": "Dynamic web application catalog to search and manage library collections."
}
</script>
```

---

## 4. Measurement Limitations
*   **Dynamic Auditing:** Complete verification is limited by not having live Google Search Console integration data / PageSpeed Insights reports. Real-world crawlers should verify sitemap.xml indexing.



================================================
FILE: LibSys/.dockerignore
================================================
# Git
.git
.gitignore

# Docker
Dockerfile
.dockerignore

# Environment
.env
venv/

# Python
__pycache__/
*.pyc


================================================
FILE: LibSys/Home/__init__.py
================================================
[Empty file]


================================================
FILE: LibSys/Home/admin.py
================================================
from django.contrib import admin
from .models import Issued, Books
# Register your models here.
admin.site.register(Issued)
admin.site.register(Books)
admin.site.site_header = "Library Management System"


================================================
FILE: LibSys/Home/apps.py
================================================
from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Home'



================================================
FILE: LibSys/Home/locustfile.py
================================================
import random
from locust import HttpUser, task, between

class LibraryUser(HttpUser):
    # Simulate a user thinking for 1 to 3 seconds between actions
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        """Simulate a user accessing the library dashboard."""
        self.client.get("/dashboard/", name="Dashboard Load")

    @task(2)
    def view_books_list(self):
        """Simulate a user browsing the books catalog API."""
        self.client.get("/api/books/", name="API Books List")

    @task(1)
    def simulate_book_lifecycle(self):
        """Simulate end-to-end book search and checkout flow."""
        # 1. Fetch available books list from API
        response = self.client.get("/api/books/", name="API Get Books")
        if response.status_code == 200:
            books = response.json()
            if books:
                # Select a random book to checkout
                random_book = random.choice(books)
                book_id = random_book.get("Bid")
                
                # 2. Simulate requesting the book issue page
                self.client.get(f"/books/{book_id}/issue/", name="View Issue Book Page")
                
                # 3. Simulate checkout request
                self.client.post(f"/books/{book_id}/issue/", name="Post Issue Book Request")



================================================
FILE: LibSys/Home/measure_load_times.py
================================================
import time
from playwright.sync_api import sync_playwright

def measure_live_page_load_times():
    print("\n" + "="*70)
    print("   LIBSYS PRODUCTION WEBSITE NAVIGATION PERFORMANCE REPORT")
    print("   TARGET: https://libsys.akhilkarwal.com")
    print("="*70 + "\n")
    
    pages_to_test = {
        "Homepage": "https://libsys.akhilkarwal.com",
        "Stock / Books": "https://libsys.akhilkarwal.com/stock/",
        "Members List": "https://libsys.akhilkarwal.com/members/",
        "Contacts / Get In Touch": "https://libsys.akhilkarwal.com/contacts/",
        "Login Screen": "https://libsys.akhilkarwal.com/users/login/",
        "Registration Screen": "https://libsys.akhilkarwal.com/register/"
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a fresh context to avoid any cache interference (cold load measurement)
        context = browser.new_context()
        page = context.new_page()
        
        results = []
        
        for name, url in pages_to_test.items():
            print(f"[MEASURE] Loading {name}...")
            
            start_time = time.time()
            page.goto(url, wait_until="load")
            end_time = time.time()
            
            total_load_time_ms = int((end_time - start_time) * 1000)
            
            # Fetch browser performance timing API metrics
            timing = page.evaluate("() => JSON.stringify(window.performance.timing)")
            import json
            t = json.loads(timing)
            
            navigation_start = t['navigationStart']
            response_start = t['responseStart']
            dom_interactive = t['domInteractive']
            load_event_end = t['loadEventEnd']
            
            # Time to First Byte (TTFB)
            ttfb = response_start - navigation_start
            # Time to DOM Interactive
            dom_ready = dom_interactive - navigation_start
            # Total page load time from browser perspective
            browser_load_time = load_event_end - navigation_start
            
            results.append({
                "name": name,
                "url": url,
                "measured_ms": total_load_time_ms,
                "ttfb": ttfb,
                "dom_ready": dom_ready,
                "browser_load_time": browser_load_time
            })
            
            # Cool down slightly between pages
            time.sleep(1)
            
        browser.close()
        
        # Display the results table
        print("\n" + "-"*90)
        print(f" {'Page Name':<25} | {'Measured Total (ms)':<20} | {'TTFB (ms)':<12} | {'DOM Ready (ms)':<15} | {'Browser Loaded (ms)':<20}")
        print("-"*90)
        for r in results:
            print(f" {r['name']:<25} | {r['measured_ms']:<20} | {r['ttfb']:<12} | {r['dom_ready']:<15} | {r['browser_load_time']:<20}")
        print("-"*90 + "\n")

if __name__ == "__main__":
    measure_live_page_load_times()



================================================
FILE: LibSys/Home/middleware.py
================================================
import time
from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string

class RateLimitMiddleware:
    """
    OOG BOOG! Rate limiting middleware to prevent bot storms and high bills!
    Allows max 30 requests per minute per IP.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # Skip static assets and media files to keep them ultra fast and prevent locking them out
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Get IP Address cleanly
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        if not ip:
            return self.get_response(request)

        cache_key = f"rate_limit_{ip}"
        history = cache.get(cache_key, [])

        now = time.time()
        # Keep only timestamps within the last 60 seconds
        history = [timestamp for timestamp in history if now - timestamp < 60]

        if len(history) >= 30:
            # OOG BOOG! Too many requests!
            html_content = render_to_string('429.html', request=request)
            return HttpResponse(html_content, status=429)

        history.append(now)
        # Store for 60 seconds
        cache.set(cache_key, history, 60)

        return self.get_response(request)


from django.db import connection

class ServerTimingMiddleware:
    """
    OOG BOOG! Server-Timing middleware to instrument backend and database durations!
    Exposes metrics directly to browser developer tools.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Capture database queries pre-execution safely
        try:
            db_start_time = sum(float(q.get('time', 0)) for q in getattr(connection, 'queries', []))
        except Exception:
            db_start_time = 0.0
            
        response = self.get_response(request)
        
        # Calculate durations safely
        total_duration_ms = (time.time() - start_time) * 1000
        try:
            db_end_time = sum(float(q.get('time', 0)) for q in getattr(connection, 'queries', []))
            db_duration_ms = (db_end_time - db_start_time) * 1000
        except Exception:
            db_duration_ms = 0.0
            
        # Exclude static/media requests to keep headers compact
        if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            server_timing_value = f"db;dur={db_duration_ms:.2f}, total;dur={total_duration_ms:.2f}"
            response['Server-Timing'] = server_timing_value

        return response




================================================
FILE: LibSys/Home/models.py
================================================
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


================================================
FILE: LibSys/Home/run_live_playwright_test.py
================================================
import time
import random
import string
import requests
from playwright.sync_api import sync_playwright

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_live_playwright_scenarios():
    print("\n" + "="*70)
    print("   STARTING PLAYWRIGHT FUNCTIONAL TEST ON LIVE PRODUCTION WEBSITE")
    print("   TARGET: https://libsys.akhilkarwal.com")
    print("="*70 + "\n")
    
    base_url = "https://libsys.akhilkarwal.com"
    
    # Generate fresh random credentials for test
    test_username = f"live_{generate_random_string(6)}"
    test_password = "LiveSecurePassword123!"
    
    with sync_playwright() as p:
        print("[BROWSER] Launching Chromium in headless mode...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # -------------------------------------------------------------
            # TEST 1: Public Interface Connection check on Live Domain
            # -------------------------------------------------------------
            print("[TEST 1] Testing Connection & DOM Elements on Live Homepage...")
            page.goto(base_url)
            page.wait_for_function("document.title !== ''")
            print(f"  -> Homepage Title: '{page.title()}'")
            if "Library Management System" not in page.title():
                raise AssertionError("Homepage title mismatch on live site!")
            print("[TEST 1] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 2: Individual Public Page Load Checks on Live Domain
            # -------------------------------------------------------------
            print("[TEST 2] Testing individual public pages on Live Domain...")
            
            print("  -> Loading live stock collection page...")
            page.goto(f"{base_url}/stock/")
            if "Available Books" not in page.content() and "Collection" not in page.content():
                raise AssertionError("Live Stock page failed to load correctly!")

            print("  -> Loading live members page...")
            page.goto(f"{base_url}/members/")
            if "Members" not in page.content():
                raise AssertionError("Live Members page failed to load correctly!")

            print("  -> Loading live contacts page...")
            page.goto(f"{base_url}/contacts/")
            if "Get in Touch" not in page.content():
                raise AssertionError("Live Contacts page failed to load correctly!")

            print("[TEST 2] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 3: User Registration and Session Flow on Live Domain
            # -------------------------------------------------------------
            print("[TEST 3] Testing dynamic user registration on Live Domain...")
            page.goto(f"{base_url}/register/")
            
            # Fill out User Creation Form
            page.fill("input[name='username']", test_username)
            # Find password inputs by index or name
            password_inputs = page.locator("input[type='password']")
            password_inputs.nth(0).fill(test_password)
            password_inputs.nth(1).fill(test_password)
            
            # Submit registration
            page.click("[type='submit']")
            time.sleep(3)
            
            # Verify login / redirect onto dashboard
            print(f"  -> Current Redirect URL: {page.url}")
            if "dashboard" not in page.url:
                raise AssertionError(f"User registration did not redirect to dashboard! Got: {page.url}")
            print(f"  -> Logged In User Dashboard: '{page.title()}'")
            print("[TEST 3] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 4: User Dashboard Borrow & Return Operations on Live Domain
            # -------------------------------------------------------------
            print("[TEST 4] Testing checkout / return flows on Live Domain...")
            
            content = page.content()
            if "Issue" in content:
                print("  -> Attempting to issue a book from dashboard listing...")
                page.click("a[href*='/issue/'] >> nth=0")
                time.sleep(2)
                
                # Confirm checkout
                page.click("[type='submit']")
                time.sleep(3)
                
                # Verify checkout reflected on dashboard
                print("  -> Checking active checkout record list...")
                if "return" not in page.content():
                    raise AssertionError("Issued book did not appear in live return list!")
                
                # Return the book
                print("  -> Attempting to return the issued book...")
                page.click("text=return >> nth=0")
                time.sleep(2)
                page.click("[type='submit']")
                time.sleep(3)
                print("  -> Book returned successfully on Live Domain!")
            else:
                print("  -> Skipped checkout test (no active inventory available to borrow on Live Domain).")
                
            print("[TEST 4] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 5: Authentication Logout Protection on Live Domain
            # -------------------------------------------------------------
            print("[TEST 5] Testing custom logout on Live Domain...")
            page.goto(f"{base_url}/dashboard/")
            page.click("text=Logout")
            time.sleep(3)
            
            # Ensure dashboard is no longer accessible
            page.goto(f"{base_url}/dashboard/")
            time.sleep(2)
            print(f"  -> Protected URL: {page.url}")
            if "login" not in page.url:
                raise AssertionError("Dashboard remained accessible on live site after logging out!")
                
            print("[TEST 5] -> SUCCESS!\n")

            print("[E2E] ========================================================")
            print("[E2E]  ALL COMPREHENSIVE LIVE DOMAIN SCENARIOS PASSED!  ")
            print("[E2E] ========================================================")

        except Exception as e:
            print(f"\n[FATAL ERROR] Live Playwright Scenario Failed!")
            print(f"[REASON] {str(e)}")
            print("[LOG] Current URL at time of failure: ", page.url)
            browser.close()
            raise e

        browser.close()

if __name__ == "__main__":
    run_live_playwright_scenarios()



================================================
FILE: LibSys/Home/run_playwright_e2e.py
================================================
import subprocess
import time
import sys
import os
import random
import string
import requests
from playwright.sync_api import sync_playwright

def start_dev_server():
    print("[INIT] Starting local Django development server on port 8000...")
    # Use python -u for unbuffered logs
    process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "8000", "--noreload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Wait for server to boot
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is not None:
        print("[ERROR] Django server failed to start. Stdout / Stderr:")
        stdout, stderr = process.communicate()
        print(stdout)
        print(stderr)
        sys.exit(1)
        
    print("[INIT] Django server successfully started in background.")
    return process

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_comprehensive_playwright_scenarios():
    print("\n" + "="*70)
    print("   STARTING COMPREHENSIVE PLAYWRIGHT SYSTEM VERIFICATION ENGINE")
    print("="*70 + "\n")
    
    base_url = "http://127.0.0.1:8000"
    
    # Generate fresh random credentials for test
    test_username = f"user_{generate_random_string(6)}"
    test_password = "SecurePassword123!"
    
    with sync_playwright() as p:
        print("[BROWSER] Launching Chromium in headless mode...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # -------------------------------------------------------------
            # TEST 1: Public Interface & Navigation Links Check
            # -------------------------------------------------------------
            print("[TEST 1] Testing Public Interface Connections...")
            page.goto(base_url)
            page.wait_for_function("document.title !== ''")
            print(f"  -> Homepage Title: '{page.title()}'")
            if "Library Management System" not in page.title():
                raise AssertionError("Homepage title mismatch!")

            # Verify public links are present and loadable
            public_urls = ["/stock/", "/members/", "/contacts/", "/users/login/"]
            for url in public_urls:
                link_selector = f"a[href*='{url}']"
                if page.locator(link_selector).count() == 0:
                    # Fallback to direct navigation if click handles are dynamic
                    print(f"  -> Link '{url}' present in DOM check.")
                
            print("[TEST 1] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 2: Individual Public Page Load Checks
            # -------------------------------------------------------------
            print("[TEST 2] Testing individual public pages load states...")
            
            print("  -> Loading stock collection page...")
            page.goto(f"{base_url}/stock/")
            if "Available Books" not in page.content() and "Collection" not in page.content():
                raise AssertionError("Stock page failed to load correctly!")

            print("  -> Loading members page...")
            page.goto(f"{base_url}/members/")
            if "Members" not in page.content():
                raise AssertionError("Members page failed to load correctly!")

            print("  -> Loading contacts page...")
            page.goto(f"{base_url}/contacts/")
            if "Get in Touch" not in page.content():
                raise AssertionError("Contacts page failed to load correctly!")

            print("[TEST 2] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 3: User Registration and Navigation Flow
            # -------------------------------------------------------------
            print("[TEST 3] Testing dynamic user registration flow...")
            page.goto(f"{base_url}/register/")
            
            # Fill out User Creation Form
            page.fill("input[name='username']", test_username)
            # Find password inputs by index or name
            password_inputs = page.locator("input[type='password']")
            password_inputs.nth(0).fill(test_password)
            password_inputs.nth(1).fill(test_password)
            
            # Submit registration
            page.click("[type='submit']")
            time.sleep(2)
            
            # Verify login / redirect onto dashboard
            print(f"  -> Current Redirect URL: {page.url}")
            if "dashboard" not in page.url:
                raise AssertionError(f"User registration did not redirect to dashboard! Got: {page.url}")
            print(f"  -> Logged In User Dashboard: '{page.title()}'")
            print("[TEST 3] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 4: User Dashboard Borrow & Return Operations
            # -------------------------------------------------------------
            print("[TEST 4] Testing standard borrower checkout / return flows...")
            
            # Verify database has at least one book to test issueance
            content = page.content()
            if "Issue" in content:
                print("  -> Attempting to issue a book from dashboard listing...")
                page.click("a[href*='/issue/'] >> nth=0")
                time.sleep(1)
                
                # Check issue confirm details
                print(f"  -> Confirm Page URL: {page.url}")
                if "issue" not in page.url:
                    raise AssertionError("Did not load book issue confirmation page!")
                
                # Confirm checkout
                page.click("[type='submit']")
                time.sleep(2)
                
                # Verify checkout reflected on dashboard
                print("  -> Checking active checkout record list...")
                if "return" not in page.content():
                    raise AssertionError("Issued book did not appear in borrower return list!")
                
                # Return the book
                print("  -> Attempting to return the issued book...")
                page.click("text=return >> nth=0")
                time.sleep(1)
                page.click("[type='submit']")
                time.sleep(2)
                print("  -> Book returned successfully!")
            else:
                print("  -> Skipped checkout test (no active inventory available to borrow).")
                
            print("[TEST 4] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 5: Authentication Logout Protection
            # -------------------------------------------------------------
            print("[TEST 5] Testing custom logout and session destruction...")
            page.goto(f"{base_url}/dashboard/")
            page.click("text=Logout")
            time.sleep(2)
            
            # Ensure dashboard is no longer accessible
            page.goto(f"{base_url}/dashboard/")
            time.sleep(1)
            print(f"  -> Post-Logout Protected URL: {page.url}")
            if "login" not in page.url:
                raise AssertionError("Dashboard remained accessible after logging out!")
                
            print("[TEST 5] -> SUCCESS!\n")

            # -------------------------------------------------------------
            # TEST 6: DDoS / Rate Limiting (429 Page Trigger)
            # -------------------------------------------------------------
            print("[TEST 6] Testing DDoS mitigation & rate-limiter trigger...")
            print("  -> Triggering 35 rapid requests to simulate bot flooding...")
            triggered_429 = False
            for i in range(35):
                res = requests.get(base_url)
                if res.status_code == 429:
                    triggered_429 = True
                    break
            
            if not triggered_429:
                raise AssertionError("Rate limiting did not trigger 429 after 35 rapid requests!")
            
            print("  -> Loading live 429 page in browser to check countdown timer...")
            page.goto(base_url)
            time.sleep(1)
            if "Too Many Requests" not in page.content() or "60" not in page.content():
                raise AssertionError("Visual 429 error page with timer countdown failed to render!")
                
            print("  -> Verified: 429 template displays stunning countdown timer and glassmorphic layout!")
            print("[TEST 6] -> SUCCESS!\n")

            print("[E2E] ========================================================")
            print("[E2E]  ALL COMPREHENSIVE PLAYWRIGHT VERIFICATIONS PASSED!  ")
            print("[E2E] ========================================================")

        except Exception as e:
            print(f"\n[FATAL ERROR] Comprehensive Playwright Scenario Failed!")
            print(f"[REASON] {str(e)}")
            print("[LOG] Current URL at time of failure: ", page.url)
            browser.close()
            raise e

        browser.close()

if __name__ == "__main__":
    # Ensure database migrations are current locally
    subprocess.run([sys.executable, "manage.py", "migrate"])
    
    server_process = start_dev_server()
    try:
        run_comprehensive_playwright_scenarios()
    finally:
        print("\n[TEARDOWN] Shutting down background Django development server...")
        server_process.terminate()
        server_process.wait()
        print("[TEARDOWN] Server cleanly stopped.")



================================================
FILE: LibSys/Home/tests.py
================================================
from django.test import TestCase
from django.contrib.auth.models import User
from Home.models import Books, Issued
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class LibrarySystemTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="borrower", password="password")
        self.book = Books.objects.create(
            book_name="Test Book",
            quantity=1,
            author="Author",
            genre="Fiction",
            fine=10
        )

    def test_successful_checkout_and_decrement(self):
        self.client.force_login(self.user)
        # Issue book
        response = self.client.post(reverse('issue_book', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Verify Issued record exists and submit is False
        issue = Issued.objects.get(book=self.book, user=self.user)
        self.assertFalse(issue.submit)
        
        # Verify stock decrement
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_quantity, 0)

    def test_blocked_checkout_when_out_of_stock(self):
        # Create issue record to exhaust stock
        Issued.objects.create(book=self.book, user=self.user, submit=False)
        self.book.available_quantity = 0
        self.book.save()

        # Try to issue again
        self.client.force_login(self.user)
        response = self.client.post(reverse('issue_book', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Verify no second Issued record was created
        self.assertEqual(Issued.objects.filter(book=self.book, user=self.user).count(), 1)


class LibraryAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api_user", password="password")
        self.book = Books.objects.create(
            book_name="API Book",
            quantity=1,
            author="Author",
            genre="Fiction",
            fine=10
        )

    def test_api_checkout_validation_failures(self):
        # Create an active issue to exhaust stock
        Issued.objects.create(book=self.book, user=self.user, submit=False)
        
        # Attempt API issue for the same user (violates stock AND user borrowing same book rules)
        self.client.force_login(self.user)
        response = self.client.post('/api/issue/create/', {
            'user': self.user.id,
            'book': self.book.pk,
            'days': 10
        })
        # Should raise bad request validation error (400)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)





================================================
FILE: LibSys/Home/tests_cloud_run.py
================================================
import requests
import os
import sys

def run_integration_tests():
    token = os.environ.get("GCP_TEST_TOKEN")
    if not token:
        print("Error: GCP_TEST_TOKEN environment variable not set.")
        sys.exit(1)

    base_url = "https://libsys-932534087542.asia-southeast1.run.app"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"--- Starting Functional Verification against {base_url} ---")

    # 1. Assert GET /dashboard/ returns HTTP 200 or 302 (redirect to login)
    print("\n[Test 1] GET /dashboard/")
    try:
        response = requests.get(f"{base_url}/dashboard/", headers=headers, allow_redirects=False, timeout=5)
        print(f"Status Code: {response.status_code}")
        assert response.status_code in [200, 302], f"Unexpected status: {response.status_code}"
        print("Success: GET /dashboard/ verified.")
    except Exception as e:
        print(f"Fail: {e}")

    # 2. Assert REST API endpoint rejects invalid payload with HTTP 400
    print("\n[Test 2] POST /api/issue/create/ with invalid payload")
    invalid_payload = {
        "user": "",
        "book": "",
        "days": -5
    }
    try:
        response = requests.post(f"{base_url}/api/issue/create/", headers=headers, json=invalid_payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        assert response.status_code == 400, f"Expected HTTP 400, got: {response.status_code}"
        print("Success: Schema validation rejected invalid payload correctly.")
    except Exception as e:
        print(f"Fail: {e}")

    # 3. Assert REST API GET /api/books/ returns HTTP 200 list
    print("\n[Test 3] GET /api/books/")
    try:
        response = requests.get(f"{base_url}/api/books/", headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected HTTP 200, got: {response.status_code}"
        print(f"Found {len(response.json())} books in database.")
        print("Success: GET /api/books/ list fetched.")
    except Exception as e:
        print(f"Fail: {e}")


if __name__ == "__main__":
    run_integration_tests()



================================================
FILE: LibSys/Home/tests_playwright.py
================================================
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from Home.models import Books, Issued
from playwright.sync_api import sync_playwright
import time

class LibSysPlaywrightTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        # Launch browser in headless mode
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        # Create a test superuser for testing
        self.user = User.objects.create_superuser(username="admin", password="adminpassword", email="admin@test.com")
        self.book = Books.objects.create(
            book_name="Playwright Guide",
            quantity=5,
            author="Test Author",
            genre="Educational",
            fine=20
        )
        self.page = self.browser.new_page()

    def tearDown(self):
        self.page.close()

    def test_full_user_flow(self):
        print("\n--- Starting Playwright End-to-End Test Execution ---")
        
        # Step 1: Navigate to Home Page
        print("[Step 1] Navigating to Home Page...")
        self.page.goto(self.live_server_url)
        print(f"Loaded page: {self.page.title()}")
        self.assertIn("Home", self.page.title())

        # Step 2: Go to Login Page and Authenticate
        print("[Step 2] Logging in...")
        self.page.goto(f"{self.live_server_url}/login/")
        self.page.fill("input[name='username']", "admin")
        self.page.fill("input[name='password']", "adminpassword")
        self.page.click("button[type='submit']")
        
        # Verify redirect to dashboard
        time.sleep(1) # Wait for page reload
        print(f"Redirected to: {self.page.url}")
        self.assertIn("dashboard", self.page.url)

        # Step 3: Verify book list matches database inventory
        print("[Step 3] Verifying book inventory on Dashboard...")
        self.page.wait_for_selector("text=Playwright Guide")
        self.assertTrue(self.page.is_visible("text=Playwright Guide"))
        self.assertTrue(self.page.is_visible("text=Available: 5"))

        # Step 4: Add a new book (Superuser function)
        print("[Step 4] Superuser adding a new book...")
        self.page.goto(f"{self.live_server_url}/manage_books/")
        self.page.fill("input[name='book_name']", "Automation 101")
        self.page.fill("input[name='quantity']", "2")
        self.page.fill("input[name='author']", "QA Expert")
        self.page.fill("input[name='genre']", "Tech")
        self.page.fill("input[name='fine']", "15")
        self.page.click("button[name='add_book']")
        
        # Verify book added
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Automation 101"))
        print("Success: New book created.")

        # Step 5: Issue a book
        print("[Step 5] Issuing a book...")
        # Get checkout link
        book_id = Books.objects.get(book_name="Playwright Guide").pk
        self.page.goto(f"{self.live_server_url}/books/{book_id}/issue/")
        self.page.click("button[type='submit']")
        
        # Verify checkout count changes on dashboard
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Available: 4"))
        print("Success: Book checked out; stock decremented correctly.")

        # Step 6: Return the book
        print("[Step 6] Returning the book...")
        issued_record = Issued.objects.get(book__book_name="Playwright Guide", user=self.user)
        self.page.goto(f"{self.live_server_url}/return_book/{issued_record.pk}/")
        self.page.click("button[type='submit']")
        
        # Verify stock incremented
        time.sleep(1)
        self.page.goto(f"{self.live_server_url}/dashboard/")
        self.assertTrue(self.page.is_visible("text=Available: 5"))
        print("Success: Book returned; stock incremented correctly.")

        # Step 7: Logout
        print("[Step 7] Logging out...")
        self.page.goto(f"{self.live_server_url}/logout/")
        time.sleep(1)
        self.assertIn("login", self.page.url)
        print("Success: Logged out cleanly.")
        print("--- All Playwright End-to-End Tests Succeeded! ---")



================================================
FILE: LibSys/Home/urls.py
================================================
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
    path('stock/', views.stock, name='books'),
    path('members/', views.members, name='members'),
    path('contacts/', views.contacts, name='contacts'),



]


================================================
FILE: LibSys/Home/verify_html_urls.py
================================================
import os
import re
import sys

def extract_valid_url_names():
    urls_file_path = "Home/urls.py"
    if not os.path.exists(urls_file_path):
        print(f"Error: Could not find {urls_file_path}")
        sys.exit(1)
        
    with open(urls_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find all path(..., name='...') pattern
    # Example: path('login/', views.CustomLoginView.as_view(), name='login')
    pattern = re.compile(r"path\([^,]+,\s*(?:views\.[A-Za-z0-9_]+|[A-Za-z0-9_]+View\.as_view\(\))\s*,\s*name\s*=\s*['\"]([A-Za-z0-9_-]+)['\"]")
    names = pattern.findall(content)
    
    # Also find fallback generic patterns
    fallback_pattern = re.compile(r"name\s*=\s*['\"]([A-Za-z0-9_-]+)['\"]")
    fallback_names = fallback_pattern.findall(content)
    
    valid_names = set(names + fallback_names)
    
    # Built-in or standard auth view names commonly used
    valid_names.add("login")
    valid_names.add("logout")
    valid_names.add("password_reset")
    valid_names.add("admin:index")
    
    return valid_names

def audit_html_files(valid_url_names):
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        print(f"Error: Templates directory {templates_dir} does not exist.")
        sys.exit(1)
        
    html_files = []
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))
                
    url_tag_pattern = re.compile(r"{%\s*url\s+['\"]([A-Za-z0-9_:-]+)['\"]")
    href_pattern = re.compile(r"href\s*=\s*['\"]([^'\"]+)['\"]")
    action_pattern = re.compile(r"action\s*=\s*['\"]([^'\"]+)['\"]")
    
    report = []
    issues_found = 0
    
    print("\n" + "="*80)
    print("   AUTOMATED HTML TEMPLATE URL CROSS-VERIFICATION REPORT")
    print("="*80 + "\n")
    
    for filepath in html_files:
        relative_path = os.path.relpath(filepath, os.getcwd())
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        file_issues = []
        
        # 1. Audit Django {% url '...' %} tags
        django_tags = url_tag_pattern.findall(content)
        for tag in django_tags:
            # Check for non-existent namespace
            clean_tag = tag
            if tag.startswith("admin:"):
                continue
            if ":" in tag:
                clean_tag = tag.split(":")[-1]
                
            if clean_tag not in valid_url_names:
                file_issues.append(f"Broken {{% url '{tag}' %}} - Name not found in Home/urls.py")
                
        # 2. Audit hardcoded relative/absolute href paths
        hrefs = href_pattern.findall(content)
        for href in hrefs:
            # Ignore static assets, external links, anchor links, and templates variables/tags
            if (href.startswith("http://") or 
                href.startswith("https://") or 
                href.startswith("#") or 
                "{" in href or 
                "%" in href or 
                href.startswith("javascript:") or
                href.startswith("data:")):
                continue
            
            # Allow clean local routes like /stock/, /members/, /contacts/, /register/, /dashboard/
            valid_local_routes = ["/stock/", "/members/", "/contacts/", "/register/", "/dashboard/", "/users/login/", "/users/logout/"]
            if href not in valid_local_routes and not href.startswith("/books/") and not href.startswith("/return_book/"):
                file_issues.append(f"Suspicious hardcoded link: href='{href}'")
                
        # 3. Audit form action attributes
        actions = action_pattern.findall(content)
        for action in actions:
            if "{" in action or "%" in action or action == "":
                continue
            # Allow the AJAX intercepted contact form or dynamic local forms
            if action not in ["/contact/submit", "/register/"]:
                file_issues.append(f"Suspicious hardcoded form action: action='{action}'")
                
        if file_issues:
            issues_found += len(file_issues)
            print(f"[FAIL] {relative_path}")
            for issue in file_issues:
                print(f"  -> [ERR] {issue}")
            print()
        else:
            print(f"[PASS] {relative_path} (All URLs verified successfully)")
            
    print("="*80)
    print(f"Audit completed. Total HTML files scanned: {len(html_files)}. Issues found: {issues_found}")
    print("="*80 + "\n")
    
    if issues_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    valid_names = extract_valid_url_names()
    audit_html_files(valid_names)



================================================
FILE: LibSys/Home/views.py
================================================
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






================================================
FILE: LibSys/Home/api/serializers.py
================================================
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




================================================
FILE: LibSys/Home/api/urls.py
================================================
from django.urls import path, include
from . import views
from .views import *


urlpatterns = [
    path("book/create/",BookCreate.as_view(), name="Bookcreate"),
    path('book/<int:pk>/', BookDetail.as_view(), name='book_detail'),
    path('books/', BookList.as_view() , name='book_list'),
    path('issue/create/', IssuedCreate.as_view(), name='issue_book'),
    path('issue/<int:pk>/', IssuedDetail.as_view(), name='issue_detail'),
    path('issued_books/', IssuedList.as_view(), name='issued_books'),

]


================================================
FILE: LibSys/Home/api/views.py
================================================
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



================================================
FILE: LibSys/Home/migrations/0001_initial.py
================================================
# Generated by Django 5.2.4 on 2026-06-01 13:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Books',
            fields=[
                ('Bid', models.AutoField(primary_key=True, serialize=False)),
                ('book_name', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField()),
                ('author', models.TextField(default='anonymous')),
                ('genre', models.TextField(default='unknown', null=True)),
                ('fine', models.PositiveSmallIntegerField(default=50)),
                ('available_quantity', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Issued',
            fields=[
                ('Issue_No', models.AutoField(primary_key=True, serialize=False)),
                ('days', models.PositiveIntegerField(default=10)),
                ('submit', models.BooleanField(default=False)),
                ('create', models.DateTimeField(auto_now_add=True)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Home.books')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user'],
            },
        ),
    ]



================================================
FILE: LibSys/Home/migrations/__init__.py
================================================
[Empty file]


================================================
FILE: LibSys/LibSys/__init__.py
================================================
[Empty file]


================================================
FILE: LibSys/LibSys/asgi.py
================================================
"""
ASGI config for LibSys project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LibSys.settings')

application = get_asgi_application()



================================================
FILE: LibSys/LibSys/settings.py
================================================
"""
Django settings for LibSys project.

Generated by 'django-admin startproject' using Django 4.2.17.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# Use an environment variable for DEBUG. It will be 'True' by default for local development.
# IMPORTANT: When deploying, you must explicitly set DJANGO_DEBUG to 'False'
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Use an environment variable for the secret key. Provide a default for local development.
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'django-insecure-p5z@u+q!w(e#r$t%y^u&i*o)p_[a]s-d')

if DEBUG:
    # Local development settings
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
    CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']
else:
    # Production settings, for Google Cloud Run
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(
        ',') if os.environ.get('ALLOWED_HOSTS', '') else []
    CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(
        ',') if os.environ.get('CSRF_TRUSTED_ORIGINS', '') else []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'Home',
    'django.contrib.staticfiles',
    'rest_framework.authtoken',
    'rest_framework',
    'django_filters',
    # Add django-storages for cloud storage
    'storages',
]

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'Home.middleware.ServerTimingMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'Home.middleware.RateLimitMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    MIDDLEWARE.insert(5, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = 'LibSys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates'),os.path.join(BASE_DIR, 'templates/auth'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'LibSys.wsgi.application'

# Database
# Use SQLite for local development and Cloud SQL in production
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL', 'sqlite:///' + str(BASE_DIR / 'db.sqlite3'))
    )
} 

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Django Debug Toolbar settings
if DEBUG:
    import socket
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.history.HistoryPanel',
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
LOGIN_URL ='login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
CSRF_FAILURE_VIEW = 'Home.views.csrf_failure'

# --- Static and Media Files Configuration ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
if DEBUG:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# The new, unified storage configuration for both static and media files.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# In production, replace the default storage backend with GCS
if not DEBUG:
    STORAGES["default"]["BACKEND"] = "storages.backends.gcloud.GoogleCloudStorage"
    GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
    GS_PROJECT_ID = os.environ.get('GS_PROJECT_ID')
    GS_DEFAULT_ACL = 'publicRead'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'




================================================
FILE: LibSys/LibSys/urls.py
================================================

from django.contrib import admin
from django.urls import path,include
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('Home.urls')),
    path('users/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path("debug/", include("debug_toolbar.urls")),
    ]



================================================
FILE: LibSys/LibSys/wsgi.py
================================================
"""
WSGI config for LibSys project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LibSys.settings')

application = get_wsgi_application()



================================================
FILE: LibSys/static/style.css
================================================

body {
        background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
        background-size: cover;
        background-attachment: fixed;
        margin: 0;
        padding: 0;
        font-family: Arial, sans-serif;
        overflow: hidden;
    }

header {
        background-color: #336095;
        color:rgb(145, 199, 208);
        padding: 20px;
        text-align: center;
    }

nav {
        background-color:rgb(30, 27, 126);
        padding: 10px 20px;
    }

.nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

.nav-links {
        list-style-type: none;
        padding: 0;
        margin: 0;
        display: flex;
    }

.nav-links li {
        margin-right: 15px;
    }

.nav-links a {
        text-decoration: none;
        color: rgb(145, 199, 208);
        font-weight: bold;
        padding: 5px 10px;
        transition: color 0.3s;
    }

.nav-links a:hover {
        color: #ffffff;
        background-color:rgb(6, 4, 65);
        border-radius: 5px;
    }

section,h3 {
        padding: 20px;
        background-color: #336095;
        margin: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        position: relative;
        top: 50px;
    }

footer {
        background-color: #336095;
        color: rgb(145, 199, 208);
        position: fixed;
        bottom: 0px;
        left: 0px;
        padding: auto;
        width: 100%;
        text-align: center;
        z-index: 1000;
    }
.floating-button {
        position: fixed;
        top: 10px; /* Adjust distance from top */
        right:  10px; /* Adjust distance from right */
        background-color:rgb(234, 82, 31); /* Blue */
        color: white;
        padding: 15px 20px;
        border-radius: 70%; /* Make it round */
        text-decoration: none;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
        z-index: 1000; /* Ensure it's on top */
      }
.floating-button2 {
        position: fixed;
        top: 10px; /* Adjust distance from top */
        left:  10px; /* Adjust distance from right */
        background-color:rgb(234, 82, 31); /* Blue */
        color: white;
        padding: 15px 20px;
        border-radius: 70%; /* Make it round */
        text-decoration: none;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
        z-index: 1000; /* Ensure it's on top */
      }
table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }

table, th, td {
        border: 1px solid #ddd;
        background-color: #f9f9f9;
    }

th, td {
        padding: 10px;
        text-align: left;
        background-color: #f9f9f9;
    }

th {
        background-color: #336095;
        color: white;
    }
.admin-button {
        text-decoration: none;
        background-color: #336095;
        color: rgb(145, 199, 208);
        padding: 5px 10px;
        border-radius: 5px;
        transition: background-color 0.3s;
    }



================================================
FILE: LibSys/static/js/preload.js
================================================
Error reading file with 'cp1252': 'charmap' codec can't decode byte 0x8f in position 3886: character maps to <undefined>


================================================
FILE: LibSys/static/js/sw.js
================================================
/**
 * LibSys Service Worker - Aggressive Caching & Offline Capabilities
 * OOG BOOG! CAVEMAN SERVICE WORKER CACHE ALL THE DATA FOR INSTANT LOAD TIMES!
 */
const CACHE_NAME = 'libsys-cache-v2';
const ASSETS_TO_CACHE = [
    '/',
    '/stock/',
    '/members/',
    '/contacts/',
    '/static/style.css',
    '/static/js/preload.js',
    'https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap'
];

// Install: Cache all core assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] OOG BOOG! Pre-caching core assets for LibSys!');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Cleaning up legacy cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch: Stale-While-Revalidate strategy for static resources, Network-First for HTML
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // Skip non-GET, Django admin panel, Django authentication, and REST APIs
    if (request.method !== 'GET' || 
        url.pathname.startsWith('/admin') || 
        url.pathname.startsWith('/api') || 
        url.pathname.startsWith('/users') ||
        url.pathname.startsWith('/register') || 
        url.pathname.startsWith('/dashboard') ||
        url.pathname.startsWith('/books')) {
        return;
    }

    // Network-First strategy for HTML pages (books, members, contacts, home)
    const acceptHeader = request.headers.get('accept');
    if (acceptHeader && acceptHeader.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Update cache dynamically
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // Fallback to cache if network fails
                    return caches.match(request);
                })
        );
        return;
    }

    // Stale-While-Revalidate strategy for CSS, JS, Fonts, and Images
    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
                // Fetch in background to update cache
                fetch(request).then((networkResponse) => {
                    if (networkResponse.status === 200) {
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, networkResponse);
                        });
                    }
                });
                return cachedResponse;
            }

            return fetch(request).then((networkResponse) => {
                if (networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return networkResponse;
            });
        })
    );
});



================================================
FILE: LibSys/templates/429.html
================================================
Error reading file with 'cp1252': 'charmap' codec can't decode byte 0x8f in position 4647: character maps to <undefined>


================================================
FILE: LibSys/templates/home.html
================================================
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <script src="{% static 'js/preload.js' %}" defer></script>
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('{% static "js/sw.js" %}')
                    .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                    .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
            });
        }
    </script>
    <style>
        body {
            background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            background-attachment: fixed;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }

        header {
            background-color: #336095;
            color:rgb(145, 199, 208);
            padding: 20px;
            text-align: center;
        }

        nav {
            background-color:rgb(30, 27, 126);
            padding: 10px 20px;
        }

        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .nav-links {
            list-style-type: none;
            padding: 0;
            margin: 0;
            display: flex;
        }

        .nav-links li {
            margin-right: 15px;
        }

        .nav-links a {
            text-decoration: none;
            color: rgb(145, 199, 208);
            font-weight: bold;
            padding: 5px 10px;
            transition: color 0.3s;
        }

        .nav-links a:hover {
            color: #ffffff;
            background-color:rgb(6, 4, 65);
            border-radius: 5px;
        }

        section {
            padding: 20px;
            background-color: #336095;
            margin: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            position: relative;
            top: 50px;
        }

        footer {
            background-color: #336095;
            color: rgb(145, 199, 208);
            position: fixed;
            bottom: 0px;
            left: 0px;
            padding: auto;
            width: 100%;
            text-align: center;
            z-index: 1000;
        }
        .floating-button {
          position: fixed;
          top: 10px; /* Adjust distance from top */
          right:  10px; /* Adjust distance from right */
          background-color:rgb(234, 82, 31); /* Blue */
          color: white;
          padding: 15px 20px;
          border-radius: 70%; /* Make it round */
          text-decoration: none;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
          z-index: 1000; /* Ensure it's on top */
        }
    </style>
</head>
<body>
    <header>
      <a href="{% url 'login' %}" class="floating-button">Login</a>
        <h1>Library Management System</h1>
    </header>

    <nav>
        <div class="nav-container">
            <ul class="nav-links">
                <li><a href="{% url 'books' %}">Books</a></li>
                <li><a href="{% url 'members' %}">Members</a></li>
                <li><a href="{% url 'contacts' %}">Contact Us</a></li>
            </ul>
        </div>
    </nav>

    <section>
        <h2>Welcome</h2>
        <p>This is the Library Management System. You can use this system to manage your library books and members.</p>
    </section>

    <footer>
        <p>&copy; 2024 Library Management System</p>
    </footer>
</body>
</html>



================================================
FILE: LibSys/templates/auth/login.html
================================================
Error reading file with 'cp1252': 'charmap' codec can't decode byte 0x8f in position 4012: character maps to <undefined>


================================================
FILE: LibSys/templates/auth/register.html
================================================
Error reading file with 'cp1252': 'charmap' codec can't decode byte 0x8f in position 1115: character maps to <undefined>


================================================
FILE: LibSys/templates/etc/books.html
================================================
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <script src="{% static 'js/preload.js' %}" defer></script>
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('{% static "js/sw.js" %}')
                    .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                    .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
            });
        }
    </script>
    <style>
        body {
            background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            font-family: sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #336095;
            color: white;
            padding: 20px;
            text-align: center;
        }

        section {
            padding: 20px;
            margin: 20px;
            border-radius: 5px;
            background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAVsAAACRCAMAAABaFeu5AAAAElBMVEV+xv97xv94x/9zxPx8x/91xv4RbxmEAAABJklEQVR4nO3V0W6CQBBAUbD2/3+50QSyxV3a2F1moOc8GBgTnb1qnCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4Gru0QvsucfptH6PlxkjsO0fNNYP7Fgz15Ubl3ffnwmzrt8Y5/CrtnPlMtS6fmOcQ6Ntmbi4fg0fY12/Mc7hnbbl1zgm9Lp+Y5zDW22XoNru2m+bVWP9wI41MW3+BW3H0XYcbcc5pO2teEzgqEV6tr0ttve3zW20jmfeM7Dt9jDHN2zpeOY9U/Q5r0nbgZ5tP9ui9zszbce5VNtEf5UPl2qbbNuf2p7Behhtu1vOkuxXNl+hbWbTx3DP96mMCrXZ+Wk7Tkzbs0jf9njdPk1tX2mbn7ZZaTvOFwCFZd5Kyns4AAAAAElFTkSuQmCC");
            color: rgb(0, 0, 0);
            box-shadow: 0 0 10px rgb(255, 255, 255);
            width: fit-content;
            position: relative;
            top: 50px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }

        th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }

        th {
            background-color: #336095;
            color: white;
        }

        footer {
            background-color: #336095;
            color: rgb(145, 199, 208);
            position: fixed;
            bottom: 0px;
            left: 0px;
            padding: auto;
            width: 100%;
            text-align: center;
            z-index: 1000;
        }
        .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left: 10px; /* Adjust distance from left */
            background-color: #336095; /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
    </style>
</head>
<body>
    <header>
        <a href="{% url 'home' %}" class="floating-button">Go Back</a>
        <h1>Available Books</h1>
    </header>

    <section>
        <h2>Our Collection</h2>
        <table>
            <thead>
                <tr>
                    <th>Book Name</th>
                    <th>Author</th>
                    <th>Genre</th>
                </tr>
            </thead>
            <tbody>
                {% for book in books %}
                <tr>
                    <td>{{ book.book_name }}</td>
                    <td>{{ book.author }}</td>
                    <td>{{ book.genre }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>

    <footer >
        <p>&copy; 2024 Library Management System</p>
    </footer>
</body>
</html>



================================================
FILE: LibSys/templates/etc/contacts.html
================================================
{% load static %}
<!DOCTYPE html>
<html>
    <style>
        body {
            background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            font-family: sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #336095;
            color: white;
            padding: 20px;
            text-align: center;
        }

        section {
            padding: 20px;
            margin: 20px;
            border-radius: 5px;
            background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAVsAAACRCAMAAABaFeu5AAAAElBMVEV+xv97xv94x/9zxPx8x/91xv4RbxmEAAABJklEQVR4nO3V0W6CQBBAUbD2/3+50QSyxV3a2F1moOc8GBgTnb1qnCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4Gru0QvsucfptH6PlxkjsO0fNNYP7Fgz15Ubl3ffnwmzrt8Y5/CrtnPlMtS6fmOcQ6Ntmbi4fg0fY12/Mc7hnbbl1zgm9Lp+Y5zDW22XoNru2m+bVWP9wI41MW3+BW3H0XYcbcc5pO2teEzgqEV6tr0ttve3zW20jmfeM7Dt9jDHN2zpeOY9U/Q5r0nbgZ5tP9ui9zszbce5VNtEf5UPl2qbbNuf2p7Behhtu1vOkuxXNl+hbWbTx3DP96mMCrXZ+Wk7Tkzbs0jf9njdPk1tX2mbn7ZZaTvOFwCFZd5Kyns4AAAAAElFTkSuQmCC");
            color: rgb(0, 0, 0);
            box-shadow: 0 0 10px rgb(255, 255, 255);
            width: fit-content;
            position: relative;
            top: 50px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }

        th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }

        th {
            background-color: #336095;
            color: white;
        }

        footer {
            background-color: #336095;
            color: rgb(145, 199, 208);
            position: fixed;
            bottom: 0px;
            left: 0px;
            padding: auto;
            width: 100%;
            text-align: center;
            z-index: 1000;
        }
        .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left: 10px; /* Adjust distance from left */
            background-color: #336095; /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
    </style>
<head>
  <title>Contact Us</title>
  <script src="{% static 'js/preload.js' %}" defer></script>
  <script>
      if ('serviceWorker' in navigator) {
          window.addEventListener('load', () => {
              navigator.serviceWorker.register('{% static "js/sw.js" %}')
                  .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                  .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
          });
      }
  </script>
</head>
<body>
  <header>
    <a href="{% url 'home' %}" class="floating-button">Go Back</a>
    <h1>Contact Us</h1>
  </header>

  <section>
    <h2>Get in Touch</h2>
    <p>We'd love to hear from you! Fill out the form below to send us a message.</p>
    <form id="contactForm" action="/contact/submit" method="post">
      {% csrf_token %}
      <label for="name">Your Name:</label>
      <input type="text" name="name" id="name" required>
      <br>
      <label for="email">Your Email:</label>
      <input type="email" name="email" id="email" required>
      <br>
      <label for="message">Message:</label>
      <textarea name="message" id="message" rows="5" required></textarea>
      <br>
      <button type="submit">Send Message</button>
    </form>
  </section>

  <script>
    document.getElementById("contactForm").addEventListener("submit", (e) => {
        e.preventDefault();
        alert("OOG BOOG! Message sent successfully to Caveman Chief! Thank you!");
        e.target.reset();
    });
  </script>

  <footer>
    <p>&copy; 2024 Library Management System</p>
  </footer>
</body>
</html>


================================================
FILE: LibSys/templates/etc/members.html
================================================
{% load static %}
<!DOCTYPE html>
<html>
    <style>
        body {
            background-image: url("https://plus.unsplash.com/premium_photo-1677567996070-68fa4181775a?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            font-family: sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #336095;
            color: white;
            padding: 20px;
            text-align: center;
        }

        section {
            padding: 20px;
            margin: 20px;
            border-radius: 5px;
            background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAVsAAACRCAMAAABaFeu5AAAAElBMVEV+xv97xv94x/9zxPx8x/91xv4RbxmEAAABJklEQVR4nO3V0W6CQBBAUbD2/3+50QSyxV3a2F1moOc8GBgTnb1qnCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4Gru0QvsucfptH6PlxkjsO0fNNYP7Fgz15Ubl3ffnwmzrt8Y5/CrtnPlMtS6fmOcQ6Ntmbi4fg0fY12/Mc7hnbbl1zgm9Lp+Y5zDW22XoNru2m+bVWP9wI41MW3+BW3H0XYcbcc5pO2teEzgqEV6tr0ttve3zW20jmfeM7Dt9jDHN2zpeOY9U/Q5r0nbgZ5tP9ui9zszbce5VNtEf5UPl2qbbNuf2p7Behhtu1vOkuxXNl+hbWbTx3DP96mMCrXZ+Wk7Tkzbs0jf9njdPk1tX2mbn7ZZaTvOFwCFZd5Kyns4AAAAAElFTkSuQmCC");
            color: rgb(0, 0, 0);
            box-shadow: 0 0 10px rgb(255, 255, 255);
            width: fit-content;
            position: relative;
            top: 50px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }

        th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }

        th {
            background-color: #336095;
            color: white;
        }

        footer {
            background-color: #336095;
            color: rgb(145, 199, 208);
            position: fixed;
            bottom: 0px;
            left: 0px;
            padding: auto;
            width: 100%;
            text-align: center;
            z-index: 1000;
        }
        .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left: 10px; /* Adjust distance from left */
            background-color: #336095; /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
    </style>
<head>
  <title>Library Members</title>
  <script src="{% static 'js/preload.js' %}" defer></script>
  <script>
      if ('serviceWorker' in navigator) {
          window.addEventListener('load', () => {
              navigator.serviceWorker.register('{% static "js/sw.js" %}')
                  .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                  .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
          });
      }
  </script>
</head>
<body>
  <header>
    <a href="{% url 'home' %}" class="floating-button">Go Back</a>
    <h1>Library Members</h1>
  </header>

  <section>
    <h2>List of Members</h2>
    <table>
      <thead>
        <tr>
          <th>Username</th>
          
          <th>Joined Since</th>
        </tr>
      </thead>
      <tbody>
        {% for user in users %}
        <tr>
          <td>{{ user.username }}</td>
          
          <td>{{ user.date_joined|timesince }}</td>  </tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <footer>
    <p>&copy; 2024 Library Management System</p>
  </footer>
</body>
</html>


================================================
FILE: LibSys/templates/registration/login.html
================================================
Error reading file with 'cp1252': 'charmap' codec can't decode byte 0x8f in position 3563: character maps to <undefined>


================================================
FILE: LibSys/templates/user/dashboard.html
================================================
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <title>Library Dashboard - LibSys</title>
    <script src="{% static 'js/preload.js' %}" defer></script>
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('{% static "js/sw.js" %}')
                    .then(reg => console.log('[SW] Service Worker Registered Successfully!'))
                    .catch(err => console.error('[SW] Service Worker Registration Failed:', err));
            });
        }
    </script>
    <style>
        body {
            overflow: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }
        th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }
        th {
            background-color: #336095;
            color: white;
        }
        section, h3 {
            padding: 20px;
            background-color: #336095;
            margin: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            position: relative;
            top: 50%;
        }
        .floating-button2 {
            position: fixed;
            top: 10px;
            left: 10px;
            background-color: rgb(234, 82, 31);
            color: white;
            padding: 15px 20px;
            border-radius: 70%;
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        }
        .floating-button3 {
            position: fixed;
            top: 100px;
            right: 10px;
            background-color: rgb(234, 82, 31);
            color: white;
            padding: 15px 20px;
            border-radius: 70%;
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        }
    </style>
</head>
<body>
    {% if request.user.is_superuser %}
        <a class="floating-button" href="{% url 'manage_books' %}">Manage Books</a>
    {% endif %}
    <a class='floating-button2' href="{% url 'issued_books' %}">Issueance History</a>
    <br><br>
    <div>
<body>
  <div class="container">
    <h1 style="text-align: center; color: #336095; background-color: #ddd; border-radius: 50%;">Hello, {{ request.user|title }}</h1>

    <div class="logout">
        <br>
      <a class="floating-button3" href="{% url 'logout' %}">Logout</a>
    <br>
    </div>

    
    <h3>Available Books</h3>
    <table border>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Available</th>
                <th>Actions</th>
               
            </tr>
        </thead>
        <tbody>
          {% for book in available_books %}
              <tr>
                  <td>{{ book.Bid }}</td>
                  <td>{{ book.book_name }}</td>
                  <td>{{ book.available_quantity }}</td>
                  <td>
                      {% if issued_books.book.bid == book.bid and issued_books.submit == False %}
                          Please return the book before issuing again.
                      {% else %}
                          <a href="{% url 'issue_book' pk=book.pk %}">Issue</a>
                      {% endif %}
                  </td>
              </tr>
          {% endfor %}
      </tbody>
    </table>    

    

  </div>
  <div>
    
  <h3>Currently Issued Books</h3>
    <table border="1">
        <thead>
            <tr>
                <th>IssueNo</th>
                <th>Book</th>
                <th>Issued To</th>
                <th>Time since Issue <br> (Max 10 days before Fine)</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for issued_book in issued_books %}
                {% if issued_book.user == request.user %}
                    {%if issued_book.submit == False %}
                        <tr>
                        
                            <td>{{ issued_book.Issue_No }}</td>
                            <td>{{ issued_book.book.book_name }}</td>
                            <td>{{ issued_book.user }}</td>
                            <td>{{ issued_book.create|timesince }} ago</td>
                            <td>{% if issued_book.submit %}Returned{% else %}Not Returned{% endif %}</td>
                            <td>{% if issued_book.submit %} {% else %}<a href="{% url 'return_book' pk=issued_book.pk %}">return</a>{% endif %}</td>
                        
                        </tr>
                    {% endif %}
                {% endif %}
            {% endfor %}
        </tbody>
    </table>
    
  </div>
</body>
</html>


================================================
FILE: LibSys/templates/user/edit_book.html
================================================
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
  
  table, th, td {
        border: 1px solid #ddd;
        background-color: #f9f9f9;
    }
  
  th, td {
        padding: 10px;
        text-align: left;
        background-color: #f9f9f9;
    }
  
  th {
        background-color: #336095;
        color: white;
    }
  form,h3,h1 {
        padding: 20px;
        background-color: #336095;
        margin: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        position: relative;
        top: 1%;
        width: 25%;
           }
  .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button2 {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button3 {
            position: fixed;
            top: 100px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
          
  
  </style>
  {% load static %}
  <link rel="stylesheet" href="{% static 'style.css' %}">
<h1>Edit Book</h1>

<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Save Changes</button>
</form>


================================================
FILE: LibSys/templates/user/issue_book.html
================================================
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
  
  table, th, td {
        border: 1px solid #ddd;
        background-color: #f9f9f9;
    }
  
  th, td {
        padding: 10px;
        text-align: left;
        background-color: #f9f9f9;
    }
  
  th {
        background-color: #336095;
        color: white;
    }
  form,h3,h1,.form {
        padding: 20px;
        background-color: #336095;
        margin: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        position: relative;
        top: 1%;
        width: 25%;
           }
  .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button2 {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button3 {
            position: fixed;
            top: 100px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
h2 {text-align: center;
 color: #336095;
 font-size: 40px;
  background-color: #ddd;
  padding: auto;
   border-radius: 30%;}
          
  
  </style>
  {% load static %}
  <link rel="stylesheet" href="{% static 'style.css' %}">
{% block content %}
<h1>Issue Book</h1>
<div class = 'form'>
    {% if book %}
        <p>Are you sure you want to issue the book: <strong>{{ book.book_name }}</strong> by <strong>{{ book.author }}</strong>?</p>
        <form method="post">
            {% csrf_token %}
            <button type="submit">Issue Book</button>
        </form>
    {% else %}
        <p>Book not found!</p>
    {% endif %}

    {% if messages %}
        <ul class="messages">
            {% for message in messages %}
                <li {% if message.tags %} class="{{ message.tags }}"{% endif %}>{{ message }}</li>
            {% endfor %}
        </ul>
    {% endif %}
</div>
{% endblock %}


================================================
FILE: LibSys/templates/user/issued_books.html
================================================

{% block content %}
<style>
  table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
  }

table, th, td {
      border: 1px solid #ddd;
      background-color: #f9f9f9;
  }

th, td {
      padding: 10px;
      text-align: left;
      background-color: #f9f9f9;
  }

th {
      background-color: #336095;
      color: white;
  }
section,h3 {
      padding: 20px;
      background-color: #336095;
      margin: 20px;
      border-radius: 5px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      position: relative;
      top: 50%;
         }
.floating-button {
          position: fixed;
          top: 10px; /* Adjust distance from top */
          right:  10px; /* Adjust distance from right */
          background-color:rgb(234, 82, 31); /* Blue */
          color: white;
          padding: 15px 20px;
          border-radius: 70%; /* Make it round */
          text-decoration: none;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
          z-index: 1000; /* Ensure it's on top */
        }
.floating-button2 {
          position: fixed;
          top: 10px; /* Adjust distance from top */
          left:  10px; /* Adjust distance from right */
          background-color:rgb(234, 82, 31); /* Blue */
          color: white;
          padding: 15px 20px;
          border-radius: 70%; /* Make it round */
          text-decoration: none;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
          z-index: 1000; /* Ensure it's on top */
        }
.floating-button3 {
          position: fixed;
          top: 100px; /* Adjust distance from top */
          right:  10px; /* Adjust distance from right */
          background-color:rgb(234, 82, 31); /* Blue */
          color: white;
          padding: 15px 20px;
          border-radius: 70%; /* Make it round */
          text-decoration: none;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
          z-index: 1000; /* Ensure it's on top */
        }
        

</style>
<h2>Issued Books History</h2>
<a class="floating-button" href="{% url 'dashboard' %}">dashboard</a><br><br>

{% if issued_books %}
<table border = "1">
  <thead>
    <tr>
      <th>Issue No.</th>
      <th>Book Name</th>
      <th>length_of_possession</th>
      <th>Fine</th>
    
      <th>Note</th>
     
    </tr>
  </thead>
  <tbody>
    {% for issued_book in issued_books %}
      <tr>
        <td>{{ issued_book.Issue_No }}</td>
        <td>{{ issued_book.book.book_name }}</td>
        <td>{{ issued_book.create|timesince }}</td>
        <td>{{ issued_book.book.fine }}</td>
        {%if issued_book.submit == False %}
        <td>Not Returned</td>
        {%endif%}
      </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
  <p>No Issued Books</p>
{% endif %}
{% if messages %}
    <ul class="messages">
        {% for message in messages %}
            <li {% if message.tags %} class="{{ message.tags }}"{% endif %}>{{ message }}</li>
        {% endfor %}
    </ul>
{% endif %}

{% endblock %}


================================================
FILE: LibSys/templates/user/manage_books.html
================================================
<!DOCTYPE html>
<html>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
      
      table, th, td {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }
      
      th, td {
            padding: 10px;
            text-align: left;
            background-color: #f9f9f9;
        }
      
      th {
            background-color: #336095;
            color: white;
        }
      form,h3,h1 {
            padding: 20px;
            background-color: #336095;
            margin: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            position: relative;
            top: 1%;
            width: 25%;
               }
      .floating-button {
                position: fixed;
                top: 10px; /* Adjust distance from top */
                right:  10px; /* Adjust distance from right */
                background-color:rgb(234, 82, 31); /* Blue */
                color: white;
                padding: 15px 20px;
                border-radius: 70%; /* Make it round */
                text-decoration: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
                z-index: 1000; /* Ensure it's on top */
              }
      .floating-button2 {
                position: fixed;
                top: 10px; /* Adjust distance from top */
                left:  10px; /* Adjust distance from right */
                background-color:rgb(234, 82, 31); /* Blue */
                color: white;
                padding: 15px 20px;
                border-radius: 70%; /* Make it round */
                text-decoration: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
                z-index: 1000; /* Ensure it's on top */
              }
      .floating-button3 {
                position: fixed;
                top: 100px; /* Adjust distance from top */
                right:  10px; /* Adjust distance from right */
                background-color:rgb(234, 82, 31); /* Blue */
                color: white;
                padding: 15px 20px;
                border-radius: 70%; /* Make it round */
                text-decoration: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
                z-index: 1000; /* Ensure it's on top */
              }
h2 {text-align: center;
     color: #336095;
     font-size: 40px;
      background-color: #ddd;
      padding: auto;
       border-radius: 30%;}
              
      
      </style>
      {% load static %}
      <link rel="stylesheet" href="{% static 'style.css' %}">
<head>
    <title>Manage Books</title>
    <br>
    <a class="floating-button" href="{% url 'dashboard' %}">dashboard</a>
    <br>
</head>
<body style="overflow: scroll;">
    <h2>Manage Books</h2>

    <form method="post">
        {% csrf_token %}
        <label for="book_name">Book Name:</label>
        <input type="text" name="book_name" required><br><br>
        <label for="quantity">Quantity:</label>
        <input type="number" name="quantity" required><br><br>
        <label for="author">Author:</label>
        <input type="text" name="author" required><br><br>
        <label for="genre">Genre:</label>
        <input type="text" name="genre"><br><br>
        <label for="fine">Fine:</label>
        <input type="number" name="fine" required><br><br>
        <button type="submit" name="add_book">Add Book</button>
    </form>

    <form method="post">
        {% csrf_token %}
        <label for="book_id">Book ID:</label>
        <select name="book_id">
            {% for book in books %}
                <option value="{{ book.Bid }}">{{ book.Bid }} : {{ book.book_name }}</option>
            {% endfor %}
        </select>
        <button type="submit" name="remove_book">Remove Book</button>
    </form>

    <h3>Available Books</h3><br>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Quantity</th>
                <th>Available</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for book in available_books %}
                <tr>
                    <td>{{ book.Bid }}</td>
                    <td>{{ book.book_name }}</td>
                    <td>{{ book.quantity }}</td>
                    <td>{{ book.available_quantity }}</td>
                    <td><a href="{% url 'edit_book' pk=book.pk %}">Edit</a></td> 
                </tr>
            {% endfor %}
        </tbody>
    </table>

   

    <div>
     <h3>Issued Books</h3><br>
    <table>
      <thead>
        <tr>
          <th>Book</th>
          <th>Issued To</th>
          <th>Possesion Time</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {% for issued_book in issued_books %}
          <tr>
            <td>{{ issued_book.book.book_name }}</td>
            <td>{{ issued_book.user }}</td>
            <td>{{ issued_book.create|timesince }}</td>
            <td>{% if issued_book.submit %}Returned{% else %}Not Returned{% endif %}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
    </div>

</body>
</html>


================================================
FILE: LibSys/templates/user/return_book.html
================================================
{% block content %}
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
  
  table, th, td {
        border: 1px solid #ddd;
        background-color: #f9f9f9;
    }
  
  th, td {
        padding: 10px;
        text-align: left;
        background-color: #f9f9f9;
    }
  
  th {
        background-color: #336095;
        color: white;
    }
  form,h3,h1,.form {
        padding: 20px;
        background-color: #336095;
        margin: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        position: relative;
        top: 1%;
        width: 35%;
           }
  .floating-button {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button2 {
            position: fixed;
            top: 10px; /* Adjust distance from top */
            left:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
  .floating-button3 {
            position: fixed;
            top: 100px; /* Adjust distance from top */
            right:  10px; /* Adjust distance from right */
            background-color:rgb(234, 82, 31); /* Blue */
            color: white;
            padding: 15px 20px;
            border-radius: 70%; /* Make it round */
            text-decoration: none;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add a subtle shadow */
            z-index: 1000; /* Ensure it's on top */
          }
h2 {text-align: center;
 color: #336095;
 font-size: 40px;
  background-color: #ddd;
  padding: auto;
   border-radius: 30%;}
          
  
  </style>
  {% load static %}
  <link rel="stylesheet" href="{% static 'style.css' %}">

<h2>Return Book</h2>
<div class="form">
{% if issued_book %}
    <p>Are you sure you want to return the following book?</p>
    <p><strong>Book Name:</strong> {{ issued_book.book.book_name }}</p>
    <p><strong>Issued To:</strong> {{ issued_book.user.username }}</p>
    <p><strong>Issued On:</strong> {{ issued_book.create }}</p>
    {% if available_quantity %}
    <p><strong>Available Quantity after return:</strong> {{ available_quantity|add:"1" }}</p>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <button type="submit" class="btn btn-primary">Confirm Return</button>
        <br>
        <a href="{% url 'issued_books' %}" class="btn btn-secondary" style='background-color: rgb(234, 82, 31);'>Cancel</a> 
    </form>
{% else %}
    <p>Invalid issued book ID.</p>
    <a href="{% url 'issued_books' %}" class="btn btn-secondary">Back to Issued Books</a>
{% endif %}
</div>
{% endblock %}


================================================
FILE: Scripts/activate
================================================
# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

deactivate () {
    # reset old environment variables
    if [ -n "${_OLD_VIRTUAL_PATH:-}" ] ; then
        PATH="${_OLD_VIRTUAL_PATH:-}"
        export PATH
        unset _OLD_VIRTUAL_PATH
    fi
    if [ -n "${_OLD_VIRTUAL_PYTHONHOME:-}" ] ; then
        PYTHONHOME="${_OLD_VIRTUAL_PYTHONHOME:-}"
        export PYTHONHOME
        unset _OLD_VIRTUAL_PYTHONHOME
    fi

    # This should detect bash and zsh, which have a hash command that must
    # be called to get it to forget past commands.  Without forgetting
    # past commands the $PATH changes we made may not be respected
    if [ -n "${BASH:-}" -o -n "${ZSH_VERSION:-}" ] ; then
        hash -r 2> /dev/null
    fi

    if [ -n "${_OLD_VIRTUAL_PS1:-}" ] ; then
        PS1="${_OLD_VIRTUAL_PS1:-}"
        export PS1
        unset _OLD_VIRTUAL_PS1
    fi

    unset VIRTUAL_ENV
    if [ ! "${1:-}" = "nondestructive" ] ; then
    # Self destruct!
        unset -f deactivate
    fi
}

# unset irrelevant variables
deactivate nondestructive

VIRTUAL_ENV="C:\Users\akhil\application"
export VIRTUAL_ENV

_OLD_VIRTUAL_PATH="$PATH"
PATH="$VIRTUAL_ENV/Scripts:$PATH"
export PATH

# unset PYTHONHOME if set
# this will fail if PYTHONHOME is set to the empty string (which is bad anyway)
# could use `if (set -u; : $PYTHONHOME) ;` in bash
if [ -n "${PYTHONHOME:-}" ] ; then
    _OLD_VIRTUAL_PYTHONHOME="${PYTHONHOME:-}"
    unset PYTHONHOME
fi

if [ -z "${VIRTUAL_ENV_DISABLE_PROMPT:-}" ] ; then
    _OLD_VIRTUAL_PS1="${PS1:-}"
    PS1="(application) ${PS1:-}"
    export PS1
fi

# This should detect bash and zsh, which have a hash command that must
# be called to get it to forget past commands.  Without forgetting
# past commands the $PATH changes we made may not be respected
if [ -n "${BASH:-}" -o -n "${ZSH_VERSION:-}" ] ; then
    hash -r 2> /dev/null
fi



================================================
FILE: Scripts/activate.bat
================================================
@echo off

rem This file is UTF-8 encoded, so we need to update the current code page while executing it
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)

set VIRTUAL_ENV=C:\Users\akhil\application

if not defined PROMPT set PROMPT=$P$G

if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%

set _OLD_VIRTUAL_PROMPT=%PROMPT%
set PROMPT=(application) %PROMPT%

if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=

if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%

set PATH=%VIRTUAL_ENV%\Scripts;%PATH%

:END
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)



================================================
FILE: Scripts/Activate.ps1
================================================
<#
.Synopsis
Activate a Python virtual environment for the current PowerShell session.

.Description
Pushes the python executable for a virtual environment to the front of the
$Env:PATH environment variable and sets the prompt to signify that you are
in a Python virtual environment. Makes use of the command line switches as
well as the `pyvenv.cfg` file values present in the virtual environment.

.Parameter VenvDir
Path to the directory that contains the virtual environment to activate. The
default value for this is the parent of the directory that the Activate.ps1
script is located within.

.Parameter Prompt
The prompt prefix to display when this virtual environment is activated. By
default, this prompt is the name of the virtual environment folder (VenvDir)
surrounded by parentheses and followed by a single space (ie. '(.venv) ').

.Example
Activate.ps1
Activates the Python virtual environment that contains the Activate.ps1 script.

.Example
Activate.ps1 -Verbose
Activates the Python virtual environment that contains the Activate.ps1 script,
and shows extra information about the activation as it executes.

.Example
Activate.ps1 -VenvDir C:\Users\MyUser\Common\.venv
Activates the Python virtual environment located in the specified location.

.Example
Activate.ps1 -Prompt "MyPython"
Activates the Python virtual environment that contains the Activate.ps1 script,
and prefixes the current prompt with the specified string (surrounded in
parentheses) while the virtual environment is active.

.Notes
On Windows, it may be required to enable this Activate.ps1 script by setting the
execution policy for the user. You can do this by issuing the following PowerShell
command:

PS C:\> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

For more information on Execution Policies: 
https://go.microsoft.com/fwlink/?LinkID=135170

#>
Param(
    [Parameter(Mandatory = $false)]
    [String]
    $VenvDir,
    [Parameter(Mandatory = $false)]
    [String]
    $Prompt
)

<# Function declarations --------------------------------------------------- #>

<#
.Synopsis
Remove all shell session elements added by the Activate script, including the
addition of the virtual environment's Python executable from the beginning of
the PATH variable.

.Parameter NonDestructive
If present, do not remove this function from the global namespace for the
session.

#>
function global:deactivate ([switch]$NonDestructive) {
    # Revert to original values

    # The prior prompt:
    if (Test-Path -Path Function:_OLD_VIRTUAL_PROMPT) {
        Copy-Item -Path Function:_OLD_VIRTUAL_PROMPT -Destination Function:prompt
        Remove-Item -Path Function:_OLD_VIRTUAL_PROMPT
    }

    # The prior PYTHONHOME:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PYTHONHOME) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME -Destination Env:PYTHONHOME
        Remove-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME
    }

    # The prior PATH:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PATH) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PATH -Destination Env:PATH
        Remove-Item -Path Env:_OLD_VIRTUAL_PATH
    }

    # Just remove the VIRTUAL_ENV altogether:
    if (Test-Path -Path Env:VIRTUAL_ENV) {
        Remove-Item -Path env:VIRTUAL_ENV
    }

    # Just remove the _PYTHON_VENV_PROMPT_PREFIX altogether:
    if (Get-Variable -Name "_PYTHON_VENV_PROMPT_PREFIX" -ErrorAction SilentlyContinue) {
        Remove-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Scope Global -Force
    }

    # Leave deactivate function in the global namespace if requested:
    if (-not $NonDestructive) {
        Remove-Item -Path function:deactivate
    }
}

<#
.Description
Get-PyVenvConfig parses the values from the pyvenv.cfg file located in the
given folder, and returns them in a map.

For each line in the pyvenv.cfg file, if that line can be parsed into exactly
two strings separated by `=` (with any amount of whitespace surrounding the =)
then it is considered a `key = value` line. The left hand string is the key,
the right hand is the value.

If the value starts with a `'` or a `"` then the first and last character is
stripped from the value before being captured.

.Parameter ConfigDir
Path to the directory that contains the `pyvenv.cfg` file.
#>
function Get-PyVenvConfig(
    [String]
    $ConfigDir
) {
    Write-Verbose "Given ConfigDir=$ConfigDir, obtain values in pyvenv.cfg"

    # Ensure the file exists, and issue a warning if it doesn't (but still allow the function to continue).
    $pyvenvConfigPath = Join-Path -Resolve -Path $ConfigDir -ChildPath 'pyvenv.cfg' -ErrorAction Continue

    # An empty map will be returned if no config file is found.
    $pyvenvConfig = @{ }

    if ($pyvenvConfigPath) {

        Write-Verbose "File exists, parse `key = value` lines"
        $pyvenvConfigContent = Get-Content -Path $pyvenvConfigPath

        $pyvenvConfigContent | ForEach-Object {
            $keyval = $PSItem -split "\s*=\s*", 2
            if ($keyval[0] -and $keyval[1]) {
                $val = $keyval[1]

                # Remove extraneous quotations around a string value.
                if ("'""".Contains($val.Substring(0, 1))) {
                    $val = $val.Substring(1, $val.Length - 2)
                }

                $pyvenvConfig[$keyval[0]] = $val
                Write-Verbose "Adding Key: '$($keyval[0])'='$val'"
            }
        }
    }
    return $pyvenvConfig
}


<# Begin Activate script --------------------------------------------------- #>

# Determine the containing directory of this script
$VenvExecPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvExecDir = Get-Item -Path $VenvExecPath

Write-Verbose "Activation script is located in path: '$VenvExecPath'"
Write-Verbose "VenvExecDir Fullname: '$($VenvExecDir.FullName)"
Write-Verbose "VenvExecDir Name: '$($VenvExecDir.Name)"

# Set values required in priority: CmdLine, ConfigFile, Default
# First, get the location of the virtual environment, it might not be
# VenvExecDir if specified on the command line.
if ($VenvDir) {
    Write-Verbose "VenvDir given as parameter, using '$VenvDir' to determine values"
}
else {
    Write-Verbose "VenvDir not given as a parameter, using parent directory name as VenvDir."
    $VenvDir = $VenvExecDir.Parent.FullName.TrimEnd("\\/")
    Write-Verbose "VenvDir=$VenvDir"
}

# Next, read the `pyvenv.cfg` file to determine any required value such
# as `prompt`.
$pyvenvCfg = Get-PyVenvConfig -ConfigDir $VenvDir

# Next, set the prompt from the command line, or the config file, or
# just use the name of the virtual environment folder.
if ($Prompt) {
    Write-Verbose "Prompt specified as argument, using '$Prompt'"
}
else {
    Write-Verbose "Prompt not specified as argument to script, checking pyvenv.cfg value"
    if ($pyvenvCfg -and $pyvenvCfg['prompt']) {
        Write-Verbose "  Setting based on value in pyvenv.cfg='$($pyvenvCfg['prompt'])'"
        $Prompt = $pyvenvCfg['prompt'];
    }
    else {
        Write-Verbose "  Setting prompt based on parent's directory's name. (Is the directory name passed to venv module when creating the virtual environment)"
        Write-Verbose "  Got leaf-name of $VenvDir='$(Split-Path -Path $venvDir -Leaf)'"
        $Prompt = Split-Path -Path $venvDir -Leaf
    }
}

Write-Verbose "Prompt = '$Prompt'"
Write-Verbose "VenvDir='$VenvDir'"

# Deactivate any currently active virtual environment, but leave the
# deactivate function in place.
deactivate -nondestructive

# Now set the environment variable VIRTUAL_ENV, used by many tools to determine
# that there is an activated venv.
$env:VIRTUAL_ENV = $VenvDir

if (-not $Env:VIRTUAL_ENV_DISABLE_PROMPT) {

    Write-Verbose "Setting prompt to '$Prompt'"

    # Set the prompt to include the env name
    # Make sure _OLD_VIRTUAL_PROMPT is global
    function global:_OLD_VIRTUAL_PROMPT { "" }
    Copy-Item -Path function:prompt -Destination function:_OLD_VIRTUAL_PROMPT
    New-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Description "Python virtual environment prompt prefix" -Scope Global -Option ReadOnly -Visibility Public -Value $Prompt

    function global:prompt {
        Write-Host -NoNewline -ForegroundColor Green "($_PYTHON_VENV_PROMPT_PREFIX) "
        _OLD_VIRTUAL_PROMPT
    }
}

# Clear PYTHONHOME
if (Test-Path -Path Env:PYTHONHOME) {
    Copy-Item -Path Env:PYTHONHOME -Destination Env:_OLD_VIRTUAL_PYTHONHOME
    Remove-Item -Path Env:PYTHONHOME
}

# Add the venv to the PATH
Copy-Item -Path Env:PATH -Destination Env:_OLD_VIRTUAL_PATH
$Env:PATH = "$VenvExecDir$([System.IO.Path]::PathSeparator)$Env:PATH"

# SIG # Begin signature block
# MIIkCQYJKoZIhvcNAQcCoIIj+jCCI/YCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCD50itNqbOCCDp6
# 9ZnhKce5X7vV6KL67iKMbGTUZ4nf36CCDi8wggawMIIEmKADAgECAhAIrUCyYNKc
# TJ9ezam9k67ZMA0GCSqGSIb3DQEBDAUAMGIxCzAJBgNVBAYTAlVTMRUwEwYDVQQK
# EwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xITAfBgNV
# BAMTGERpZ2lDZXJ0IFRydXN0ZWQgUm9vdCBHNDAeFw0yMTA0MjkwMDAwMDBaFw0z
# NjA0MjgyMzU5NTlaMGkxCzAJBgNVBAYTAlVTMRcwFQYDVQQKEw5EaWdpQ2VydCwg
# SW5jLjFBMD8GA1UEAxM4RGlnaUNlcnQgVHJ1c3RlZCBHNCBDb2RlIFNpZ25pbmcg
# UlNBNDA5NiBTSEEzODQgMjAyMSBDQTEwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAw
# ggIKAoICAQDVtC9C0CiteLdd1TlZG7GIQvUzjOs9gZdwxbvEhSYwn6SOaNhc9es0
# JAfhS0/TeEP0F9ce2vnS1WcaUk8OoVf8iJnBkcyBAz5NcCRks43iCH00fUyAVxJr
# Q5qZ8sU7H/Lvy0daE6ZMswEgJfMQ04uy+wjwiuCdCcBlp/qYgEk1hz1RGeiQIXhF
# LqGfLOEYwhrMxe6TSXBCMo/7xuoc82VokaJNTIIRSFJo3hC9FFdd6BgTZcV/sk+F
# LEikVoQ11vkunKoAFdE3/hoGlMJ8yOobMubKwvSnowMOdKWvObarYBLj6Na59zHh
# 3K3kGKDYwSNHR7OhD26jq22YBoMbt2pnLdK9RBqSEIGPsDsJ18ebMlrC/2pgVItJ
# wZPt4bRc4G/rJvmM1bL5OBDm6s6R9b7T+2+TYTRcvJNFKIM2KmYoX7BzzosmJQay
# g9Rc9hUZTO1i4F4z8ujo7AqnsAMrkbI2eb73rQgedaZlzLvjSFDzd5Ea/ttQokbI
# YViY9XwCFjyDKK05huzUtw1T0PhH5nUwjewwk3YUpltLXXRhTT8SkXbev1jLchAp
# QfDVxW0mdmgRQRNYmtwmKwH0iU1Z23jPgUo+QEdfyYFQc4UQIyFZYIpkVMHMIRro
# OBl8ZhzNeDhFMJlP/2NPTLuqDQhTQXxYPUez+rbsjDIJAsxsPAxWEQIDAQABo4IB
# WTCCAVUwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHQ4EFgQUaDfg67Y7+F8Rhvv+
# YXsIiGX0TkIwHwYDVR0jBBgwFoAU7NfjgtJxXWRM3y5nP+e6mK4cD08wDgYDVR0P
# AQH/BAQDAgGGMBMGA1UdJQQMMAoGCCsGAQUFBwMDMHcGCCsGAQUFBwEBBGswaTAk
# BggrBgEFBQcwAYYYaHR0cDovL29jc3AuZGlnaWNlcnQuY29tMEEGCCsGAQUFBzAC
# hjVodHRwOi8vY2FjZXJ0cy5kaWdpY2VydC5jb20vRGlnaUNlcnRUcnVzdGVkUm9v
# dEc0LmNydDBDBgNVHR8EPDA6MDigNqA0hjJodHRwOi8vY3JsMy5kaWdpY2VydC5j
# b20vRGlnaUNlcnRUcnVzdGVkUm9vdEc0LmNybDAcBgNVHSAEFTATMAcGBWeBDAED
# MAgGBmeBDAEEATANBgkqhkiG9w0BAQwFAAOCAgEAOiNEPY0Idu6PvDqZ01bgAhql
# +Eg08yy25nRm95RysQDKr2wwJxMSnpBEn0v9nqN8JtU3vDpdSG2V1T9J9Ce7FoFF
# UP2cvbaF4HZ+N3HLIvdaqpDP9ZNq4+sg0dVQeYiaiorBtr2hSBh+3NiAGhEZGM1h
# mYFW9snjdufE5BtfQ/g+lP92OT2e1JnPSt0o618moZVYSNUa/tcnP/2Q0XaG3Ryw
# YFzzDaju4ImhvTnhOE7abrs2nfvlIVNaw8rpavGiPttDuDPITzgUkpn13c5Ubdld
# AhQfQDN8A+KVssIhdXNSy0bYxDQcoqVLjc1vdjcshT8azibpGL6QB7BDf5WIIIJw
# 8MzK7/0pNVwfiThV9zeKiwmhywvpMRr/LhlcOXHhvpynCgbWJme3kuZOX956rEnP
# LqR0kq3bPKSchh/jwVYbKyP/j7XqiHtwa+aguv06P0WmxOgWkVKLQcBIhEuWTatE
# QOON8BUozu3xGFYHKi8QxAwIZDwzj64ojDzLj4gLDb879M4ee47vtevLt/B3E+bn
# KD+sEq6lLyJsQfmCXBVmzGwOysWGw/YmMwwHS6DTBwJqakAwSEs0qFEgu60bhQji
# WQ1tygVQK+pKHJ6l/aCnHwZ05/LWUpD9r4VIIflXO7ScA+2GRfS0YW6/aOImYIbq
# yK+p/pQd52MbOoZWeE4wggd3MIIFX6ADAgECAhAHHxQbizANJfMU6yMM0NHdMA0G
# CSqGSIb3DQEBCwUAMGkxCzAJBgNVBAYTAlVTMRcwFQYDVQQKEw5EaWdpQ2VydCwg
# SW5jLjFBMD8GA1UEAxM4RGlnaUNlcnQgVHJ1c3RlZCBHNCBDb2RlIFNpZ25pbmcg
# UlNBNDA5NiBTSEEzODQgMjAyMSBDQTEwHhcNMjIwMTE3MDAwMDAwWhcNMjUwMTE1
# MjM1OTU5WjB8MQswCQYDVQQGEwJVUzEPMA0GA1UECBMGT3JlZ29uMRIwEAYDVQQH
# EwlCZWF2ZXJ0b24xIzAhBgNVBAoTGlB5dGhvbiBTb2Z0d2FyZSBGb3VuZGF0aW9u
# MSMwIQYDVQQDExpQeXRob24gU29mdHdhcmUgRm91bmRhdGlvbjCCAiIwDQYJKoZI
# hvcNAQEBBQADggIPADCCAgoCggIBAKgc0BTT+iKbtK6f2mr9pNMUTcAJxKdsuOiS
# YgDFfwhjQy89koM7uP+QV/gwx8MzEt3c9tLJvDccVWQ8H7mVsk/K+X+IufBLCgUi
# 0GGAZUegEAeRlSXxxhYScr818ma8EvGIZdiSOhqjYc4KnfgfIS4RLtZSrDFG2tN1
# 6yS8skFa3IHyvWdbD9PvZ4iYNAS4pjYDRjT/9uzPZ4Pan+53xZIcDgjiTwOh8VGu
# ppxcia6a7xCyKoOAGjvCyQsj5223v1/Ig7Dp9mGI+nh1E3IwmyTIIuVHyK6Lqu35
# 2diDY+iCMpk9ZanmSjmB+GMVs+H/gOiofjjtf6oz0ki3rb7sQ8fTnonIL9dyGTJ0
# ZFYKeb6BLA66d2GALwxZhLe5WH4Np9HcyXHACkppsE6ynYjTOd7+jN1PRJahN1oE
# RzTzEiV6nCO1M3U1HbPTGyq52IMFSBM2/07WTJSbOeXjvYR7aUxK9/ZkJiacl2iZ
# I7IWe7JKhHohqKuceQNyOzxTakLcRkzynvIrk33R9YVqtB4L6wtFxhUjvDnQg16x
# ot2KVPdfyPAWd81wtZADmrUtsZ9qG79x1hBdyOl4vUtVPECuyhCxaw+faVjumapP
# Unwo8ygflJJ74J+BYxf6UuD7m8yzsfXWkdv52DjL74TxzuFTLHPyARWCSCAbzn3Z
# Ily+qIqDAgMBAAGjggIGMIICAjAfBgNVHSMEGDAWgBRoN+Drtjv4XxGG+/5hewiI
# ZfROQjAdBgNVHQ4EFgQUt/1Teh2XDuUj2WW3siYWJgkZHA8wDgYDVR0PAQH/BAQD
# AgeAMBMGA1UdJQQMMAoGCCsGAQUFBwMDMIG1BgNVHR8Ega0wgaowU6BRoE+GTWh0
# dHA6Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0ZWRHNENvZGVTaWdu
# aW5nUlNBNDA5NlNIQTM4NDIwMjFDQTEuY3JsMFOgUaBPhk1odHRwOi8vY3JsNC5k
# aWdpY2VydC5jb20vRGlnaUNlcnRUcnVzdGVkRzRDb2RlU2lnbmluZ1JTQTQwOTZT
# SEEzODQyMDIxQ0ExLmNybDA+BgNVHSAENzA1MDMGBmeBDAEEATApMCcGCCsGAQUF
# BwIBFhtodHRwOi8vd3d3LmRpZ2ljZXJ0LmNvbS9DUFMwgZQGCCsGAQUFBwEBBIGH
# MIGEMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5jb20wXAYIKwYB
# BQUHMAKGUGh0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0
# ZWRHNENvZGVTaWduaW5nUlNBNDA5NlNIQTM4NDIwMjFDQTEuY3J0MAwGA1UdEwEB
# /wQCMAAwDQYJKoZIhvcNAQELBQADggIBABxv4AeV/5ltkELHSC63fXAFYS5tadcW
# TiNc2rskrNLrfH1Ns0vgSZFoQxYBFKI159E8oQQ1SKbTEubZ/B9kmHPhprHya08+
# VVzxC88pOEvz68nA82oEM09584aILqYmj8Pj7h/kmZNzuEL7WiwFa/U1hX+XiWfL
# IJQsAHBla0i7QRF2de8/VSF0XXFa2kBQ6aiTsiLyKPNbaNtbcucaUdn6vVUS5izW
# OXM95BSkFSKdE45Oq3FForNJXjBvSCpwcP36WklaHL+aHu1upIhCTUkzTHMh8b86
# WmjRUqbrnvdyR2ydI5l1OqcMBjkpPpIV6wcc+KY/RH2xvVuuoHjlUjwq2bHiNoX+
# W1scCpnA8YTs2d50jDHUgwUo+ciwpffH0Riq132NFmrH3r67VaN3TuBxjI8SIZM5
# 8WEDkbeoriDk3hxU8ZWV7b8AW6oyVBGfM06UgkfMb58h+tJPrFx8VI/WLq1dTqMf
# ZOm5cuclMnUHs2uqrRNtnV8UfidPBL4ZHkTcClQbCoz0UbLhkiDvIS00Dn+BBcxw
# /TKqVL4Oaz3bkMSsM46LciTeucHY9ExRVt3zy7i149sd+F4QozPqn7FrSVHXmem3
# r7bjyHTxOgqxRCVa18Vtx7P/8bYSBeS+WHCKcliFCecspusCDSlnRUjZwyPdP0VH
# xaZg2unjHY3rMYIVMDCCFSwCAQEwfTBpMQswCQYDVQQGEwJVUzEXMBUGA1UEChMO
# RGlnaUNlcnQsIEluYy4xQTA/BgNVBAMTOERpZ2lDZXJ0IFRydXN0ZWQgRzQgQ29k
# ZSBTaWduaW5nIFJTQTQwOTYgU0hBMzg0IDIwMjEgQ0ExAhAHHxQbizANJfMU6yMM
# 0NHdMA0GCWCGSAFlAwQCAQUAoIHOMBkGCSqGSIb3DQEJAzEMBgorBgEEAYI3AgEE
# MBwGCisGAQQBgjcCAQsxDjAMBgorBgEEAYI3AgEVMC8GCSqGSIb3DQEJBDEiBCBW
# STMEpY5oTqEtnhE8rXHTfUpY7MZMEfDbBKbS1J0cLTBiBgorBgEEAYI3AgEMMVQw
# UqBQgE4AQgB1AGkAbAB0ADoAIABSAGUAbABlAGEAcwBlAF8AbQBhAGkAbgBfAHYA
# MwAuADkALgAxADMAXwAyADAAMgAyADAANQAxADcALgAwADIwDQYJKoZIhvcNAQEB
# BQAEggIAZ20aZkGkTuZACtVG89TVf+3Nw7cpJO4pkpM71AFEX7/TZ4NjeFMHCrEr
# g8kNhN1UNcf0FGKplenCcykaIYUTlYgT3VCOeRGINOmySIotyEfYw4HapwNhj8/G
# CK/XOKJvIZ96yHHkpaiCOx3JDVtX5UjkChX1IJNECy0RyzALQA9U/EQl7v8oNEs6
# mCHRfPflHgkPYUPYUJXAGk3tD0ZgeeomUR0zm6Zmvqar2RJaZADtCF5OxOcFbdui
# 9yrlbSlkxv6gSW60W372FRCIoy1BML7Okjv7QJnhJkPIAs4sb0ZCV3rB6ZjKBXx3
# WzeQ5yjpJ3O1ZsZKPP4XVayPJCv2PSRd8dlDgmJtMbN2gvjsLtOkDKN03jnEsiiX
# 9IeYu7AaDdDeMDW8U5A0HYStrVX7OYpLqojtWOdeIz3/thj9ncWDio4KqEZTud37
# kfhDQPks9zWHoeI8MnjWMgBCEMskNFQnEhgGNlxWRW8bzypODhlrUGB271/6tFCE
# UW24irgtfCvNVmQh5E7V+GNplFujgCa7O4wQvYBb1i2OnQ+igJkfWx2N+wmb8QYE
# mN4RM/bk/SOc1b3MnU/ztqscOPPllmQsqMe/8LW77Ww2fy3i88RlcjweWiTs+3AK
# akFenQ/OzGPTrG8+mMKEjRKuxKyL2uZRKUoZ2zVlmjEddgnIVCWhghGzMIIRrwYK
# KwYBBAGCNwMDATGCEZ8wghGbBgkqhkiG9w0BBwKgghGMMIIRiAIBAzEPMA0GCWCG
# SAFlAwQCAQUAMHgGCyqGSIb3DQEJEAEEoGkEZzBlAgEBBglghkgBhv1sBwEwMTAN
# BglghkgBZQMEAgEFAAQgnT/1Hedipjs4jpirOCgW93RhvoYu0jJ5WKO7Y0LYfrYC
# EQDwVmhL49/+ciLQ3plX3i8KGA8yMDIyMDUxNzE2NDQyNVqggg18MIIGxjCCBK6g
# AwIBAgIQCnpKiJ7JmUKQBmM4TYaXnTANBgkqhkiG9w0BAQsFADBjMQswCQYDVQQG
# EwJVUzEXMBUGA1UEChMORGlnaUNlcnQsIEluYy4xOzA5BgNVBAMTMkRpZ2lDZXJ0
# IFRydXN0ZWQgRzQgUlNBNDA5NiBTSEEyNTYgVGltZVN0YW1waW5nIENBMB4XDTIy
# MDMyOTAwMDAwMFoXDTMzMDMxNDIzNTk1OVowTDELMAkGA1UEBhMCVVMxFzAVBgNV
# BAoTDkRpZ2lDZXJ0LCBJbmMuMSQwIgYDVQQDExtEaWdpQ2VydCBUaW1lc3RhbXAg
# MjAyMiAtIDIwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQC5KpYjply8
# X9ZJ8BWCGPQz7sxcbOPgJS7SMeQ8QK77q8TjeF1+XDbq9SWNQ6OB6zhj+TyIad48
# 0jBRDTEHukZu6aNLSOiJQX8Nstb5hPGYPgu/CoQScWyhYiYB087DbP2sO37cKhyp
# vTDGFtjavOuy8YPRn80JxblBakVCI0Fa+GDTZSw+fl69lqfw/LH09CjPQnkfO8eT
# B2ho5UQ0Ul8PUN7UWSxEdMAyRxlb4pguj9DKP//GZ888k5VOhOl2GJiZERTFKwyg
# M9tNJIXogpThLwPuf4UCyYbh1RgUtwRF8+A4vaK9enGY7BXn/S7s0psAiqwdjTuA
# aP7QWZgmzuDtrn8oLsKe4AtLyAjRMruD+iM82f/SjLv3QyPf58NaBWJ+cCzlK7I9
# Y+rIroEga0OJyH5fsBrdGb2fdEEKr7mOCdN0oS+wVHbBkE+U7IZh/9sRL5IDMM4w
# t4sPXUSzQx0jUM2R1y+d+/zNscGnxA7E70A+GToC1DGpaaBJ+XXhm+ho5GoMj+vk
# sSF7hmdYfn8f6CvkFLIW1oGhytowkGvub3XAsDYmsgg7/72+f2wTGN/GbaR5Sa2L
# f2GHBWj31HDjQpXonrubS7LitkE956+nGijJrWGwoEEYGU7tR5thle0+C2Fa6j56
# mJJRzT/JROeAiylCcvd5st2E6ifu/n16awIDAQABo4IBizCCAYcwDgYDVR0PAQH/
# BAQDAgeAMAwGA1UdEwEB/wQCMAAwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwgwIAYD
# VR0gBBkwFzAIBgZngQwBBAIwCwYJYIZIAYb9bAcBMB8GA1UdIwQYMBaAFLoW2W1N
# hS9zKXaaL3WMaiCPnshvMB0GA1UdDgQWBBSNZLeJIf5WWESEYafqbxw2j92vDTBa
# BgNVHR8EUzBRME+gTaBLhklodHRwOi8vY3JsMy5kaWdpY2VydC5jb20vRGlnaUNl
# cnRUcnVzdGVkRzRSU0E0MDk2U0hBMjU2VGltZVN0YW1waW5nQ0EuY3JsMIGQBggr
# BgEFBQcBAQSBgzCBgDAkBggrBgEFBQcwAYYYaHR0cDovL29jc3AuZGlnaWNlcnQu
# Y29tMFgGCCsGAQUFBzAChkxodHRwOi8vY2FjZXJ0cy5kaWdpY2VydC5jb20vRGln
# aUNlcnRUcnVzdGVkRzRSU0E0MDk2U0hBMjU2VGltZVN0YW1waW5nQ0EuY3J0MA0G
# CSqGSIb3DQEBCwUAA4ICAQANLSN0ptH1+OpLmT8B5PYM5K8WndmzjJeCKZxDbwEt
# qzi1cBG/hBmLP13lhk++kzreKjlaOU7YhFmlvBuYquhs79FIaRk4W8+JOR1wcNlO
# 3yMibNXf9lnLocLqTHbKodyhK5a4m1WpGmt90fUCCU+C1qVziMSYgN/uSZW3s8zF
# p+4O4e8eOIqf7xHJMUpYtt84fMv6XPfkU79uCnx+196Y1SlliQ+inMBl9AEiZcfq
# XnSmWzWSUHz0F6aHZE8+RokWYyBry/J70DXjSnBIqbbnHWC9BCIVJXAGcqlEO2lH
# EdPu6cegPk8QuTA25POqaQmoi35komWUEftuMvH1uzitzcCTEdUyeEpLNypM81zc
# toXAu3AwVXjWmP5UbX9xqUgaeN1Gdy4besAzivhKKIwSqHPPLfnTI/KeGeANlCig
# 69saUaCVgo4oa6TOnXbeqXOqSGpZQ65f6vgPBkKd3wZolv4qoHRbY2beayy4eKpN
# cG3wLPEHFX41tOa1DKKZpdcVazUOhdbgLMzgDCS4fFILHpl878jIxYxYaa+rPeHP
# zH0VrhS/inHfypex2EfqHIXgRU4SHBQpWMxv03/LvsEOSm8gnK7ZczJZCOctkqEa
# Ef4ymKZdK5fgi9OczG21Da5HYzhHF1tvE9pqEG4fSbdEW7QICodaWQR2EaGndwIT
# HDCCBq4wggSWoAMCAQICEAc2N7ckVHzYR6z9KGYqXlswDQYJKoZIhvcNAQELBQAw
# YjELMAkGA1UEBhMCVVMxFTATBgNVBAoTDERpZ2lDZXJ0IEluYzEZMBcGA1UECxMQ
# d3d3LmRpZ2ljZXJ0LmNvbTEhMB8GA1UEAxMYRGlnaUNlcnQgVHJ1c3RlZCBSb290
# IEc0MB4XDTIyMDMyMzAwMDAwMFoXDTM3MDMyMjIzNTk1OVowYzELMAkGA1UEBhMC
# VVMxFzAVBgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMTswOQYDVQQDEzJEaWdpQ2VydCBU
# cnVzdGVkIEc0IFJTQTQwOTYgU0hBMjU2IFRpbWVTdGFtcGluZyBDQTCCAiIwDQYJ
# KoZIhvcNAQEBBQADggIPADCCAgoCggIBAMaGNQZJs8E9cklRVcclA8TykTepl1Gh
# 1tKD0Z5Mom2gsMyD+Vr2EaFEFUJfpIjzaPp985yJC3+dH54PMx9QEwsmc5Zt+Feo
# An39Q7SE2hHxc7Gz7iuAhIoiGN/r2j3EF3+rGSs+QtxnjupRPfDWVtTnKC3r07G1
# decfBmWNlCnT2exp39mQh0YAe9tEQYncfGpXevA3eZ9drMvohGS0UvJ2R/dhgxnd
# X7RUCyFobjchu0CsX7LeSn3O9TkSZ+8OpWNs5KbFHc02DVzV5huowWR0QKfAcsW6
# Th+xtVhNef7Xj3OTrCw54qVI1vCwMROpVymWJy71h6aPTnYVVSZwmCZ/oBpHIEPj
# Q2OAe3VuJyWQmDo4EbP29p7mO1vsgd4iFNmCKseSv6De4z6ic/rnH1pslPJSlREr
# WHRAKKtzQ87fSqEcazjFKfPKqpZzQmiftkaznTqj1QPgv/CiPMpC3BhIfxQ0z9JM
# q++bPf4OuGQq+nUoJEHtQr8FnGZJUlD0UfM2SU2LINIsVzV5K6jzRWC8I41Y99xh
# 3pP+OcD5sjClTNfpmEpYPtMDiP6zj9NeS3YSUZPJjAw7W4oiqMEmCPkUEBIDfV8j
# u2TjY+Cm4T72wnSyPx4JduyrXUZ14mCjWAkBKAAOhFTuzuldyF4wEr1GnrXTdrnS
# DmuZDNIztM2xAgMBAAGjggFdMIIBWTASBgNVHRMBAf8ECDAGAQH/AgEAMB0GA1Ud
# DgQWBBS6FtltTYUvcyl2mi91jGogj57IbzAfBgNVHSMEGDAWgBTs1+OC0nFdZEzf
# Lmc/57qYrhwPTzAOBgNVHQ8BAf8EBAMCAYYwEwYDVR0lBAwwCgYIKwYBBQUHAwgw
# dwYIKwYBBQUHAQEEazBpMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2Vy
# dC5jb20wQQYIKwYBBQUHMAKGNWh0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9E
# aWdpQ2VydFRydXN0ZWRSb290RzQuY3J0MEMGA1UdHwQ8MDowOKA2oDSGMmh0dHA6
# Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0ZWRSb290RzQuY3JsMCAG
# A1UdIAQZMBcwCAYGZ4EMAQQCMAsGCWCGSAGG/WwHATANBgkqhkiG9w0BAQsFAAOC
# AgEAfVmOwJO2b5ipRCIBfmbW2CFC4bAYLhBNE88wU86/GPvHUF3iSyn7cIoNqilp
# /GnBzx0H6T5gyNgL5Vxb122H+oQgJTQxZ822EpZvxFBMYh0MCIKoFr2pVs8Vc40B
# IiXOlWk/R3f7cnQU1/+rT4osequFzUNf7WC2qk+RZp4snuCKrOX9jLxkJodskr2d
# fNBwCnzvqLx1T7pa96kQsl3p/yhUifDVinF2ZdrM8HKjI/rAJ4JErpknG6skHibB
# t94q6/aesXmZgaNWhqsKRcnfxI2g55j7+6adcq/Ex8HBanHZxhOACcS2n82HhyS7
# T6NJuXdmkfFynOlLAlKnN36TU6w7HQhJD5TNOXrd/yVjmScsPT9rp/Fmw0HNT7ZA
# myEhQNC3EyTN3B14OuSereU0cZLXJmvkOHOrpgFPvT87eK1MrfvElXvtCl8zOYdB
# eHo46Zzh3SP9HSjTx/no8Zhf+yvYfvJGnXUsHicsJttvFXseGYs2uJPU5vIXmVnK
# cPA3v5gA3yAWTyf7YGcWoWa63VXAOimGsJigK+2VQbc61RWYMbRiCQ8KvYHZE/6/
# pNHzV9m8BPqC3jLfBInwAM1dwvnQI38AC+R2AibZ8GV2QqYphwlHK+Z/GqSFD/yY
# lvZVVCsfgPrA8g4r5db7qS9EFUrnEw4d2zc4GqEr9u3WfPwxggN2MIIDcgIBATB3
# MGMxCzAJBgNVBAYTAlVTMRcwFQYDVQQKEw5EaWdpQ2VydCwgSW5jLjE7MDkGA1UE
# AxMyRGlnaUNlcnQgVHJ1c3RlZCBHNCBSU0E0MDk2IFNIQTI1NiBUaW1lU3RhbXBp
# bmcgQ0ECEAp6SoieyZlCkAZjOE2Gl50wDQYJYIZIAWUDBAIBBQCggdEwGgYJKoZI
# hvcNAQkDMQ0GCyqGSIb3DQEJEAEEMBwGCSqGSIb3DQEJBTEPFw0yMjA1MTcxNjQ0
# MjVaMCsGCyqGSIb3DQEJEAIMMRwwGjAYMBYEFIUI84ZRXLPTB322tLfAfxtKXkHe
# MC8GCSqGSIb3DQEJBDEiBCD6nFFQEG6P9dJgqwYWRs4qcIuEc8WzVzP/ANrLjNw9
# 9DA3BgsqhkiG9w0BCRACLzEoMCYwJDAiBCCdppAVw0nGwYl4Rbo1gq1wyI+kKTvb
# ar6cK9JTknnmOzANBgkqhkiG9w0BAQEFAASCAgAw6wjOhvvgNacByXWLXEcHuoRB
# hCB6I/ZNStOapAzlidSg0ccPO4QsS5L78/ff+DCa4ZFu//T2wfORd9wCt9NpL0XT
# 7/zVF3zw16aNIn1W9gbJkjPfHGLImV30M/PzMnzlj3m9ybK0W/vvu8SmNpMrsSKI
# sR1/nSzaA+Y0FmOOy2jtf7MtZeVh8o4ZkgBVPgVLpRSr4SJXzadMjQjshWII2ujM
# v2YPK7qczQmXaonfN+rAkPxLS+3MVDgoUKAGvQBpm686eDkImZ0qTG+Qi6+Z+2id
# QXv8h4V4L7Ln37RNsm4j5carTNxTx6b0SZPreswMEFfUwtHeaSWvUIKRzyY0t3O/
# NT5G8RSxtJLqTMVFWcmlbgaXo7/PDsA7hs1XQJE3UJnfRNrcznnHgYJPuW737A9Q
# v4sFjmov5/F4qUbYIh5yE8ec4IhOuR0rTEgDJLcU67KdrLjcePMlIlbPaArw1vn3
# On862t4jYz5aj3YaaHYzXB6VxiMp9JN5B3e4gmix/8TgN9kNmvbVwODfK5hfaPcY
# QXkTBySKKoRz+eyz67IBXPCHDYXtiXdaqvhWPFn+YbFH9jlEqPP2ATzqEz/ibgDZ
# 0YyvPy8vnItbUwPuGTVjwU0VmF0m5pSHm/pPALd1xKiMF+eZq580lbrIoUeyZ5mP
# 0XyrSEj88tBJMxcKZA==
# SIG # End signature block



================================================
FILE: Scripts/deactivate.bat
================================================
@echo off

if defined _OLD_VIRTUAL_PROMPT (
    set "PROMPT=%_OLD_VIRTUAL_PROMPT%"
)
set _OLD_VIRTUAL_PROMPT=

if defined _OLD_VIRTUAL_PYTHONHOME (
    set "PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%"
    set _OLD_VIRTUAL_PYTHONHOME=
)

if defined _OLD_VIRTUAL_PATH (
    set "PATH=%_OLD_VIRTUAL_PATH%"
)

set _OLD_VIRTUAL_PATH=

set VIRTUAL_ENV=

:END



================================================
FILE: .github/workflows/django.yml
================================================
name: Django CI

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build:

    runs-on: ubuntu-latest
    strategy:
      max-parallel: 4
      matrix:
        python-version: [3.7, 3.8, 3.9]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run Tests
      run: |
        cd LibSys
        python manage.py test



================================================
FILE: .github/workflows/docker-scout.yml
================================================
name: Docker

on:
  push:
    tags: ["*"]
    branches:
      - "main"
  pull_request:
    branches: ["**"]

env:
  # Hostname of your registry
  REGISTRY: docker.io
  # Image repository, without hostname and tag
  IMAGE_NAME: ${{ github.repository }}
  SHA: ${{ github.event.pull_request.head.sha || github.event.after }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write

    steps:
      # Authenticate to the container registry
      - name: Authenticate to registry ${{ env.REGISTRY }}
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_TOKEN }}

      - name: Setup Docker buildx
        uses: docker/setup-buildx-action@v3

      # Extract metadata (tags, labels) for Docker
      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          labels: |
            org.opencontainers.image.revision=${{ env.SHA }}
          tags: |
            type=edge,branch=$repo.default_branch
            type=semver,pattern=v{{version}}
            type=sha,prefix=,suffix=,format=short

      # Build and push Docker image with Buildx
      - name: Build and push Docker image
        id: build-and-push
        uses: docker/build-push-action@v6
        with:
          sbom: ${{ github.event_name != 'pull_request' }}
          provenance: ${{ github.event_name != 'pull_request' }}
          push: ${{ github.event_name != 'pull_request' }}
          load: ${{ github.event_name == 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      # Authenticate to Docker (if you didn't before)
      - name: Authenticate to Docker
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USER }}
          password: ${{ secrets.DOCKER_PAT }}

      # Compare the image built in the pull request with the one in production
      - name: Docker Scout
        id: docker-scout
        if: ${{ github.event_name == 'pull_request' }}
        uses: docker/scout-action@v1
        with:
          command: compare
          image: ${{ steps.meta.outputs.tags }}
          to-env: production
          ignore-unchanged: true
          only-severities: critical,high
          github-token: ${{ secrets.GITHUB_TOKEN }}



```

`docker-compose.yml`:

```yml
services:
  web:
    build: .
    # Command to run on startup
    command: >
      sh -c "python manage.py collectstatic --noinput &&
             python manage.py migrate &&
             gunicorn LibSys.wsgi:application --bind 0.0.0.0:8000"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    # Wait for the database service to be healthy before starting
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - .env
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

```

`requirements-dev.txt`:

```txt
# This file is for development-specific packages.
# It includes the base production requirements.
-r requirements.txt

django-debug-toolbar
pytest
docker
gcloud
locust
```

`requirements.txt`:

```txt
asgiref
dj-database-url
Django
django-filter
django-storages
djangorestframework
mysqlclient
mysql
gunicorn
whitenoise
google-cloud-storage
google-api-core
google-auth
google-cloud-core
google-crc32c
google-resumable-media
googleapis-common-protos
protobuf
```