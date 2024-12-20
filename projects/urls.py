from django.urls import path
from . import views
from .views import upload_file, view_files, project_calendar, project_events, add_event, delete_file

app_name = 'projects'
urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.create_project, name='create_project'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/add_issue/', views.create_issue, name='add_issue'),
    path('<int:project_pk>/issue/<int:issue_pk>/', views.issue_detail, name='issue_detail'), 
    path('<int:pk>/request_join/', views.request_join, name='request_join'),
    path('<int:pk>/leave/', views.leave_project, name='leave_project'),
    path('<int:pk>/approve_join/<int:user_id>/', views.approve_join_request, name='approve_join_request'),
    path('<int:pk>/deny_join/<int:user_id>/', views.deny_join_request, name='deny_join_request'),
    path('<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('upload/<int:project_id>/', upload_file, name='upload_file'),
    path('projects/<int:project_id>/view_files/', view_files, name='view_files'),
    path('project/<int:project_id>/calendar/', project_calendar, name='project_calendar'),
    path('project/<int:project_id>/events/', project_events, name='project_events'),
    path('project/<int:project_id>/add_event/', add_event, name='add_event'),
    path('<int:project_pk>/issue/<int:issue_pk>/', views.issue_detail, name='issue_detail'),
    path('projects/<int:project_id>/delete_file/<str:file_key>/', views.delete_file, name='delete_file'),

]