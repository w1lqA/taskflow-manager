from django.db import models
from django.conf import settings

class Project(models.Model):
    """проект (категория) для группировки задач."""
    title = models.CharField('Название', max_length=255)
    color = models.CharField('Цвет', max_length=7, default='#3498db')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name='Владелец'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        db_table = 'tasks_project'
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Tag(models.Model):
    """тег для категоризации задач."""
    name = models.CharField('Название', max_length=100, unique=True)
    color = models.CharField('Цвет', max_length=7, default='#95a5a6')

    class Meta:
        db_table = 'tasks_tag'
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name

class Task(models.Model):
    """дефолтная сущность - задача."""
    STATUS_CHOICES = [
        ('todo', 'К выполнению'),
        ('in_progress', 'В процессе'),
        ('done', 'Выполнено'),
        ('backlog', 'Отложено'),
    ]

    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo'
    )
    priority = models.IntegerField('Приоритет', default=3)  # 1-5, где 1 - высший
    due_date = models.DateTimeField('Срок выполнения', null=True, blank=True)
    completed_at = models.DateTimeField('Дата завершения', null=True, blank=True)
    
    # связи
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Проект'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name='Автор'
    )
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='edited_tasks',
        verbose_name='Редактор',
        null=True,
        blank=True
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='tasks',
        verbose_name='Теги',
        blank=True
    ) #многие ко многим
    
    # Временные метки
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        db_table = 'tasks_task'
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['author', 'created_at']),
        ]


    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'


class Comment(models.Model):
    """комментарий к задаче."""
    content = models.TextField('Текст комментария')
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Задача'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        db_table = 'tasks_comment'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']

    def __str__(self):
        return f'Комментарий от {self.author} к задаче #{self.task.id}'

class TaskHistory(models.Model):
    ACTION_CHOICES = [
        ('created', 'Создано'),
        ('updated', 'Обновлено'),
        ('deleted', 'Удалено'),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Задача'
    )
    changes = models.JSONField('Изменения', default=dict)
    action = models.CharField('Действие', max_length=20, choices=ACTION_CHOICES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Кем изменено'
    )
    changed_at = models.DateTimeField('Дата изменения', auto_now_add=True)

    class Meta:
        db_table = 'tasks_taskhistory'
        verbose_name = 'История задачи'
        verbose_name_plural = 'Истории задач'
        ordering = ['-changed_at']

    def __str__(self):
        return f'Изменение #{self.id} задачи "{self.task.title}"'