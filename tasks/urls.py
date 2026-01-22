from django.urls import path
from . import views

urlpatterns = [
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
    
    # Вложения
    path('task/<int:pk>/upload-attachment/', views.upload_attachment, name='upload_attachment'),
    path('task/<int:pk>/upload-multiple-attachments/', views.upload_multiple_attachments, name='upload_multiple_attachments'),
    path('attachment/<int:pk>/delete/', views.delete_attachment, name='delete_attachment'),
]