from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('member/dashboard/', views.member_dashboard, name='member_dashboard'),
    path('', views.index, name='index'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('member/tasks/', views.member_tasks, name='member_tasks'),
    path('member/tasks/<int:task_id>/update-status/', views.update_task_status, name='update_task_status'),
]
