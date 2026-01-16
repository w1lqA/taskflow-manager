from django.contrib import admin
from django.utils.html import format_html
from .models import Project, Tag, Task, Comment, TaskHistory

# вспомогательный класс для inline
class CommentInline(admin.TabularInline):
    """Inline для отображения комментариев внутри задачи."""
    model = Comment
    extra = 0  # не показываем пустые формы для новых комментариев
    readonly_fields = ('author', 'created_at', 'updated_at')
    fields = ('content', 'author', 'created_at', 'updated_at')
    verbose_name = 'Комментарий'
    verbose_name_plural = 'Комментарии к задаче'


# админ класс для проектов/
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'colored_title', 'owner_link', 'tasks_count', 'created_at')
    list_display_links = ('id', 'colored_title')  # Кликабельные поля
    list_filter = ('created_at',)  # Фильтр по дате создания
    search_fields = ('title', 'owner__username')  # Поиск по названию и владельцу
    raw_id_fields = ('owner',)  # Поле для поиска пользователя по ID вместо списка
    readonly_fields = ('created_at', 'updated_at')  # Только для чтения
    date_hierarchy = 'created_at'  # Навигация по датам сверху
    list_per_page = 20

    # Кастомный метод для отображения в list_display
    @admin.display(description='Название (с цветом)')
    def colored_title(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            obj.color,
            obj.title
        )
    colored_title.short_description = 'Название'  # Заголовок колонки

    # Кастомный метод для отображения владельца как ссылки
    @admin.display(description='Владелец')
    def owner_link(self, obj):
        from django.urls import reverse
        from django.utils.html import escape
        url = reverse('admin:users_user_change', args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, escape(obj.owner.username))

    # Кастомный метод для подсчета задач в проекте
    @admin.display(description='Кол-во задач', ordering='tasks_count')
    def tasks_count(self, obj):
        return obj.tasks.count()


# админ клас для тегов
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'colored_name', 'tasks_count_display')
    list_display_links = ('id', 'colored_name')
    search_fields = ('name',)
    list_per_page = 25

    @admin.display(description='Тег (с цветом)')
    def colored_name(self, obj):
        return format_html(
            '<span style="color: {}; background-color: {}20; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color,
            obj.name
        )

    @admin.display(description='Используется в задачах')
    def tasks_count_display(self, obj):
        return obj.tasks.count()


# админ класс для задач (дефолтный)
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # нвстройка отображаемых полей в списке
    list_display = (
        'id',
        'title',
        'project_link',
        'author_link',
        'status',  # <-- Оригинальное поле для list_editable
        'status_display',  # <-- Красивое отображение (только для просмотра)
        'priority_display',
        'due_date',
        'completed_at',
        'created_at'
    )
    list_display_links = ('id', 'title')  # Кликабельные поля
    list_filter = ('status', 'priority', 'due_date', 'created_at')  # Фильтры справа
    search_fields = ('title', 'description', 'project__title')  # Поиск
    raw_id_fields = ('project', 'author', 'editor')  # Поиск по ID для ForeignKey
    filter_horizontal = ('tags',)  # Виджет для ManyToMany
    readonly_fields = ('created_at', 'updated_at', 'completed_at_display')
    date_hierarchy = 'created_at'  # Навигация по датам
    inlines = (CommentInline,)  # Inline для комментариев
    list_per_page = 30
    list_editable = ('status',)  # Редактирование статуса прямо в списке

    # группировка полей на форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'project', 'tags')
        }),
        ('Статус и приоритет', {
            'fields': ('status', 'priority', 'due_date')
        }),
        ('Авторы и даты', {
            'fields': ('author', 'editor', 'created_at', 'updated_at', 'completed_at_display')
        }),
    )

    # кастомные методы для отображения
    @admin.display(description='Проект')
    def project_link(self, obj):
        if obj.project:
            from django.urls import reverse
            url = reverse('admin:tasks_project_change', args=[obj.project.id])
            return format_html('<a href="{}">{}</a>', url, obj.project.title)
        return '-'

    @admin.display(description='Автор')
    def author_link(self, obj):
        if obj.author:
            from django.urls import reverse
            url = reverse('admin:users_user_change', args=[obj.author.id])
            return format_html('<a href="{}">{}</a>', url, obj.author.username)
        return '-'

    @admin.display(description='Статус', ordering='status')
    def status_display(self, obj):
        colors = {
            'todo': '#e74c3c',  # Красный
            'in_progress': '#f39c12',  # Оранжевый
            'done': '#27ae60',  # Зеленый
            'backlog': '#95a5a6',  # Серый
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Приоритет', ordering='priority')
    def priority_display(self, obj):
        icons = {1: '🔥', 2: '⚠️', 3: '📌', 4: '📄', 5: '💤'}
        return f"{icons.get(obj.priority, '?')} {obj.priority}"

    @admin.display(description='Дата завершения')
    def completed_at_display(self, obj):
        if obj.completed_at:
            return obj.completed_at.strftime('%d.%m.%Y %H:%M')
        return 'Не завершена'

    # Сохранение редактора при изменении
    def save_model(self, request, obj, form, change):
        if change:  # Если редактируем существующую задачу
            obj.editor = request.user
        super().save_model(request, obj, form, change)


# админ класс для комментов
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_content', 'task_link', 'author_link', 'created_at')
    list_display_links = ('id', 'short_content')
    list_filter = ('created_at', 'task__project')
    search_fields = ('content', 'author__username', 'task__title')
    raw_id_fields = ('task', 'author')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 25

    @admin.display(description='Комментарий')
    def short_content(self, obj):
        if len(obj.content) > 50:
            return f'{obj.content[:50]}...'
        return obj.content

    @admin.display(description='Задача')
    def task_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:tasks_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)

    @admin.display(description='Автор')
    def author_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:users_user_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.username)


# админ класс для истории изменений (пока что история изменений не реализована)
@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_link', 'action_display', 'changed_by_link', 'changed_at')
    list_display_links = ('id',)
    list_filter = ('action', 'changed_at')
    search_fields = ('task__title', 'changed_by__username')
    raw_id_fields = ('task', 'changed_by')
    readonly_fields = ('task', 'changes', 'action', 'changed_by', 'changed_at')
    date_hierarchy = 'changed_at'
    list_per_page = 25

    @admin.display(description='Задача')
    def task_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:tasks_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)

    @admin.display(description='Действие')
    def action_display(self, obj):
        actions = {
            'created': ('📝', 'Создано'),
            'updated': ('✏️', 'Обновлено'),
            'deleted': ('🗑️', 'Удалено'),
        }
        icon, text = actions.get(obj.action, ('?', obj.action))
        return f"{icon} {text}"

    @admin.display(description='Кем изменено')
    def changed_by_link(self, obj):
        if obj.changed_by:
            from django.urls import reverse
            url = reverse('admin:users_user_change', args=[obj.changed_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.changed_by.username)
        return 'Система'