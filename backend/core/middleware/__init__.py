"""
Core middleware
"""
from .timezone_middleware import TimezoneMiddleware
from .admin_title_middleware import DynamicAdminTitleMiddleware

__all__ = ['TimezoneMiddleware', 'DynamicAdminTitleMiddleware']
