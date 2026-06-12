import logging
import traceback
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # This catches errors BEFORE the user is saved
        try:
            logger.info(f"Social login attempt for: {sociallogin.account.extra_data.get('email')}")
        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}")

    def save_user(self, request, sociallogin, form=None):
        try:
            logger.info("Starting save_user process...")
            user = super().save_user(request, sociallogin, form)
            
            if not user:
                logger.error("super().save_user returned None!")
                raise ValueError("Adapter returned None user object")
                
            logger.info(f"Successfully saved user: {user.email}")
            return user
            
        except Exception as e:
            logger.error("!!! CRITICAL ERROR IN SAVE_USER !!!")
            logger.error(str(e))
            traceback.print_exc()
            # Still return the user to avoid breaking the flow, 
            # but now the error will be in your Render logs!
            return super().save_user(request, sociallogin, form)

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        logger.error(f"Auth error detected: {error}")
        if exception:
            logger.error(f"Exception details: {str(exception)}")
            traceback.print_exc()
        super().on_authentication_error(request, provider, error, exception, extra_context)