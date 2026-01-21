from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_api import TaskViewSet, ProjectViewSet

# создаём роутер для API
router = DefaultRouter()
router.register(r'api/tasks', TaskViewSet, basename='task')
router.register(r'api/projects', ProjectViewSet, basename='project')

urlpatterns = [
    # старые URL для веб-интерфейса
    path('', views.task_list, name='task_list'),
    
    # AJAX endpoints для модалок
    path('task/<int:pk>/detail/', views.task_detail_modal, name='task_detail_modal'),
    path('task/form/', views.task_form_modal, name='task_form_modal'),
    path('task/<int:pk>/form/', views.task_form_modal, name='task_form_modal_edit'),
    path('task/<int:pk>/delete-modal/', views.task_delete_modal, name='task_delete_modal'),
    
    # AJAX endpoints для действий
    path('task/create/', views.task_create, name='task_create_ajax'),
    path('task/<int:pk>/update/', views.task_update, name='task_update_ajax'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete_ajax'),
    
    # подключаем API роутер
    path('', include(router.urls)),
]