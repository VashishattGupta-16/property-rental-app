import logging
import traceback
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.conf import settings

logger = logging.getLogger(__name__)

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        try:
            email = sociallogin.account.extra_data.get('email')
            logger.debug(f"[Adapter.pre_social_login] Processing sociallogin for email: {email}")
        except Exception as e:
            logger.error(f"[Adapter.pre_social_login] Unhandled error: {e}", exc_info=True)
            raise

    def save_user(self, request, sociallogin, form=None):
        try:
            user = super().save_user(request, sociallogin, form)
            logger.info(f"[Adapter.save_user] User {user.email} (PK: {user.pk}) processed successfully.")
            return user
        except Exception as e:
            logger.error(f"[Adapter.save_user] CRITICAL ERROR during save_user: {e}", exc_info=True)
            raise

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        # ---------------------------------------------------------------------
        # EXACT FIX: Android PWA Double-Callback Workaround
        # ---------------------------------------------------------------------
        # Android Chrome hits the OAuth callback TWICE when transitioning
        # from a Custom Tab back to an installed WebAPK/PWA.
        # Request 1: Succeeds, logs user in, returns 302.
        # Request 2: Fails (OAuth code used), triggers this error handler.
        # If the user is already authenticated, Request 1 succeeded. 
        # We ignore the error and force redirect them to the success page!
        if request.user.is_authenticated:
            logger.info(f"[Adapter.on_authentication_error] User {request.user.email} is already authenticated! "
                        f"Bypassing PWA double-callback error and redirecting to success.")
            raise ImmediateHttpResponse(HttpResponseRedirect(settings.LOGIN_REDIRECT_URL))

        # Log the full traceback and actual exception class/message
        error_msg = f"Authentication error with provider '{provider.name}'. Error: {error}"
        if exception:
            error_msg += f" | Exception: {type(exception).__name__} - {str(exception)}"
        
        logger.error(f"[Adapter.on_authentication_error] {error_msg}", exc_info=True)
        
        super().on_authentication_error(request, provider, error, exception, extra_context)