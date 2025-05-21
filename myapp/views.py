from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
from django.contrib.auth.hashers import check_password
from django.contrib.sessions.models import Session

def index(request):
    return render(request, 'index.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password_hash):
                request.session['user_id'] = user.id
                request.session['user_role'] = user.role
                request.session['user_name'] = user.name

                if user.role == 'manager':
                    return redirect('manager_dashboard')
                else:
                    return redirect('member_dashboard')
            else:
                messages.error(request, 'Invalid email or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
    return render(request, 'login.html')

def user_logout(request):
    request.session.flush()
    return redirect('user_login')

from django.shortcuts import render, redirect
from .models import Task, User
from django.db.models import Count, Q
from django.utils.dateparse import parse_date

def manager_dashboard(request):
    if request.session.get('user_role') != 'manager':
        return redirect('user_login')

    user_id = request.session.get('user_id')
    
    # Filters from GET params
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assigned_user_filter = request.GET.get('assigned_user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    tasks = Task.objects.filter(created_by_id=user_id)

    # Search by title, description or assigned user's name
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(assigned_to__name__icontains=search)
        )

    # Filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if assigned_user_filter:
        tasks = tasks.filter(assigned_to__id=assigned_user_filter)
    if date_from:
        try:
            date_from_parsed = parse_date(date_from)
            if date_from_parsed:
                tasks = tasks.filter(created_at__date__gte=date_from_parsed)
        except:
            pass
    if date_to:
        try:
            date_to_parsed = parse_date(date_to)
            if date_to_parsed:
                tasks = tasks.filter(created_at__date__lte=date_to_parsed)
        except:
            pass

    # Stats for pie chart (task status counts)
    status_stats = tasks.values('status').annotate(count=Count('status'))
    status_data = {stat['status']: stat['count'] for stat in status_stats}

    # For dropdowns
    assigned_users = User.objects.filter(role='member')

    context = {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'assigned_users': assigned_users,
        'status_data': status_data,
        'search': search,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'assigned_user_filter': assigned_user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'user_name': request.session.get('user_name'),
    }
    return render(request, 'manager_dashboard.html', context)


from django.shortcuts import render, redirect
from .models import Task
from django.db.models import Count, Q
from django.utils.dateparse import parse_date

from datetime import date, timedelta

def member_dashboard(request):
    if request.session.get('user_role') != 'member':
        return redirect('user_login')

    user_id = request.session.get('user_id')

    # Filters from GET params
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    tasks = Task.objects.filter(assigned_to_id=user_id)

    # Search by title or description
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    # Filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if date_from:
        try:
            date_from_parsed = parse_date(date_from)
            if date_from_parsed:
                tasks = tasks.filter(created_at__date__gte=date_from_parsed)
        except:
            pass
    if date_to:
        try:
            date_to_parsed = parse_date(date_to)
            if date_to_parsed:
                tasks = tasks.filter(created_at__date__lte=date_to_parsed)
        except:
            pass

    # Stats for pie chart (task status counts)
    status_stats = tasks.values('status').annotate(count=Count('status'))
    status_data = {stat['status']: stat['count'] for stat in status_stats}

    # Detect overdue and near due tasks
    today = date.today()
    near_due_threshold = today + timedelta(days=3)

    overdue_tasks = tasks.filter(deadline__lt=today)
    near_due_tasks = tasks.filter(deadline__gte=today, deadline__lte=near_due_threshold)

    context = {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'status_data': status_data,
        'search': search,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'date_from': date_from,
        'date_to': date_to,
        'user_name': request.session.get('user_name'),
        'overdue_tasks': overdue_tasks,
        'near_due_tasks': near_due_tasks,
    }
    return render(request, 'member_dashboard.html', context)





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Task, User
from django.utils import timezone

def manager_required(view_func):
    # Simple decorator for manager role check
    def wrapper(request, *args, **kwargs):
        if request.session.get('user_role') != 'manager':
            return redirect('user_login')
        return view_func(request, *args, **kwargs)
    return wrapper

@manager_required
def task_list(request):
    tasks = Task.objects.filter(created_by_id=request.session.get('user_id'))
    return render(request, 'task_list.html', {'tasks': tasks})

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Task, User

@manager_required
def task_create(request):
    members = User.objects.filter(role='member')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        status = request.POST.get('status')
        deadline = request.POST.get('deadline') or None
        assigned_to_id = request.POST.get('assigned_to') or None

        assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None

        task = Task.objects.create(
            title=title,
            description=description,
            priority=priority,
            status=status,
            deadline=deadline,
            assigned_to=assigned_to,
            created_by=User.objects.get(id=request.session.get('user_id')),
            created_at=timezone.now()
        )

        # Send email notification to assigned member if assigned
        if assigned_to and assigned_to.email:
            subject = 'New Task Assigned'
            message = (
                f"Hello {assigned_to.name},\n\n"
                f"You have been assigned a new task:\n"
                f"Title: {task.title}\n"
                f"Description: {task.description or 'No description provided.'}\n"
                f"Priority: {task.priority}\n"
                f"Deadline: {task.deadline if task.deadline else 'No deadline'}\n\n"
                "Please log in to your account to check the task details.\n\n"
                "Best regards,\nTask Management System"
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [assigned_to.email]

            try:
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                # Log error or notify admin, but don't block task creation
                print(f"Email sending failed: {e}")

        messages.success(request, 'Task created successfully.')
        return redirect('task_list')

    return render(request, 'task_create.html', {'members': members})


@manager_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id, created_by_id=request.session.get('user_id'))
    members = User.objects.filter(role='member')
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.priority = request.POST.get('priority')
        task.status = request.POST.get('status')
        deadline = request.POST.get('deadline') or None
        task.deadline = deadline
        assigned_to_id = request.POST.get('assigned_to') or None
        task.assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
        task.save()
        messages.success(request, 'Task updated successfully.')
        return redirect('task_list')

    return render(request, 'task_edit.html', {'task': task, 'members': members})

@manager_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, created_by_id=request.session.get('user_id'))
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('task_list')
    return render(request, 'task_delete.html', {'task': task})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Task
from django.contrib.auth.decorators import login_required

def member_tasks(request):
    if request.session.get('user_role') != 'member':
        return redirect('user_login')

    user_id = request.session.get('user_id')
    tasks = Task.objects.filter(assigned_to_id=user_id)

    return render(request, 'member_tasks.html', {'tasks': tasks, 'user_name': request.session.get('user_name')})

def update_task_status(request, task_id):
    if request.session.get('user_role') != 'member':
        return redirect('user_login')

    user_id = request.session.get('user_id')
    task = get_object_or_404(Task, id=task_id, assigned_to_id=user_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES).keys():
            task.status = new_status
            task.save()
            messages.success(request, 'Task status updated successfully.')
            return redirect('member_tasks')
        else:
            messages.error(request, 'Invalid status value.')

    return render(request, 'update_task_status.html', {
        'task': task,
        'status_choices': Task.STATUS_CHOICES,
        'user_name': request.session.get('user_name')
    })
