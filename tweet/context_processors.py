from .models import Wishlist, Rental

def base_template(request):
    """
    Standardizes the base template selection for HTMX shells.
    'is_htmx_partial' is True only when we need a fragment (no Nav/Footer).
    """
    is_hx = request.headers.get("HX-Request", "").lower() == "true"
    is_history = request.headers.get("HX-History-Restore-Request", "").lower() == "true"

    # We only want a partial if it's an HTMX request that IS NOT a history restoration
    is_partial = is_hx and not is_history
    
    return {
        "base_template": "base_htmx.html" if is_partial else "layout.html",
        "is_htmx_partial": is_partial
    }
