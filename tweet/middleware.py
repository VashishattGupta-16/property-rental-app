from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.conf import settings
from django.utils.cache import patch_vary_headers
import logging

logger = logging.getLogger(__name__)


class UptimeRobotMiddleware:
    """
    Intercepts UptimeRobot health checks and returns a 200 OK response immediately
    to avoid processing the full Django request lifecycle and generating verbose logs.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'UptimeRobot' in user_agent:
            return HttpResponse("OK")
        return self.get_response(request)


class ProfileCompletionMiddleware:
    """
    Ensures that users complete their profile before accessing other parts of the site.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Pre-resolve static route names to paths to avoid regex overhead per request
        self.allowed_route_names = [
            'profile_setup', 'account_logout', 'offline', 'manifest', 'service_worker'
        ]
        self.protected_path_prefixes = (
            '/accounts/',
            settings.STATIC_URL,
            settings.MEDIA_URL,
        )

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            # If the profile is incomplete, redirect to the setup page,
            if not request.user.profile_is_complete():
                allowed_paths = [reverse(name) for name in self.allowed_route_names]

                # Allow access to static/media, accounts, PWA files, and API/AJAX requests
                is_allowed_path = (
                    request.path in allowed_paths
                    or request.path.startswith(self.protected_path_prefixes)
                    or request.headers.get('x-requested-with') == 'XMLHttpRequest'
                    or 'application/json' in request.headers.get('Accept', '')
                )

                if not is_allowed_path:
                    return redirect('profile_setup')

        return self.get_response(request)


class HtmxVaryMiddleware:
    """
    When the same URL can return either a full page or a fragment depending on
    HTMX headers, caches must key on those headers to avoid mixing variants.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        content_type = response.get("Content-Type", "")
        if isinstance(content_type, str) and content_type.lower().startswith("text/html"):
            patch_vary_headers(response, ("HX-Request", "HX-History-Restore-Request"))

        return response
