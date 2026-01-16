from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Кастомизированная модель пользователя с аватаром."""
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/%Y/%m/%d/',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'users_user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username