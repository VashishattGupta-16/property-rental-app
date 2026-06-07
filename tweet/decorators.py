import functools

def hardware_permission_required(permissions):
    """
    Safe, non-blocking decorator that attaches required hardware metadata 
    to the request for use by the frontend or view logic.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Attach metadata to request. This is purely informative and non-blocking.
            request.required_hardware = permissions
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator