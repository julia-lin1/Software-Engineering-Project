from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import Project, Issue, JoinRequest, FileUpload, CalendarEvent  # Import JoinRequest
from .forms import ProjectForm, IssueForm, FileUploadForm, CalendarEventForm, CommentForm
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth import login, logout 
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
import boto3
from .forms import CustomUserCreationForm
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth import login
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt


def project_list(request):
    if request.user.is_authenticated:
        # Get projects the user owns or is a member of
        my_projects = (Project.objects.filter(owner=request.user) | Project.objects.filter(members=request.user)).distinct()
        # Get projects the user is not involved in
        available_projects = Project.objects.exclude(id__in=my_projects.values_list('id', flat=True))
    else:
        # Anonymous users see all available projects
        my_projects = Project.objects.none()
        available_projects = Project.objects.all()

    context = {
        'my_projects': my_projects,
        'available_projects': available_projects,
        'is_common_user': request.user.groups.filter(name="CommonUser").exists() if request.user.is_authenticated else False,
        'is_manager': request.user.groups.filter(name="Manager").exists() if request.user.is_authenticated else False,
    }

    return render(request, 'projects/project_list.html', context) 



def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    is_owner = False
    is_member = False
    is_admin = False
    open_issues = []
    completed_issues = []
    total_issues = 0
    completed_issues_count = 0
    progress = 0
    accepted_members = []

    if request.user.is_authenticated:
        is_owner = request.user == project.owner
        is_member = project.members.filter(id=request.user.id).exists()
        is_admin = request.user.groups.filter(name="Manager").exists()
        open_issues = project.issues.filter(status='open')
        completed_issues = project.issues.filter(status='completed')

        total_issues = project.issues.count()
        completed_issues_count = completed_issues.count()
        if total_issues > 0:
            progress = (completed_issues_count / total_issues * 100)
        accepted_members = project.members.all()
    context = {
        'project': project,
        'owner': project.owner,
        'open_issues': open_issues if request.user.is_authenticated else [],
        'completed_issues': completed_issues if request.user.is_authenticated else [],
        'total_issues': total_issues,
        'is_owner': is_owner,
        'is_member': is_member,
        'is_admin': is_admin,
        'join_requests': project.join_requests.all() if is_owner else None,
        'progress': progress,
        'accepted_members': accepted_members,
    }
    return render(request, "projects/project_detail.html", context)

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.members.add(request.user)
            return redirect('projects:project_list')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form, 'is_admin': request.user.groups.filter(name="Manager").exists()})

