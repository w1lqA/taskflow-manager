from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Task, Project

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
    """детали задачи """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        task = get_object_or_404(Task, pk=pk, author=request.user)
        html = render_to_string('tasks/task_detail_content.html', {'task': task})
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
    # создание через ajax
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            task = Task.objects.create(
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                status=request.POST.get('status', 'todo'),
                priority=int(request.POST.get('priority', 3)),
                due_date=request.POST.get('due_date') or None,
                author=request.user,
                project_id=request.POST.get('project') or None
            )
            return JsonResponse({
                'success': True,
                'message': f'Задача "{task.title}" создана!',
                'task_id': task.id
            })
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