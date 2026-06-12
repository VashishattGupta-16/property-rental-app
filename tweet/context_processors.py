from .models import Wishlist, Rental
from django.urls import reverse

def base_template(request):
    """
    Standardizes the base template selection for HTMX shells.
    'is_htmx_partial' is True only when we need a fragment (no Nav/Footer).
    """
    is_hx = request.headers.get("HX-Request", "").lower() == "true"
    is_history = request.headers.get("HX-History-Restore-Request", "").lower() == "true"

    # We only want a partial if it's an HTMX request that IS NOT a history restoration
    is_partial = is_hx and not is_history

    # Determine if the Terms & Conditions modal should be shown for the current user.
    show_terms_modal = False
    if request.user.is_authenticated and not request.user.is_staff:
        # Check if the user has a record of accepting the terms.
        if not getattr(request.user, 'terms_accepted_at', None):
            # Define paths where the modal should NOT be shown to avoid loops or interruptions.
            excluded_paths = [reverse('account_logout'), reverse('accept_terms')]
            # Show the modal if the current path is not in the exclusion list.
            if request.path not in excluded_paths:
                show_terms_modal = True

    return {
        "base_template": "base_htmx.html" if is_partial else "layout.html",
        "is_htmx_partial": is_partial,
        "show_terms_modal": show_terms_modal,
    }
