from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from tasks.views_api import TaskViewSet, ProjectViewSet, AttachmentViewSet

# создаём роутер для API
router = DefaultRouter()
router.register(r'api/tasks', TaskViewSet, basename='task')
router.register(r'api/projects', ProjectViewSet, basename='project')
router.register(r'api/attachments', AttachmentViewSet, basename='attachment')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # веб-интерфейс задач (HTML)
    path('tasks/', include('tasks.urls')), 
    
    path('', include(router.urls)), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)