@login_required
def create_issue(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.project = project
            issue.created_by = request.user
            if not issue.status:  
                issue.status = 'open'
            issue.save()
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = IssueForm()
        form.fields['assigned_to'].queryset = project.members.all()
    
    return render(request, 'projects/issue_form.html', {'form': form, 'project': project})


@login_required
def request_join(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_member(request.user):
        JoinRequest.objects.get_or_create(project=project, user=request.user)
    return redirect('projects:project_detail', pk=project.pk)


@login_required
def leave_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.members.all():
        return HttpResponseForbidden("You are not a member of this project.")

    if request.user == project.owner:
        return HttpResponseForbidden("The project owner cannot leave their own project.")

    project.members.remove(request.user)

    return redirect('projects:project_list')


@login_required
def approve_join_request(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    user = get_object_or_404(User, id=user_id)
    join_request = get_object_or_404(JoinRequest, project=project, user=user)
    project.members.add(user)
    join_request.delete()
    return redirect('projects:project_detail', pk=project.pk)


@login_required
def deny_join_request(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    user = get_object_or_404(User, id=user_id)
    join_request = get_object_or_404(JoinRequest, project=project, user=user)
    join_request.delete()
    return redirect('projects:project_detail', pk=project.pk)

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


@user_passes_test(lambda u: u.groups.filter(name="Manager").exists())
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    project.delete()
    return redirect('projects:project_list')


@login_required
def issue_detail(request, project_pk, issue_pk):
    project = get_object_or_404(Project, pk=project_pk)
    issue = get_object_or_404(Issue, pk=issue_pk, project=project)
    comments = issue.comments.all().order_by('-created_date')
    comment_form = CommentForm()

    if request.method == 'POST':
        if 'mark_complete' in request.POST:
            issue.status = 'completed'
            issue.save()
            return redirect('projects:project_detail', pk=project.pk)

        if 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.issue = issue
                comment.user = request.user
                comment.save()
                return redirect('projects:issue_detail', project_pk=project.pk, issue_pk=issue.pk)

    context = {
        'issue': issue,
        'project': project,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'projects/issue_detail.html', context)


@login_required
@login_required
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if (not request.user.groups.filter(name="Manager").exists()) and request.user != project.owner:
        return HttpResponseForbidden("You are not allowed to delete this project.")

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    folder = f"{project.name}/"
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder)
        if 'Contents' in response:
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete})
    except Exception as e:
        return HttpResponse(f"Error deleting project files from S3: {str(e)}")

    FileUpload.objects.filter(project=project).delete()
    project.delete()

    return redirect('projects:project_list')


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect('projects:project_list') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def upload_file(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            keywords = form.cleaned_data['keywords']
            file = request.FILES['file']

            s3 = boto3.client('s3')

            try:
                s3_path = f"{project.name}/{file.name}"
                s3.upload_fileobj(
                    file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_path,
                    ExtraArgs={
                        'ContentType': file.content_type,
                        'Metadata': {
                            'title': title,
                            'description': description,
                            'keywords': keywords,
                        }
                    }
                )
                FileUpload.objects.create(
                    project=project,
                    title=title,
                    description=description,
                    keywords=keywords,
                    file=s3_path
                )

                return redirect('projects:view_files', project_id=project.id)
            except Exception as e:
                return HttpResponse(f'Error uploading file: {str(e)}')
        else:
            return HttpResponse('Invalid form.')
    else:
        form = FileUploadForm()
    return render(request, 'projects/file_upload.html', {'form': form, 'project': project})


def view_files(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    uploaded_files = []

    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=f"{project.name}/")
        if 'Contents' in response:
            file_objects = FileUpload.objects.filter(project=project)
            file_dict = {file.file.name.split('/')[-1]: file for file in file_objects}

            for item in response['Contents']:
                file_name = item['Key'].split('/')[-1]
                if file_name in file_dict:
                    file_metadata = file_dict[file_name]
                    file_url = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket_name, 'Key': item['Key']},
                        ExpiresIn=3600  # URL expires in 1 hour
                    )
                    uploaded_files.append({
                        'file_name': file_name,
                        'file_url': file_url,
                        'title': file_metadata.title,
                        'timestamp': file_metadata.timestamp,
                        'description': file_metadata.description,
                        'keywords': file_metadata.keywords
                    })


    except Exception as e:
        return HttpResponse(f'Error retrieving files: {str(e)}')
    return render(request, 'projects/view_files.html', {'uploaded_files': uploaded_files, 'project': project})


@login_required
def delete_file(request, project_id, file_key):
    project = get_object_or_404(Project, id=project_id)
    if not (request.user == project.owner or project.is_member(request.user) or request.user.groups.filter(name="Manager").exists()):
        return JsonResponse({'error': 'You do not have permission to delete this file.'}, status=403)

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    s3_key = f"{project.name}/{file_key}"
    s3.delete_object(Bucket=bucket_name, Key=s3_key)
    FileUpload.objects.filter(project=project, file__endswith=file_key).delete()
    return view_files(request, project_id)
    

def some_view(request):
    timezone.activate(request.session.get('django_timezone', 'UTC'))


@login_required
def project_calendar(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, 'projects/calendar.html', {'project': project})

@login_required
def project_events(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    events = []

    for issue in project.issues.all():
        if issue.due_date:
            events.append({
                'title': f"Issue: {issue.title}",
                'start': issue.due_date.isoformat(),
                'end': issue.due_date.isoformat(),
                'backgroundColor': 'blue',
                'borderColor': 'blue',
                'textColor': 'white',
            })

    for event in project.calendarevent_set.all():
        events.append({
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat(),
            'backgroundColor': 'green' if event.is_meeting else 'red',
            'borderColor': 'green' if event.is_meeting else 'red',
            'textColor': 'white',
        })

    return JsonResponse(events, safe=False)

@login_required
def add_event(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.project = project
            event.save()
            return redirect('projects:project_calendar', project_id=project.id)
    else:
        form = CalendarEventForm()
    return render(request, 'projects/add_event.html', {'form': form, 'project': project})



def custom_logout(request):
    if request.method == 'GET':
        logout(request)
        return redirect('/')  # Redirect to the homepage or desired URL
    return redirect('accounts:login')  # Fallback for unsupported methods

@csrf_exempt  
def google_callback(request):
    token = request.POST.get("credential")
    if not token:
        return redirect('/accounts/login/')  # Redirect if token is missing

    try:
        # Verify the token using Google's library
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
        email = idinfo.get("email")
        name = idinfo.get("name")

        # Check if the user exists, or create a new one
        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "first_name": name}
        )

        # Log the user in
        login(request, user)
        return redirect('projects:project_list')  # Redirect to your main page

    except ValueError as e:
        # Handle invalid token
        print(f"Google token verification failed: {e}")
        return redirect('/accounts/login/')
    
def login_view(request):
    return render(request, 'login.html', {'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID})