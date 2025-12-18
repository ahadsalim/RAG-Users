from django.conf import settings


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
            except Exception:
                pass
        
        response = self.get_response(request)
        return response
