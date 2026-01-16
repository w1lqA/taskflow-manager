from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    
    # ajax эндпоинты для модалок
    path('task/<int:pk>/detail/', views.task_detail_modal, name='task_detail_modal'),
    path('task/form/', views.task_form_modal, name='task_form_modal'),
    path('task/<int:pk>/form/', views.task_form_modal, name='task_form_modal_edit'),
    path('task/<int:pk>/delete-modal/', views.task_delete_modal, name='task_delete_modal'),
    
    # ajax эндпоинты для действий
    path('task/create/', views.task_create, name='task_create_ajax'),
    path('task/<int:pk>/update/', views.task_update, name='task_update_ajax'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete_ajax'),
]