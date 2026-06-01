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
