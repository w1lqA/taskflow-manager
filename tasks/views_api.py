from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import Task, Project
from .serializers import TaskSerializer, ProjectSerializer, CommentSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    """API для управления проектами"""
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title']
    
    def get_queryset(self):
        # показываем только проекты текущего пользователя
        return Project.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        # автоматически устанавливаем владельца
        serializer.save(owner=self.request.user)

class TaskViewSet(viewsets.ModelViewSet):
    """API для управления задачами (ОСНОВНОЙ)"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    # настройки фильтрации (позже расширим)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'project']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    ordering = ['-created_at']  # по умолчанию сортируем по дате создания
    
    def get_queryset(self):
        # базовый queryset - задачи текущего пользователя
        queryset = Task.objects.filter(author=self.request.user)
        
        return queryset
    
    # @action методы (специальные эндпоинты)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """получить все просроченные задачи (detail=False - для списка)"""
        queryset = self.get_queryset().filter(
            Q(due_date__lt=timezone.now()) &  # срок прошел
            ~Q(status='done') &                # и задача не выполнена
            ~Q(status='backlog')               # и не отложена
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """изменить статус задачи (detail=True - для конкретного объекта)"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'не указан статус'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # проверяем, что статус допустимый
        valid_statuses = dict(Task.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return Response(
                {'error': f'неверный статус. допустимые: {list(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # обновляем статус
        task.status = new_status
        
        # если статус "выполнено" - ставим дату выполнения
        if new_status == 'done' and not task.completed_at:
            task.completed_at = timezone.now()
        # если статус изменился с "выполнено" на другой - очищаем дату
        elif new_status != 'done' and task.completed_at:
            task.completed_at = None
        
        task.save()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """задачи на ближайшие 7 дней (пример сложного запроса с Q)"""
        seven_days_later = timezone.now() + timedelta(days=7)
        
        queryset = self.get_queryset().filter(
            Q(due_date__gte=timezone.now()) &      # срок еще не наступил
            Q(due_date__lte=seven_days_later) &    # но в ближайшие 7 дней
            ~Q(status='done') &                     # и не выполнена
            ~Q(status='backlog')                    # и не отложена
        ).order_by('due_date')  # сортируем по сроку
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)