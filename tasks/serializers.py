from rest_framework import serializers
from django.utils import timezone
from .models import Task, Project, Tag, Comment, Attachment
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectSerializer(serializers.ModelSerializer):
    # явно объявляем поле owner, чтобы видеть имя пользователя, а не id
    owner_username = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Project
        fields = ['id', 'title', 'color', 'owner', 'owner_username', 'created_at', 'updated_at']
        read_only_fields = ['owner', 'created_at', 'updated_at']
    
    def validate_title(self, value):
        # проверяем, что название не пустое
        if not value.strip():
            raise serializers.ValidationError('название проекта не может быть пустым')
        return value

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']


class AttachmentSerializer(serializers.ModelSerializer):
    """Сериализатор для вложений"""
    uploaded_by_username = serializers.ReadOnlyField(source='uploaded_by.username')
    file_url = serializers.FileField(source='file', read_only=True)
    file_icon = serializers.ReadOnlyField(source='get_file_icon')
    readable_size = serializers.ReadOnlyField(source='get_readable_size')
    
    class Meta:
        model = Attachment
        fields = [
            'id',
            'task',
            'file',
            'file_url',
            'file_type',
            'original_name',
            'file_size',
            'readable_size',
            'file_icon',
            'uploaded_by',
            'uploaded_by_username',
            'uploaded_at',
            'updated_at',
            'description'
        ]
        read_only_fields = [
            'uploaded_by',
            'uploaded_at',
            'updated_at',
            'file_type',
            'original_name',
            'file_size'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user
        return super().create(validated_data)


class TaskSerializer(serializers.ModelSerializer):
    # поля только для чтения
    project = ProjectSerializer(read_only=True)
    author_username = serializers.ReadOnlyField(source='author.username')
    tags = TagSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    attachments = AttachmentSerializer(many=True, read_only=True)
    
    # поля только для записи
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source='project',
        write_only=True,
        required=False,
        allow_null=True
    )
    tags_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'priority', 'due_date', 'completed_at',
            
            # для чтения
            'project', 'author_username', 'tags', 'attachments', 
            
            # для записи
            'project_id', 'tags_ids',
            
            'author', 'editor', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'author', 'editor', 'created_at', 'updated_at', 
            'completed_at', 'status_display', 'attachments' 
        ]
    
    # ВАЛИДАЦИЯ 1: проверка приоритета (должен быть 1-5)
    def validate_priority(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('приоритет должен быть от 1 до 5')
        return value
    
    # ВАЛИДАЦИЯ 2: проверка даты окончания (не может быть в прошлом при создании)
    def validate_due_date(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError('срок выполнения не может быть в прошлом')
        return value
    
    # ВАЛИДАЦИЯ 3: проверка уникальности названия для пользователя
    def validate_title(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # проверяем, нет ли уже задачи с таким названием у пользователя
            existing_task = Task.objects.filter(
                title=value,
                author=request.user
            ).exists()
            
            # если задача уже существует (и мы её редактируем, а не создаём)
            if existing_task and (not self.instance or self.instance.title != value):
                raise serializers.ValidationError('у вас уже есть задача с таким названием')
        
        return value
    
    # автоматически устанавливаем автора при создании
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)
    
    # автоматически обновляем редактора при изменении
    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            instance.editor = request.user
        return super().update(instance, validated_data)

# сериализатор для комментариев
class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'task', 'author', 'author_username', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'date_joined']
        read_only_fields = ['date_joined']
