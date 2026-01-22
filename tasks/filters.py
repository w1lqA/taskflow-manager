import django_filters
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Task

class TaskFilter(django_filters.FilterSet):
    # 1. Фильтрация задач по статусу
    status = django_filters.ChoiceFilter(
        choices=Task.STATUS_CHOICES,
        label='Статус'
    )
    
    # 2. Фильтрация по приоритету
    priority = django_filters.NumberFilter(
        label='Приоритет (1-5)'
    )
    
    # 3. Фильтрация по дате окончания
    due_date = django_filters.DateFilter(
        method='filter_due_date',
        label='Конкретная дата окончания (ГГГГ-ММ-ДД)'
    )
    
    # 4. Фильтрация по диапазону дат
    due_date__gte = django_filters.DateFilter(
        method='filter_due_date_gte',
        label='Дата окончания от (ГГГГ-ММ-ДД)'
    )
    due_date__lte = django_filters.DateFilter(
        method='filter_due_date_lte',
        label='Дата окончания до (ГГГГ-ММ-ДД)'
    )
    
    # Дополнительные фильтры
    has_due_date = django_filters.BooleanFilter(
        method='filter_has_due_date',
        label='Есть срок выполнения'
    )
    
    search = django_filters.CharFilter(
        method='filter_search',
        label='Поиск по названию/описанию'
    )
    
    class Meta:
        model = Task
        fields = ['status', 'priority', 'project']
    
    # Кастомные методы для фильтрации по датам
    
    def filter_due_date(self, queryset, name, value):
        """Фильтр по конкретной дате (игнорируя время)"""
        if value:
            # Преобразуем date в datetime для сравнения
            start_datetime = timezone.make_aware(
                datetime.combine(value, datetime.min.time())
            )
            end_datetime = timezone.make_aware(
                datetime.combine(value, datetime.max.time())
            )
            
            return queryset.filter(
                due_date__gte=start_datetime,
                due_date__lte=end_datetime
            )
        return queryset
    
    def filter_due_date_gte(self, queryset, name, value):
        """Фильтр: дата окончания >= указанной даты"""
        if value:
            start_datetime = timezone.make_aware(
                datetime.combine(value, datetime.min.time())
            )
            return queryset.filter(due_date__gte=start_datetime)
        return queryset
    
    def filter_due_date_lte(self, queryset, name, value):
        """Фильтр: дата окончания <= указанной даты"""
        if value:
            end_datetime = timezone.make_aware(
                datetime.combine(value, datetime.max.time())
            )
            return queryset.filter(due_date__lte=end_datetime)
        return queryset
    
    def filter_has_due_date(self, queryset, name, value):
        """Фильтр: есть/нет срок выполнения"""
        if value:
            return queryset.filter(due_date__isnull=False)
        else:
            return queryset.filter(due_date__isnull=True)
    
    def filter_search(self, queryset, name, value):
        """Поиск по названию и описанию"""
        return queryset.filter(
            Q(title__icontains=value) | 
            Q(description__icontains=value)
        )