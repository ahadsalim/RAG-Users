from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.TicketDepartmentViewSet, basename='department')
router.register(r'categories', views.TicketCategoryViewSet, basename='category')
router.register(r'tickets', views.TicketViewSet, basename='ticket')
router.register(r'canned-responses', views.CannedResponseViewSet, basename='canned-response')
router.register(r'sla-policies', views.SLAPolicyViewSet, basename='sla-policy')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.TicketDashboardView.as_view(), name='ticket-dashboard'),
]
