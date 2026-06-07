import logging
import traceback
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def on_authentication_error(
        self, request, provider, error=None, exception=None, extra_context=None
    ):
        print("\n" + "=" * 80)
        print("FULL SOCIAL AUTH TRACEBACK")
        if exception:
            print(type(exception).__name__)
            print(str(exception))
        traceback.print_exc()
        print("=" * 80 + "\n")
        super().on_authentication_error(request, provider, error, exception, extra_context)