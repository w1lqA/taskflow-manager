from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Task, Project, Attachment
import os

# основной view (главная страница)
@login_required
def task_list(request):
    """Главная страница со списком задач."""
    tasks = Task.objects.filter(author=request.user).order_by('-created_at')
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'projects': projects
    })

# ajax views для модалок 
@login_required
def task_detail_modal(request, pk):
    """детали задачи С ВЛОЖЕНИЯМИ"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        task = get_object_or_404(Task, pk=pk, author=request.user)
        attachments = task.attachments.all()  # явно получаем вложения
        html = render_to_string('tasks/task_detail_content.html', {
            'task': task,
            'attachments': attachments  # передаем в template
        })
        return JsonResponse({'html': html})
    return redirect('task_list')


@login_required
def task_form_modal(request, pk=None):
    """форма создания/редактирования задачи"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        task = None
        if pk:
            task = get_object_or_404(Task, pk=pk, author=request.user)
        
        projects = Project.objects.filter(owner=request.user)
        html = render_to_string('tasks/task_form_content.html', {
            'task': task,
            'projects': projects
        })
        return JsonResponse({'html': html})
    return redirect('task_list')

@login_required
def task_delete_modal(request, pk):
    """подтверждение удаления."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        task = get_object_or_404(Task, pk=pk, author=request.user)
        html = render_to_string('tasks/task_delete_content.html', {'task': task})
        return JsonResponse({'html': html})
    return redirect('task_list')

# обработка форм 
@login_required
def task_create(request):
    # создание через ajax С ФАЙЛАМИ
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Создаем задачу
            task = Task.objects.create(
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                status=request.POST.get('status', 'todo'),
                priority=int(request.POST.get('priority', 3)),
                due_date=request.POST.get('due_date') or None,
                author=request.user,
                project_id=request.POST.get('project') or None
            )
            
            # Обрабатываем файлы если есть
            files = request.FILES.getlist('files')
            uploaded_files = []
            
            for file_obj in files:
                if file_obj:
                    attachment = Attachment.objects.create(
                        task=task,
                        file=file_obj,
                        uploaded_by=request.user,
                        description=request.POST.get('description', '')
                    )
                    uploaded_files.append(attachment.original_name)
            
            response_data = {
                'success': True,
                'message': f'Задача "{task.title}" создана!',
                'task_id': task.id
            }
            
            if uploaded_files:
                response_data['files_message'] = f'Загружено файлов: {len(uploaded_files)}'
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def task_update(request, pk):
    # обновление задачи через ajax.
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            task = get_object_or_404(Task, pk=pk, author=request.user)
            task.title = request.POST.get('title')
            task.description = request.POST.get('description', '')
            task.status = request.POST.get('status', 'todo')
            task.priority = int(request.POST.get('priority', 3))
            task.due_date = request.POST.get('due_date') or None
            task.project_id = request.POST.get('project') or None
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Задача "{task.title}" обновлена!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def task_delete(request, pk):
    # удаление черещ ajax
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            task = get_object_or_404(Task, pk=pk, author=request.user)
            task_title = task.title
            task.delete()
            return JsonResponse({
                'success': True,
                'message': f'Задача "{task_title}" удалена!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def upload_multiple_attachments(request, pk):
    """загрузка нескольких вложений к задаче через AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            task = get_object_or_404(Task, pk=pk, author=request.user)
            
            files = request.FILES.getlist('files')
            if not files:
                return JsonResponse({
                    'success': False, 
                    'error': 'Файлы не выбраны'
                })
            
            uploaded_attachments = []
            for file_obj in files:
                if file_obj:
                    attachment = Attachment.objects.create(
                        task=task,
                        file=file_obj,
                        uploaded_by=request.user,
                        description=request.POST.get('description', '')
                    )
                    uploaded_attachments.append({
                        'id': attachment.id,
                        'original_name': attachment.original_name,
                        'file_url': attachment.file.url,
                        'file_icon': attachment.get_file_icon(),
                        'readable_size': attachment.get_readable_size(),
                        'uploaded_at': attachment.uploaded_at.strftime('%d.%m.%Y %H:%M'),
                    })
            
            return JsonResponse({
                'success': True,
                'message': f'Загружено {len(uploaded_attachments)} файлов',
                'attachments': uploaded_attachments
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })


@login_required
def upload_attachment(request, pk):
    """загрузка вложения к задаче через AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            task = get_object_or_404(Task, pk=pk, author=request.user)
            
            if 'file' not in request.FILES:
                return JsonResponse({
                    'success': False, 
                    'error': 'Файл не выбран'
                })
            
            file_obj = request.FILES['file']
            
            # создаем вложение
            attachment = Attachment.objects.create(
                task=task,
                file=file_obj,
                uploaded_by=request.user,
                description=request.POST.get('description', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Файл "{attachment.original_name}" загружен',
                'attachment': {
                    'id': attachment.id,
                    'original_name': attachment.original_name,
                    'file_url': attachment.file.url,
                    'file_type': attachment.file_type,  # добавляем тип файла
                    'file_icon': attachment.get_file_icon(),
                    'readable_size': attachment.get_readable_size(),
                    'uploaded_at': attachment.uploaded_at.strftime('%d.%m.%Y %H:%M'),
                    'description': attachment.description
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })

@login_required
def delete_attachment(request, pk):
    """удаление вложения через AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Ищем вложение по ID и проверяем, что пользователь владелец задачи
            attachment = get_object_or_404(Attachment, pk=pk)
            
            # Проверяем, что текущий пользователь - автор задачи
            if attachment.task.author != request.user:
                return JsonResponse({
                    'success': False, 
                    'error': 'У вас нет прав на удаление этого файла'
                })
            
            attachment_name = attachment.original_name
            file_path = attachment.file.path if attachment.file else None
            
            # Удаляем файл и запись
            attachment.delete()
            
            # Если файл существует на диске - удаляем
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass  # Не критично если файл не удалился
            
            return JsonResponse({
                'success': True,
                'message': f'Файл "{attachment_name}" удален'
            })
            
        except Attachment.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Файл не найден'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })