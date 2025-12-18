from django.conf import settings
from datetime import datetime


class DynamicAdminTitleMiddleware:
    """Middleware to dynamically set admin site title from SiteSettings"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only process admin requests
        if request.path.startswith('/admin/'):
            try:
                from core.models import SiteSettings
                site_settings = SiteSettings.get_settings()
                if site_settings and site_settings.admin_site_name:
                    from django.contrib import admin
                    admin.site.site_header = site_settings.admin_site_name
                    admin.site.site_title = site_settings.admin_site_name
                    admin.site.index_title = f"خوش آمدید به {site_settings.admin_site_name}"
                    
                    # Update Jazzmin settings dynamically
                    if hasattr(settings, 'JAZZMIN_SETTINGS'):
                        settings.JAZZMIN_SETTINGS['copyright'] = site_settings.copyright_text or f"{site_settings.admin_site_name} © {datetime.now().year}"
                        settings.JAZZMIN_SETTINGS['site_title'] = site_settings.admin_site_name
                        settings.JAZZMIN_SETTINGS['site_header'] = site_settings.admin_site_name
                        settings.JAZZMIN_SETTINGS['welcome_sign'] = f"خوش آمدید به {site_settings.admin_site_name}"
            except Exception:
                pass
        
        response = self.get_response(request)
        return response
