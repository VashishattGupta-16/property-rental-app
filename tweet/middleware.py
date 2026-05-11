from django.shortcuts import redirect
from django.urls import reverse


class ProfileCompletionMiddleware:
    """
    Ensures that users complete their profile before accessing other parts of the site.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            if not request.user.profile_is_complete():
                allowed_paths = [
                    reverse('profile_setup'),
                    reverse('account_logout'),
                ]
                # Allow access to allauth URLs to prevent login loops
                if request.path_info.startswith('/accounts/'):
                    return self.get_response(request)

                if request.path not in allowed_paths:
                    return redirect('profile_setup')

        return self.get_response(request)