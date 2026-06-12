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
            logger.debug(f"[Adapter.pre_social_login] Request PATH: {request.path}")
            logger.debug(f"[Adapter.pre_social_login] Request GET Params: {dict(request.GET)}")
            email = sociallogin.account.extra_data.get('email')
            logger.debug(f"[Adapter.pre_social_login] Processing sociallogin for email: {email}. Existing user: {sociallogin.is_existing}")
        except Exception as e:
            logger.error(f"[Adapter.pre_social_login] Unhandled error: {e}", exc_info=True)
            raise

    def populate_user(self, request, sociallogin, data):
        """
        Traced to ensure Google's data is mapping to the CustomUser fields correctly without IntegrityErrors.
        """
        logger.debug(f"[Adapter.populate_user] Populating user with data: {data}")
        try:
            user = super().populate_user(request, sociallogin, data)
            logger.debug(f"[Adapter.populate_user] Successfully populated user: {getattr(user, 'email', None)}")
            return user
        except Exception as e:
            logger.error(f"[Adapter.populate_user] CRITICAL ERROR during populate_user: {e}", exc_info=True)
            raise

    def save_user(self, request, sociallogin, form=None):
        logger.debug(f"[Adapter.save_user] Beginning save for user: {getattr(sociallogin.user, 'email', 'N/A')}")
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

        # ---------------------------------------------------------------------
        # FORENSIC DEBUGGING DUMP
        # ---------------------------------------------------------------------
        log_parts = [
            "================================================================================",
            "GOOGLE OAUTH EXCEPTION / AUTHENTICATION ERROR",
            f"Provider: {provider.name if provider else 'None'}",
            f"Error Code: {error}",
            f"Exception Type: {type(exception).__name__ if exception else 'None'}",
            f"Exception Message: {str(exception) if exception else 'None'}",
            "--------------------------------------------------------------------------------",
            "REQUEST DETAILS",
            f"Path: {request.path}",
            f"GET Params: {dict(request.GET)}",
            f"Headers: {dict(request.headers)}",
            f"OAuth Code Present: {'code' in request.GET}",
            f"State Param: {request.GET.get('state', 'MISSING')}",
            "--------------------------------------------------------------------------------",
            "SESSION & COOKIE DUMP",
            f"Session Key: {request.session.session_key}",
            f"Session Data: {dict(request.session)}",
            f"Cookies: {dict(request.COOKIES)}",
            "--------------------------------------------------------------------------------",
        ]
        
        if extra_context and 'sociallogin' in extra_context:
            sl = extra_context['sociallogin']
            log_parts.extend([
                "SOCIAL LOGIN DATA",
                f"Is Existing: {sl.is_existing}",
                f"User Email: {getattr(sl.user, 'email', 'N/A')}",
                f"Account UID: {getattr(sl.account, 'uid', 'N/A')}",
                f"Extra Data: {getattr(sl.account, 'extra_data', 'N/A')}",
                "--------------------------------------------------------------------------------"
            ])
            
        log_parts.append("FULL TRACEBACK:")
        if exception:
            log_parts.append("".join(traceback.format_exception(type(exception), exception, exception.__traceback__)))
        else:
            log_parts.append("No Python exception attached. This is likely an OAuth flow/state validation failure.")
        log_parts.append("================================================================================")
        
        logger.error("\n".join(log_parts))

        super().on_authentication_error(request, provider, error, exception, extra_context)