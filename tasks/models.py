from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords
import os

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
    
    #Временные метки
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    history = HistoricalRecords()

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




class Attachment(models.Model):
    """вложение к задаче (файлы, изображения)"""
    FILE_TYPES = [
        ('image', 'Изображение'),
        ('document', 'Документ'),
        ('archive', 'Архив'),
        ('other', 'Другое'),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Задача'
    )
    file = models.FileField('Файл', upload_to='attachments/%Y/%m/%d/')
    file_type = models.CharField('Тип файла', max_length=20, choices=FILE_TYPES)
    original_name = models.CharField('Оригинальное имя', max_length=255)
    file_size = models.IntegerField('Размер файла (байт)', default=0)
    
    # кто загрузил
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_attachments',
        verbose_name='Кто загрузил'
    )
    
    # временные метки
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)
    description = models.CharField('Описание', max_length=255, blank=True)
    
    class Meta:
        db_table = 'tasks_attachment'
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['task', 'file_type']),
        ]
    
    def __str__(self):
        return f"Вложение: {self.original_name} (к задаче #{self.task_id})"
    
    def save(self, *args, **kwargs):
        # сохраняем оригинальное имя файла
        if not self.original_name and self.file:
            self.original_name = os.path.basename(self.file.name)
        
        # определяем тип файла по расширению
        if self.file and not self.file_type:
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                self.file_type = 'image'
            elif ext in ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx']:
                self.file_type = 'document'
            elif ext in ['.zip', '.rar', '.7z', '.tar.gz']:
                self.file_type = 'archive'
            else:
                self.file_type = 'other'
        
        # сохраняем размер файла
        if self.file:
            try:
                self.file_size = self.file.size
            except (OSError, ValueError):
                self.file_size = 0
        
        super().save(*args, **kwargs)
    
    def get_file_icon(self):
        """возвращает иконку в зависимости от типа файла"""
        icons = {
            'image': '🖼️',
            'document': '📄',
            'archive': '🗜️',
            'other': '📎',
        }
        return icons.get(self.file_type, '📎')
    
    def get_readable_size(self):
        """возвращает размер файла в читаемом формате"""
        if self.file_size < 1024:
            return f"{self.file_size} Б"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} КБ"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} МБ"