import logging
import traceback
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates with a
        social provider, but before the login is actually processed.
        This is the ideal place to inspect data or interrupt the login.
        """
        try:
            email = sociallogin.account.extra_data.get('email')
            logger.info(f"[Adapter.pre_social_login] Pre-login check for user: {email}")
            # You could add logic here to prevent certain users from logging in.
            # For example:
            # if not email.endswith('@example.com'):
            #     logger.warning(f"Blocking non-example.com email: {email}")
            #     raise ImmediateHttpResponse(redirect(reverse('account_login')))
        except Exception as e:
            logger.error(f"[Adapter.pre_social_login] Error: {e}", exc_info=True)

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a user instance to the database. This is a critical point for debugging
        OAuth issues, as it's where user data from the social provider is finalized.
        """
        try:
            logger.debug("[Adapter.save_user] Starting user save process...")
            # The super() call handles the logic of creating or finding the user.
            user = super().save_user(request, sociallogin, form)
            logger.info(f"[Adapter.save_user] User {user.email} (PK: {user.pk}) processed successfully.")
            return user
        except Exception as e:
            # This block catches any error during the user creation/update process.
            # Re-raising the exception is better than returning None, as it gives a clear
            # traceback in the logs and triggers the on_authentication_error handler.
            logger.error(f"[Adapter.save_user] CRITICAL ERROR during save_user: {e}", exc_info=True)
            raise

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        """
        This method is called when an error occurs during the authentication process.
        We add detailed logging here to capture the exact reason for the failure.
        """
        logger.error(f"[Adapter.on_authentication_error] Authentication error with provider '{provider.name}'. Error: {error}")
        if exception:
            logger.error(f"[Adapter.on_authentication_error] Exception details: {str(exception)}", exc_info=True)
        super().on_authentication_error(request, provider, error, exception, extra_context)