"""
Custom JWT tokens for Core API compatibility
"""
from rest_framework_simplejwt.tokens import AccessToken as BaseAccessToken, RefreshToken as BaseRefreshToken


class CustomAccessToken(BaseAccessToken):
    """
    Custom access token with additional user fields required by Core API.
    
    Core API expects these fields in JWT payload:
    - sub: user ID
    - username: user's username
    - email: user's email
    - tier: subscription tier (free, basic, premium, enterprise)
    - exp: expiration time
    - iat: issued at time
    - type: token type (should be 'access')
    """
    
    @classmethod
    def for_user(cls, user):
        """
        Create token with username, email, and tier fields for Core API.
        
        Args:
            user: User instance
            
        Returns:
            Token with all required fields
        """
        token = super().for_user(user)
        
        # Add username (Core requires this)
        if user.username:
            token['username'] = user.username
        else:
            # Generate username from email or ID if not set
            if user.email:
                token['username'] = user.email.split('@')[0]
            else:
                token['username'] = f"user_{str(user.id)[:8]}"
        
        # Add email (Core requires this)
        token['email'] = user.email if user.email else None
        
        # Determine tier based on subscription
        tier = 'free'  # Default
        
        if hasattr(user, 'subscription') and user.subscription:
            # Map subscription tier to Core tier
            subscription_tier = getattr(user.subscription, 'tier', 'free')
            tier_mapping = {
                'free': 'free',
                'basic': 'basic',
                'professional': 'premium',
                'premium': 'premium',
                'enterprise': 'enterprise',
            }
            tier = tier_mapping.get(subscription_tier, 'free')
        elif hasattr(user, 'is_superuser') and user.is_superuser:
            tier = 'enterprise'
        elif hasattr(user, 'is_staff') and user.is_staff:
            tier = 'premium'
        
        token['tier'] = tier
        
        # Change 'token_type' to 'type' for Core API compatibility
        if 'token_type' in token:
            token['type'] = token['token_type']
            del token['token_type']
        else:
            token['type'] = 'access'
        
        return token


class CustomRefreshToken(BaseRefreshToken):
    """Custom refresh token with type field."""
    
    @classmethod
    def for_user(cls, user):
        """Create refresh token with type field."""
        token = super().for_user(user)
        
        # Change 'token_type' to 'type'
        if 'token_type' in token:
            token['type'] = token['token_type']
            del token['token_type']
        else:
            token['type'] = 'refresh'
        
        return token
