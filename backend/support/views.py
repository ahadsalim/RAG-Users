from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    TicketDepartment, TicketCategory, Ticket, TicketMessage,
    TicketAttachment, TicketForward, TicketHistory, CannedResponse,
    SLAPolicy
)
from .serializers import (
    TicketDepartmentSerializer, TicketDepartmentListSerializer,
    TicketCategorySerializer, TicketCategoryListSerializer,
    TicketSerializer, TicketListSerializer, TicketCreateSerializer,
    TicketUpdateSerializer, TicketRatingSerializer,
    TicketMessageSerializer, TicketMessageCreateSerializer,
    TicketAttachmentSerializer, TicketHistorySerializer,
    TicketForwardSerializer, CannedResponseSerializer,
    SLAPolicySerializer, TicketStatsSerializer,
    ForwardTicketSerializer
)
from .permissions import IsStaffOrReadOnly, IsTicketOwnerOrStaff


class TicketDepartmentViewSet(viewsets.ModelViewSet):
    """
    ویوست دپارتمان‌های پشتیبانی
    """
    queryset = TicketDepartment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'created_at']
    ordering = ['-priority', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list' and not self.request.user.is_staff:
            return TicketDepartmentListSerializer
        return TicketDepartmentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True, is_public=True)
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def agents(self, request, pk=None):
        """لیست کارشناسان دپارتمان"""
        department = self.get_object()
        from .serializers import UserMinimalSerializer
        agents = department.get_available_agents()
        serializer = UserMinimalSerializer(agents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """آمار دپارتمان"""
        department = self.get_object()
        tickets = department.tickets.all()
        
        stats = {
            'total_tickets': tickets.count(),
            'open_tickets': tickets.filter(status='open').count(),
            'in_progress_tickets': tickets.filter(status='in_progress').count(),
            'waiting_tickets': tickets.filter(status='waiting').count(),
            'resolved_tickets': tickets.filter(status='resolved').count(),
            'closed_tickets': tickets.filter(status='closed').count(),
            'agents_count': department.agents.filter(is_active=True).count(),
        }
        return Response(stats)


class TicketCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ویوست دسته‌بندی تیکت‌ها
    """
    queryset = TicketCategory.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order']
    ordering = ['order', 'name']
    
    def get_serializer_class(self):
        if self.request.user.is_staff:
            return TicketCategorySerializer
        return TicketCategorySerializer
    
    def get_queryset(self):
        queryset = TicketCategory.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        """لیست همه دسته‌بندی‌ها (بدون سلسله مراتب)"""
        queryset = TicketCategory.objects.filter(is_active=True)
        serializer = TicketCategoryListSerializer(queryset, many=True)
        return Response(serializer.data)


class TicketViewSet(viewsets.ModelViewSet):
    """
    ویوست تیکت‌ها
    """
    queryset = Ticket.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsTicketOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'department', 'assigned_to']
    search_fields = ['ticket_number', 'subject', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        elif self.action == 'create':
            return TicketCreateSerializer
        elif self.action in ['update', 'partial_update']:
            if self.request.user.is_staff:
                return TicketUpdateSerializer
            return TicketRatingSerializer
        elif self.action == 'rate':
            return TicketRatingSerializer
        return TicketSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.is_staff:
            # کارشناسان می‌توانند تیکت‌های دپارتمان خود را ببینند
            if not user.is_superuser:
                departments = user.support_departments.all()
                queryset = queryset.filter(
                    Q(department__in=departments) | Q(assigned_to=user)
                )
        else:
            # کاربران فقط تیکت‌های خود را می‌بینند
            queryset = queryset.filter(user=user)
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # فیلتر تیکت‌های خوانده نشده
        unread = self.request.query_params.get('unread')
        if unread == 'true':
            if user.is_staff:
                queryset = queryset.filter(staff_read=False)
            else:
                queryset = queryset.filter(user_read=False)
        
        return queryset.select_related(
            'user', 'assigned_to', 'category', 'department', 'organization'
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # علامت‌گذاری به عنوان خوانده شده
        if request.user.is_staff:
            instance.staff_read = True
        else:
            instance.user_read = True
        instance.save(update_fields=['staff_read', 'user_read'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """پاسخ به تیکت"""
        ticket = self.get_object()
        
        serializer = TicketMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.save(
            ticket=ticket,
            sender=request.user,
            is_staff_reply=request.user.is_staff
        )
        
        # به‌روزرسانی وضعیت تیکت
        if request.user.is_staff:
            if ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save(update_fields=['status'])
        else:
            if ticket.status == 'waiting':
                ticket.status = 'in_progress'
                ticket.save(update_fields=['status'])
        
        # ثبت در تاریخچه
        TicketHistory.objects.create(
            ticket=ticket,
            user=request.user,
            action='message_added',
            description='پیام جدید اضافه شد'
        )
        
        return Response(
            TicketMessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def forward(self, request, pk=None):
        """فوروارد تیکت به کارشناس یا دپارتمان دیگر"""
        if not request.user.is_staff:
            return Response(
                {'error': 'فقط کارشناسان می‌توانند تیکت را فوروارد کنند'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ticket = self.get_object()
        serializer = ForwardTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        to_agent = None
        to_department = None
        
        if serializer.validated_data.get('to_agent'):
            to_agent = get_object_or_404(
                User, id=serializer.validated_data['to_agent'], is_staff=True
            )
        
        if serializer.validated_data.get('to_department'):
            to_department = get_object_or_404(
                TicketDepartment, id=serializer.validated_data['to_department']
            )
        
        # ایجاد رکورد فوروارد
        forward = TicketForward.objects.create(
            ticket=ticket,
            from_agent=request.user,
            to_agent=to_agent,
            to_department=to_department,
            reason=serializer.validated_data.get('reason', '')
        )
        
        # به‌روزرسانی تیکت
        if to_agent:
            ticket.assigned_to = to_agent
        if to_department:
            ticket.department = to_department
            # تخصیص خودکار به کارشناس دپارتمان جدید
            if to_department.auto_assign and not to_agent:
                new_agent = to_department.get_agent_with_least_tickets()
                if new_agent:
                    ticket.assigned_to = new_agent
        
        ticket.save()
        
        # ثبت در تاریخچه
        TicketHistory.objects.create(
            ticket=ticket,
            user=request.user,
            action='forwarded',
            new_value={
                'to_agent': str(to_agent.id) if to_agent else None,
                'to_department': str(to_department.id) if to_department else None
            },
            description=f'تیکت فوروارد شد'
        )
        
        # ایجاد یادداشت داخلی
        if serializer.validated_data.get('reason'):
            TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                content=f"فوروارد شد: {serializer.validated_data['reason']}",
                message_type='forward',
                is_staff_reply=True
            )
        
        return Response(
            TicketForwardSerializer(forward).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """بستن تیکت"""
        ticket = self.get_object()
        
        if ticket.status == 'closed':
            return Response(
                {'error': 'تیکت قبلاً بسته شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ticket.status = 'closed'
        ticket.closed_at = timezone.now()
        ticket.save()
        
        # ثبت در تاریخچه
        TicketHistory.objects.create(
            ticket=ticket,
            user=request.user,
            action='closed',
            description='تیکت بسته شد'
        )
        
        return Response({'message': 'تیکت با موفقیت بسته شد'})
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """بازگشایی تیکت"""
        ticket = self.get_object()
        
        if ticket.status not in ['closed', 'resolved']:
            return Response(
                {'error': 'فقط تیکت‌های بسته یا حل شده قابل بازگشایی هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ticket.status = 'open'
        ticket.closed_at = None
        ticket.resolved_at = None
        ticket.save()
        
        # ثبت در تاریخچه
        TicketHistory.objects.create(
            ticket=ticket,
            user=request.user,
            action='reopened',
            description='تیکت بازگشایی شد'
        )
        
        return Response({'message': 'تیکت با موفقیت بازگشایی شد'})
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """امتیازدهی به تیکت"""
        ticket = self.get_object()
        
        if ticket.user != request.user:
            return Response(
                {'error': 'فقط صاحب تیکت می‌تواند امتیاز دهد'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if ticket.status not in ['resolved', 'closed']:
            return Response(
                {'error': 'فقط تیکت‌های حل شده یا بسته قابل امتیازدهی هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TicketRatingSerializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # ثبت در تاریخچه
        TicketHistory.objects.create(
            ticket=ticket,
            user=request.user,
            action='rated',
            new_value={'rating': ticket.satisfaction_rating},
            description=f'امتیاز {ticket.satisfaction_rating} داده شد'
        )
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """تاریخچه تیکت"""
        ticket = self.get_object()
        history = ticket.history.all()
        serializer = TicketHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """افزودن یادداشت داخلی (فقط کارشناسان)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'فقط کارشناسان می‌توانند یادداشت داخلی اضافه کنند'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ticket = self.get_object()
        content = request.data.get('content')
        
        if not content:
            return Response(
                {'error': 'محتوای یادداشت الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            content=content,
            message_type='note',
            is_staff_reply=True
        )
        
        return Response(
            TicketMessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_tickets(self, request):
        """تیکت‌های من (برای کاربران)"""
        queryset = self.get_queryset().filter(user=request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TicketListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TicketListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        """تیکت‌های تخصیص داده شده به من (برای کارشناسان)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'فقط کارشناسان دسترسی دارند'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(assigned_to=request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TicketListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TicketListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unassigned(self, request):
        """تیکت‌های بدون کارشناس (برای کارشناسان)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'فقط کارشناسان دسترسی دارند'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(
            assigned_to__isnull=True,
            status__in=['open', 'in_progress']
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TicketListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TicketListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """آمار تیکت‌ها"""
        queryset = self.get_queryset()
        
        # محاسبه میانگین زمان پاسخ
        tickets_with_response = queryset.filter(first_response_at__isnull=False)
        avg_response = None
        if tickets_with_response.exists():
            from django.db.models import ExpressionWrapper, DurationField
            avg_response = tickets_with_response.annotate(
                response_time=ExpressionWrapper(
                    F('first_response_at') - F('created_at'),
                    output_field=DurationField()
                )
            ).aggregate(avg=Avg('response_time'))['avg']
        
        # محاسبه میانگین زمان حل
        tickets_resolved = queryset.filter(resolved_at__isnull=False)
        avg_resolution = None
        if tickets_resolved.exists():
            from django.db.models import ExpressionWrapper, DurationField
            avg_resolution = tickets_resolved.annotate(
                resolution_time=ExpressionWrapper(
                    F('resolved_at') - F('created_at'),
                    output_field=DurationField()
                )
            ).aggregate(avg=Avg('resolution_time'))['avg']
        
        # محاسبه میانگین رضایت
        satisfaction_avg = queryset.filter(
            satisfaction_rating__isnull=False
        ).aggregate(avg=Avg('satisfaction_rating'))['avg']
        
        # شمارش تیکت‌های SLA نقض شده
        now = timezone.now()
        sla_breached = queryset.filter(
            Q(response_due__lt=now, first_response_at__isnull=True) |
            Q(resolution_due__lt=now, resolved_at__isnull=True)
        ).count()
        
        stats = {
            'total_tickets': queryset.count(),
            'open_tickets': queryset.filter(status='open').count(),
            'in_progress_tickets': queryset.filter(status='in_progress').count(),
            'waiting_tickets': queryset.filter(status='waiting').count(),
            'resolved_tickets': queryset.filter(status='resolved').count(),
            'closed_tickets': queryset.filter(status='closed').count(),
            'sla_breached': sla_breached,
            'avg_response_time': avg_response,
            'avg_resolution_time': avg_resolution,
            'satisfaction_avg': satisfaction_avg,
        }
        
        serializer = TicketStatsSerializer(stats)
        return Response(serializer.data)


class CannedResponseViewSet(viewsets.ModelViewSet):
    """
    ویوست پاسخ‌های آماده
    """
    queryset = CannedResponse.objects.filter(is_active=True)
    serializer_class = CannedResponseSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'department', 'is_public']
    search_fields = ['title', 'content']
    ordering_fields = ['title', 'usage_count', 'created_at']
    ordering = ['-usage_count', 'title']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_staff:
            return CannedResponse.objects.none()
        
        # فیلتر بر اساس دپارتمان کارشناس
        if not user.is_superuser:
            departments = user.support_departments.all()
            queryset = queryset.filter(
                Q(department__in=departments) |
                Q(department__isnull=True) |
                Q(is_public=True)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """ثبت استفاده از پاسخ آماده"""
        canned_response = self.get_object()
        canned_response.usage_count += 1
        canned_response.save(update_fields=['usage_count'])
        return Response({'message': 'ثبت شد'})


class SLAPolicyViewSet(viewsets.ModelViewSet):
    """
    ویوست سیاست‌های SLA
    """
    queryset = SLAPolicy.objects.filter(is_active=True)
    serializer_class = SLAPolicySerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['priority', 'department', 'category']
    search_fields = ['name', 'description']
    ordering = ['name']


class TicketDashboardView(APIView):
    """
    داشبورد تیکت‌ها برای کارشناسان
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not user.is_staff:
            # داشبورد کاربر عادی
            tickets = Ticket.objects.filter(user=user)
            return Response({
                'total_tickets': tickets.count(),
                'open_tickets': tickets.filter(status='open').count(),
                'in_progress_tickets': tickets.filter(status='in_progress').count(),
                'waiting_tickets': tickets.filter(status='waiting').count(),
                'resolved_tickets': tickets.filter(status='resolved').count(),
                'closed_tickets': tickets.filter(status='closed').count(),
                'unread_tickets': tickets.filter(user_read=False).count(),
            })
        
        # داشبورد کارشناس
        if user.is_superuser:
            all_tickets = Ticket.objects.all()
        else:
            departments = user.support_departments.all()
            all_tickets = Ticket.objects.filter(
                Q(department__in=departments) | Q(assigned_to=user)
            )
        
        my_tickets = all_tickets.filter(assigned_to=user)
        
        # تیکت‌های SLA نقض شده
        now = timezone.now()
        sla_breached = all_tickets.filter(
            Q(response_due__lt=now, first_response_at__isnull=True) |
            Q(resolution_due__lt=now, resolved_at__isnull=True)
        ).count()
        
        return Response({
            'all_tickets': {
                'total': all_tickets.count(),
                'open': all_tickets.filter(status='open').count(),
                'in_progress': all_tickets.filter(status='in_progress').count(),
                'waiting': all_tickets.filter(status='waiting').count(),
                'on_hold': all_tickets.filter(status='on_hold').count(),
                'resolved': all_tickets.filter(status='resolved').count(),
                'closed': all_tickets.filter(status='closed').count(),
                'unassigned': all_tickets.filter(assigned_to__isnull=True).count(),
                'sla_breached': sla_breached,
            },
            'my_tickets': {
                'total': my_tickets.count(),
                'open': my_tickets.filter(status='open').count(),
                'in_progress': my_tickets.filter(status='in_progress').count(),
                'waiting': my_tickets.filter(status='waiting').count(),
                'unread': my_tickets.filter(staff_read=False).count(),
            },
            'today': {
                'new_tickets': all_tickets.filter(
                    created_at__date=timezone.now().date()
                ).count(),
                'closed_tickets': all_tickets.filter(
                    closed_at__date=timezone.now().date()
                ).count(),
            }
        })
