import logging
import traceback
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def on_authentication_error(
        self, request, provider, error=None, exception=None, extra_context=None
    ):
        """
        Overrides the default error handler to print the exact error to the terminal.
        """
        print("\n" + "!" * 60)
        print("SOCIAL AUTHENTICATION ERROR")
        print(f"Provider: {provider}")
        print(f"Error Code: {error}")
        print(f"Request Path: {request.path}")
        print(f"Session Key: {request.session.session_key}")
        
        # Filter out large binary blobs if any, show relevant OAuth keys
        session_data = {k: v for k, v in request.session.items() if 'state' in k.lower() or 'social' in k.lower()}
        print(f"Relevant Session Data: {session_data}")

        print(f"Exception: {repr(exception)}")
        if exception:
            traceback.print_exc()
        if extra_context:
            print(f"Extra Context: {extra_context}")
        print("!" * 60 + "\n")
        super().on_authentication_error(request, provider, error, exception, extra_context)