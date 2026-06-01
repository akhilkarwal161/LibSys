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
