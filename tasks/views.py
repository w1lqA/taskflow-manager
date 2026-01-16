from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task

# === READ: Список всех задач ===
@login_required
def task_list(request):
    """Страница со списком всех задач текущего пользователя."""
    tasks = Task.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'tasks/task_list.html', {'tasks': tasks})

# === READ: Детали одной задачи ===
@login_required
def task_detail(request, pk):
    """Страница с деталями конкретной задачи."""
    task = get_object_or_404(Task, pk=pk, author=request.user)
    return render(request, 'tasks/task_detail.html', {'task': task})

# === CREATE: Создание новой задачи ===
@login_required
def task_create(request):
    """Страница создания новой задачи."""
    if request.method == 'POST':
        # Создаем задачу из данных формы
        task = Task.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            status=request.POST.get('status', 'todo'),
            priority=int(request.POST.get('priority', 3)),
            due_date=request.POST.get('due_date') or None,
            author=request.user,
            project_id=request.POST.get('project') or None
        )
        messages.success(request, f'Задача "{task.title}" создана!')
        return redirect('task_detail', pk=task.pk)
    
    # GET запрос - показываем пустую форму
    from .models import Project
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'tasks/task_form.html', {
        'form_title': 'Создать задачу',
        'projects': projects
    })

# === UPDATE: Редактирование задачи ===
@login_required
def task_update(request, pk):
    """Страница редактирования существующей задачи."""
    task = get_object_or_404(Task, pk=pk, author=request.user)
    
    if request.method == 'POST':
        # Обновляем задачу
        task.title = request.POST.get('title')
        task.description = request.POST.get('description', '')
        task.status = request.POST.get('status', 'todo')
        task.priority = int(request.POST.get('priority', 3))
        task.due_date = request.POST.get('due_date') or None
        task.project_id = request.POST.get('project') or None
        task.save()
        
        messages.success(request, f'Задача "{task.title}" обновлена!')
        return redirect('task_detail', pk=task.pk)
    
    # GET запрос - показываем форму с данными задачи
    from .models import Project
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'tasks/task_form.html', {
        'form_title': 'Редактировать задачу',
        'task': task,
        'projects': projects
    })

# === DELETE: Удаление задачи ===
@login_required
def task_confirm_delete(request, pk):
    """Страница подтверждения удаления задачи."""
    task = get_object_or_404(Task, pk=pk, author=request.user)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Задача "{task_title}" удалена!')
        return redirect('task_list')
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})