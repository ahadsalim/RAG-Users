"""
Custom authentication backends for phone and email login
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class PhoneOrEmailBackend(ModelBackend):
    """
    Authentication backend that allows login with:
    - Phone number (primary)
    - Email (for Django admin and backend)
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # Try to find user by phone number or email
            user = User.objects.get(
                Q(phone_number=username) | Q(email=username)
            )
            
            # Check password
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing
            # difference between existing and non-existing users
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # This shouldn't happen with unique constraints, but handle it
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
