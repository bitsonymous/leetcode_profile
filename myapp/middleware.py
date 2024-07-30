import time
from django.core.cache import cache

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self.is_rate_limited(request):
            from django.http import HttpResponseTooManyRequests
            return HttpResponseTooManyRequests("Rate limit exceeded")
        response = self.get_response(request)
        return response

    def is_rate_limited(self, request):
        ip = self.get_client_ip(request)
        key = f"rate_limit_{ip}"
        request_count = cache.get(key, 0)

        if request_count >= 5:
            return True

        cache.set(key, request_count + 1, timeout=60)
        return False

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
