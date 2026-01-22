from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Отправляет напоминания о задачах'
    
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='На сколько дней вперед проверять задачи (по умолчанию: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать задачи без отправки уведомлений'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        today = timezone.now().date()
        target_date = today + timedelta(days=days)
        
        self.stdout.write(f"Поиск задач на {target_date.strftime('%d.%m.%Y')}")
        
        # Находим задачи, срок которых наступает через указанное количество дней
        upcoming_tasks = Task.objects.filter(
            due_date__date=target_date,  # срок выполнения в указанный день
            status__in=['todo', 'in_progress'],  # только невыполненные
            due_date__isnull=False  # только задачи со сроком
        ).select_related('author', 'project')
        
        task_count = upcoming_tasks.count()
        self.stdout.write(f"Найдено задач: {task_count}")
        
        if task_count == 0:
            self.stdout.write(self.style.WARNING('Нет задач для напоминаний'))
            return
        
        # Группируем по пользователям
        tasks_by_user = {}
        for task in upcoming_tasks:
            if task.author not in tasks_by_user:
                tasks_by_user[task.author] = []
            tasks_by_user[task.author].append(task)
        
        # Формируем уведомления
        for user, tasks in tasks_by_user.items():
            self.stdout.write(f"\nПользователь: {user.username} ({user.email})")
            self.stdout.write(f"Задач на {target_date.strftime('%d.%m.%Y')}: {len(tasks)}")
            
            for i, task in enumerate(tasks, 1):
                self.stdout.write(
                    f"  {i}. {task.title} "
                    f"(приоритет: {task.priority}, проект: {task.project.title if task.project else 'без проекта'})"
                )
            
            # В реальном проекте здесь была бы отправка email
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(f"  → Уведомление отправлено"))
            else:
                self.stdout.write(self.style.WARNING(f"  → DRY RUN: уведомление НЕ отправлено"))
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nОбработка завершена. Задач: {task_count}, "
                f"пользователей: {len(tasks_by_user)}"
            )
        )
    
    def send_email_reminder(self, user, tasks, target_date):
        """Отправка email с напоминанием (заглушка)"""
        # Логируем вместо отправки
        logger.info(
            f"Напоминание для {user.email}: "
            f"{len(tasks)} задач на {target_date.strftime('%d.%m.%Y')}"
        )
    
    def build_email_message(self, tasks, target_date):
        """Создание текста email"""
        lines = [
            f"У вас {len(tasks)} задач, срок которых наступает {target_date.strftime('%d.%m.%Y')}:",
            ""
        ]
        
        for i, task in enumerate(tasks, 1):
            lines.append(
                f"{i}. {task.title} "
                f"(приоритет: {task.priority}, проект: {task.project.title if task.project else 'без проекта'})"
            )
        
        lines.extend([
            "",
            "---",
            "С уважением,",
            "Система управления задачами TaskFlow"
        ])
        
        return "\n".join(lines)