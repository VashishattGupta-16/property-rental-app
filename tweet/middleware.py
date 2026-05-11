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
            # If the profile is incomplete, redirect to the setup page,
            # unless the user is already on an allowed page.
            if not request.user.profile_is_complete():
                # Allowed pages include the profile setup itself, logout,
                # and any URL under the /accounts/ path to prevent auth loops.
                is_allowed_path = (
                    request.path == reverse('profile_setup') or
                    request.path.startswith('/accounts/')
                )

                if not is_allowed_path:
                    return redirect('profile_setup')

        return self.get_response(request)