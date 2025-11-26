"""
Custom password validators with Persian error messages
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class PersianMinimumLengthValidator:
    """
    Validate whether the password is of a minimum length.
    """
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _('رمز عبور باید حداقل %(min_length)d کاراکتر باشد.'),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _(
            'رمز عبور شما باید حداقل %(min_length)d کاراکتر داشته باشد.'
            % {'min_length': self.min_length}
        )


class PersianNumericPasswordValidator:
    """
    Validate whether the password is not entirely numeric.
    """
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                _('رمز عبور نمی‌تواند فقط از اعداد تشکیل شده باشد.'),
                code='password_entirely_numeric',
            )

    def get_help_text(self):
        return _('رمز عبور شما نمی‌تواند فقط شامل اعداد باشد.')


class PersianCommonPasswordValidator:
    """
    Validate whether the password is a common password.
    """
    def validate(self, password, user=None):
        # Common Persian/English passwords
        common_passwords = [
            '12345678', '123456789', '1234567890',
            'password', 'qwerty', 'abc123',
            '11111111', '00000000',
            'admin123', 'password123',
        ]
        
        if password.lower() in common_passwords:
            raise ValidationError(
                _('این رمز عبور بسیار رایج است. لطفا رمز عبور قوی‌تری انتخاب کنید.'),
                code='password_too_common',
            )

    def get_help_text(self):
        return _('رمز عبور شما نباید یک رمز عبور رایج باشد.')


class PersianUserAttributeSimilarityValidator:
    """
    Validate whether the password is sufficiently different from user attributes.
    """
    def __init__(self, user_attributes=('username', 'first_name', 'last_name', 'email'), max_similarity=0.7):
        self.user_attributes = user_attributes
        self.max_similarity = max_similarity

    def validate(self, password, user=None):
        if not user:
            return

        for attribute_name in self.user_attributes:
            value = getattr(user, attribute_name, None)
            if not value or len(value) < 3:
                continue
            
            # Simple similarity check
            if value.lower() in password.lower() or password.lower() in value.lower():
                raise ValidationError(
                    _('رمز عبور نباید شبیه به اطلاعات شخصی شما باشد.'),
                    code='password_too_similar',
                )

    def get_help_text(self):
        return _('رمز عبور شما نباید شبیه به اطلاعات شخصی شما باشد.')
