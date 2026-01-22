from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin
from import_export.admin import ExportMixin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.formats.base_formats import CSV, XLSX

from .models import Project, Tag, Task, Comment, Attachment


class TaskResource(resources.ModelResource):
    """Ресурс для экспорта задач"""
    
    # Кастомные поля
    project_title = fields.Field(
        column_name='Проект',
        attribute='project',
        widget=ForeignKeyWidget(Project, 'title')
    )
    
    author_name = fields.Field(
        column_name='Автор',
        attribute='author',
        widget=ForeignKeyWidget(settings.AUTH_USER_MODEL, 'username')
    )
    
    # 1. Кастомный метод для статуса
    status_display = fields.Field(
        column_name='Статус',
        attribute='status'
    )
    
    # 2. Кастомный метод для даты выполнения
    due_date_formatted = fields.Field(
        column_name='Дата выполнения'
    )
    
    # 3. Кастомный метод для приоритета
    priority_category = fields.Field(
        column_name='Категория приоритета'
    )
    
    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'status_display', 
            'priority', 'priority_category', 'due_date_formatted',
            'project_title', 'author_name', 'created_at', 'updated_at'
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False
    
    # 1 для фильтрации queryset (только задачи с высоким приоритетом)
    def get_export_queryset(self, request):
        """Экспортировать только задачи с высоким приоритетом (1-2)"""
        queryset = super().get_export_queryset(request)
        return queryset.filter(priority__lte=2)
    
    # 2. для преобразования даты
    def dehydrate_due_date_formatted(self, task):
        """Преобразовать поле due_date в формат DD-MM-YYYY"""
        if task.due_date:
            return task.due_date.strftime('%d-%m-%Y')
        return 'Нет срока'
    
    # 3. для преобразования статуса
    def dehydrate_status_display(self, task):
        """Преобразовать поле status в читаемый формат"""
        status_map = {
            'todo': 'К выполнению',
            'in_progress': 'В процессе',
            'done': 'Выполнено',
            'backlog': 'Отложено'
        }
        return status_map.get(task.status, task.status)
    
    # доп.кастомный метод
    def dehydrate_priority_category(self, task):
        """Категория приоритета"""
        if task.priority == 1:
            return 'Критический'
        elif task.priority == 2:
            return 'Высокий'
        elif task.priority == 3:
            return 'Средний'
        elif task.priority == 4:
            return 'Низкий'
        else:
            return 'Минимальный'
    
    # форматирование дат создания/обновления
    def dehydrate_created_at(self, task):
        if task.created_at:
            return task.created_at.strftime('%d-%m-%Y %H:%M')
        return ''
    
    def dehydrate_updated_at(self, task):
        if task.updated_at:
            return task.updated_at.strftime('%d-%m-%Y %H:%M')
        return ''

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


class AttachmentInline(admin.TabularInline):
    """Inline для отображения вложений внутри задачи."""
    model = Attachment
    extra = 0
    readonly_fields = ('file_preview', 'file_size_display', 'uploaded_by', 'uploaded_at')
    fields = ('file', 'file_preview', 'description', 'file_size_display', 'uploaded_by', 'uploaded_at')
    verbose_name = 'Вложение'
    verbose_name_plural = 'Вложения'
    
    def file_preview(self, obj):
        if obj.file_type == 'image' and obj.file:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.file.url
            )
        return obj.get_file_icon()
    file_preview.short_description = 'Превью'
    
    def file_size_display(self, obj):
        return obj.get_readable_size()
    file_size_display.short_description = 'Размер'


# админ класс для задач (дефолтный)
@admin.register(Task)
class TaskAdmin(ExportMixin, SimpleHistoryAdmin):
    resource_class = TaskResource
    formats = [XLSX, CSV]

    # Существующие настройки остаются
    list_display = (
        'id',
        'title',
        'project_link',
        'author_link',
        'status',
        'status_display',
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

    actions = ['export_selected_objects']
    
    def export_selected_objects(self, request, queryset):
        """Кастомное действие для экспорта выбранных задач"""
        # Используем встроенный функционал ExportMixin
        return self.export_action(request, queryset)
    export_selected_objects.short_description = "Экспортировать выбранные задачи в Excel"


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




@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """админка для вложений"""
    list_display = (
        'id',
        'file_icon_display',
        'original_name_display',
        'task_link',
        'uploaded_by_link',
        'file_type_display',
        'file_size_display',
        'uploaded_at'
    )
    list_display_links = ('id', 'file_icon_display')
    list_filter = ('file_type', 'uploaded_at', 'task__project')
    search_fields = ('original_name', 'description', 'task__title')
    raw_id_fields = ('task', 'uploaded_by')
    readonly_fields = (
        'file_size',
        'uploaded_at',
        'updated_at',
        'file_preview',
        'file_type',
        'original_name'
    )
    date_hierarchy = 'uploaded_at'
    list_per_page = 25
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('task', 'uploaded_by', 'description')
        }),
        ('Файл', {
            'fields': ('file', 'file_preview', 'original_name', 'file_type')
        }),
        ('Информация о файле', {
            'fields': ('file_size', 'uploaded_at', 'updated_at')
        }),
    )
    
    # кастомные методы для отображения
    
    @admin.display(description='Файл')
    def file_icon_display(self, obj):
        return f"{obj.get_file_icon()} {obj.original_name[:30]}..."
    
    @admin.display(description='Имя файла')
    def original_name_display(self, obj):
        if len(obj.original_name) > 30:
            return f"{obj.original_name[:30]}..."
        return obj.original_name
    
    @admin.display(description='Задача')
    def task_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:tasks_task_change', args=[obj.task.id])
        return format_html('<a href="{}">#{}</a>', url, obj.task.id)
    
    @admin.display(description='Кто загрузил')
    def uploaded_by_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:users_user_change', args=[obj.uploaded_by.id])
        return format_html('<a href="{}">{}</a>', url, obj.uploaded_by.username)
    
    @admin.display(description='Тип файла')
    def file_type_display(self, obj):
        colors = {
            'image': '#e74c3c',
            'document': '#3498db',
            'archive': '#f39c12',
            'other': '#95a5a6',
        }
        color = colors.get(obj.file_type, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_file_type_display()
        )
    
    @admin.display(description='Размер')
    def file_size_display(self, obj):
        return obj.get_readable_size()
    
    @admin.display(description='Превью')
    def file_preview(self, obj):
        if obj.file_type == 'image' and obj.file:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.file.url
            )
        elif obj.file_type == 'document':
            return '📄 Документ'
        elif obj.file_type == 'archive':
            return '🗜️ Архив'
        else:
            return '📎 Файл'
    file_preview.short_description = 'Предпросмотр'
    
    # автоматически устанавливаем uploaded_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # только при создании
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
