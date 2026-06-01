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
