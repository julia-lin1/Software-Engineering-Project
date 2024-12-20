from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.ForeignKey(User, related_name='owned_projects', on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    members = models.ManyToManyField(User, related_name='joined_projects', blank=True)

    def is_member(self, user):
        return self.members.filter(id=user.id).exists()

    def __str__(self):
        return self.name

class Issue(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('completed', 'Completed')
    ]
    title = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    project = models.ForeignKey('Project', related_name='issues', on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class JoinRequest(models.Model):
    project = models.ForeignKey(Project, related_name='join_requests', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='join_requests', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} requests to join {self.project.name}"


class FileUpload(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    keywords = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')

    def __str__(self):
        return self.title


class CalendarEvent(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_meeting = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Comment(models.Model):
    issue = models.ForeignKey(Issue, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:20]}"